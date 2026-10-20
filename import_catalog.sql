-- ==============================================================================
-- 1. DDL: Creación de la Tabla 'product_boardgame'
-- ==============================================================================

CREATE TABLE IF NOT EXISTS product_boardgame (
    id SERIAL PRIMARY KEY,
    bgg_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(250) UNIQUE NOT NULL,
    release_year SMALLINT NOT NULL,
    min_players SMALLINT NOT NULL,
    max_players SMALLINT NOT NULL,
    playing_time_minutes SMALLINT NOT NULL,
    min_age SMALLINT NOT NULL,
    weight NUMERIC(3, 2) NOT NULL,            -- Escala BGG (1.00 - 5.00)
    category VARCHAR(250) NOT NULL,
    price_amount NUMERIC(12, 2) NOT NULL,     -- Precisión monetaria fija
    publisher VARCHAR(150) NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    image_filename VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0)
);

ALTER TABLE product_boardgame
    ADD COLUMN IF NOT EXISTS quantity INTEGER NOT NULL DEFAULT 0
    CHECK (quantity >= 0);

-- ==============================================================================
-- 2. DML: Inserción Masiva de Datos (49 Registros)
-- ==============================================================================

INSERT INTO product_boardgame (
    bgg_id, name, release_year, min_players, max_players,
    playing_time_minutes, min_age, weight, category,
    price_amount, publisher, image_url, image_filename
) VALUES
    (274364, 'Watergate', 2019, 2, 2, 60, 12, 2.25, 'Juegos de Estrategia', 90000.00, 'Salt & Pepper Games', '/media/portadas/2743640.webp', '2743640.webp'),
    (230244, 'Black Angel', 2019, 1, 4, 120, 12, 3.82, 'Juegos de Estrategia', 186000.00, 'Asmodee Pearl Games', '/media/portadas/2302440.webp', '2302440.webp'),
    (272409, 'Pequeñas Grandes Tácticas', 2019, 1, 4, 60, 14, 0.24, 'Juegos de Estrategia', 101800.00, 'Devir', '/media/portadas/2724090.webp', '2724090.webp'),
    (241451, 'Aeon''s End: Legacy', 2019, 1, 4, 90, 14, 2.84, 'Juegos de Estrategia, Juegos Temáticos', 181500.00, 'SD Games', '/media/portadas/2414510.webp', '2414510.webp'),
    (297030, 'Tekhenu: El Obelisco del Sol', 2020, 1, 4, 120, 14, 4.01, 'Juegos de Estrategia', 193200.00, 'Maldito Games', '/media/portadas/2970300.webp', '2970300.webp'),
    (286096, 'Tapestry', 2019, 1, 5, 120, 12, 2.98, 'Juegos de Estrategia', 203000.00, 'Maldito Games', '/media/portadas/2860960.webp', '2860960.webp'),
    (256916, 'Paladines del Reino del Oeste', 2019, 1, 4, 120, 12, 3.73, 'Juegos de Estrategia', 140000.00, 'Ediciones Primigenias', '/media/portadas/2569160.webp', '2569160.webp'),
    (266830, 'Dune (2019)', 2019, 2, 6, 120, 14, 3.51, 'Juegos de Estrategia, Juegos Temáticos', 165000.00, 'Gale Force Nine', '/media/portadas/2668300.webp', '2668300.webp'),
    (287936, 'Marco Polo II: Al Servicio del Khán', 2019, 1, 4, 120, 12, 3.57, 'Juegos de Estrategia', 155000.00, 'Devir', '/media/portadas/2879360.webp', '2879360.webp'),
    (283863, 'Kitchen Rush (Edición Revisada)', 2019, 1, 4, 60, 8, 2.15, 'Juegos de Estrategia, Juegos Familiares', 125000.00, 'MasQueOca', '/media/portadas/2838630.webp', '2838630.webp'),
    (284083, 'El Banquete de Odín: Los Noruegos', 2019, 1, 4, 120, 12, 4.15, 'Juegos de Estrategia', 110000.00, 'Devir', '/media/portadas/2840830.webp', '2840830.webp'),
    (285905, 'Amun-Re: El Juego de Cartas', 2019, 3, 5, 45, 12, 2.00, 'Juegos de Estrategia', 65000.00, 'Allplay', '/media/portadas/2859050.webp', '2859050.webp'),
    (266507, 'Clank! Legacy: Adquisiciones Incorporadas', 2019, 2, 4, 120, 13, 2.70, 'Juegos de Estrategia, Juegos Temáticos', 215000.00, 'Devir', '/media/portadas/2665070.webp', '2665070.webp'),
    (281259, 'Isla de Gatos', 2019, 1, 4, 90, 8, 2.36, 'Juegos de Estrategia, Juegos Familiares', 145000.00, 'Maldito Games', '/media/portadas/2812590.webp', '2812590.webp'),
    (266192, 'Res Arcana', 2019, 2, 4, 60, 12, 2.37, 'Juegos de Estrategia', 115000.00, 'Asmodee / Sand Castle Games', '/media/portadas/2661920.webp', '2661920.webp'),
    (251247, 'Tainted Grail: La Caída de Ávalon', 2019, 1, 4, 120, 14, 3.32, 'Juegos Temáticos, Juegos de Estrategia', 240000.00, 'Maldito Games / Awaken Realms', '/media/portadas/2512470.webp', '2512470.webp'),
    (284378, 'ZOOM In Barcelona', 2019, 2, 6, 45, 8, 1.80, 'Juegos Familiares', 72000.00, 'Catan Studio / Devir', '/media/portadas/2843780.webp', '2843780.webp'),
    (269207, 'Cooper Island', 2019, 1, 4, 120, 12, 4.18, 'Juegos de Estrategia', 178000.00, 'Maldito Games', '/media/portadas/2692070.webp', '2692070.webp'),
    (271320, 'Draftosaurus', 2019, 2, 5, 15, 8, 1.25, 'Juegos Familiares', 55000.00, 'Zebra Games / Ankama', '/media/portadas/2713200.webp', '2713200.webp'),
    (286063, 'Teotihuacan: La Sombra de Xibalba', 2019, 1, 4, 120, 14, 3.75, 'Juegos de Estrategia', 85000.00, 'Maldito Games', '/media/portadas/2860630.webp', '2860630.webp'),
    (282433, 'Praga Caput Regni', 2020, 1, 4, 120, 12, 3.73, 'Juegos de Estrategia', 185000.00, 'Arrakis Games', '/media/portadas/2824330.webp', '2824330.webp'),
    (312480, 'Dune: Imperium', 2020, 1, 4, 120, 14, 3.05, 'Juegos de Estrategia, Juegos Temáticos', 198000.00, 'Asmodee / Dire Wolf', '/media/portadas/3124800.webp', '3124800.webp'),
    (284108, 'Las Ruinas Perdidas de Arnak', 2020, 1, 4, 120, 12, 2.91, 'Juegos de Estrategia', 175000.00, 'Devir / CGE', '/media/portadas/2841080.webp', '2841080.webp'),
    (295770, 'Gloomhaven: Mandíbulas del León', 2020, 1, 4, 120, 14, 3.11, 'Juegos Temáticos, Juegos de Estrategia', 162000.00, 'Asmodee / Cephalofair', '/media/portadas/2957700.webp', '2957700.webp'),
    (287923, 'Anachrony: Fractures of Time', 2020, 1, 4, 150, 15, 4.50, 'Juegos de Estrategia', 135000.00, 'Maldito Games / Mindclash', '/media/portadas/2879230.webp', '2879230.webp'),
    (302260, 'Viscondes del Reino del Oeste', 2020, 1, 4, 90, 12, 3.45, 'Juegos de Estrategia', 142000.00, 'Ediciones Primigenias', '/media/portadas/3022600.webp', '3022600.webp'),
    (291457, 'Calico', 2020, 1, 4, 45, 10, 2.21, 'Juegos Familiares, Juegos de Estrategia', 88000.00, 'Maldito Games / Flatout', '/media/portadas/2914570.webp', '2914570.webp'),
    (316554, 'Dune: Imperium - El Auge de IX', 2021, 1, 4, 120, 14, 3.38, 'Juegos de Estrategia', 112000.00, 'Asmodee / Dire Wolf', '/media/portadas/3165540.webp', '3165540.webp'),
    (314040, 'MicroMacro: Crime City', 2020, 1, 4, 45, 12, 1.24, 'Juegos Familiares', 68000.00, 'SD Games / Edition Spielwiese', '/media/portadas/3140400.webp', '3140400.webp'),
    (285192, 'DESTINIES', 2021, 1, 3, 120, 14, 2.05, 'Juegos Temáticos', 148000.00, 'Lucky Duck Games', '/media/portadas/2851920.webp', '2851920.webp'),
    (290448, 'Merv: El Corazón de la Ruta de la Seda', 2020, 1, 4, 90, 14, 3.61, 'Juegos de Estrategia', 168000.00, 'Maldito Games / Osprey', '/media/portadas/2904480.webp', '2904480.webp'),
    (296880, 'Bonfire', 2020, 1, 4, 100, 12, 3.74, 'Juegos de Estrategia', 172000.00, 'Maldito Games / Hall Games', '/media/portadas/2968800.webp', '2968800.webp'),
    (300582, 'Beyond the Sun', 2020, 1, 4, 120, 14, 3.53, 'Juegos de Estrategia', 195000.00, 'Maldito Games / Rio Grande', '/media/portadas/3005820.webp', '3005820.webp'),
    (310873, 'Caral', 2022, 2, 4, 90, 12, 2.80, 'Juegos de Estrategia', 128000.00, 'Maldito Games', '/media/portadas/3108730.webp', '3108730.webp'),
    (298047, 'Polynesians', 2020, 2, 4, 75, 12, 2.40, 'Juegos de Estrategia', 95000.00, 'Ludonova', '/media/portadas/2980470.webp', '2980470.webp'),
    (284380, 'Tapestry: Planes y Maniobras', 2020, 1, 5, 120, 12, 3.10, 'Juegos de Estrategia', 82000.00, 'Maldito Games', '/media/portadas/2843800.webp', '2843800.webp'),
    (312251, 'Unmatched: Cobble & Fog', 2020, 2, 4, 45, 14, 2.12, 'Juegos Temáticos', 105000.00, 'TCG Factory / Restoration', '/media/portadas/3122510.webp', '3122510.webp'),
    (317072, 'Iwari', 2020, 2, 5, 45, 14, 2.28, 'Juegos de Estrategia', 132000.00, 'TCG Factory / Thundergryph', '/media/portadas/3170720.webp', '3170720.webp'),
    (306188, 'Kemet: Sangre y Arena', 2021, 2, 5, 120, 14, 3.35, 'Juegos de Estrategia, Juegos Temáticos', 210000.00, 'Maldito Games / Matagot', '/media/portadas/3061880.webp', '3061880.webp'),
    (282524, 'Nidavellir', 2020, 2, 5, 45, 10, 2.02, 'Juegos de Estrategia, Juegos Familiares', 92000.00, 'Maldito Games / GRRRE Games', '/media/portadas/2825240.webp', '2825240.webp'),
    (316552, 'Cascardia', 2021, 1, 4, 45, 10, 2.07, 'Juegos Familiares, Juegos de Estrategia', 89000.00, 'Delirium Games / Flatout', '/media/portadas/3165520.webp', '3165520.webp'),
    (342942, 'Ark Nova', 2021, 1, 4, 150, 14, 3.73, 'Juegos de Estrategia', 225000.00, 'Maldito Games / Feuerland', '/media/portadas/3429420.webp', '3429420.webp'),
    (318084, 'Golem', 2021, 1, 4, 120, 14, 3.98, 'Juegos de Estrategia', 188000.00, 'Maldito Games / Cranio', '/media/portadas/3180840.webp', '3180840.webp'),
    (312680, '7 Wonders Architects', 2021, 2, 7, 25, 8, 1.22, 'Juegos Familiares', 98000.00, 'Asmodee / Repos Production', '/media/portadas/3126800.webp', '3126800.webp'),
    (324856, 'Las Ruinas Perdidas de Arnak: Líderes de la Expedición', 2021, 1, 4, 120, 12, 3.25, 'Juegos de Estrategia', 94000.00, 'Devir / CGE', '/media/portadas/3248560.webp', '3248560.webp'),
    (316410, 'Messina 1347', 2021, 1, 4, 120, 14, 3.86, 'Juegos de Estrategia', 176000.00, 'Arrakis Games / Delicious Games', '/media/portadas/3164100.webp', '3164100.webp'),
    (338300, 'Bitoku', 2021, 1, 4, 120, 14, 3.55, 'Juegos de Estrategia', 182000.00, 'Devir', '/media/portadas/3383000.webp', '3383000.webp'),
    (328871, 'Braintrust', 2021, 2, 5, 30, 8, 1.50, 'Juegos Party', 45000.00, 'Zebra Games', '/media/portadas/3288710.webp', '3288710.webp'),
    (346702, 'Ages of Gilded: Industrial Revolution', 2022, 1, 4, 90, 12, 2.95, 'Juegos de Estrategia', 138000.00, 'Maldito Games', '/media/portadas/3467020.webp', '3467020.webp');

