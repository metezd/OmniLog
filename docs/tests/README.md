# Test documentation

All test documents of the project. Start with the Software Testing Report: it summarizes every part and links to the details. The documents were brought together on 2026-11-26 (review of #234): one document per subject, and every number measured on the current code.

| Document | Content |
|---|---|
| [Software Testing Report](software-testing-report.md) | Summary, strategy, environment, results of every kind of test, defects, residual risks, how to repeat (#296) |
| [Traceability](traceability.md) | Which tests check which requirement: the generated matrix, every acceptance criterion with its test, and the frontend tests per requirement (#300, #234) |
| [Coverage](coverage.md) | Backend and frontend code coverage, what is not covered and why (#297) |
| [Performance](performance.md) | NFR-01 and the HTTP load test, with the re-run on the current code (#298) |
| [Penetration test](penetration/README.md) | Findings F1 to F7, the fixes and the retests, OWASP ZAP (#306) |
| [SonarQube](sonarqube.md) | The scan, its findings and what was done, with screenshots (#299, #349) |
| [Static analysis](static-analysis.md) | Ruff, Bandit, `pip-audit`, `npm audit`, ESLint, TypeScript and Radon (#234) |
| [Mitigation plan](mitigation-plan.md) | Every quality finding with its severity, its status and its fix (#234) |
| [TDD evidence](tdd-evidence.md) | Tests before code, and the red then green fix cycles (#307) |

The tests themselves are in [`tests/`](../../tests/): `tests/requirements/` (requirement and edge case tests), `tests/test_*.py` (health, security and the checks of the repository), `tests/performance/` (load test), `tests/pentest/` (penetration test) and [`frontend/tests/`](../../frontend/tests/) (frontend).
