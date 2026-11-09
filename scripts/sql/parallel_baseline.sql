-- Only unmanaged commercial tables, before the real graphql migrations.
-- Sources: import_catalog.sql and tests/test_graphql_chat.py legacy review fixture.
CREATE TABLE product_boardgame (
    id SERIAL PRIMARY KEY,
    bgg_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(250) UNIQUE NOT NULL,
    release_year SMALLINT NOT NULL,
    min_players SMALLINT NOT NULL,
    max_players SMALLINT NOT NULL,
    playing_time_minutes SMALLINT NOT NULL,
    min_age SMALLINT NOT NULL,
    max_age SMALLINT NOT NULL DEFAULT 0,
    weight NUMERIC(3, 2) NOT NULL,
    category VARCHAR(250) NOT NULL,
    price_amount NUMERIC(12, 2) NOT NULL,
    publisher VARCHAR(150) NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    image_filename VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0)
);

CREATE TABLE product_review (
    id BIGSERIAL PRIMARY KEY,
    bgg_id INTEGER NOT NULL REFERENCES product_boardgame(bgg_id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    body VARCHAR(2000) NOT NULL CHECK (char_length(btrim(body)) BETWEEN 1 AND 2000),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_product_review_user_game UNIQUE (user_id, bgg_id),
    CONSTRAINT chk_product_review_status
        CHECK (status IN ('PENDING', 'APPROVED', 'HIDDEN', 'DELETED'))
);
CREATE INDEX idx_product_review_approved_game
    ON product_review (bgg_id, created_at) WHERE status = 'APPROVED';
CREATE INDEX idx_product_review_user ON product_review(user_id);

CREATE TABLE wishlist_entry (
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    bgg_id INTEGER NOT NULL REFERENCES product_boardgame(bgg_id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, bgg_id)
);
CREATE TABLE shopping_cart (
    cart_id UUID PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES auth_user(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE shopping_cart_line (
    cart_id UUID NOT NULL REFERENCES shopping_cart(cart_id) ON DELETE CASCADE,
    bgg_id INTEGER NOT NULL REFERENCES product_boardgame(bgg_id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (cart_id, bgg_id)
);
CREATE SEQUENCE purchase_invoice_number_seq;
CREATE TABLE purchase_order (
    id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    status VARCHAR(32) NOT NULL DEFAULT 'pending_payment',
    total NUMERIC(12, 2) NOT NULL CHECK (total >= 0),
    currency VARCHAR(3) NOT NULL,
    shipping_mode VARCHAR(16) NOT NULL,
    recipient VARCHAR(250),
    street VARCHAR(500),
    city VARCHAR(150),
    postal_code VARCHAR(32),
    phone VARCHAR(50),
    mp_preference_id VARCHAR(128),
    mp_payment_id VARCHAR(128),
    payment_status VARCHAR(32),
    payment_status_detail VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMPTZ,
    CONSTRAINT chk_purchase_order_status CHECK
        (status IN ('pending_payment', 'paid', 'rejected', 'cancelled', 'paid_stock_conflict')),
    CONSTRAINT chk_purchase_order_shipping_mode CHECK (shipping_mode IN ('standard', 'pickup'))
);
CREATE INDEX idx_purchase_order_user_created ON purchase_order(user_id, created_at DESC);
CREATE TABLE purchase_order_line (
    order_id UUID NOT NULL REFERENCES purchase_order(id) ON DELETE CASCADE,
    bgg_id INTEGER NOT NULL REFERENCES product_boardgame(bgg_id) ON DELETE RESTRICT,
    name VARCHAR(250) NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    subtotal NUMERIC(12, 2) NOT NULL CHECK (subtotal >= 0),
    PRIMARY KEY (order_id, bgg_id)
);
CREATE TABLE invoice (
    order_id UUID PRIMARY KEY REFERENCES purchase_order(id) ON DELETE CASCADE,
    number BIGINT NOT NULL DEFAULT nextval('purchase_invoice_number_seq'),
    issued_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total NUMERIC(12, 2) NOT NULL CHECK (total >= 0)
);
CREATE TABLE gift_card (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code_hash BYTEA NOT NULL UNIQUE CHECK (octet_length(code_hash) = 32),
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    redeemed_at TIMESTAMPTZ,
    redeemed_by INTEGER REFERENCES auth_user(id) ON DELETE RESTRICT,
    CONSTRAINT chk_gift_card_redemption CHECK ((redeemed_at IS NULL) = (redeemed_by IS NULL))
);
