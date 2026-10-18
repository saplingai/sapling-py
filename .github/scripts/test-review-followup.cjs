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
if (parsed.error) throw parsed.error;
assert.equal(parsed.status, 0, parsed.stderr);
const workflow = JSON.parse(parsed.stdout);
const job = workflow.jobs.claude;
const prepareScript = job.steps.find(step => step.id === 'prepare').with.script;
const publishJob = workflow.jobs.publish;
const publishStep = publishJob.steps.find(step => step.id === 'publish');
const publishScript = publishStep.with.script;
const trust = job.steps.find(step => step.id === 'trust');
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
  const contextPath = path.join(temp, 'context.json');
  fs.writeFileSync(contextPath, JSON.stringify({head_sha: head,
    threads: f.reviewedThreads || f.threads}));
  const previous = {...process.env};
  Object.assign(process.env, {THREAD_QUERY: workflow.env.THREAD_QUERY,
    PR_NUMBER: '848', FOLLOWUP_KEY: f.workKey,
    FOLLOWUP_CONTEXT: contextPath,
    FOLLOWUP_SNAPSHOT: JSON.stringify({head_sha: head, threads: f.reviewedThreads || f.threads}),
    CLAUDE_STRUCTURED_OUTPUT: f.rawResult ?? (f.result === null ? '' : JSON.stringify(f.result))});
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
      if (f.moveHeadBeforePublish) f.pr.head.sha = newerHead;
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
      assert.equal(query, workflow.env.THREAD_QUERY);
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
    /no structured review result/);
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


// Exercise the real trust-gate script and composite expressions, not a fixture file
// fabricated on Claude's behalf. GitHub's own expression syntax is linted separately.
async function runTrust({explicitToken = false, changed = false, error = null} = {}) {
  const previous = {...process.env};
  const outputs = {};
  const warnings = [];
  const summaries = [];
  const refs = [];
  Object.assign(process.env, {USE_GITHUB_TOKEN: String(explicitToken),
    WORKFLOW_SHA: head, DEFAULT_BRANCH: 'master'});
  const summary = {
    addHeading: () => summary,
    addRaw: message => { summaries.push(message); return summary; },
    write: async () => {}
  };
  try {
    await new AsyncFunction('github', 'context', 'core', trust.with.script)({rest: {repos: {
      getContent: async ({ref, path: file}) => {
        assert.equal(file, '.github/workflows/claude-respond-to-codex.yml');
        refs.push(ref);
        if (error) throw error;
        return {data: {sha: changed && ref === head ? 'changed-blob' : 'trusted-blob'}};
      }
    }}}, {repo: {owner: 'example', repo: 'service'}}, {
      setOutput: (key, value) => { outputs[key] = value; },
      warning: message => warnings.push(message), summary
    });
    return {outputs, warnings, summaries, refs};
  } finally {
    for (const key of Object.keys(process.env)) if (!(key in previous)) delete process.env[key];
    Object.assign(process.env, previous);
  }
}

test('changed App workflows explicitly skip without running or publishing', async () => {
  const result = await runTrust({changed: true});
  assert.equal(result.outputs.run, undefined);
  assert.match(result.warnings[0], /No findings were verified or resolved/);
  assert.match(result.summaries[0], /workflow_dispatch/);
  assert.deepEqual(result.refs, [head, 'master']);
  for (const step of job.steps.slice(job.steps.indexOf(trust) + 1)) {
    assert.equal(step.if, "steps.trust.outputs.run == 'true'", step.name);
  }
});

test('matching App workflows run and existing explicit-token policy is preserved', async () => {
  assert.equal((await runTrust()).outputs.run, 'true');
  const result = await runTrust({explicitToken: true, changed: true});
  assert.equal(result.outputs.run, 'true');
  assert.equal(result.refs.length, 0);
  assert.equal(trust.env.USE_GITHUB_TOKEN,
    String(Boolean(job.steps.find(step => step.id === 'claude').with['github-token'])));
  await assert.rejects(runTrust({error: new Error('GitHub unavailable')}), /GitHub unavailable/);
});

test('missing, malformed, and null output cannot publish a completed review', async () => {
  for (const rawResult of ['', ' ', 'not json', 'null', '[]']) {
    await assert.rejects(run(publishScript, fixture({rawResult})),
      /no structured review result|invalid structured JSON|nonempty summary/);
  }
});

test('a push during publishing prevents a stale summary and review request', async () => {
  await assert.rejects(run(publishScript, fixture({moveHeadBeforePublish: true})),
    /PR changed before publishing/);
});

