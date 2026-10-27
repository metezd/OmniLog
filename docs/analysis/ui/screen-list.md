# UI Screen List and Figma Plan: OmniLog

This document starts the UI mockup work. It lists every screen of the application and gives a plan for the Figma file.

The Figma file itself is not part of this repository. The plan below is detailed enough to build the first draft directly in Figma.

## 1. Screen list

Roles: **V** is Visitor, **U** is User, **A** is Admin (Operator).

| ID | Screen | Route | Role | Epic and stories | Data and endpoints | Priority |
|---|---|---|---|---|---|---|
| S-01 | Landing page | `/` | V | 1, 2 | None | Must |
| S-02 | Register | `/register` | V | 2, US-02 | `POST /auth/register` | Must |
| S-03 | Log in | `/login` | V | 2, US-03 | `POST /auth/login` | Must |
| S-04 | Library | `/library` | U | 2, US-04, US-05 | `GET /library`, `PATCH /library/{id}`, `DELETE /library/{id}` | Must |
| S-05 | Catalog search | `/search` | U | 3, US-08 | `GET /catalog/search` | Must |
| S-06 | Title details | `/title/[id]` | U | 3, 4, US-09 to US-12, US-14 | `GET /catalog/{id}`, `POST /library`, chapter endpoints, `POST /library/{id}/review` | Must |
| S-07 | Custom lists | `/lists` | U | 2, US-06 | `GET /lists`, `POST /lists`, `DELETE /lists/{id}` | Should |
| S-08 | List details | `/lists/[id]` | U | 2, US-06 | `GET /lists/{id}`, `POST /lists/{id}/items`, `DELETE /lists/{id}/items/{media_item_id}` | Should |
| S-09 | Activity diary | `/diary` | U | 2, US-07 | `GET /diary` | Should |
| S-10 | Recommendations | `/recommendations` | U | 5, US-13 | `GET /recommendations?target=` | Should |
| S-11 | Statistics | `/stats` | U | 6, US-15 | `GET /stats` | Should |
| S-12 | Profile | `/profile` | U | 2 (no story yet) | None yet | Could |
| S-13 | Admin: Integrations | `/admin/integrations` | A | 3 | Status of IGDB and TMDB keys (never the keys themselves) | Could |
| S-14 | Admin: Sync status | `/admin/sync` | A | 3 | `POST /admin/sync`, `GET /admin/sync/status` | Could |
| S-15 | Error and empty states | All routes | All | NFR-02, NFR-04 | 401, 404 and 503 answers | Must |

## 2. Screen details

### S-01 Landing page
- Short explanation of OmniLog and a picture of the main features.
- Buttons: Register and Log in.
- Uses the existing `Navbar`, `Logo` and `Footer` components.

### S-02 Register and S-03 Log in
- Forms with React Hook Form validation.
- Register fields: username, email, password. Show the 409 error (already used) and the 422 error (invalid input) next to the fields.
- Log in fields: username and password. Show a clear message for 401.
- After log in, go to the Library.

### S-04 Library
- A grid or list of the user's titles with poster, title, status and rating.
- Filter by status (Plan to watch, In progress, Completed, Dropped) and by media type.
- Change the status and the rating (1 to 10) on the card.
- Empty state: a message and a button to the Catalog search.

### S-05 Catalog search
- Search field and a type switch (Game, Series).
- Result cards with poster, title and release date. A button "Add to library".
- States: loading, no results, outside service not available (503 message).

### S-06 Title details
This is the most important screen.
- Header: poster, title, type, release date, genres, description.
- Library panel: add to library, status, rating (US-04, US-05).
- Seasons and chapters list. A series shows seasons with episodes. An episodic game shows chapters (US-09).
- Chapter panel for each chapter: star rating from 1 to 5 (US-10), playtime entry in minutes with a running total (US-11), and a decision choice with options such as A and B (US-12).
- Review box with a spoiler badge after saving (US-14).

### S-07 Custom lists and S-08 List details
- S-07: all lists of the user and a form to create a list. The name cannot be empty.
- S-08: the titles in one list, and a way to add a title.

