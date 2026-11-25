# Penetration Test

Part of the review checklist in #252 (section D). The results feed the security part of the Software Testing Report (#157, #234).

## 1. Summary

| | |
|---|---|
| Date | 23.11.2026 |
| Target | Backend API at commit `46c9072` of `main`, running on this computer |
| Method | Black-box attacks over HTTP, then a review of the deployment files for each result |
| Script | [`tests/pentest/run_pentest.py`](../../../tests/pentest/run_pentest.py) |
| Raw results | [`raw/results.json`](raw/results.json), [`raw/forwarded-header-proof.json`](raw/forwarded-header-proof.json) |
| Automated checks | 28: 21 passed, 7 raised a finding |
| Confirmed issues | 7: 1 high, 2 medium, 3 low, 1 informational |
| **Retest after the fixes** | 25.11.2026 at `74f1f3a`: **31 checks, 31 passed, 0 findings**. All 7 issues are fixed. See [section 5](#5-retest-after-the-fixes) |
| Retest raw results | [`raw/results-after-fixes.json`](raw/results-after-fixes.json) |

The core protections held. No attack read or changed the data of another user, forged a token, or bypassed the login with SQL injection. The most important issue is that the login rate limit can be bypassed with the settings in `render.yaml`.

## 2. Scope and limits

Tested: authentication, tokens, access control between users, mass assignment, SQL injection, stored content, malformed input, error answers, CORS, security headers and rate limits.

Not tested, so these results say nothing about them:

- **The deployed system.** All attacks ran locally. Findings about Render come from `render.yaml` and a local run with the same uvicorn options.
- **The Caddy proxy and the Docker stack.** Docker was not available on the test computer.
- **Redis.** It was off, so the rate limits used the in-process counter.
- **pgvector.** The test database has no pgvector, so the `media_embeddings` table was left out and the vector query of `GET /recommendations` was not attacked.
- **The frontend in a browser.** Its code was read for F3, but no browser attack was run. (Closed by the retest, section 5.)
- **Automated scanners** such as OWASP ZAP or sqlmap. The checks are written by hand, so they cover only the listed attacks.

## 3. Findings

| ID | Severity | Finding | Check |
|---|---|---|---|
| F1 | High | Login rate limit can be bypassed on the Render setup | RATE-02 |
| F2 | Medium | API documentation is public on the Render setup | Config review |
| F3 | Medium | Any user can add catalog titles with any image address | XSS-01, CAT-01 |
| F4 | Low | Four malformed inputs cause a 500 error | INPUT-01 |
| F5 | Low | Validation errors repeat the rejected password | DATA-02 |
| F6 | Low | No limit on the body size, and large values are sent back | INPUT-03 |
| F7 | Info | The `Server` header names uvicorn | CONF-04 |

### F1. Login rate limit can be bypassed on the Render setup (High)

`render.yaml` starts uvicorn with `--proxy-headers --forwarded-allow-ips="*"`. With `*`, uvicorn trusts every caller and uses the **first** address in `X-Forwarded-For`, which the client can choose.

**Proof (local, same uvicorn options):**

| Requests | Result |
|---|---|
| 12 wrong logins with one address | 10 x 401, then 429 |
| 30 wrong logins with a new fake first address each time | 30 x 401, **no 429** |

**Impact:** unlimited password guessing, and the limit on registration can be bypassed in the same way.

**To confirm:** whether the proxy of Render keeps the first address sent by the client. This was not tried on the deployed system.

**Fix:** do not take the client address from the leftmost value. Use the address that the Render proxy adds, and add a test with a fake header. The Docker setup is not affected by this configuration, because `FORWARDED_ALLOW_IPS` lists only the fixed proxy addresses. See also #251.

**Status:** fixed in #301 (first step in #251). The backend counts the right-most address of `X-Forwarded-For` (`FORWARDED_TRUSTED_HOPS=1` in `render.yaml`), which the proxy of Render writes. Calls from the frontend send the browser address in `X-Client-IP` with a shared key, and the backend ignores that header without the key. With the start options of `render.yaml`, 30 wrong logins that each send a new fake first address now get 10 x 401 and then 429 (`tests/requirements/test_f1_render_rate_limit.py`). `RATE-02` of the script now sends such addresses and fails if the bypass comes back. The behaviour of the proxy of Render was not checked on the deployed system.

### F2. API documentation is public on the Render setup (Medium)

`ENABLE_DOCS` defaults to `true`. `docker-compose.prod.yml` sets it to `false`, but `render.yaml` does not set it, so `/docs`, `/redoc` and `/openapi.json` stay open there. This gap came from #231.

**Fix:** add `ENABLE_DOCS` with the value `"false"` to the `omnilog-api` service in `render.yaml`.

### F3. Any user can add catalog titles with any image address (Medium)

`POST /media` accepts any logged-in user (open issue #218), and `poster_url` is not validated. Both `javascript:alert(...)` and `http://attacker.example/pixel.png` were stored with 201.

**Impact:** the frontend places `poster_url` in `<img src>`. Browsers do not run `javascript:` there, so this is **not** a working XSS. An outside image is loaded by every user who sees the title, so an attacker learns their IP address and when they viewed it. The catalog can also be filled with false titles.

**Fix:** close #218, allow only `https` addresses from the IGDB and TMDB image hosts, and add a Content-Security-Policy for images in the frontend.

**Status:** fixed for the backend in #218. `POST /media` answers 404 unless `ALLOW_MEDIA_CREATE` is on, and then `poster_url` must be an `https` address on `image.tmdb.org` or `images.igdb.com`. `GET /media/{id}` needs a login. Fixed completely in #303: the update schema checks `poster_url` the same way, and the frontend sends a Content-Security-Policy with `img-src 'self' data: blob: https://image.tmdb.org https://images.igdb.com` and scripts only with a nonce. In a browser on the production stack, an image from another host was blocked (`Loading the image 'https://attacker.example/pixel.png' violates ... img-src`), and an injected `onerror` handler did not run.

### F4. Four malformed inputs cause a 500 error (Low)

| Input | Answer |
|---|---|
| NUL byte in a list name | 500 |
| NUL byte in a review | 500 |
| NUL byte in a media title | 500 |
| `external_api_id` larger than the database integer | 500 |

A logged-in user can trigger these. No data changes.

**Fix:** refuse NUL bytes in the text fields and add an upper limit to `external_api_id`, so that these answer 422.

**Status:** fixed in #302. One check (`reject_nul`, type `NoNulStr` in `backend/app/core/validation.py`) is used by every text that a client sends, also `poster_url`, `release_date`, the decision choice and the search text. `external_api_id` must be between 1 and 2**31 - 1. All of them answer 422 now (`tests/requirements/test_malformed_input.py`).

### F5. Validation errors repeat the rejected password (Low)

A registration with a short password gets a 422 whose `input` field contains the password. It goes back only to the sender, but it can end up in browser tools or in logs of a proxy.

**Fix:** remove `input` from the answer in `validation_exception_handler` (`backend/app/core/errors.py`).

**Status:** fixed in #302. A 422 now holds only `type`, `loc` and `msg` of each error, never `input` or `ctx`. This also fixed a problem found later: a value nested about 3000 levels deep gave a 500, because the handler walked the echoed value once per level.

### F6. No limit on the body size (Low)

A list name of 3 MB is refused with 422, but the answer contains the full 3 MB value. The API reads the whole body first, so large requests cost memory and bandwidth. The same fix as F5 removes the repeated value.

**Fix:** also set a maximum body size in the proxy or in a middleware.

**Status:** fixed in #302. `BodySizeLimitMiddleware` (`backend/app/core/body_limit.py`) answers 413 for a body over 1 MB, before it is read when `Content-Length` says so, and while it is read for a chunked body. A `Content-Length` that is not a whole number gets 400. The answers keep the security headers. Caddy has the same limit (`request_body { max_size 1MB }`). A refused 3 MB value is no longer sent back (F5).

### F7. The `Server` header names uvicorn (Info)

**Fix:** start uvicorn with `--no-server-header`.

**Status:** fixed in #304. `backend/Dockerfile` and `render.yaml` start uvicorn with `--no-server-header`, Caddy removes `Server` (`-Server`), and the frontend no longer sends `X-Powered-By`. The API also sends `X-Frame-Options: DENY`, a strict `Content-Security-Policy` and `Permissions-Policy` on every answer, now also on a 500. `curl -I` on the production stack in Docker showed no `Server` header on the backend, through Caddy and on the frontend.

## 4. Attacks that failed

| Check | Attack | Result |
|---|---|---|
| AUTH-01 | 17 protected endpoints without a token | All 401 |
| AUTH-02 | 10 forged tokens (`alg: none`, wrong key, changed payload, HS384, expired, no `exp`, no `sub`, text `sub`, unknown user, huge `sub`) | All 401 |
| AUTH-03, AUTH-04 | Find valid usernames through the login answer or its timing | Same answer, 1 ms median gap |
| IDOR-01 to 03 | User B reads, changes or deletes the library, reviews, chapters and lists of user A | All 404, data unchanged |
| MASS-01 | Send `id`, `is_admin` and `hashed_password` at registration | Ignored |
| DATA-01 | Look for a password or a hash in answers | None |
| SQLI-01, SQLI-02 | SQL injection in login, search, names and paths | No bypass, no error |
| INPUT-02 | NUL bytes in the login | 422 |
| XSS-02 | HTML in a title | Returned only as JSON with `nosniff` |
| CONF-01 to 03, 05 | Docs when off, `.env`, `.git`, path traversal, security headers, TRACE | Protected |
| CORS-01 | Calls from another origin and from `null` | Not allowed |
| RATE-01, 03, 04 | Password guessing, mass registration, search flood | 429 |

## 5. Retest after the fixes

Issue #306. Run on 25.11.2026 against `main` at `74f1f3a`, after #340, #341, #342 and #343 were merged.

**Setup.** The backend ran on this computer with the options of `render.yaml`: `--proxy-headers --forwarded-allow-ips="*" --no-server-header`, `FORWARDED_TRUSTED_HOPS=1`, a `FRONTEND_PROXY_SECRET` and `ENABLE_DOCS=false`. `ALLOW_MEDIA_CREATE=true` was set so the script can add titles. A separate check showed that `POST /media` answers 404 with the default `false`. The frontend ran as a production build (`next build`, `next start`) against this backend. The database was PostgreSQL 17 without pgvector and Redis was off, as in the first run.

### Before and after

| ID | Before (23.11) | Fix | After (25.11) |
|---|---|---|---|
| F1 | 30 fake addresses, no 429 | #340 (#301) | **Fixed.** RATE-02: 429 at try 11 with a new fake first address each time |
| F2 | `/docs` open with the settings of `render.yaml` | #260 | **Fixed.** CONF-01: `/docs`, `/redoc`, `/openapi.json` answer 404. A test checks both production files |
| F3 | `javascript:` and outside image addresses stored (201) | #218, #342 (#303) | **Fixed.** XSS-01 and CAT-01: 422. `POST /media` is 404 by default |
| F4 | NUL bytes and a huge id gave 500 | #341 (#302) | **Fixed.** INPUT-01: no 5xx in 12 malformed inputs |
| F5 | A 422 repeated the rejected password | #341 (#302) | **Fixed.** DATA-02: the password is not in the answer |
| F6 | A 3 MB value was refused and sent back (3 MB answer) | #341 (#302) | **Fixed.** INPUT-03: 413 with a 43 byte answer |
| F7 | `Server: uvicorn` | #343 (#304) | **Fixed.** CONF-04: no `Server` header |

### New checks in the retest

| Check | Attack | Result |
|---|---|---|
| CONF-06 | `X-Frame-Options`, `Content-Security-Policy`, `Permissions-Policy` and `nosniff` on 200, 404 and 422 | All present |
| INPUT-04 | JSON nested 3000 levels deep in a list name | 400 with a 48 byte answer |
| RATE-05 | 12 wrong logins with a forged `X-Client-IP` and a wrong `X-Frontend-Key` | 429 at try 11, so the header is ignored without the key |

All 28 checks of the first run passed again. With the 3 new ones the script now has 31 checks.

### Frontend in a browser

A user was created with `<img src=x onerror="window.__xss=1">` and `<script>window.__xss=2</script>` in a title, a review and a list name. The pages were opened in Chrome, logged in as that user.

| Check | Result |
|---|---|
| `/library`, `/title/4`, `/lists`, `/lists/6`, `/diary` | The payloads show as text. `window.__xss` stayed unset and the pages have no injected `<img>` or `<script>` element |
| Login token cookie | Not visible to JavaScript (`document.cookie` is empty after the login), so it is `HttpOnly` |
| `SameSite` and `Secure` | Set in `frontend/src/lib/server/session.ts` (`sameSite: "lax"`, `secure` in production). Read in the code, not seen in the browser, because the test ran over HTTP |
| Logged out | `/library`, `/lists`, `/lists/6`, `/diary`, `/stats`, `/recommendations`, `/title/4` and `/search` answer 307 to `/login` |
| Frontend headers | `X-Frame-Options: DENY` and a `Content-Security-Policy` with a nonce and `strict-dynamic`, no `X-Powered-By` |

**A false alarm that was checked:** on `/title/4` the text `window.__xss=2` was found inside one `<script>` element. It is the data that Next.js sends to the page (`self.__next_f.push`), where `<` is written as the escape `<`, so it is a string and not a tag. The script did not set `window.__xss`.

### Not tested yet

These parts of #306 need Docker, which is not installed on the test computer (it needs WSL 2), or the agreement of the team:

- **The production stack** of `docker-compose.prod.yml` with Caddy, Redis and the pgvector database. Section F7 says that `curl -I` on that stack showed no `Server` header, but the attack script was not run against it.
- **`GET /recommendations` and the embedding paths with pgvector.** The `media_embeddings` table was still left out.
- **OWASP ZAP**, or another automated scanner. The checks are still written by hand.
- **The hosted system on Render.** No request was sent to it. F1 and the headers there need one harmless request each, after the team agrees.

## 6. How to run it again

Use a throwaway database, because the script creates users and titles. It refuses every address that is not local.

```bash
PENTEST_SECRET=<SECRET_KEY of the local API> python tests/pentest/run_pentest.py --base-url http://127.0.0.1:8000 --out results.json
```

Start the API with `ENABLE_DOCS=false`, `ALLOW_MEDIA_CREATE=true` (the script adds titles with `POST /media`, which is off by default since #218) and the options of `render.yaml` for F1: `FORWARDED_TRUSTED_HOPS=1` and `uvicorn app.main:app --proxy-headers --forwarded-allow-ips="*"`. RATE-02 then sends 12 wrong logins with a new fake first address each, followed by `127.0.0.1` as the address that a proxy adds, and passes when the limit still answers 429 (#301).
