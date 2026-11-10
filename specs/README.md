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

## Service feature directories, evidence, and contracts

Core, BFF, and Frontend group service-owned materials in
`specs/<feature>/`. These files record layer-specific design, implementation,
and verification evidence; they do not replace the canonical cross-service
product spec. CU-A01's older requirement task ledgers are named
`006-manage-catalog-inventory/legacy-requirements-tasks.md`, separately from
the current CU-A01 implementation artifacts under
`007-manage-catalog-inventory/`. CU-A02 service ledgers live at
`010-sales-metrics-reports/tasks.md`. Service-only notes, such as Core's
operations-and-keys notes, are grouped with their related feature materials
without becoming cross-service requirements.

Authoritative contracts remain in their owning service repositories and stay
flat under `specs/`: Core's `schema.graphql` and BFF's `openapi.yaml`. Feature
grouping does not relocate or duplicate either contract.
