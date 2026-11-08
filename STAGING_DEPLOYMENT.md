# DelphiaFit staging deployment

This procedure configures an isolated staging environment. Do not reuse
production databases, JWT secrets, SMTP credentials, or invitation credentials.
Do not configure the staging frontend against the production API.

Staging frontend and backend services must be separate from production.
Staging frontends and preview builds must connect only to their approved
staging backend; never configure a staging preview to use the production API.
Staging PostgreSQL must never use the production `DATABASE_URL`, and staging
must use its own `JWT_SECRET`. Staging SMTP must use approved synthetic test
inboxes or mail capture. Invitation rotation and testing in this procedure are
limited to synthetic staging records. Never modify production invitations or
use production data for destructive staging tests. Any production change
requires separate explicit authorization and is outside this staging procedure.

## Separate services and URLs

Create separate staging services and record their assigned HTTPS origins:

- Frontend: `https://<approved-staging-frontend-host>`
- Backend: `https://<staging-backend-host>`

The hostname values above are placeholders. Use only hosts approved for the
staging project. Configure the staging frontend's `VITE_API_URL` as the backend
origin, without a trailing slash. Configure the staging backend's `FRONTEND_URL`
as the frontend origin, without a trailing slash.

## Staging environment variables

Set these in the staging service configuration only:

| Variable | Staging value |
| --- | --- |
| `DATABASE_URL` | Connection URL for a dedicated, disposable/staging PostgreSQL database. Never point it at production. |
| `JWT_SECRET` | A newly generated, high-entropy staging-only secret stored in the platform's secret manager. Do not reuse the production value or commit it. |
| `STAGING_FRONTEND_ORIGIN` | Exact approved frontend origin, e.g. `https://<approved-staging-frontend-host>`. It must be HTTPS and contain no path, query, fragment, credentials, or wildcard. |
| `FRONTEND_URL` | Exact staging frontend origin, used to create invitation and password-recovery links. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM` | Optional isolated mail-capture service or staging mail provider settings. Use a staging-only sender. |
| `SMTP_USERNAME`, `SMTP_PASSWORD` | Optional credentials for the isolated mail-capture/provider. Store as secrets; never reuse production SMTP credentials. |
| `SMTP_STARTTLS`, `SMTP_SSL` | Match the staging SMTP provider's documented transport settings. |
| `PASSWORD_RESET_DEBUG_RETURN_TOKEN` | Set to `false` (or leave unset). Never enable token-return debugging in a deployed environment. |
| `PORT` | Leave to Railway's injected runtime value. The container binds to `0.0.0.0:${PORT:-8080}`. |

The CORS allowlist retains the existing production origins and development
origin `http://localhost:5173`, and adds only the normalized origin in
`STAGING_FRONTEND_ORIGIN`. An invalid configured staging origin prevents app
startup; incoming request origins are never added dynamically. Credentials
remain enabled only for explicitly allowed origins; wildcard origins are not
used.

Frontend Vercel staging must set `VITE_API_URL` to the staging backend origin.
Every staging frontend and preview build must use only its approved staging API
origin; do not share the production API with staging previews.

## Database migration and health checks

Railway's configured pre-deploy command runs:

```text
python -m app.database.migrate
```

Confirm the pre-deploy environment has the staging `DATABASE_URL` and can reach
the staging PostgreSQL service before releasing the application. This migration
runner is additive/idempotent; run it against staging first and inspect the
deployment logs for its completion message.

Configure the platform health check to `GET /health` (Railway configuration
uses `/health` with a 120-second timeout). Confirm it returns HTTP 200 after
startup. The application uses Railway's injected `PORT`; do not hardcode a
production port in the service settings.

## Email and secure logging

Prefer an isolated mail-capture inbox in staging. If a mail provider is used,
use staging-only credentials and verify delivered invitation/reset links point
to the staging frontend. Never copy production credentials or real user
invitation/reset tokens into staging.

