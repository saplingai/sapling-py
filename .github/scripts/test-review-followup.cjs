// Run: node .github/scripts/test-review-followup.cjs
// Requires Python 3 + PyYAML to read the workflow; no GitHub calls or agent runs.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');

const workflowPath = path.resolve(__dirname, '../workflows/claude-respond-to-codex.yml');
const parsed = spawnSync('python3', ['-c',
  'import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1]))))', workflowPath],
  {encoding: 'utf8'});
assert.equal(parsed.status, 0, parsed.stderr);
const workflow = JSON.parse(parsed.stdout);
const job = workflow.jobs.claude;
const prepareScript = job.steps.find(step => step.id === 'prepare').with.script;
const publishScript = job.steps.at(-1).with.script;
const structured = publishScript.includes('CLAUDE_STRUCTURED_OUTPUT');
const readOnly = publishScript.includes('result.resolutions');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const head = 'a'.repeat(40);
const newerHead = 'b'.repeat(40);
const codex = 'chatgpt-codex-connector';
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'review-followup-test-'));

function thread(id, author = codex, resolved = false) {
  return {id, isResolved: resolved, comments: {
    totalCount: 1, nodes: [{id: `comment-${id}`, updatedAt: '2026-10-16T23:41:09Z',
      author: {login: author}}]
  }};
}

function summary(state = {}) {
  return '<!-- codex-pull-request-review-summary -->\n' +
    '<!-- codex-review-state:v1 ' + JSON.stringify({code_review: {
      commit_sha: head, status: 'completed', has_unresolved_findings: true, ...state
    }}) + ' -->';
}

function fixture(overrides = {}) {
  return {
    eventName: 'issue_comment',
    payload: {issue: {number: 848, pull_request: {}}, comment: {id: 17}},
    pr: {state: 'open', draft: false, head: {sha: head, repo: {full_name: 'example/service'}}},
    liveComment: {user: {login: `${codex}[bot]`}, body: summary()},
    comments: [], threads: [thread('old-finding')], pageSize: 100,
    result: {head_sha: head, summary: 'Verified the fix; see commit and test evidence.',
      resolutions: []},
    workKey: 'input-snapshot',
    ...overrides
  };
}

async function run(script, f = fixture()) {
  const outputs = {};
  const posted = [];
  const cursors = [];
  const logs = [];
  const mutations = [];
  const resultPath = path.join(temp, 'result.json');
  const contextPath = path.join(temp, 'context.json');
  fs.writeFileSync(contextPath, JSON.stringify({head_sha: head,
    threads: f.reviewedThreads || f.threads}));
  if (f.result === null) fs.rmSync(resultPath, {force: true});
  else fs.writeFileSync(resultPath, JSON.stringify(f.result));
  const previous = {...process.env};
  Object.assign(process.env, {THREAD_QUERY: job.env.THREAD_QUERY,
    FOLLOWUP_RESULT: resultPath, PR_NUMBER: '848', FOLLOWUP_KEY: f.workKey,
    FOLLOWUP_CONTEXT: contextPath,
    CLAUDE_STRUCTURED_OUTPUT: f.result === null ? '' : JSON.stringify(f.result)});
  const github = {
    rest: {
      pulls: {listReviewComments: 'listReviewComments', get: async args => {
        assert.equal(args.pull_number, 848);
        return {data: f.pr};
      }},
      issues: {
        getComment: async () => ({data: f.liveComment}),
        listComments: 'listComments',
        createComment: async args => { posted.push(args); return {data: {id: 99}}; }
      }
    },
    paginate: async (method, args) => {
      if (method === 'listReviewComments') return [];
      assert.equal(method, 'listComments');
      assert.equal(args.per_page, 100);
      return f.comments;
    },
    graphql: async (query, args) => {
      if (query.includes('mutation(')) {
        mutations.push({query, args});
        const finding = f.threads.find(t => t.id === args.id);
        assert.ok(finding, 'mutation must address an existing thread');
        if (query.includes('addPullRequestReviewThreadReply')) {
          return {addPullRequestReviewThreadReply: {comment: {id: 'reply'}}};
        }
        assert.ok(query.includes('resolveReviewThread'));
        finding.isResolved = !f.failResolution;
        return {resolveReviewThread: {thread: {id: finding.id, isResolved: finding.isResolved}}};
      }
      assert.equal(query, job.env.THREAD_QUERY);
      assert.equal(args.owner, 'example');
      assert.equal(args.repo, 'service');
      cursors.push(args.cursor);
      const offset = Number(args.cursor || 0);
      const end = offset + f.pageSize;
      return {repository: {pullRequest: {reviewThreads: {
        nodes: f.threads.slice(offset, end),
        pageInfo: {hasNextPage: end < f.threads.length, endCursor: String(end)}
      }}}};
    }
  };
  try {
    const execute = new AsyncFunction('github', 'context', 'core', 'require', script);
    await execute(github, {repo: {owner: 'example', repo: 'service'},
      eventName: f.eventName, payload: f.payload},
    {setOutput: (key, value) => { outputs[key] = value; }, info: msg => logs.push(msg)}, require);
    return {outputs, posted, cursors, logs, mutations};
  } finally {
    for (const key of Object.keys(process.env)) if (!(key in previous)) delete process.env[key];
    Object.assign(process.env, previous);
  }
}

