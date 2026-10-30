# Credit Migration And Recovery

## Scope

This procedure covers local PostgreSQL credit migrations `graphql.0001_credit_accounts` through `0011_credit_retry_attempt_release`. It is a recovery plan, not authorization to modify an existing database. Migrations 0001 through 0005 and 0007 through 0011 are irreversible through Django; do not use `migrate graphql <earlier version>`, delete migration records, or drop credit tables as a rollback. Migration 0006 only creates a reversible index; reversing it is still an operational change that may affect performance and requires review. Migration 0007 changes the review foreign key to reference the purchase order, allowing reviews without a credit retry guard; it does not delete existing review or resolution records. Migration 0008 adds the release audit table and requires an existing resolution for each release. Migration 0009 assigns each existing and future retry attempt a unique UUID using PostgreSQL's `gen_random_uuid()`; verify function availability and database compatibility before deployment. Migration 0010 adds a durable observation table without requiring the attempt to remain present. Migration 0011 adds the manual-release audit and a record for provider preference responses received after release.

The current Core Mercado Pago checkout and retry paths also depend on the credit tables. Stop writers and coordinate the schema and code versions before starting those paths. A restore does not cancel or reconcile provider payments or previously issued payment links.

## Preconditions

1. Identify the exact source database and schema. Stop all writers, including Core, BFF clients, background jobs, and any external writers. Keep them stopped through backup and migration verification.
2. Confirm the existing commercial schema supplies `auth_user`, `gift_card`, `purchase_order`, `purchase_order_line`, `product_boardgame`, `shopping_cart`, `shopping_cart_line`, `wishlist_entry`, and `invoice`. Check column types, primary and foreign keys, constraints, and compatibility with the migration SQL; table names alone are not sufficient.
3. Confirm the `django_migrations` history matches the actual schema. The first credit migration depends on Django authentication and an externally provisioned `gift_card`; the second also requires the existing `purchase_order`. Partially created tables or constraints without matching history need separate investigation. Do not use fake migrations to bypass a mismatch.
4. Do not run the complete `import_catalog.sql` against an existing database as a migration. It contains seed writes, inventory updates, and deletes, and its preliminary seeds require tables that may not yet exist.
5. Preserve the Django `SECRET_KEY` and applicable `SECRET_KEY_FALLBACKS` securely outside the database backup. Credit idempotency fingerprints depend on those keys; restoring the database with unrelated keys can turn valid retries into conflicts. Do not print or commit keys, tokens, or gift card codes.

Core reads `SECRET_KEY_FALLBACKS` as a JSON array of nonempty strings; an unset value defaults to an empty array. Supply previous keys through the environment or an approved secret manager, without recording their values in files or logs. This allows credit idempotency retries after a reviewed key rotation, but GraphQL JWT authentication uses only the current `SECRET_KEY`, so existing access tokens become invalid. With `DEBUG` disabled, Core rejects a short or clearly weak current key; this check does not prove that a key is unpredictable. The local compose configuration enables `DEBUG` and retains a known development default, so it is not a secure deployment configuration.

With a deliberately configured read-only connection, inspect the target before any write:

```sql
BEGIN READ ONLY;
SELECT current_database(), current_schema();
SELECT name, to_regclass(name) AS relation
FROM unnest(ARRAY[
  'auth_user', 'gift_card', 'purchase_order', 'purchase_order_line',
  'product_boardgame', 'shopping_cart', 'shopping_cart_line',
  'wishlist_entry', 'invoice', 'django_migrations'
]) AS required(name);
SELECT name, applied FROM django_migrations WHERE app = 'graphql' ORDER BY name;
COMMIT;
```

If any prerequisite, schema definition, or migration history is uncertain, stop. Do not infer that applying or reversing a migration is safe.

## Backup And Migration

