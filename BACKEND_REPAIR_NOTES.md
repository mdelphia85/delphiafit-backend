# DelphiaFit Backend Repair Notes

## What was repaired

This repair focused on restoring a coherent, bootable FastAPI/SQLAlchemy backend from the expanded V2 codebase without rolling the entire project back.

Key fixes include:

- repaired circular imports and files that contained code from the wrong architectural layer;
- recovered stronger CRUD implementations from the repository's earlier V2 Git history where later generated commits had replaced them with broken/truncated stubs;
- standardized model imports on the shared SQLAlchemy `Base` and registered every model before relationship configuration;
- repaired model/schema/CRUD/router field contracts across the core fitness and nutrition systems;
- restored legacy/core routes that the V2 `main.py` had dropped;
- corrected router ordering/path collisions and duplicate HTTP method/path registrations;
- updated remaining Pydantic schemas to Pydantic v2 configuration and removed legacy `.dict()` usage;
- corrected the user/JWT subject contract so user-scoped dependencies use a numeric user ID;
- hardened `DATABASE_URL` and `JWT_SECRET` handling so production cannot silently fall back to insecure defaults;
- repaired account deletion/cascades and self/admin authorization on `/users` routes;
- stopped admin user APIs from serializing password hashes, and made admin authorization re-check the current database role;
- replaced the broken Mongo-style admin config implementation with SQLAlchemy storage;
- repaired Live and hardware persistence so SQLAlchemy 2 does not execute invalid raw SQL against missing tables;
- repaired AI method mismatches, coaching invite acceptance, medical datetime handling, and several generated route/CRUD incompatibilities;
- removed obsolete duplicate/insecure login/register/test routers;
- added an idempotent pre-deploy migration runner for known legacy schema changes;
- replaced stale Railway/Nixpacks deployment configuration with Dockerfile config-as-code and a healthcheck.

## Initial repair validation

Before the frontend integration pass, local validation of the repaired tree:

- 0 Python syntax errors found by `compileall`;
- 204 application modules imported with 0 import failures;
- 114 SQLAlchemy mappers configured;
- 114 tables created in a fresh SQLite validation database;
- 338 FastAPI routes registered;
- 295 OpenAPI paths generated;
- 0 duplicate HTTP method/path pairs;
- 40/40 core create/read smoke checks passed;
- 291 broad GET/POST requests produced 0 server-side 5xx responses;
- 39 PUT/PATCH/DELETE mutation probes produced 0 server-side 5xx responses;
- admin-config save/read, persisted streak reset, safe admin-user serialization, admin-role revocation, and account deletion were explicitly checked;
- a real Uvicorn process started locally and returned HTTP 200 from `/health` and `/`;
- a simulated legacy database preserved existing users/workout rows while adding `users.streak`, the V2 workout columns, and the remaining V2 tables.

The broad route probes intentionally generate generic test data. A 4xx in those probes can be an expected business-validation result (for example a missing referenced object); the important repair criterion was eliminating unhandled 5xx errors, followed by explicit lifecycle tests for the high-risk subsystems.

## Railway deployment

The repository now contains `railway.json`, a root `Dockerfile`, and `/health`.

Required Railway variables:

- `DATABASE_URL` — the production PostgreSQL URL;
- `JWT_SECRET` — a long random production secret.

The Dockerfile starts:

```text
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

The Railway config deliberately sets the Start Command override to `null`, runs `python -m app.database.migrate` as a pre-deploy command, and checks `/health` before declaring the deployment healthy.

Before the first repaired production deployment, take/confirm a database backup or restore point. The migration runner is intentionally small and idempotent, but its PostgreSQL behavior should still be treated as a production schema change.

## Important: repaired does not mean every phase is fully implemented

Several advanced systems currently expose working API shapes but still contain placeholder/synthetic business logic. Examples include:

- wearable/device sync returns synthetic metrics until real Apple Health / Garmin / Fitbit / Whoop / Oura provider clients and OAuth flows are connected;
- live rep counting uses simple threshold logic rather than an edge/computer-vision model;
- video AI returns generated placeholder status/results rather than running a GPU/video pipeline;
- some K9, SAR, and aviation scoring is rule-based placeholder logic;
- the AI coach/personalization layer is currently local rules/algorithms, not a fully autonomous external model-backed coaching system.

Do not mark these as production-complete solely because their routes now import and respond.

## Authorization backlog before broad public launch

The expanded feature set needs a deliberate RBAC/ownership pass. Many coach/team/competition/organization/medical/tactical phase routes were generated without enforcing resource ownership or a role policy. Requiring a valid token is not enough if any authenticated account can submit another user's or organization's ID.

In the final dependency audit, 251 of 334 API operations did not have a FastAPI authentication dependency recognizable as `get_current_user`, `decode_access_token`, or `verify_admin`. That count includes intentionally public endpoints (for example registration and public sports catalog reads), so it is not a count of 251 vulnerabilities; it is a map of the surface that still needs an explicit public-vs-authenticated-vs-role-restricted decision.

Before exposing these systems broadly, define and enforce roles such as:

- athlete/user;
- coach;
- parent/guardian;
- teacher/school administrator;
- organization administrator;
- federation administrator;
- medical/PT roles;
- platform administrator.

Then bind resource access to those roles and to ownership/membership records. This is especially important for minors, medical/rehab data, organization administration, and tactical/first-responder modules.

## Migration scope

This project still does not have a full migration history (for example Alembic revisions). The included migration runner handles the legacy-to-current differences identified in this repository (`users.streak`, V2 `workout_logs` columns, and `personal_records.notes`) and creates missing tables; it is not a substitute for a long-term migration framework. Add Alembic before future model changes become frequent.

The execution environment used for this repair did not have `python-jose`, `passlib`, or `bcrypt` installed, so local API/runtime checks used temporary test-only stubs for those three libraries. Those stubs are **not** included in this repository. Railway previously installed the declared dependencies successfully, and the repaired requirements still declare them, but the real cryptographic JWT/password path should get one register/login smoke test in staging after a clean dependency install.

## Local validation command

After installing `requirements.txt` and from the repository root:

```bash
python scripts/validate_backend.py
```

For a real local server, set `DATABASE_URL` and `JWT_SECRET`, then run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```


## Frontend integration pass (2026-08-18)

After comparing the uploaded React/Vite frontend against this repaired backend, the backend gained compatibility and persistence for the live UI contracts (profile/progress/workout/drill compatibility, coach/staff/invite workflows, admin response contracts, public sports catalog access, and authenticated/user-scoped tactical persistence).

Final post-integration gates:

- 211 application modules imported;
- 116 SQLAlchemy mappers configured and 116 tables created on a fresh migration;
- 365 FastAPI routes registered;
- 321 OpenAPI paths generated;
- 0 duplicate HTTP method/path pairs;
- all 62 unique frontend HTTP method/path contracts matched a backend route (70/70 fetch call sites);
- 69/69 end-to-end frontend workflow checks passed against a fresh database;
- simulated legacy rows were preserved while new integration columns/tables were added;
- real Uvicorn startup returned HTTP 200 from `/health`.

See `FRONTEND_BACKEND_INTEGRATION_REPORT.md` for the screen-by-screen integration map and remaining product work.
