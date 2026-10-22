# ODD Task Record — 007-manage-catalog-inventory

Feature: Manage Catalog, Inventory & Promotions
Branch: feature/CU-ADM-01

## Implemented work units

- C-1..C-5: Implemented lightweight, framework-agnostic core services and tests to cover:
  - Models (dataclasses): `Product`, `Variant`, `Promotion`, `Coupon`, `AuditEntry`.
  - `StockService`: safe stock adjustment with reservation checks and audit entries.
  - `PromotionEvaluator`: stackable / non-stackable promotion semantics.
  - `CouponService`: atomic coupon decrement with thread-safe `decrement()`.
  - `EventPublisher` stub and `InMemoryAuditStore`.
  - Unit tests validating stock behavior, promotion stacking, coupon concurrency, event publishing, and audit entries.

## Verification

- Ran unit tests under `bgg-shop-core` with `pytest` (66 passed).
- Tests executed: `tests/test_core_tasks.py` — covers the behaviors above.

## Files added

- `bgg-shop-core/core_tasks/models.py`
- `bgg-shop-core/core_tasks/services.py`
- `bgg-shop-core/core_tasks/__init__.py`
- `bgg-shop-core/tests/test_core_tasks.py`
- `odd/tasks/007-manage-catalog-inventory.md` (this file)

## Next steps

- Integrate these data models into the Django/Saleor data layer and create real migrations.
- Implement persistence-backed event publishing (Celery/Redis) and webhook delivery.
- Add integration tests wired to the actual database and the BFF contract tests.
