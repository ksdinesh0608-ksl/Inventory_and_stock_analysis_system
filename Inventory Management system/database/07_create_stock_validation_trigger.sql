
USE inventory_management;

DROP TRIGGER IF EXISTS prevent_negative_stock;

DELIMITER $$

CREATE TRIGGER prevent_negative_stock
BEFORE INSERT ON stock_transactions
FOR EACH ROW
BEGIN
    DECLARE v_opening_stock INT DEFAULT 0;
    DECLARE v_stock_in BIGINT DEFAULT 0;
    DECLARE v_stock_out BIGINT DEFAULT 0;
    DECLARE v_current_stock BIGINT DEFAULT 0;
    DECLARE v_product_found INT DEFAULT 1;

    DECLARE CONTINUE HANDLER FOR NOT FOUND
        SET v_product_found = 0;

    -- Find and lock the product row
    SELECT opening_stock
    INTO v_opening_stock
    FROM products
    WHERE product_id = NEW.product_id
    FOR UPDATE;

    -- Reject a transaction for a nonexistent product
    IF v_product_found = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Product does not exist';
    END IF;

    -- Calculate existing stock movements
    SELECT
        COALESCE(SUM(
            CASE
                WHEN transaction_type = 'STOCK_IN'
                    THEN quantity
                ELSE 0
            END
        ), 0),
        COALESCE(SUM(
            CASE
                WHEN transaction_type = 'STOCK_OUT'
                    THEN quantity
                ELSE 0
            END
        ), 0)
    INTO v_stock_in, v_stock_out
    FROM stock_transactions
    WHERE product_id = NEW.product_id;

    SET v_current_stock =
        v_opening_stock + v_stock_in - v_stock_out;

    -- Reject stock-out when stock is insufficient
    IF NEW.transaction_type = 'STOCK_OUT'
       AND NEW.quantity > v_current_stock THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'Insufficient stock for this transaction';
    END IF;
END$$

DELIMITER ;