Invitation and reset credentials are carried in URL fragments from the email
link and sent to the API in POST bodies. Do not add credentials to query
strings, redirects, analytics, client/server logs, error messages, or referrer
data. Do not log request bodies for invitation, reset, login, or other
credential endpoints. Keep platform, proxy, and application access/error logs
enabled with secret redaction; do not disable logging globally. Verify Railway
or any proxy does not record POST bodies, authorization headers, or fragment
values. URL fragments are not sent in HTTP requests, but still must not be
copied into analytics or logs.

## Existing invitation and reset links

Before enabling the new staging flow, identify pending invitations created
in the staging environment before the secure link format and acceptance checks
were deployed. Using synthetic staging records only, revoke pending staging
invitations through the authorized invitation-management flow, then create and
email fresh staging invitations to approved test inboxes or mail capture. This
rotates the invitation token without changing coach/client accounts or
existing team/client relationships. Do not revoke accepted invitations or
delete membership/relationship records. Never modify production invitations
during staging verification; any production change requires separate explicit
authorization.

For outstanding password-recovery links issued before the secure link format,
ask the account holder to request a new reset email; the new request replaces
the active reset token. Do not send old tokens through chat, tickets, logs, or
query-string URLs. Verify all replacement links use the staging frontend and
POST-based API flows.

## Candidate verification

The repository includes frontend CI and a disposable-PostgreSQL Docker
verification workflow. CI can validate only the exact revision made available
to its runner. These working-tree changes have not been committed or deployed;
remote CI verification remains pending until the candidate is submitted to the
runner. The PostgreSQL workflow uses an isolated PostgreSQL service and must
never be given production database credentials.

## Staging rollback and recovery

### Stop conditions

Stop the rollout and do not continue to the next service or environment if any
of these occur:

- The staging CORS preflight or an expected authenticated/unauthenticated
  request behaves incorrectly.
- `/health` is not HTTP 200, the service repeatedly restarts, or startup
  migrations fail.
- Login, coach authentication, administrator authorization, invitation
  handling, or a critical user flow regresses.
- Logs contain credentials, reset/invitation tokens, synthetic credential
  markers, database URLs, or other sensitive values.
- A service is configured with a production URL, secret, database, SMTP
  account, or user data.
- Data integrity, migration compatibility, or the target revision cannot be
  established.

Record the observed failure, time, affected staging service, and revision.
Keep the rollout stopped while determining whether the problem is application
code, configuration, migration, or infrastructure. Do not attempt a production
rollback or change production settings as part of staging recovery.

### Identify revisions and assess schema compatibility before rollback

1. Stop staging traffic to the affected frontend/backend (for example, enable
   staging maintenance mode or pause/scale down the affected service using its
   staging controls). Keep traffic stopped until the rollback target and
   database compatibility have been assessed. Do not alter production traffic.
2. In staging deployment history, record the exact last-verified frontend and
   backend revisions (commit SHA/build identifier), deployment times, and
   configuration version. Confirm those revisions were previously healthy in
   staging; do not identify a revision by mutable branch name alone.
3. Before redeploying an older backend, inspect the migrations applied during
   the failed rollout and compare the resulting staging schema and data changes
   with the previous backend's expected schema. Review queries, columns,
   constraints, defaults, indexes, and transformations in both revisions.
   Establish and document whether the existing staging schema supports the
   previous backend. Do not infer compatibility merely because a migration
   completed or appears additive.
4. If the existing schema is backward-compatible, restore the previous
   backend revision through the staging provider's history/rollback mechanism.
   Restore the previous frontend revision as needed, and confirm its
   `VITE_API_URL` points only to the staging backend. Preserve staging-only
   `DATABASE_URL`, `JWT_SECRET`, `FRONTEND_URL`,
   `STAGING_FRONTEND_ORIGIN`, and mail-capture settings. Keep traffic stopped
   until post-rollback checks pass.
