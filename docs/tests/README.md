# Test Documentation

Deliverable "Software Test Document" (branch `test_work`).

| Folder or file | Content |
|---|---|
| [`software-testing-report.md`](software-testing-report.md) | The report: strategy, important tests, results, how to interpret them, findings (PDF: [`software-testing-report.pdf`](software-testing-report.pdf)) |
| [`coverage/`](coverage/) | Traceability matrix (tests, requirements, acceptance criteria), coverage report, charts, raw coverage and JUnit files |
| [`non-func-tests/`](non-func-tests/) | Kinds of non-functional tests, method, results (performance, load, security, reliability, maintainability) |
| [`quality/`](quality/) | SonarQube procedure and results template, static analysis results, mitigation plan |

The tests themselves are in [`tests/`](../../tests/): `tests/requirements/` (functional and edge cases), `tests/test_*.py` (health and security), `tests/nonfunctional/run_load_test.py` (load test), `frontend/tests/` (frontend).
