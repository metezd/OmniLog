# OmniLog - Gantt Chart

Task dates come from the PERT analysis in [pert.md](pert.md), rounded to whole days. Red bars are on the critical path. Milestones follow the Project Charter. The presentation date is not announced yet (TBA), so it is shown tentatively at the start of December.

```mermaid
gantt
    title OmniLog Project Schedule
    dateFormat YYYY-MM-DD
    axisFormat %d.%m

    section Milestones
    Project Charter delivered            :milestone, m0, 2026-10-02, 0d
    Requirements Definition Report       :milestone, m1, 2026-10-11, 0d
    Requirement Analysis Report          :milestone, m2, 2026-10-18, 0d
    Software Design Report               :milestone, m3, 2026-11-15, 0d
    Software Testing Report              :milestone, m4, 2026-11-22, 0d
    Codebase                             :milestone, m5, 2026-11-30, 0d
    Presentation (TBA, tentative)        :milestone, m6, 2026-12-01, 0d

    section Requirements and Analysis
    A Requirements definition            :active, a, 2026-10-03, 8d
    B Requirements analysis              :b, 2026-10-11, 7d

    section Design
    D Software design                    :d, 2026-10-18, 28d

    section Implementation
    C Backend foundation (Epic 1 and 2)  :crit, active, c, 2026-10-03, 15d
    E Media aggregation (Epic 3)         :crit, e, 2026-10-18, 10d
    F Episodic and decision logging (Epic 4) :crit, f, 2026-10-28, 8d
    G Frontend Next.js                   :g, 2026-10-18, 18d
    H AI engine (Epic 5)                 :h, 2026-10-28, 14d
    I Analytics dashboard (Epic 6)       :crit, i, 2026-11-05, 7d

    section Deployment
    J Integration and deployment         :j, 2026-11-12, 7d

    section Testing and Delivery
    K Testing and QA                     :crit, k, 2026-11-12, 10d
    L Stabilization and packaging        :crit, l, 2026-11-22, 8d
    M Presentation preparation           :m, 2026-11-22, 4d
```