const tests = [];
const test = (name, fn) => tests.push([name, fn]);

test('completed summary on the current head handles old unresolved findings', async () => {
  const {outputs} = await run(prepareScript);
  assert.equal(outputs.run, 'true');
  assert.equal(outputs.number, 848);
  assert.equal(outputs.head_sha, head);
});

test('live summary wins over a stale queued event', async () => {
  const f = fixture();
  f.payload.comment.body = summary({status: 'in_progress'});
  assert.equal((await run(prepareScript, f)).outputs.run, 'true');
});

test('running, stale, clean, malformed, and impersonated summaries are ignored', async () => {
  for (const body of [summary({status: 'in_progress'}), summary({commit_sha: newerHead}),
    summary({has_unresolved_findings: false}), '<!-- codex-review-state:v1 broken -->']) {
    const f = fixture();
    f.liveComment.body = body;
    assert.equal((await run(prepareScript, f)).outputs.run, undefined);
  }
  const f = fixture();
  f.liveComment.user.login = 'someone-else';
  assert.equal((await run(prepareScript, f)).outputs.run, undefined);
});

test('closed, draft, fork, and deleted-head PRs never start the agent', async () => {
  for (const change of [pr => { pr.state = 'closed'; }, pr => { pr.draft = true; },
    pr => { pr.head.repo.full_name = 'outsider/service'; }, pr => { pr.head.repo = null; }]) {
    const f = fixture();
    change(f.pr);
    assert.equal((await run(prepareScript, f)).outputs.run, undefined);
  }
});

test('thread pagination finds a Gemini finding beyond resolved and human threads', async () => {
  const f = fixture({eventName: 'pull_request_review', pageSize: 1,
    threads: [thread('done', codex, true), thread('human', 'alice'),
      thread('gemini', 'gemini-code-assist[bot]')]});
  const result = await run(prepareScript, f);
  assert.equal(result.outputs.run, 'true');
  assert.deepEqual(result.cursors, [null, '1', '2']);
});

test('submitted reviews with only resolved or human threads do not start work', async () => {
  const f = fixture({eventName: 'pull_request_review',
    threads: [thread('done', codex, true), thread('human', 'alice')]});
  assert.equal((await run(prepareScript, f)).outputs.run, undefined);
});

test('duplicate submitted/summary events are skipped, but new evidence is handled', async () => {
  const f = fixture();
  const first = await run(prepareScript, f);
  f.comments.push({user: {login: 'github-actions[bot]'},
    body: `<!-- review-followup:v1 ${first.outputs.work_key} -->`});
  assert.equal((await run(prepareScript, f)).outputs.run, undefined);
  f.eventName = 'pull_request_review';
  assert.equal((await run(prepareScript, f)).outputs.run, undefined);
  f.threads[0].comments.totalCount += 1;
  assert.equal((await run(prepareScript, f)).outputs.run, 'true');
  f.threads[0].comments.totalCount -= 1;
  f.threads[0].comments.nodes[0].updatedAt = '2026-10-17T00:00:00Z';
  assert.equal((await run(prepareScript, f)).outputs.run, 'true');
});

test('untrusted comments cannot suppress follow-up', async () => {
  const f = fixture();
  const first = await run(prepareScript, f);
  f.comments.push({user: {login: 'someone-else'},
    body: `<!-- review-followup:v1 ${first.outputs.work_key} -->`});
  assert.equal((await run(prepareScript, f)).outputs.run, 'true');
});

test('manual dispatch can retry deferred work with a prior completion marker', async () => {
  const f = fixture();
  const first = await run(prepareScript, f);
  f.comments.push({user: {login: 'github-actions[bot]'},
    body: `<!-- review-followup:v1 ${first.outputs.work_key} -->`});
  f.eventName = 'workflow_dispatch';
  f.payload = {inputs: {pull_request: '848'}};
  assert.equal((await run(prepareScript, f)).outputs.run, 'true');
  f.payload.inputs.pull_request = 'invalid';
  await assert.rejects(run(prepareScript, f), /valid pull request number/);
});

