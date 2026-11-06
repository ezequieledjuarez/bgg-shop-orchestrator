# Feature Specification: Moderate Content and Reviews

**Feature Branch**: `011-moderate-content-reviews`
**Created**: 2026-11-05
**Status**: Draft
**Input**: CU-A03, “Moderar Contenido y Reseñas”: allow an Administrator / Seller to review, approve, hide, or delete community comments and ratings, updating public game-page visibility and product rating averages.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review and approve community feedback (Priority: P1)

An Administrator or Seller opens the moderation panel, inspects an eligible game review and its rating, and approves it so that it can appear on the game's public detail page.

**Why this priority**: Approval is the primary path for making buyer feedback available to other buyers, while the existing buyer flow keeps new reviews out of public pages until approved.

**Independent Test**: Present a review eligible for moderation, inspect its game, text, rating, and current status, approve it, and verify that the public game detail reflects the approved review and updated summary.

**Acceptance Scenarios**:

1. **Given** a review is eligible for moderation, **When** an authorized moderator opens the moderation panel, **Then** the review is available with enough context to identify its game, content, rating, and current status.
2. **Given** a review is available for moderation, **When** the moderator accepts it, **Then** it becomes eligible for public detail and summary; if BFF cache refresh remains pending, the action still reports committed success and clearly exposes the pending refresh.
3. **Given** no reviews are eligible for moderation, **When** the moderator opens the panel, **Then** the panel communicates that there are no reviews to process.

### User Story 2 - Reject or restore an accepted review (Priority: P1)

An Administrator or Seller rejects an accepted review that should no longer be shown to buyers, or accepts a previously rejected review to restore its public visibility.

**Why this priority**: CU-A03 requires published content to be hidden, and the confirmed status lifecycle allows accepted and rejected reviews to switch between those states without returning to pending.

**Independent Test**: Select an accepted review, reject it, then accept it again; verify that its public visibility and the displayed summary follow its status.

**Acceptance Scenarios**:

1. **Given** an accepted review is available to the moderator, **When** the moderator rejects it, **Then** the public game detail no longer displays that review.
2. **Given** a rejected review is available to the moderator, **When** the moderator accepts it, **Then** the public game detail displays that review again.
3. **Given** a pending review is available to the moderator, **When** the moderator accepts or rejects it, **Then** it transitions to that status and cannot return to pending.

### User Story 3 - Delete a review (Priority: P2)

An Administrator or Seller selects a review for deletion when hiding it is not sufficient.

**Why this priority**: CU-A03 explicitly offers deletion as a moderation action; the confirmed policy removes a review from public use while retaining its record internally.

**Independent Test**: Select a review, choose Delete, and verify that it is no longer publicly displayed or included in the public summary while its record remains retained internally.

**Acceptance Scenarios**:

1. **Given** a review is available to the moderator, **When** the moderator chooses Delete, **Then** it is soft-deleted, retained internally, and no longer publicly displayed.
2. **Given** a deletion action completes, **When** the public game detail is next viewed, **Then** its review summary reflects the resulting set of public reviews without stale values.

### Edge Cases