5. If the existing schema is not backward-compatible or compatibility cannot
   be established, keep traffic stopped. Do not connect the old backend to the
   changed schema. Evaluate a reviewed forward fix or restore a pre-migration
   staging snapshot into a new isolated staging database, as described below.
   Validate the restored database and schema with an isolated verification
   backend before reconnecting any staging application.
6. Do not promote, retarget, or reuse production services, variables, or
   databases to perform the rollback.

### Migration compatibility and database recovery

Before each staging release that can change schema, review the migration and
application versions together and determine whether the migration is
backward-compatible with the last-verified backend before deciding to roll back.
Additive nullable columns/tables may be compatible, but verify actual queries,
constraints, defaults, indexes, data transformations, and both application
versions. Do not assume a migration is reversible or compatible because it
completed successfully.

Create a staging PostgreSQL snapshot/backup immediately before any release
that runs a schema migration, changes data shape, or performs a staging data
operation that could be difficult to reproduce. Confirm the snapshot belongs
to the isolated staging database, note its identifier and timestamp, and
verify that the provider reports it usable. Never take or restore a production
snapshot as part of this procedure.

If a migration is compatible with the previous backend, first roll back the
application version only after recording the compatibility assessment, and
verify the old version against the migrated staging schema while traffic
remains stopped. Keep the snapshot until verification and release review
complete.

If a migration is not backward-compatible, do not point the old application at
the changed database and do not blindly reverse migration SQL. Keep traffic to
the failing staging revision stopped. Prefer a reviewed forward-fix that
restores compatibility. If restoration of the pre-migration state is required,
use the database provider's documented snapshot/PITR restore to a new isolated
staging database. Validate that database's schema, migrations, and synthetic
records using an isolated verification backend before reconnecting the staging
application. After validation and approval, update only the staging backend's
database setting. Preserve the failed database/snapshot for diagnosis until
recovery is confirmed. Never run destructive drops, truncates, or unreviewed
down migrations.

### Post-rollback verification

After restoring application revisions or an isolated staging database:

1. Confirm the frontend still calls the staging backend and staging CORS
   accepts only the configured origins.
2. Confirm backend `/health` returns HTTP 200 and the service remains stable.
3. Using synthetic staging accounts, verify user login and an authenticated
   protected request; verify unauthenticated access is rejected.
4. Verify coach login and a protected coach request using a synthetic coach.
   Verify administrator login and an administrator-only request using a
   synthetic staging administrator. Do not elevate real or production accounts
   for this test.
5. Confirm the preselected synthetic test records still exist and are
   unchanged. Compare only the expected synthetic records; do not inspect or
   alter production data.
6. Review staging application, platform, proxy, and migration logs. Ensure
   they contain no synthetic credential markers, bearer tokens, reset/invite
   tokens, database URLs, or secret values. Preserve sanitized error and
   revision information for the incident record.
7. Record the frontend/backend revisions, database snapshot or restore ID,
   migration compatibility decision, test results, log review, operator, and
   timestamp. Mark rollback successful only when all checks pass. Otherwise
   record it as failed, keep rollout stopped, and escalate without destructive
   retries.

### Staging backup and restore drill

Run this drill before relying on staging as a release gate, and repeat after
changes to database backup procedures:

1. Create a synthetic-only marker record in the isolated staging database and
   record its identifier and expected values.
2. Create a provider-managed snapshot of that staging database and record the
   snapshot ID and time.
3. Restore the snapshot into a separate temporary staging/test database using
   the provider's documented restore procedure. Never restore over production
   or use production data.
4. Point only an isolated verification backend at the restored temporary
   database, using a distinct temporary staging secret. Confirm migrations,
   `/health`, and synthetic user/coach/admin authentication checks work as
   applicable.
5. Confirm the marker record matches the expected values and inspect sanitized
   logs. Record elapsed recovery time, snapshot ID, checks, and any failures.
6. Remove the temporary database only through the provider's explicit
   staging-resource cleanup process after the drill is documented and the
   restored data is no longer needed. Do not issue broad or unreviewed
   destructive database commands.
