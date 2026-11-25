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

The core protections held. No attack read or changed the data of another user, forged a token, or bypassed the login with SQL injection. The most important issue is that the login rate limit can be bypassed with the settings in `render.yaml`.

## 2. Scope and limits

Tested: authentication, tokens, access control between users, mass assignment, SQL injection, stored content, malformed input, error answers, CORS, security headers and rate limits.

Not tested, so these results say nothing about them:

- **The deployed system.** All attacks ran locally. Findings about Render come from `render.yaml` and a local run with the same uvicorn options.
- **The Caddy proxy and the Docker stack.** Docker was not available on the test computer.
- **Redis.** It was off, so the rate limits used the in-process counter.
- **pgvector.** The test database has no pgvector, so the `media_embeddings` table was left out and the vector query of `GET /recommendations` was not attacked.
- **The frontend in a browser.** Its code was read for F3, but no browser attack was run.
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

### F5. Validation errors repeat the rejected password (Low)

A registration with a short password gets a 422 whose `input` field contains the password. It goes back only to the sender, but it can end up in browser tools or in logs of a proxy.

**Fix:** remove `input` from the answer in `validation_exception_handler` (`backend/app/core/errors.py`).

### F6. No limit on the body size (Low)

A list name of 3 MB is refused with 422, but the answer contains the full 3 MB value. The API reads the whole body first, so large requests cost memory and bandwidth. The same fix as F5 removes the repeated value.

**Fix:** also set a maximum body size in the proxy or in a middleware.

### F7. The `Server` header names uvicorn (Info)

**Fix:** start uvicorn with `--no-server-header`.

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

## 5. How to run it again

Use a throwaway database, because the script creates users and titles. It refuses every address that is not local.

```bash
PENTEST_SECRET=<SECRET_KEY of the local API> python tests/pentest/run_pentest.py --base-url http://127.0.0.1:8000 --out results.json
```

Start the API with `ENABLE_DOCS=false`, `ALLOW_MEDIA_CREATE=true` (the script adds titles with `POST /media`, which is off by default since #218) and the options of `render.yaml` for F1: `FORWARDED_TRUSTED_HOPS=1` and `uvicorn app.main:app --proxy-headers --forwarded-allow-ips="*"`. RATE-02 then sends 12 wrong logins with a new fake first address each, followed by `127.0.0.1` as the address that a proxy adds, and passes when the limit still answers 429 (#301).