test('only verified current heads with a result can publish', async () => {
  await assert.rejects(run(publishScript, fixture({result: null})),
    structured ? /Unexpected end/ : /ENOENT/);
  await assert.rejects(run(publishScript, fixture({result: {head_sha: head, summary: ''}})),
    /nonempty summary/);
  const f = fixture();
  f.pr.head.sha = newerHead;
  await assert.rejects(run(publishScript, f), /stale verification/);
});

test('resolved bot findings request a fresh review while human threads stay untouched', async () => {
  const f = fixture({threads: [thread('done', codex, true), thread('human', 'alice')]});
  const {posted} = await run(publishScript, f);
  assert.equal(posted.length, 1);
  assert.match(posted[0].body, /@codex review/);
  assert.match(posted[0].body, /Unresolved Codex\/Gemini threads: 0/);
  assert.ok(posted[0].body.includes(`<!-- codex-rereview:v1 ${head} -->`));
});

test('remaining bot findings on later pages prevent a fresh review request', async () => {
  const f = fixture({pageSize: 1,
    threads: [thread('done', codex, true), thread('deferred', 'gemini-code-assist')]});
  const {posted, cursors} = await run(publishScript, f);
  assert.deepEqual(cursors, [null, '1']);
  assert.doesNotMatch(posted[0].body, /@codex review/);
  assert.match(posted[0].body, /Unresolved Codex\/Gemini threads: 1/);
});

test('a head gets at most one explicit request, even on manual retries', async () => {
  const f = fixture({threads: [thread('done', codex, true)]});
  f.comments.push({user: {login: 'github-actions[bot]'},
    body: `<!-- codex-rereview:v1 ${head} -->`});
  assert.doesNotMatch((await run(publishScript, f)).posted[0].body, /@codex review/);
  assert.equal((await run(prepareScript, f)).outputs.run, undefined);
});

test('a clean Codex result and Gemini-only PRs do not request another review', async () => {
  const f = fixture({threads: [thread('done', codex, true)], comments: [
    {user: {login: `${codex}[bot]`}, body: summary({has_unresolved_findings: false})}
  ]});
  assert.doesNotMatch((await run(publishScript, f)).posted[0].body, /@codex review/);
  f.threads = [thread('gemini', 'gemini-code-assist', true)];
  f.comments = [];
  assert.doesNotMatch((await run(publishScript, f)).posted[0].body, /@codex review/);
});

test('findings arriving during a run remain eligible for the queued event', async () => {
  const f = fixture();
  f.workKey = (await run(prepareScript, f)).outputs.work_key;
  f.threads.push(thread('arrived-during-run'));
  const {posted} = await run(publishScript, f);
  f.comments.push({user: {login: 'github-actions[bot]'}, body: posted[0].body});
  assert.equal((await run(prepareScript, f)).outputs.run, 'true');
});

if (readOnly) {
  test('read-only assessment resolves a verified bot thread through the workflow', async () => {
    const f = fixture();
    f.result.resolutions = [{thread_id: 'old-finding', evidence: 'Verified at the current SHA.'}];
    const {mutations, posted} = await run(publishScript, f);
    assert.equal(mutations.length, 2);
    assert.match(mutations[0].query, /addPullRequestReviewThreadReply/);
    assert.match(mutations[1].query, /resolveReviewThread/);
    assert.match(posted[0].body, /Unresolved Codex\/Gemini threads: 0/);
  });

  test('read-only resolution rejects human, unknown, and changed threads', async () => {
    for (const id of ['human', 'unknown', 'changed']) {
      const f = fixture({threads: [thread('human', 'alice'), thread('changed')]});
      f.reviewedThreads = JSON.parse(JSON.stringify(f.threads));
      f.threads[1].comments.totalCount = 2;
      f.result.resolutions = [{thread_id: id, evidence: 'Claimed fix'}];
      await assert.rejects(run(publishScript, f), /reviewed bot thread|changed during assessment/);
    }
  });

  test('read-only resolution requires GitHub to confirm success', async () => {
    const f = fixture({failResolution: true});
    f.result.resolutions = [{thread_id: 'old-finding', evidence: 'Verified fix'}];
    await assert.rejects(run(publishScript, f), /did not confirm/);
  });
}

(async () => {
  try {
    for (const [name, fn] of tests) {
      await fn();
      console.log(`PASS ${name}`);
    }
    console.log(`${tests.length} workflow regression tests passed`);
  } finally {
    fs.rmSync(temp, {recursive: true, force: true});
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