1. Take a consistent full-database backup after stopping writers. Store it securely with restricted access; it can contain account and order data. Retain the matching application version and secret-key configuration separately.
2. Verify the archive can be listed and restore it into a **new isolated database** before relying on it. For example, with `SOURCE_SERVICE` and `RESTORE_SERVICE` already configured as distinct PostgreSQL service names and credentials managed outside the command line:

   ```bash
   umask 077
   pg_dump --format=custom --file="$BACKUP_FILE" --dbname="service=$SOURCE_SERVICE"
   pg_restore --list "$BACKUP_FILE"
   pg_restore --exit-on-error --no-owner --no-acl --dbname="service=$RESTORE_SERVICE" "$BACKUP_FILE"
   ```

   The restore target must be newly created and empty. `--no-owner --no-acl` requires separately restoring and checking the target's ownership and access policy before any use. Do not point the restore command at the active database.
3. In the isolated copy, apply the migrations with the matching Core code and inspect `python manage.py showmigrations graphql`. Verify the migration history, credit balances, gift card redemption state, order/payment ownership, invoices, inventory, and idempotent retries.
4. Only after review and explicit authorization, run migrations on the intended target while writers remain stopped. If migration fails, retain the database and logs for investigation. Do not automatically retry with schema edits, fake migration records, or a destructive import.

## Recovery After A Failure

- Keep writers stopped. Record whether any credit, card, order, stock, or provider activity occurred after the backup. A backup taken before those changes cannot reproduce them; restoring it over later activity would lose data.
- Take and retain a separate backup of the post-failure state before considering recovery. Restore both backups only into distinct isolated databases and compare migration history and financial records. Use the corresponding secret-key configuration without exposing it.
- If writes or provider activity occurred after the pre-migration backup, reconciliation and a reviewed recovery procedure are required before any cutover. Core records administrator observations and explicit releases for ambiguous attempts, but does not independently verify their provider outcomes.
- Only an explicitly authorized, reviewed cutover can replace the active database. Do not apply the isolated restore directly to it or claim that restoring a pre-migration snapshot preserves later transactions.

## Verification Evidence

- Automated PostgreSQL tests execute Django's `MigrationExecutor` for all five credit migrations in a disposable schema, check migration records and preserved synthetic data, confirm repeated migration is a no-op, and verify the fifth migration raises `IrreversibleError` on reversal. The fixture uses a minimal commercial schema and marks synthetic authentication migrations as already applied; it is not a complete existing deployment.
- A separate `MigrationExecutor` test applied, reversed, and reapplied the 0006 index in a disposable schema without deleting synthetic idempotency records. Creating the index on an existing database may take locks and must be planned for that database.
- A separate disposable PostgreSQL database with Django authentication, selected commercial DDL, and all three credit migrations was populated with a synthetic redemption and credit purchase. A custom-format `pg_dump` was restored with `pg_restore --no-owner --no-acl` into a new empty database. Balance, stock, redemption, orders, payments, transactions, invoices, idempotency records, and migration records matched; constraints were validated and no orphan payment or transaction was found.
- On the restored copy, using the same synthetic secret key, retrying the prior checkout returned its original snapshot without creating another payment. These checks do not validate production access policies, external payment reconciliation, a restore into the active database, or preservation of writes after a backup.
- The earlier backup/restore test covered migrations through 0003, not review or resolution records from 0004 and 0005. A later synthetic test covered all migrations through 0011 as described below.
- A read-only inspection of the active local `saleor` database found PostgreSQL 15.19, the named commercial tables, `gen_random_uuid()`, no `graphql` migration records and no credit tables. Its Django migration plan lists 0001 through 0011. Its schema and migration history were copied separately while services remained active to a disposable empty database, where all 11 migrations succeeded and a repeated migration was a no-op. This does not establish a coordinated snapshot, data preservation or permission to migrate the active database.
- A full synthetic database containing all 11 migrations and synthetic review, attempt and release audit rows was backed up to a custom-format file with mode `600`, listed and restored to a new empty database. Counts and content matched in 21 selected tables; 137 constraints were validated and all 11 migration records were present. An authenticated GraphQL replay with the same synthetic signing key returned the original paid order without changing payments, invoices, balance or stock. A streaming restore was also checked. These tests did not back up active application data or validate access policies or post-backup changes.

## Late Payments

This section documents existing behavior retained for operational safety. Late-payment handling, discovery, reviews, scheduling and notifications are excluded from remaining feature work by user request; this exclusion does not prove the associated risk has been resolved.

