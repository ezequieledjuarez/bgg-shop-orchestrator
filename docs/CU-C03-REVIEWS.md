# CU-C03: Product reviews

## Implemented flow

The review flow is implemented through the existing service boundaries:

```text
Frontend React → BFF Flask REST → Core Django/GraphQL → PostgreSQL
```

The public product route is slug-based:

```text
/juegos/{slug}
```

The slug is derived from the unique game name. Internal product, user, and
review identifiers are not exposed to the Frontend.

## Persistence

`import_catalog.sql` defines `product_review` with:

- one review per authenticated user and game;
- rating from 1 to 5;
- body from 1 to 2000 characters;
- `PENDING`, `APPROVED`, `HIDDEN`, and `DELETED` states;
- foreign keys to `product_boardgame` and `auth_user`;
- indexes for user lookups and approved public reviews.

New reviews start as `PENDING`. Only `APPROVED` reviews contribute to the
public detail and average rating. Moderation is intentionally outside CU-C03.

## Core GraphQL

The Core exposes:

- `productBySlug(slug)`, returning product information, approved reviews, and
  the approved-review summary.
- `createReview(input)`, requiring the Bearer access token in the GraphQL
  request context.

The mutation accepts only `productSlug`, `rating`, and `body`. The Core
resolves the authenticated user from the token and returns explicit domain
errors for invalid input, missing products, unauthenticated requests, and
duplicate reviews.

## BFF REST

### Detail

```http
GET /api/v1/games/{slug}
```

### Create review

```http
POST /api/v1/games/{slug}/reviews
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "rating": 5,
  "body": "Excelente juego de estrategia."
}
```

Successful creation returns only:

```json
{
  "created": true,
  "status": "PENDING",
  "created_at": "2026-10-20T00:00:00Z"
}
```

The BFF keeps the controller, service, DTO, and GraphQL proxy responsibilities
separate. It forwards the token to Core and does not forward the internal
review object to the Frontend.

## Frontend behavior

The detail view handles loading, not-found, error, empty approved reviews,
authenticated submission, validation errors, duplicate submissions, and
pending moderation confirmation. The review request sends only `rating` and
`body`.

Catalog filters appear in this order:

1. Año de publicación
2. Mínimo de jugadores
3. Máximo de jugadores
4. Precio mínimo
5. Precio máximo

## Validation performed

- Core existing GraphQL tests: 6 passed.
- BFF existing tests: 19 passed.
- Frontend tests: 15 passed.
- Frontend OpenAPI types regenerated with `npm run generate:types`.
- Frontend lint completed with one pre-existing-style `set-state-in-effect`
  warning in the catalog loading effect.
- Frontend production build passed.
- Python compilation and `git diff --check` passed.

Full end-to-end PostgreSQL validation remains environment-dependent. The
database schema is loaded in the target environment, but this workspace does
not provide `psql` or running service containers for an independent database
execution check.

## Related commits

- `ece3221` — review persistence schema.
- `38aae5c` — Core GraphQL review contract.
- `a6e3f9b` — BFF slug-based review endpoints.

## Authentication copy correction

The login and registration screens now use Spanish for all visible copy:
labels, buttons, navigation, validation messages, service errors, and success
states. Routes, request payloads, session storage keys, and API error codes
remain unchanged.

The review persistence flow was also exercised against the loaded database by
the user; no additional schema change was required for this correction.

The Frontend authentication tests, full test suite, lint, and production build
were rerun after the translation.
