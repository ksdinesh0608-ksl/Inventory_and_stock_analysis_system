
USE inventory_management;

CREATE TABLE IF NOT EXISTS stock_transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    transaction_type ENUM('STOCK_IN', 'STOCK_OUT') NOT NULL,
    quantity INT NOT NULL,
    supplier_id INT NULL,
    notes VARCHAR(255),

    CONSTRAINT chk_quantity
        CHECK (quantity > 0),

    CONSTRAINT fk_transaction_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_transaction_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES suppliers(supplier_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    INDEX idx_product_date (product_id, transaction_date),
    INDEX idx_transaction_date (transaction_date)
);
