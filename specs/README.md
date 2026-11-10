# Feature specification ownership

## Canonical cross-service feature definitions

Cross-service feature behavior is defined once in the orchestrator repository
under `specs/<feature>/spec.md`. The as-built canonical specifications for
features 001–006 are:

- [001 — Customer Authentication](001-authentication-as-built/spec.md)
- [002 — Catalog Search and Filters](002-catalog-search-filters-as-built/spec.md)
- [003 — Product Detail and Reviews](003-product-detail-reviews-as-built/spec.md)
- [004 — Shopping Cart](004-shopping-cart-as-built/spec.md)
- [005 — Checkout, Orders, and Invoice](005-checkout-orders-invoice-as-built/spec.md)
- [006 — Wishlist](006-wishlist-as-built/spec.md)

Other root entries under `specs/` document additional features and engineering
work. The service repositories' matching `spec.md` files for features 001–006
are pointer pages to these canonical definitions, not alternate feature
requirements.

## Service-owned evidence and contracts

Core, BFF, and Frontend retain their feature-local `plan.md` and `tasks.md` as
layer-specific design and execution evidence. Authoritative service contracts,
including the Core GraphQL schema and BFF OpenAPI document, remain in their
owning service repositories under `specs/`.

Service-only engineering notes may remain in their existing flat locations.
Moving those notes is a separate link-aware migration; their presence does not
make them competing cross-service feature specifications.
