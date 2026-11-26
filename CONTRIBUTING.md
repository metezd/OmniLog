# Contributing

This guide explains how a change goes from an idea to the `main` branch. The rules are short on purpose.

## Workflow

1. Start from an issue. Every change has one, so the reason is written down.
2. Create a branch from an up to date `main`.
3. Make small commits. Each commit builds and passes the tests on its own.
4. Open a pull request. Link the issue with `Closes #123` in the description.
5. Wait for the CI checks and the review. Fix what the review finds with new commits.
6. Merge with **Create a merge commit**, the only method that the ruleset of `main` allows. The commits stay as they were written, and the merge commit names the pull request. See [Code review](#code-review) for the rules.

Keep a pull request to one topic. A reviewer can read 10 files well and cannot read 80 files well. When a change has a database migration, put it in its own commit.

## Branching model

We use trunk-based development with short-lived branches. There is one long-lived branch, `main`, and nothing else.

- `main` always builds, passes the tests and can be deployed. Nobody pushes to it directly. The ruleset in `.github/rulesets/main.json` enforces this (see [Protecting `main`](#protecting-main)).
- Every change lives on its own branch that starts from an up to date `main` and is named as in the table below.
- A branch lives for days, not weeks. When a topic is bigger than one pull request, split it into steps that each leave `main` working, and hide unfinished behavior instead of keeping a long branch.
- A branch is merged by a pull request only, and it is deleted after the merge (turn on "Automatically delete head branches" in the repository settings).
- There are no `develop`, `staging` or `release/*` branches. A release is a tag on `main` (see [Versioning and releases](#versioning-and-releases)).
- A problem in production is fixed the same way as any other change: a `fix/` branch, a pull request, a new patch release. If a release must be rolled back first, see section 5 of [`docs/deployment.md`](docs/deployment.md).

## Branch names

Use `type/short-description` in lower case with hyphens.

| Type | Use |
|---|---|
| `feat/` | New behavior for users |
| `fix/` | A bug fix |
| `chore/` | Tooling, dependencies, project setup |
| `docs/` | Documentation only |
| `test/` | Tests only |

Examples: `feat/title-description-and-genres`, `fix/login-redirect`, `chore/project-tooling`.

Both names are checked. The ruleset in [`.github/rulesets/branch-names.json`](.github/rulesets/branch-names.json) refuses to create a branch with another name (Dependabot branches are allowed), and the workflow `pr-title.yml` fails the checks "Branch name" and "PR title" when the branch name or the pull request title is not in this form.

## Commit messages

One line in the form `type(scope): subject`. We follow Conventional Commits.

- **type:** `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`
- **scope:** `backend`, `frontend`, or none when the change is for the whole repository
- **subject:** starts with a lower case verb in the imperative, has no period at the end, and the whole line is at most 72 characters

Good: `feat(backend): add DELETE /library/{id} with a diary event`

Not good: `Fixed some stuff.`

## Pull requests

The pull request template asks for a summary, the linked issues, the list of changes and how the change was tested. Fill all of it in. The description must match the files that changed. Say it clearly when a pull request:

- adds a library or framework that is not in the Charter,
- adds a feature that is not one of the user stories,
- needs a migration or a new environment variable.

Add the labels of the area (`backend`, `frontend`, `ci`, `documentation`) and the milestone of the roadmap step.

## AI assistance

AI may help with code, tests, documents and reviews. How the team uses it end to end is in [`docs/ai-usage`](docs/ai-usage/README.md). Every change shows whether AI helped, so that the help can be traced later:

- **Pull request.** Fill the section "AI assistance" of the template: none, AI helped, or AI wrote most of it, the tool and the model, what you checked by hand, and what the AI got wrong that you fixed.
- **Label.** Add `ai-assisted` to every pull request where AI helped. All of them: `gh pr list --label ai-assisted --state all`.
- **Check.** The check "AI disclosure" (in `.github/workflows/pr-title.yml`) fails when the section is missing, when not exactly one of the three boxes is ticked, or when AI helped and the label is missing. It runs again when you edit the description or change the labels. Dependabot pull requests are skipped.
- **Commit trailer.** A commit that AI wrote or changed gets a trailer in a second line. The subject stays one line:

  ```bash
  git commit -m "fix: reject NUL characters" -m "Assisted-by: Claude Code (Claude Opus 5.5)"
  ```

  Use the real tool and model, for example `Assisted-by: Codex (gpt-6-luna)` or `Assisted-by: ChatGPT`.

**The author must be able to explain every line** of AI output before the merge, as if they had written it. The reviewer asks when something is unclear, and a change that the author cannot explain is not merged. AI never merges, and AI output goes through CI and a human review like any other change.

Work merged before this rule has no trailer, and history is not rewritten. It is covered by the notes of each member in [`docs/ai-usage`](docs/ai-usage/README.md).

## Versioning and releases

We use [Semantic Versioning](https://semver.org) (`MAJOR.MINOR.PATCH`). One version number is used for the whole repository. It is written in three places, and a test (`tests/test_version_consistency.py`) fails when they differ: the `version` of `FastAPI(...)` in `backend/app/main.py`, and the `version` in `frontend/package.json` and `frontend/package-lock.json`.

| Part | When it goes up |
|---|---|
| MAJOR | A change that breaks the API contract, or the code freeze release `1.0.0` |
| MINOR | A new feature set, for example a finished roadmap step from the README |
| PATCH | A bug fix, a security fix or a documentation fix with no new behavior |

Until the code freeze the project is `0.x`. The MINOR number is the roadmap step that is reached, so `0.8.0` means that Step 8 is done, `0.9.0` comes when Step 9 is done, and `1.0.0` is the code freeze (30.11.2026, see the milestones in the README). A tag is always `v` plus the version, for example `v0.8.0`.

Every change that a user or a teammate can notice gets one line in `CHANGELOG.md`, under `[Unreleased]`, in the pull request that makes the change. The format is [Keep a Changelog](https://keepachangelog.com): the groups are Added, Changed, Fixed, Removed and Security.

### How to make a release

1. Branch `chore/release-X.Y.Z` from an up to date `main`.
2. In `CHANGELOG.md`, rename `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD`, and add an empty `[Unreleased]` section above it.
3. Set the version to `X.Y.Z` in the three places above.
4. Open a pull request with the title `chore: release X.Y.Z`. After the review and the checks, merge it.
5. Tag the merge commit on `main` and push the tag:

```bash
git checkout main
git pull
git tag -a vX.Y.Z -m "OmniLog X.Y.Z"
git push origin vX.Y.Z
```

The workflow `.github/workflows/release.yml` starts on the tag. It checks that the tag is a plain version, that the commit is on `main`, that the three versions and the changelog section match the tag, and then it creates the GitHub Release with the text of the changelog section. Versions below `1.0.0` are marked as pre-releases. Render deploys `main` by itself (see section 5 of [`docs/deployment.md`](docs/deployment.md)), so the tag does not deploy anything. It marks the version that was deployed.

## Code review

Every pull request is reviewed before it is merged, including the pull requests of the repository owner.

**Who reviews.** [`.github/CODEOWNERS`](.github/CODEOWNERS) asks the owners of the changed files for a review by itself. At least **one approval** from a teammate other than the author is required. The Copilot review is an extra reader. It finds mistakes early, but it does not count as an approval. The author fixes what it finds or answers why not.

**What the reviewer checks.** The same list that the review skill in [`.github/skills/code-review`](.github/skills/code-review/SKILL.md) uses:

- The change does what the linked issue asks, and nothing more. The description matches the files.
- The Charter tech stack is kept, and a new library or feature is named in the description.
- Security: no secrets, a valid JWT on protected endpoints, input validation, no internal details in errors.
- Tests: new behavior has tests for success and for the main errors. The checks in the pull request are green.
- Database: a model change has a migration with a working `downgrade`, and `alembic check` is clean.
- Documentation: README, `docs/` and `.env.example` follow the change.

**How to review.**

- Read the description first, then the diff, then run the branch when the change is not obvious.
- Say what is wrong and how to fix it. Mark small opinions as `nit:` so the author knows that they do not block the merge.
- Use **Approve** when the change can be merged as it is or after the nits, **Request changes** when something must change first, and **Comment** for questions.
- Answer a review in two working days. Do not leave a pull request waiting without a word.

**How to answer a review.** Fix the points with new commits (do not force-push over a review in progress), reply to every conversation and resolve it yourself only when the fix is pushed. The reviewer re-reads the new commits. A new push removes an old approval, so the approval is always for the code that is merged.

**Who merges.** The author merges with **Create a merge commit** after the approval, the green checks and the resolved conversations. Dependabot pull requests that pass the checks are merged by the same rule through the auto-merge workflow.

### Review rota

Each area has an owner, the member of that role in [`docs/CHARTER.md`](docs/CHARTER.md), and [`.github/CODEOWNERS`](.github/CODEOWNERS) asks the owner for a review by itself. When the author is the owner of the area, the second reviewer in the table reviews instead, so nobody approves their own work.

| Area | Paths | Owner | Second reviewer |
|---|---|---|---|
| Architecture, CI, Docker, Render, docs | `*`, `.github/`, `docker/`, `docker-compose*.yml`, `render.yaml`, `docs/` | Mete Özdoğan (`metezd`) | Kağan Konuk (`KaganKonuk`) |
| Frontend | `frontend/` | Kerem Kenet (`KeremKenet`) | Mete Özdoğan |
| Backend | `backend/` | Kağan Konuk (`KaganKonuk`) | Mete Özdoğan |
| IGDB and TMDB integrations, catalog, sync | `backend/app/integrations/`, `catalog_service.py`, `sync.py` | Musab Alperen Başol (`musabalperenbasol`) | Kağan Konuk |
| Embeddings and recommendations | `embeddings.py`, `embedding_service.py`, `recommendations_service.py`, `api/recommendations.py`, `openai_client.py` | Sidar Ürey (`sidarurey`) | Kağan Konuk |
| Tests and the penetration test | `tests/`, `docs/tests/` | Mohammed Edris (`Mhmd77Edrees`) | Mete Özdoğan |

- A pull request that touches more than one area needs the approval of one owner. Ask the owners of the other areas too when the change in their area is more than a line.
- When the owner or the second reviewer cannot answer in two working days, any other member may review.
- Mete Özdoğan is the admin of the repository and can merge without an approval. He waits for an approval like everybody else. The [code review log](docs/code-review-log.md) shows how the pull requests were reviewed so far.
- When a member joins or the roles change, change `CODEOWNERS`, this table and the list in `tests/test_codeowners.py` in the same pull request.

### Protecting `main`

The rules above are enforced by GitHub, not by trust. The ruleset in [`.github/rulesets/main.json`](.github/rulesets/main.json) requires a pull request, one approval after the last push, resolved conversations, the merge method "Create a merge commit" and these status checks: Security lint (Ruff), Backend tests, Docker Compose smoke test, Frontend checks, gitleaks, trivy, zizmor, PR title, Branch name and AI disclosure. It also blocks force pushes and deleting `main`. `tests/test_rulesets.py` checks that every listed check is a job that runs on every pull request, and that the merge method is the one of the Dependabot workflow. The workflow `docker-build.yml` is not listed on purpose, because it runs only when some files change, and a check that does not run would block the other pull requests. The ruleset exists on GitHub (id `24520443`). After a change of the file, an admin applies it with PUT, which replaces the live ruleset (POST would add a second one next to it). List the ids with `gh api repos/metezd/OmniLog/rulesets`:

```powershell
gh api repos/metezd/OmniLog/rulesets/24520443 --method PUT --input .github/rulesets/main.json
```

The second ruleset, [`.github/rulesets/branch-names.json`](.github/rulesets/branch-names.json), enforces the [branch names](#branch-names) on every branch except `main` and `dependabot/...`. Apply it the same way:

```powershell
gh api repos/metezd/OmniLog/rulesets --method POST --input .github/rulesets/branch-names.json
```

## Checks before you push

**Test first, in its own commit.** A bug fix or a new behavior starts with a `test:` commit that holds only the new tests. Run it and check that the tests fail for the reason you expect, not because of a typo or a missing import. Then make them pass in a `fix:` or `feat:` commit. A new test that passes at once tests nothing new: change it, or say in the pull request that it is a guard. Examples are in [`docs/tests/tdd-evidence.md`](docs/tests/tdd-evidence.md), section 4.

The CI runs the same checks. Running them first saves a round trip.

```bash
# Backend, from the repository root with the virtual environment active
python -m pytest tests -v --cov=backend/app --cov-fail-under=90
cd backend && alembic upgrade head && alembic check

# Frontend
cd frontend
npm run lint
npx tsc --noEmit
npm run test:coverage
npm run build
npm audit --omit=dev --audit-level=high
```

## Code style

- Comments, commit messages and documentation are in English.
- Files use LF line endings (`.gitattributes` enforces this).
- A new endpoint comes with tests for success and for the main errors (401, 404, 409, 422).
- A migration has a working `downgrade`.
- Do not commit secrets. Settings come from environment variables, as in `.env.example`.

## Labels and milestones

- Labels: `backend`, `frontend`, `ci`, `dependencies`, `security`, `documentation`, `tests`, `enhancement`, `bug`, `scope-extension`, `follow-up`, and `ai-assisted` (see [AI assistance](#ai-assistance)).
- Milestones follow the roadmap in the README (Step 0 to Step 9).
- A change for the changelog goes into `CHANGELOG.md` under `[Unreleased]` (see [Versioning and releases](#versioning-and-releases)).