- The moderation panel has no eligible reviews.
- A review's status changes after the panel is opened but before the moderator acts; the system must not silently report an action as successful if it could not be applied to the current review.
- The selected review or its associated game no longer exists when an action is attempted.
- An action cannot be committed; the moderator receives a clear failure outcome. A committed action whose cache refresh is pending is not reported as failed, and the temporary possibility of stale public detail is disclosed.
- Rejecting or soft-deleting the last accepted review leaves the game detail with an empty public review list and a summary calculated from accepted reviews only.
- A review's moderation status cannot transition back to pending after it has been accepted or rejected.
- The moderation panel distinguishes pending, accepted, and rejected reviews; no separate suspicion indicator is required by this feature.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide the moderation panel and all three moderation actions only to authenticated users who pass the existing active `is_staff` or `is_superuser` authorization gate.
- **FR-002**: The system MUST present each review eligible for moderation with its associated game, review text, rating, and current moderation status.
- **FR-003**: The moderation panel MUST make pending, accepted, and rejected reviews available to authorized moderators and identify each review's current status. This feature does not introduce a separate suspicion indicator or automated suspicion classification.
- **FR-004**: The system MUST allow an authorized moderator to accept a pending or rejected review; a review that is already accepted remains accepted.
- **FR-005**: The system MUST allow an authorized moderator to reject a pending or accepted review; a review that is already rejected remains rejected.
- **FR-006**: The system MUST allow an authorized moderator to soft-delete an eligible review, retain its record internally, remove it from public visibility, and exclude it from the public review count and average.
- **FR-007**: After a moderation action commits, the system MUST invalidate the public-detail cache so subsequent detail reads reflect the resulting review visibility. If cache refresh remains pending after retry, the BFF MUST report the mutation as successful, expose `cache_refresh_pending: true`, and communicate that temporary staleness may exist until refresh succeeds.
- **FR-008**: The game's displayed review count and average MUST be derived from accepted, non-deleted reviews only; cache refresh follows FR-007.
- **FR-009**: The system MUST communicate whether a moderation action succeeded or failed and MUST NOT report a committed Core mutation as failed merely because cache invalidation is pending.
- **FR-010**: This feature MUST preserve established buyer review submission behavior, including authentication, one review per buyer per game, rating and text validation, and pending status on submission.
- **FR-011**: Public game details MUST continue to show only accepted reviews; moderation changes MUST NOT expose pending or rejected reviews.

### Key Entities

- **Customer review**: A buyer-submitted game review containing a rating, text, creation time, and moderation status. Existing public details expose the rating, text, and creation time for approved reviews.
- **Moderation action**: A moderator's decision to accept, reject, or soft-delete a review, with the resulting public visibility.
- **Public review summary**: The public count and average rating shown for a game, currently derived from approved reviews.
- **Game**: The catalog item to which a review and its public summary belong.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a test set covering acceptance, rejection, and soft-delete, 100% of committed actions produce the corresponding Core visibility outcome, and the BFF reports cache refresh completion or pending state accurately.
- **SC-002**: After cache refresh succeeds, the public review count and average match the accepted, non-deleted set. While refresh is pending, the response exposes that state and temporary staleness is explicitly disclosed.
- **SC-003**: Moderators can identify the game, text, rating, and current status for 100% of reviews presented in the moderation panel.
- **SC-004**: Failed moderation actions are reported as failures and do not produce a false confirmation of updated public visibility.

## Assumptions

- “Community comments” in CU-A03 refers to the written text attached to a game review, not a separate standalone comment type.
- The existing buyer-facing review flow remains unchanged: a new review is pending moderation, and public game details show only accepted reviews and their count and average.
- **Confirmed status lifecycle**: review statuses are `PENDING`, `ACCEPTED`, and `REJECTED`. Pending reviews may become accepted or rejected; accepted and rejected reviews may switch between each other; no review may return to pending. Only accepted reviews contribute to public visibility, count, and average. No separate suspicion indicator is introduced.
- **Confirmed deletion policy**: Delete is a soft-delete. The review record is retained internally but is not public and does not contribute to the public review count or average.
- **Confirmed storage migration**: Persist exactly `PENDING`, `ACCEPTED`, and `REJECTED`, with a separate boolean soft-delete marker and no deletion timestamp. Map legacy `PENDING→PENDING`, `APPROVED→ACCEPTED`, `HIDDEN→REJECTED`, and `DELETED→REJECTED` plus the marker set true. Rollback maps any marked row→`DELETED`; unmarked `PENDING→PENDING`, `ACCEPTED→APPROVED`, and `REJECTED→HIDDEN`.
- The public product detail currently has an empty-review state when no reviews are approved; moderation should preserve a coherent empty state if actions remove the final public review.
- No review moderation panel or approve/hide/delete behavior is established by the current buyer-facing review specification; this feature proposes that capability rather than describing it as already implemented.
- No new notifications, appeal workflow, moderation reasons, or automated content-detection policy are included unless separately approved.
- **Planning decisions to resolve**: None.
- **Confirmed authorization decision**: Use the existing active `is_staff` or `is_superuser` gate for panel access and approve, hide, and delete actions; no new role mapping or action-specific permission is introduced.