test('structured output is wired from the successful Claude attempt to the publisher', () => {
  const actionPath = path.resolve(__dirname, '../actions/claude-with-api-fallback/action.yml');
  const parsedAction = spawnSync('python3', ['-c',
    'import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1]))))', actionPath],
    {encoding: 'utf8'});
  if (parsedAction.error) throw parsedAction.error;
  assert.equal(parsedAction.status, 0, parsedAction.stderr);
  const action = JSON.parse(parsedAction.stdout);
  const claude = job.steps.find(step => step.id === 'claude');
  const publish = publishStep;
  assert.equal(claude.uses, './.github/actions/claude-with-api-fallback');
  assert.match(claude.with['claude-args'], /--json-schema/);
  assert.equal(publish.env.CLAUDE_STRUCTURED_OUTPUT,
    "${{ needs.claude.outputs.structured_output }}");
  assert.equal(job.outputs.structured_output, "${{ steps.claude.outputs['structured-output'] }}");
  assert.doesNotMatch(fs.readFileSync(workflowPath, 'utf8'), /FOLLOWUP_RESULT/);
  const fallback = action.runs.steps.find(step => step.id === 'api');
  const output = action.outputs['structured-output'].value;
  const evaluate = (expression, steps, inputs, cancelled = false) =>
    new Function('steps', 'inputs', 'cancelled', 'contains',
      'return (' + expression.replace(/^\s*\$\{\{|\}\}\s*$/g, '') + ');')(
      steps, inputs, () => cancelled, (value, part) => value.includes(part));
  const inputs = {'api-key': 'test-key', 'claude-args': claude.with['claude-args']};
  const steps = {
    max_plan: {outcome: 'success', outputs: {structured_output: ''}},
    api: {outcome: 'skipped', outputs: {structured_output: ''}}
  };
  // Reproduce the upstream action's successful no-op from the failed run.
  assert.equal(evaluate(fallback.if, steps, inputs), true);
  assert.equal(evaluate(output, steps, inputs), '');
  assert.equal(evaluate(fallback.if, steps, {...inputs, 'api-key': ''}), false);
  assert.equal(evaluate(fallback.if, steps, inputs, true), false);
  steps.max_plan.outcome = 'failure';
  steps.max_plan.outputs.structured_output = '{"summary":"incomplete OAuth output"}';
  assert.equal(evaluate(fallback.if, steps, inputs), true);
  assert.equal(evaluate(output, steps, inputs), '');
  steps.api = {outcome: 'success', outputs: {structured_output: '{"summary":"API result"}'}};
  assert.equal(evaluate(output, steps, inputs), steps.api.outputs.structured_output);
  steps.max_plan = {outcome: 'success', outputs: {structured_output: '{"summary":"OAuth result"}'}};
  assert.equal(evaluate(fallback.if, steps, inputs), false);
  steps.api = {outcome: 'skipped', outputs: {structured_output: ''}};
  assert.equal(evaluate(output, steps, inputs), steps.max_plan.outputs.structured_output);
  steps.max_plan.outputs.structured_output = '';
  assert.equal(evaluate(fallback.if, steps, {...inputs, 'claude-args': '--model test'}), false);
});

test('resolution permission is isolated from Claude and repository code', () => {
  assert.equal(job.permissions.contents, 'read');
  assert.equal(publishJob.permissions.contents, 'write');
  assert.equal(publishJob.permissions['pull-requests'], 'write');
  assert.equal(publishJob.needs, 'claude');
  assert.equal(publishJob.if,
    "needs.claude.result == 'success' && needs.claude.outputs.run == 'true'");
  assert.equal(publishJob.steps.length, 1);
  assert.equal(publishStep.uses,
    'actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3');
  assert.equal(publishStep.run, undefined);
  assert.doesNotMatch(publishScript, /exec\(|spawn\(|eval\(|new Function|readFileSync/);
  assert.equal(job.steps.find(step => step.name === 'Checkout repository')
    .with['persist-credentials'], false);
  const agent = job.steps.find(step => step.id === 'claude');
  assert.doesNotMatch(agent.with['claude-args'], /Read,Edit|Write|,Bash"/);
});

test('the publisher receives the prepared snapshot across the job boundary', async () => {
  const f = fixture();
  const {outputs} = await run(prepareScript, f);
  assert.deepEqual(JSON.parse(outputs.snapshot), {head_sha: head, threads: f.threads});
  assert.equal(job.outputs.snapshot, "${{ steps.prepare.outputs.snapshot }}");
  assert.equal(publishStep.env.FOLLOWUP_SNAPSHOT, "${{ needs.claude.outputs.snapshot }}");
  assert.equal(publishStep.env.PR_NUMBER, "${{ needs.claude.outputs.number }}");
  assert.equal(publishStep.env.FOLLOWUP_KEY, "${{ needs.claude.outputs.work_key }}");
  assert.equal(publishStep.env.FOLLOWUP_CONTEXT, undefined);
});

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
