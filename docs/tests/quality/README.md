# Code Quality: SonarQube and Static Analysis

**Branch:** `test_work` | **Date:** 19.11.2026

## Status of the SonarQube run (read this first)

> **The SonarQube scan has to be run by a team member on a machine with Docker. It has not been run yet.**
> The environment in which the other test results of this branch were produced has no access to a SonarQube server or to the SonarScanner download, so no SonarQube output exists yet. This folder therefore does not contain invented SonarQube numbers. The file [`sonarqube-results.md`](sonarqube-results.md) is a template that is filled in after the scan (about 15 minutes).

What this folder contains instead, and why it is still useful:

- [`static-analysis-results.md`](static-analysis-results.md): real results of the tools that could be run (Ruff security rules, Bandit, ESLint, TypeScript, Radon, `pip-audit`, `npm audit`). They are **not** SonarQube output, but cover much of the same ground (bugs, vulnerabilities, security hotspots, complexity).
- [`mitigation-plan.md`](mitigation-plan.md): the findings from these tools and from the tests, each with a severity, an owner proposal and a mitigation. The same table format is used for the SonarQube findings of high severity after the scan.
- `../../../sonar-project.properties`: ready configuration (sources, tests, coverage report paths) for the scan.

## How to run SonarQube (about 15 minutes)

1. Start a local SonarQube server (Community Build):
   ```bash
   docker run -d --name sonarqube -p 9000:9000 sonarqube:community
   ```
   Open <http://localhost:9000> (first login `admin` / `admin`, then set a new password).
2. In SonarQube: *Create project -> Manually*, project key `OmniLog`. Choose *Locally*, and create a token.
3. Create the coverage reports from the repository root:
   ```bash
   docker compose up -d                       # PostgreSQL and Redis
   python -m pytest tests --cov=backend/app --cov-report=xml      # writes coverage.xml
   cd frontend && npm ci && npm i --no-save @vitest/coverage-v8@^5 \
       && npx vitest run --coverage --coverage.reporter=lcov && cd ..   # writes frontend/coverage/lcov.info
   ```
4. Run the scanner (reads `sonar-project.properties`):
   ```bash
   docker run --rm --network host -v "$PWD:/usr/src" \
       -e SONAR_HOST_URL=http://localhost:9000 -e SONAR_TOKEN=<your token> \
       sonarsource/sonar-scanner-cli
   ```
   (On Windows or macOS replace `--network host` with `-e SONAR_HOST_URL=http://host.docker.internal:9000`.)
5. Open the project in SonarQube. Take **screenshots** of the *Overview* (Quality Gate, Bugs, Vulnerabilities, Security Hotspots, Code Smells, Coverage, Duplications) and of the *Issues* list filtered by severity *Blocker* and *High* (or *Critical* in older versions). Save them in `docs/tests/quality/sonarqube/`.
6. Fill in [`sonarqube-results.md`](sonarqube-results.md) and add each Blocker/High finding to the table in [`mitigation-plan.md`](mitigation-plan.md) (copy a row of section 2, give it the id `S-01`, `S-02`, ...).
7. Commit the screenshots and the two files.

Tip: SonarQube will probably report the dead code of finding Q-01 as duplication and unused code, the six complex functions of Q-06, and `datetime.utcnow()` (Q-07). These are already in the mitigation plan, so those rows only need the SonarQube rule key.
