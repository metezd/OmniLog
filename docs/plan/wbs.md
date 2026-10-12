# OmniLog - Work Breakdown Structure (WBS)

The WBS decomposes the project into deliverable-oriented work packages. Phases 2-4 and 6 map directly to the course deliverables, and phase 5 maps to the six epics defined in the Project Charter.

```mermaid
mindmap
  root((OmniLog))
    1 Project Management
      1.1 Project Charter
      1.2 Plan documents WBS PERT Gantt
      1.3 GitHub Projects and branching workflow
      1.4 Peer scoring and TA reviews
    2 Requirements Definition
      2.1 User stories
      2.2 Functional tests per story
      2.3 Non-functional test cases
      2.4 Requirement Specification Report
    3 Requirements Analysis
      3.1 Domain model
      3.2 Data model ER diagram
      3.3 Behavioral models BPD or DFD
      3.4 Requirement Analysis Report
    4 Software Design
      4.1 Architecture diagrams
      4.2 Class diagrams
      4.3 Sequence diagrams
      4.4 Design decisions for non-functional requirements
      4.5 Software Design Report
    5 Implementation
      5.1 Epic 1 Backend infrastructure
        Database schema and ORM
        Pydantic schemas
        CRUD layer
        Redis cache
        Environment configuration
      5.2 Epic 2 User management and social journal
        Authentication and authorization
        User profiles
        Status tracking and ratings
        Activity diary and custom lists
      5.3 Epic 3 Multi-media aggregation
        IGDB integration
        TMDB integration
        Data ingestion and caching
      5.4 Epic 4 Episodic and decision logging
        Chapter level ratings
        Playtime counters
        Branching choice tracking
      5.5 Epic 5 AI engine
        Cross-media recommendation with embeddings
        NLP spoiler detection
      5.6 Epic 6 Analytics dashboard
      5.7 Frontend with Next.js
    6 Testing and Quality Assurance
      6.1 Unit tests and code coverage
      6.2 Performance and security tests
      6.3 SonarQube analysis and penetration tests
      6.4 Software Testing Report
    7 Deployment
      7.1 Docker containerization
      7.2 CI/CD pipeline
      7.3 Cloud hosting
    8 Delivery
      8.1 Codebase packaging
      8.2 Project presentation
```

## Mapping of WBS phases to course milestones

| WBS phase | Deliverable | Deadline |
|---|---|---|
| 1.1 | Project Charter | 02.10.2026 23:59 |
| 2 | Requirements Definition Report | 11.10.2026 23:59 |
| 3 | Requirement Analysis Report | 18.10.2026 23:59 |
| 4 | Software Design Report | 15.11.2026 23:59 |
| 6 | Software Testing Report | 22.11.2026 23:59 |
| 5, 7, 8.1 | Codebase | 30.11.2026 23:59 |
| 8.2 | Presentation | TBA |
