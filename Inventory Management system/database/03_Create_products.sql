
USE inventory_management;

CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(50) NOT NULL UNIQUE,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(100),
    opening_stock INT NOT NULL DEFAULT 0,
    reorder_level INT NOT NULL DEFAULT 10,
    unit_cost DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_opening_stock
        CHECK (opening_stock >= 0),

    CONSTRAINT chk_reorder_level
        CHECK (reorder_level >= 0),

    CONSTRAINT chk_unit_cost
        CHECK (unit_cost >= 0)
);
