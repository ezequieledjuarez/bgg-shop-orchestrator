# Gift Card Credit: Follow-up

The initial non-production scope is closed. These items are not completed by that closure and require separate authorization before implementation, deployment, active-database changes, or provider operations. Historical verification is recorded in [the implementation tasks](../../odd/tasks/gift-card-credit.md).

## Deployment And Operations

- [ ] Before migrating the active database, review the target and permissions, stop writers, take a coordinated backup, verify restoration in isolation, and obtain explicit authorization. Apply the migrations and verify the resulting deployment only after those prerequisites are met. Follow [the migration and recovery procedure](migration-recovery.md).
- [ ] Review deployment security configuration, including replacement of known development signing defaults and a recovery plan for existing signing keys and credit idempotency fingerprints.
- [ ] Review historical diagnostic files for possible exposed secrets under an authorized procedure; assess whether affected credentials require rotation. Previous files have not been inspected or removed.
- [ ] Review broader application logging and concurrency risks. Existing regression and lock tests do not prove that all sensitive logs or deadlocks have been eliminated.
- [ ] Decide whether to schedule and monitor cleanup of expired idempotency rejections. The cleanup command has only been tested in disposable PostgreSQL and is not authorized for the active database.

## Deferred Functionality And Payment Risks

- [ ] When cancellation is implemented, define eligibility and restore the full credit payment exactly once for a cancelled credit-funded order.
- [ ] Address late provider payments and reconciliation separately, including discovery, notification, and verification of operator actions. This work was excluded from the remaining feature scope; existing provider preferences may remain payable, and manual release does not revoke them or prove the provider outcome.
- [ ] Verify the agreed choice between credit and Mercado Pago in the applicable checkout flow, subject to existing payment safety rules and without split payments.

## Deferred Or Waived Validation

- [ ] If provider-backed validation is later required, authorize an appropriate sandbox environment and verify the authenticated end-to-end flow and return using a suitable non-local URL. Return validation was waived for the practical project; the prior sandbox confirmation used simulated authentication.
- [ ] If required for the intended deployment, test connection loss between BFF and Core and recovery of a delivery address. The completed interruption test covered browser-to-BFF loss and pickup in the same tab.
- [ ] If cross-tab or closed-tab recovery becomes a requirement, define the desired behavior and validate it, including popup-with-opener and browser restoration. It is not required for the current same-tab scope.