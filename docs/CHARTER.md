# Project Charter: OmniLog

## 1. Project Purpose and Objectives
OmniLog is a specialised web platform designed for media tracking and social journaling. It is intended to bridge the structural disconnect between video games and television series. Although there are dedicated cataloguing platforms for films (Letterboxd), TV series (Serialized) and video games (Backlogged), modern entertainment consumption is inherently cross media.

Perhaps more importantly, contemporary narrative and episodic games (for example, Telltale series, Life is Strange, Detroit: Become Human) are regarded as unified releases within existing game databases. Gamers lack a unified platform on which to log, rate and review individual game chapters, as well as track and compare branching narrative decisions alongside standard TV episodes.

---

## 2. Stakeholders & Roles
* **Product Owner:** Mete Özdoğan (mete.ozdogan@bilgiedu.net)
* **Software Engineering Team:**
  * Member 1: Mete Özdoğan : Full-Stack Architect (mete.ozdogan@bilgiedu.net)
  * Member 2: Kerem Kenet : Frontend Lead (kerem.kenet@bilgiedu.net)
  * Member 3: Kağan Konuk : Backend Engineer (kagan.konuk@bilgiedu.net)
  * Member 4: Sidar Ürey : ML Engineer (sidar.urey@bilgiedu.net)
  * Member 5: Musab Alperen Başol : API Integration & Backend Engineer (alperen.basol@bilgiedu.net)
* **Possible Customers:** Gamers, Film & TV series enthusiasts, Tech Curious People, Players of episodic narrative games.
* **GH Repo/Project URL:** [(OmniLog)](https://github.com/metezd/OmniLog)

---

## 3. Project Scope
### Project domain
Entertainment tracking, social cataloguing, video games, television media and interactive narrative analytics.

### In-Scope
* **Epic 1 - Backend Infrastructure & Database Foundation:** FastAPI/Node.js setup, PostgreSQL schema design, SQLAlchemy/Prisma ORM, 
Redis caching layer, Docker containerization, environment configuration.
* **Epic 2 - User Management & Social Journal:** Features include authentication, user profiles, status tracking, an activity diary, star ratings and custom lists.
* **Epic 3 - Multi-Media Aggregation & Cataloging:** It provides automated data ingestion and caching from third-party APIs, including IGDB for gaming titles and TMDB for TV series, as well as metadata, artwork, seasons and chapters.
* **Epic 4 - Granular Episodic & Decision Logging System:** Chapter-level 5-star ratings, episode playtime counters and binary/branching choice tracking for episodic narrative video games.
* **Epic 5 - AI-Powered Cross-Media Engine & Review Moderation:** A content-based and collaborative cross-media recommendation engine that recommends TV shows based on played games and vice versa via embeddings, alongside automated NLP spoiler detection in user reviews.
* **Epic 6 - Analytics Dashboard:** Visual metrics include playtime histograms, genre breakdowns, rating distributions and media split ratios

### Out-of-Scope
* **Epic 1 - Direct Media Streaming & Client Hosting:** Hosting downloadable game client binaries or streaming licensed video episodes.
* **Epic 2 - Real-Time In-Game Memory Hooking:** Background OS hooks to automatically scrape local save files or memory states during runtime.
* **Epic 3 - Digital Key Marketplace & E-commerce:** In-app payment gateways, game key vending and physical merchandise transactions.

---

## 4. Technology Stack
### Backend Stack
* FastAPI
* Python
* PostgreSQL
* SQLAlchemy ORM
* Pydantic
* Redis
* Docker
* python-jose
* passlib with bcrypt (bcrypt pinned below 5.0, because passlib 1.7.4 does not work with bcrypt 5)
* requests
* python-dotenv

### Frontend Stack
* Next.js
* React
* TypeScript
* Tailwind CSS
* Lucide React & Recharts
* Axios (HTTP client)
* React Hook Form (form validation)

### AI Stack
* LangChain + OpenAI API: Orchestrating NLP processes and embedding operations
* Hugging Face Open Source: LLM and embedding models (available)
* Vector Database (pgvector, Pinecone): Cross media similarity and embeddings
* Transformer Pipeline (NLP): Spoiler detection, sentiment analysis

---

## 5. Project Milestones
| Deliverable | Deadline |
| --- | --- |
| Project Charter | 02.10.2026 23:59 |
| Requirements Definition Report | 11.10.2026 23:59 |
| Requirement Analysis Report | 18.10.2026 23:59 |
| Software Design Report | 15.11.2026 23:59 |
| Software Testing Report | 22.11.2026 23:59 |
| Codebase | 30.11.2026 23:59 |
| Presentation | TBA (see sched.) |