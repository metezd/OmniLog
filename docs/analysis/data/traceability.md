# Traceability Table: All Epics

This table links every user story and non-functional requirement to its use case, DFD process, data entities, endpoint, test and analysis document. Use it to check that the requirements, the DFDs and the data model agree.

The detailed Epic 3 requirements (R-EP3-01 to R-EP3-09) are in [traceability-epic3.md](traceability-epic3.md).

Analysis status values: draft, reviewed, accepted. Implementation status values: Implemented, Not implemented (from the test run on 10.10.2026).

| Req ID | Epic | Priority | Use case | DFD process | Data entities | Endpoint | Test | Analysis document | Analysis status | Implementation |
|---|---|---|---|---|---|---|---|---|---|---|
| US-01 | 1 | Must | UC-EP1-01 | 1.0 | - | `GET /health` | `test_epic1_infrastructure.py` | behavior/dfd-level0-1.md | draft | Implemented |
| US-02 | 2 | Must | UC-EP2-01 | 2.1 | `users` | `POST /auth/register` | `test_epic2_users.py` | behavior/dfd-epic2-journal.md | draft | Not implemented |
| US-03 | 2 | Must | UC-EP2-02 | 2.2 | `users` | `POST /auth/login` | `test_epic2_users.py` | behavior/dfd-epic2-journal.md | draft | Not implemented |
| US-04 | 2 | Must | UC-EP2-03 | 2.3, 2.5 | `user_libraries`, `media_items`, `activity_events` | `POST /library`, `GET /library` | `test_epic2_users.py` | behavior/dfd-epic2-journal.md | draft | Not implemented |
| US-05 | 2 | Must | UC-EP2-04 | 2.3, 2.5 | `user_libraries`, `activity_events` | `PATCH /library/{id}` | `test_epic2_users.py` | behavior/dfd-epic2-journal.md | draft | Implemented |
| US-06 | 2 | Should | UC-EP2-05 | 2.4, 2.5 | `custom_lists`, `custom_list_items`, `activity_events` | `POST /lists`, `GET /lists`, `POST /lists/{id}/items`, `GET /lists/{id}` | `test_epic2_users.py` | behavior/dfd-epic2-journal.md | draft | Implemented |
| US-07 | 2 | Should | UC-EP2-06 | 2.5, 2.6 | `activity_events` | `GET /diary` | `test_epic2_users.py` | behavior/dfd-epic2-journal.md | draft | Implemented |
| US-08 | 3 | Must | UC-EP3-05 | 3.2, 3.3, 3.4, 3.5 | `media_items`, `genres` | `GET /catalog/search` | `test_epic3_catalog.py` | behavior/dfd-epic3-catalog.md | draft | Implemented |
| US-09 | 3 | Must | UC-EP3-06 | 3.1, 3.3, 3.4, 3.5 | `media_items`, `seasons`, `chapters` | `GET /catalog/{id}` | `test_epic3_catalog.py`, `test_epic3_title_details_edge_cases.py` | behavior/dfd-epic3-catalog.md | draft | Implemented |
| US-10 | 4 | Must | UC-EP4-01 | 4.1, 4.2 | `chapter_progress`, `chapters` | `PUT /library/{id}/chapters/{chapter_id}/rating` | `test_epic4_episodic.py`, `test_epic4_chapter_rating_edge_cases.py` | behavior/dfd-epic4-episodic.md | draft | Implemented |
| US-11 | 4 | Should | UC-EP4-02 | 4.1, 4.3, 4.5 | `chapter_progress`, `playtime_logs` | `POST .../playtime`, `GET .../chapters/{chapter_id}` | `test_epic4_episodic.py`, `test_epic4_playtime_edge_cases.py` | behavior/dfd-epic4-episodic.md | draft | Implemented |
| US-12 | 4 | Should | UC-EP4-03 | 4.1, 4.4, 4.5 | `decision_points`, `decision_options`, `user_decisions` | `PUT .../decision` | `test_epic4_episodic.py` | behavior/dfd-epic4-episodic.md | draft | Not implemented |
| US-13 | 5 | Should | UC-EP5-01, UC-EP5-02 | 5.1, 5.2, 5.3 | `media_embeddings`, `user_taste_vectors`, `user_libraries` | `GET /recommendations` | `test_epic5_ai.py` | behavior/dfd-epic5-ai.md | draft | Not implemented |
| US-14 | 5 | Could | UC-EP5-03 | 5.4, 5.5 | `reviews` | `POST /library/{id}/review` | `test_epic5_ai.py` | behavior/dfd-epic5-ai.md | draft | Not implemented |
| US-15 | 6 | Should | UC-EP6-01 | 6.1 to 6.5 | `user_libraries`, `media_items`, `genres`, `chapter_progress` | `GET /stats` | `test_epic6_analytics.py`, `test_epic6_stats_edge_cases.py` | behavior/dfd-epic6-analytics.md | draft | Implemented |
| NFR-01 | All | - | - | 3.1, 3.2 and D9 | Redis keys | `GET /catalog/search` | `test_nfr.py` | behavior/dfd-epic3-catalog.md | draft | Implemented |
| NFR-02 | All | - | - | 1.0 | - | `/library`, `/lists`, `/diary`, `/stats` | `test_nfr.py` | behavior/dfd-level0-1.md | draft | Implemented |
| NFR-03 | All | - | - | 2.1 | `users` | All user responses | `test_nfr.py` | behavior/dfd-epic2-journal.md | draft | Not implemented |
| NFR-04 | All | - | UC-EP3-04 | 3.7 | - | Catalog endpoints | `test_nfr.py` | behavior/dfd-epic3-catalog.md | draft | Implemented |
| NFR-05 | All | - | - | - | - | - | `pytest --cov` | requirement-analysis-report.md | draft | Measured in the Testing phase |

## Consistency checks

| Check | Result |
|---|---|
| Every user story has a DFD process | Yes |
| Every DFD process is used by at least one story | Yes |
| Every table in the E-R diagram is read or written by a DFD process | Yes, with one gap. Nothing creates `decision_points` and `decision_options` yet (see open point 3 in the domain model). `user_taste_vectors` is optional |
| Every endpoint in the tests appears in a DFD | Yes. `POST /media` is a test helper and has no process |
| Every data store in Level 1 is used by a Level 2 document | Yes |

Add a row to this table for every new or changed requirement in each PR.
