# CLAUDE.md — sapling-py

Guidance for Claude Code (and other coding agents — see `AGENTS.md`) when working in
this repo: `saplingai/sapling-py`, default branch `master`, published to PyPI as
`sapling-py`. **This repository is public.** Nothing in this file, the code, tests,
docs, or commit history may contain API keys, customer data, internal hostnames, or
internal process details.

## What this is

A thin Python wrapper over the Sapling HTTP API (https://sapling.ai/docs). One class,
`SaplingClient` (`sapling/client.py`), maps Python methods to `POST` endpoints under
`https://api.sapling.ai/api/v1/`. Runtime dependency: `requests` only. Declared
`python_requires>=3.7` in `setup.py` — keep the code compatible with that (or bump it
deliberately in the same PR).

| Path | Purpose |
|------|---------|
| `sapling/client.py` | `SaplingClient` + `SaplingError`. All HTTP goes through `_request()`. |
| `sapling/version.py` | Single source of truth for the version (read by `pyproject.toml` and `docs/source/conf.py`). |
| `pyproject.toml` / `uv.lock` | Standard package metadata and reproducible uv environment. |
| `sapling/__init__.py` | Public exports: `SaplingClient`, `SaplingError`, `__version__`. |
| `test/test_client.py` | pytest suite; HTTP mocked with `responses`, no network. |
| `docs/source/` | Sphinx + MyST docs built by Read the Docs (https://sapling.readthedocs.io/). `api.md` autodocs `SaplingClient`. |
| `docs/requirements.txt` | Fully pinned docs build deps (Dependabot watches this file). |
| `README.md` | Doubles as the PyPI long description (`pyproject.toml` references it). |
| `.github/workflows/` | AI PR-review automation only; no test CI yet. |

## Commands

```bash
# uv workflow
uv sync --extra test
uv run --extra test python -m pytest test/ -q

# pip workflow
python -m pip install -e '.[test]'      # editable install + pytest + responses
python -m pytest test/ -q               # ~0.1s, 17 tests, no network

# Docs with pip — mirror the Read the Docs flow (fail_on_warning is on, so use -W)
python -m venv .venv-docs && .venv-docs/bin/pip install -r docs/requirements.txt -e .
.venv-docs/bin/sphinx-build -W -b html docs/source docs/build/html

# Docs with uv
uv venv .venv-docs
uv pip install --python .venv-docs/bin/python -r docs/requirements.txt -e .
.venv-docs/bin/sphinx-build -W -b html docs/source docs/build/html
```

There is no linter config in the repo. Style: 4-space indent, single quotes, max 100
char lines, snake_case, stdlib → third-party → local import groups.

## Client conventions (`sapling/client.py`)

- Every method builds a `data` dict with `'key': self.api_key` plus required fields,
  then calls `self._request(url, data)`. `_request` raises `SaplingError(status_code,
  body)` on non-2xx, returns parsed JSON, or `None` for an empty/non-JSON body
  (accept/reject endpoints return nothing).
- Optional parameters are only added to the body when `is not None`. Exception:
  `auto_apply` defaults to `False` and is always sent on `edits`/`spellcheck` — a test
  guards this; don't "fix" it without a deliberate decision.
- Methods that take `session_id` fall back to `self.default_session_id` (a `str`
  UUID generated per client). Always send a `str`, never a `uuid.UUID`.
- Docstrings are Sphinx field lists (`:param x:` / `:type x:` / `:rtype:` /
  `:return:`) and are rendered verbatim by autodoc into the public API reference.
  Malformed RST breaks the `-W` docs build. Language/option lists in docstrings are
  user-facing documentation — keep them accurate.
- `hostname` / `pathname` overrides exist for self-hosted deployments; keep the
  `self.url_endpoint = hostname + pathname` composition intact.

## Adding or changing an endpoint method

1. Confirm the route exists in the public HTTP API docs (https://sapling.ai/docs)
   before adding a method — don't infer routes by analogy (e.g. there is an
   `accept_complete` but no `reject_complete` endpoint).
2. Add the method following the conventions above, with a complete docstring.
3. Add a test in `test/test_client.py`: register the mocked route with `responses`,
   assert the request body (use `_last_request_body()`), and assert the return value.
   Use the `test_single_text_endpoints` parametrize list for simple `{key, text}`
   endpoints. Use the `'a' * 32` placeholder key — never a real one.
4. If it's user-facing, mention it in `README.md` and keep
   `docs/source/usage.md` in sync with the README quickstart (they duplicate it).
5. Bump `sapling/version.py` in the same PR: patch for fixes, minor for new methods.

## Release (PyPI)

Releases are currently manual.

1. Merge the version bump to `master`. Read the Docs rebuilds automatically.
2. From a clean checkout of the merged commit:
   ```bash
   rm -rf build dist *.egg-info          # stale artifacts are gitignored but still present locally

   # uv
   uv build && uvx twine check dist/*
   uv publish                            # needs a PyPI token; run from an interactive terminal

   # pip / PyPA build tooling
   python -m pip install build twine
   python -m build && python -m twine check dist/*
   python -m twine upload dist/*         # needs PyPI credentials + 2FA; run from an interactive terminal
   ```
3. Verify with either `python -m pip index versions sapling-py` or
   `uv run --with sapling-py==<version> --no-project -- python -c
   "from sapling import SaplingClient"`.

Check `python -m pip index versions sapling-py` before bumping — `version.py` should
match the latest published release at rest, and be ahead of it only on an unreleased
branch.

## PR review automation (`.github/`)

- `codex-api-review.yml`: an allowlisted maintainer commenting `/codex-api-review` on
  a PR triggers a Codex review, posted as a PR review.
- `claude-respond-to-codex.yml`: when the Codex or Gemini bot submits a review on a PR
  opened from a branch in this repo (not a fork), Claude (via
  `.github/actions/claude-with-api-fallback`) evaluates each finding and posts a
  verdict comment. It does not modify code.

Both workflows check out the **trusted default branch** and treat PR contents as
untrusted input; they read `AGENTS.md` → `CLAUDE.md` from `master`. When editing them,
keep the bot-login / not-from-a-fork / login-allowlist gates, `persist-credentials:
false`, and the read-only tool allowlist — this is a public repo and those runs spend
credits. Don't gate on `author_association`: org members with private membership are
reported as `CONTRIBUTOR`/`NONE` in webhook payloads, so such a gate never passes.

## Public-repo hygiene

- No secrets anywhere: keys come from the caller (`SaplingClient(api_key=...)`);
  examples use `<YOUR_API_KEY>`; tests use `'a' * 32`.
- Don't commit `build/`, `dist/`, `*.egg-info/`, `docs/build/`, or virtualenvs
  (`.gitignore` covers `.venv*/` and `env*/`).
- Commit messages: concise, imperative (`add rephrase endpoint`, `bump version`).