After migration 0007, an approved payment presented to Core confirmation for a guarded order, an earlier preference, or an unverifiable preference is recorded in `credit_payment_review`; repeats of the same order and payment are deduplicated. Core verifies the merchant order's payment membership, seller, order reference, and preference before crediting an approved payment. Missing or inconsistent merchant-order details go to review. The existing order, credit purchase, inventory, and invoice are not changed, and no refund is initiated. Administrators can inspect detected records with Core's `adminPaymentReviews(page, pageSize)` GraphQL query; non-administrators are denied. `creditOrderId` is null for reviews without an associated credit purchase, so consumers must accept the updated GraphQL contract. Pages use offsets, so new records can shift results while paging: repeat the scan and do not treat it as a completeness guarantee. This query is not exposed through the BFF or an administrator screen. Authorized operators can also inspect the records using a read-only database connection:

```sql
SELECT review.detected_at, review.order_id, review.payment_id, purchase.user_id, guard.credit_order_id
FROM credit_payment_review AS review
JOIN purchase_order AS purchase ON purchase.id = review.order_id
LEFT JOIN credit_retry_guard AS guard ON guard.order_id = review.order_id
ORDER BY review.detected_at, review.order_id, review.payment_id;
```

Administrators can close a detected case through Core's `resolvePaymentReview` mutation by supplying the order ID, payment ID, action taken, and reason. The record includes the authenticated administrator and server timestamp. Repeating an identical request by the same administrator returns the original resolution; a different later attempt is rejected. The application does not alter an existing resolution, issue a refund, or remove a retry guard. The operator's statement is not independent evidence that a provider action occurred. Do not put credentials, gift card codes, or unnecessary personal data in the action or reason; restrict access to both the review and resolution records. Database-level administrators can still modify these records, so database access controls and backups remain essential.

An order with an unreleased review cannot be retried, and an unguarded unreleased review also blocks the buyer's credit checkout. After resolving a review, an administrator may explicitly call Core's `releasePaymentReview(orderId, paymentId, reason)` mutation. The release records the authenticated actor, reason and server timestamp; identical retries by the same administrator are idempotent, while conflicting releases are rejected. The administrative review query exposes the release audit. Each payment must be released separately, and a newly detected payment blocks again. A previously reviewed payment is never automatically credited when presented again, even after release.

Release does not refund or credit a payment, change order status, remove a credit retry guard, reconcile a provider attempt or revoke an old provider preference. Guards, pending attempts, pending orders, and other unreleased reviews remain independently effective. An operator must investigate the provider-side payment and any still-payable preferences before authorizing release; the application does not independently verify the operator's action. A previously recorded credit checkout rejection remains idempotent for its retention period; after release a new checkout requires a new idempotency key. Do not delete audit records or guards to bypass these protections. The query and mutations are available only through Core GraphQL, not through the BFF or an administrator screen.

Core provides `python manage.py discover_credit_payments` as a read-only preview of a bounded batch; without `--apply`, it makes no provider requests. After explicitly authorizing the target database, Mercado Pago sandbox account and credentials, an operator may run `python manage.py discover_credit_payments --apply` to search guarded orders. It requires `MP_SANDBOX` and a configured token, but that flag does not prove the token belongs to a sandbox account. It searches approved payments, fetches each payment again, and checks its ID and order reference. A payment with `live_mode=false` is accepted; for `live_mode=true`, Core also queries the token's account and requires its `test_user` tag and ID to match the payment's collector ID. Missing or malformed modes and failed identity checks are rejected. The same check applies to payment confirmation. Two approved payments belonging to an observed test seller had `live_mode=true`; the identity check accepted both in an authorized read-only verification. This observation does not establish the behavior of every provider account. It does not issue refunds, unblock attempts, or change orders, balances, stock or invoices. Each provider request has a ten-second timeout without SDK retries. Payments with `live_mode=true` require an additional identity request per lookup. Defaults limit a run to 10 orders, 10 pages per order and 100 payment lookups; `--max-orders`, `--max-pages` and `--max-lookups` can set bounded limits. The implementation uses the locally tested Mercado Pago Python SDK 3.6.x.