### S-09 Activity diary
- A timeline of events, newest first. Each row has an icon, a sentence (for example "You rated Life is Strange 9") and the time.
- Empty state for new users.

### S-10 Recommendations
- A switch for the target type (Series or Games).
- Cards of recommended titles with an "Add to library" button.
- Empty state when the library is empty.

### S-11 Statistics
- Four charts (Recharts): media split (donut), rating distribution (bar), genre breakdown (bar) and playtime histogram.
- A small summary row with total titles and total playtime.
- Empty state with zero values.

### S-12 Profile (optional)
- Username, email and join date. This screen has no user story yet (finding F-15).

### S-13 and S-14 Admin screens
- S-13 shows if the IGDB and TMDB keys are set and valid. It never shows the key values.
- S-14 has a "Run sync" button and a table of the last jobs with start time, end time, status and records processed.

### S-15 Error and empty states
- 401: go to Log in.
- 404: not found page.
- 503: "Data service is not available" message with a retry button.

## 3. Main user flows

| Flow | Screens |
|---|---|
| Start | S-01, S-02, S-03, S-04 |
| Find and add a title | S-04, S-05, S-06 |
| Track an episodic game | S-06 (chapter rating, playtime, decision) |
| Write a review | S-06 |
| Organize titles | S-07, S-08 |
| Look back | S-09, S-11 |
| Discover | S-10, S-06 |
| Operate | S-13, S-14 |

## 4. Navigation

Main navigation for a logged-in user: Library, Search, Lists, Diary, Recommendations, Statistics, Profile. Admin links appear only for an admin user. A visitor only sees Log in and Register.

## 5. Figma plan

### 5.1 File structure

| Page | Content |
|---|---|
| Cover | Project name, version, status |
| Foundations | Colors, typography, spacing, icons |
| Components | Navbar, Footer, Logo, buttons, inputs, media card, status badge, star rating, chart cards, timeline row, table, toast |
| Flows | The flows in section 3 as prototype links |
| Screens Desktop | S-01 to S-15 as frames of 1440 by 1024 |
| Screens Mobile | The main screens (S-02 to S-06, S-11) as frames of 390 by 844 |

### 5.2 Foundations

- Spacing uses an 8 px grid.
- Use the same tokens as Tailwind CSS (colors, font sizes, radius). This keeps the design and the code close.
- Use Lucide icons (the frontend uses Lucide React).
- Support a light and a dark theme if time allows.

### 5.3 First draft order

1. Components: media card, status badge, star rating.
2. S-06 Title details (the hardest screen).
3. S-04 Library and S-05 Catalog search.
4. S-02 and S-03 forms.
5. S-11 Statistics.
6. The remaining screens and the error states.

### 5.4 Rough layout of the Title details screen

```text
+--------------------------------------------------------------+
| Navbar                                                       |
+--------------------------------------------------------------+
| [Poster]  Title                         [Add to library v]   |
|           Game | 2015 | Adventure       Status: In progress  |
|           Description text ...          Rating: 9 / 10       |
+--------------------------------------------------------------+
| Chapters                                                     |
|  1. Chapter One    [*****]  90 min  [+ time]  Choice: A | B  |
|  2. Chapter Two    [**---]  30 min  [+ time]  Choice: A | B  |
+--------------------------------------------------------------+
| Your review                                   [Spoiler badge]|
| [ text box ...........................................  ]   |
|                                              [Save review]   |
+--------------------------------------------------------------+
```

### 5.5 Rough layout of the Statistics screen

```text
+--------------------------------------------------------------+
| Navbar                                                       |
+--------------------------------------------------------------+
| Total titles: 4     Total playtime: 0 h                      |
+-------------------------------+------------------------------+
| Media split (donut)           | Rating distribution (bars)   |
+-------------------------------+------------------------------+
| Genre breakdown (bars)        | Playtime histogram           |
+-------------------------------+------------------------------+
```

## 6. Open questions for the frontend lead

1. Is a mobile layout required for the first version?
2. Is a dark theme required?
3. Is a profile screen needed (no story)?
4. Should the chapter panel be inside the Title details screen (proposed) or on its own page?
