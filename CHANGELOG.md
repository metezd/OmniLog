# Changelog

All notable changes to this project are written in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the versions follow [Semantic Versioning](https://semver.org). The rules for versions and releases are in [CONTRIBUTING.md](CONTRIBUTING.md#versioning-and-releases).

## [Unreleased]

### Added

- Authentication with register, login and JWT, and `GET /auth/me` (US-02, US-03).
- Catalog and library: add, rate and update titles, search in IGDB and TMDB with a Redis cache, title details with description and genres (US-04, US-05, US-08, US-09).
- Custom lists and the activity diary, with `DELETE` endpoints for library entries, list items and lists (US-06, US-07).
- Episodic logging: chapter ratings, playtime and decisions, with the seed command `python -m app.seed` (US-10 to US-12).
- Personal statistics with a Redis cache (US-15).
- Reviews with spoiler detection (US-14) and personalized, embedding-based recommendations with a popularity fallback (US-13).
- The manual sync command `python -m app.sync` and the embeddings command `python -m app.embeddings`.
- Rate limits on login, register, search and review.
- Next.js frontend that calls the backend from its server code, with the login token in an `httpOnly` cookie.
- Production Docker stack with PostgreSQL (pgvector), Redis, the backend, the frontend and a Caddy proxy with HTTPS, and a Render blueprint (`render.yaml`).
- CI for the backend, the frontend and the Docker stack, with a coverage gate of 70%, dependency audits and a check of the lock files.
- Security checks: Gitleaks, Trivy, zizmor, Ruff security rules, ESLint security rules, static security tests and a report-only Semgrep job.
- Dependabot for Python, npm, GitHub Actions and Docker.
- Project documents: Charter, requirements, analysis, design and plan.
- The API documentation is now off on Render too (`ENABLE_DOCS=false`).
- Local penetration test with its report, TDD evidence and AI usage notes (#252).
- The evidence of AI use beyond autocomplete: agent pull requests, Copilot review results, instruction files and a review session (`docs/ai-usage/evidence.md`, #311).
- Contribution rules with a branching model, versioning, code review, a pull request template, issue templates and CODEOWNERS.
- A release workflow that creates a GitHub Release from a version tag, and a ruleset that protects `main`.

### Changed

- The version of the backend, the frontend package and the Git tags is now one number (`0.8.0`), and a test checks that the files agree.
- Render deploys `main` only after the GitHub checks pass.
- The Dependabot auto-merge workflow uses rebase, so it follows the linear history rule.

### Removed

- The old root `env.example` (its `SECRET_KEY` value was too short for the backend, and `backend/.env.example` replaces it) and the unused starter images in `frontend/public`.
