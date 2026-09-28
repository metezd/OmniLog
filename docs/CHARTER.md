# Project Charter: OmniLog

## 1. Project Information
* **Project Name:** OmniLog (Unified Gaming & Media Journal with Episodic & Decision Tracking)
* **Product Owner:** Mete Özdoğan (mete.ozdogan@bilgiedu.net)
* **Software Engineering Team:**
  * Member 1: Mete Özdoğan : Full-Stack Architect (mete.ozdogan@bilgiedu.net)
  * Member 2: Kerem Kenet : Frontend Lead (kerem.kenet@bilgiedu.net)
  * Member 3: Kağan Konuk : Backend Engineer (kagan.konuk@bilgiedu.net)
  * Member 4: Sidar Ürey : ML Engineer (sidar.urey@bilgiedu.net)
  * Member 5: Musab Alperen Başol : API Integration & Backend Engineer (alperen.basol@bilgiedu.net)
* **GH Repo/Project URL:** (Waiting for approval)

---

## 2. Project Description & Problem Statement
OmniLog is a specialised web platform designed for media tracking and social journaling. It is intended to bridge the structural disconnect between video games and television series. Although there are dedicated cataloguing platforms for films (Letterboxd), TV series (Serialized) and video games (Backlogged), modern entertainment consumption is inherently cross media.

Perhaps more importantly, contemporary narrative and episodic games (for example, Telltale series, Life is Strange, Detroit: Become Human) are regarded as unified releases within existing game databases. Gamers lack a unified platform on which to log, rate and review individual game chapters, as well as track and compare branching narrative decisions alongside standard TV episodes.

---

## 3. Project Scope
### Project domain
Entertainment tracking, social cataloguing, video games, television media and interactive narrative analytics.
**Possible Customers & Key Users:** Gamers, TV series enthusiasts, completionists and communities of players of episodic narrative games.

### In-Scope
* **Epic 1 - User Management & Social Journal:** Features include authentication, user profiles, status tracking, an activity diary, star ratings and custom lists.
* **Epic 2 - Multi-Media Aggregation & Cataloging:** It provides automated data ingestion and caching from third-party APIs, including IGDB for gaming titles and TMDB for TV series, as well as metadata, artwork, seasons and chapters.
* **Epic 3 - Granular Episodic & Decision Logging System:** Chapter-level 5-star ratings, episode playtime counters and binary/branching choice tracking for episodic narrative video games.
* **Epic 4 - AI-Powered Cross-Media Engine & Review Moderation:** A content-based and collaborative cross-media recommendation engine that recommends TV shows based on played games and vice versa via embeddings, alongside automated NLP spoiler detection in user reviews.
* **Epic 5 - Analytics Dashboard:** Visual metrics include playtime histograms, genre breakdowns, rating distributions and media split ratios

### Out-of-Scope
* **Epic 1 - Direct Media Streaming & Client Hosting:** Hosting downloadable game client binaries or streaming licensed video episodes.
* **Epic 2 - Real-Time In-Game Memory Hooking:** Background OS hooks to automatically scrape local save files or memory states during runtime.
* **Epic 3 - Digital Key Marketplace & E-commerce:** In-app payment gateways, game key vending and physical merchandise transactions.

---

## 4. Technology Stack
### Backend Stack
* FastAPI and Node.js
* PostgreSQL
* SQLAlchemy / Prisma
* Redis
* Docker

### Frontend Stack
* Next.js and React
* TypeScript
* Tailwind CSS
* Lucide React & Recharts

### AI Stack
* LangChain & OpenAI API / Hugging Face Open Source Models
* Vector Database / Embeddings for semantic cross media recommendations
* NLP / Transformer Pipeline for zero-shot spoiler classification and review sentiment extraction

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