-- Development catalog seed inventory; this is not a production stock default.
UPDATE product_boardgame SET quantity = 10 WHERE bgg_id IN (
    274364, 230244, 272409, 241451, 297030, 286096, 256916, 266830, 287936,
    283863, 284083, 285905, 266507, 281259, 266192, 251247, 284378, 269207,
    271320, 286063, 282433, 312480, 284108, 295770, 287923, 302260, 291457,
    316554, 314040, 285192, 290448, 296880, 300582, 310873, 298047, 284380,
    312251, 317072, 306188, 282524, 316552, 342942, 318084, 312680, 324856,
    316410, 338300, 328871, 346702
);

-- ==============================================================================
-- 3. DDL: Creación de la tabla 'product_review'
-- ==============================================================================

CREATE TABLE IF NOT EXISTS product_review (
    id BIGSERIAL PRIMARY KEY,
    bgg_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    rating SMALLINT NOT NULL,
    body VARCHAR(2000) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_product_review_product
        FOREIGN KEY (bgg_id)
        REFERENCES product_boardgame (bgg_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_product_review_user
        FOREIGN KEY (user_id)
        REFERENCES auth_user (id)
        ON DELETE CASCADE,
    CONSTRAINT uq_product_review_user_game
        UNIQUE (user_id, bgg_id),
    CONSTRAINT chk_product_review_rating
        CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT chk_product_review_body
        CHECK (char_length(btrim(body)) BETWEEN 1 AND 2000),
    CONSTRAINT chk_product_review_status
        CHECK (status IN ('PENDING', 'APPROVED', 'HIDDEN', 'DELETED'))
);

CREATE INDEX IF NOT EXISTS idx_product_review_approved_game
    ON product_review (bgg_id, created_at)
    WHERE status = 'APPROVED';

CREATE INDEX IF NOT EXISTS idx_product_review_user
    ON product_review (user_id);

-- ==============================================================================
-- 4. DDL: Persistent carts (anonymous carts have no account user_id)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS shopping_cart (
    cart_id UUID PRIMARY KEY,
    user_id INTEGER UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_shopping_cart_user
        FOREIGN KEY (user_id)
        REFERENCES auth_user (id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS shopping_cart_line (
    cart_id UUID NOT NULL,
    bgg_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    CONSTRAINT pk_shopping_cart_line PRIMARY KEY (cart_id, bgg_id),
    CONSTRAINT fk_shopping_cart_line_cart
        FOREIGN KEY (cart_id)
        REFERENCES shopping_cart (cart_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_shopping_cart_line_product
        FOREIGN KEY (bgg_id)
        REFERENCES product_boardgame (bgg_id)
        ON DELETE CASCADE
);