If more guarded orders exist, the command reports a cursor for `--after`; start a later complete scan from the beginning because new orders can sort before an earlier cursor. A failure leaves the current order unmodified, but previously completed orders may already have review records; rerunning is idempotent. A search result is not proof that no payment exists: [Mercado Pago documents a 12-month search window](https://www.mercadopago.com.ar/developers/es/reference/online-payments/checkout-api-payments/search-payments/get), results may change during pagination, and missing or non-sandbox verification fails closed. A single order exceeding the configured lookup or page limit requires separate investigation; the command does not save a partial result for that order. The command is not scheduled and has only been tested end-to-end with a simulated provider. Do not execute it against an actual account or active database without separate explicit authorization.

This is not a complete reconciliation workflow: there is no scheduled discovery, notification, provider verification of a reported resolution, or automatic refund. Ambiguous provider attempts have a separate administrator observation and release audit, described below, but no independent verification of the reported outcome. Until the remaining controls are implemented and verified, outstanding late payments remain a delivery blocker. The query and mutation are not exposed through the BFF or an administrator screen.

## Ambiguous Attempts

Administrators can inspect outstanding initial provider attempts and retries through Core GraphQL `adminPaymentAttempts(page, pageSize)`. Each attempt has a unique `attemptId`, order ID, buyer ID, order status and optional preference ID. An entry may represent an active request rather than a stalled attempt; the list alone does not establish provider outcome. Offset pagination may shift as attempts are added or removed.

`recordPaymentAttemptObservation(orderId, attemptId, requestId, statement)` records an administrator's statement, actor, timestamp and the preference ID observed under the attempt lock. The `requestId` is a caller-generated UUID: repeating the same request by the same actor returns the same observation, while reusing it with different data is rejected. `adminPaymentAttemptObservations(attemptId, page, pageSize)` retrieves the history, including after the attempt is removed. Access is restricted to administrators and errors are sanitized. The application exposes no edit or delete operation for observations; database access controls and backups remain necessary. Avoid putting credentials, gift card codes or unnecessary personal data in statements.

Recording an observation does not query the provider, prove a payment absent, resolve the attempt or release any guard. Retry attempts, orders and balances are not modified.

After investigating the provider outcome, an administrator can explicitly call `releasePaymentAttempt(orderId, attemptId, observationId, reason, acknowledgeRisk: true)`. The observation must belong to the same current attempt and its preference snapshot must still match; otherwise release is rejected. The application does not verify the administrator's statement or prove that an older preference cannot be paid. The release records the actor, reason, accepted risk and timestamp, and removes only that retry-attempt block. Repeating the same request by the same actor is idempotent; conflicting releases are rejected. `adminPaymentAttemptRelease(attemptId)` retrieves the audit after the attempt has been removed. Other review blocks, credit guards, pending orders and their existing rules remain effective; release does not change an order, balance, stock or invoice and does not refund or cancel a provider preference.

If an in-flight preference request returns after its attempt was released, Core does not apply its response to a newer attempt or return its payment link. It records the returned preference ID, without the link, in `providerResponse` on `adminPaymentAttemptRelease`. The record is available only if Core receives the response; its absence does not prove no preference was created. It does not cancel the earlier preference or automatically block a newer one. Operators must investigate the provider state and explicitly accept this risk before release. These operations are only exposed through Core GraphQL, not the BFF or an admin screen. Migrations 0009 through 0011 were tested in disposable PostgreSQL and have not been applied to the active database.

## Rejection Retention

Core retains recorded idempotency rejections for 30 days. At or after that age the same key can be processed as a new request; successful records are not expired by this policy. Requests remove expired rejections for their own buyer while holding that buyer's account lock. Entries for inactive buyers remain until an authorized maintenance run. Time-based expiration requires a trustworthy application clock.

`python manage.py prune_credit_rejections` reports the number of eligible records without changing them. After verifying the target database, a backup, and explicit authorization, `python manage.py prune_credit_rejections --apply --batch-size 100 --max-batches 10` removes at most 1,000 expired rejections per run. It uses PostgreSQL account locks and skips accounts currently in use; more entries may remain and a later run may be needed. Successful records and rejections younger than 30 days are not removed. The command is not automatically scheduled; scheduling and monitoring require deployment review. Do not run it against an active database without authorization.