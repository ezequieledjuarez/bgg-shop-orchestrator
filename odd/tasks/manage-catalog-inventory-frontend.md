# Feature: Manage Catalog & Inventory - Frontend

## Goal
Implement admin UI for managing products, inventory, and promotions as defined in specs/007-manage-catalog-inventory-frontend.md

## Tasks
- scaffold admin router and routes: `/admin/products`, `/admin/products/new`, `/admin/promotions`
- implement `ProductsList` component (skeleton) wired to BFF `/admin/products` endpoint
- implement `ProductForm` component (skeleton) with client-side validation hooks
- implement `PromotionsPanel` skeleton and preview placeholder
- add unit tests placeholders for form validation
- add basic navigation link from app shell to `/admin`

## Acceptance
- Routes render without crashing
- Components contain placeholders and prop types

## Notes
- This is the initial scaffold; wiring to BFF endpoints and E2E tests will follow in subsequent tasks.
