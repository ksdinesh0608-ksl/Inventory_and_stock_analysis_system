
USE inventory_management;

-- Report 1: Current stock for each product
CREATE OR REPLACE VIEW current_stock_report AS
SELECT
    p.product_id,
    p.sku,
    p.product_name,
    p.category,
    p.opening_stock
        + COALESCE(SUM(
            CASE
                WHEN st.transaction_type = 'STOCK_IN'
                    THEN st.quantity
                WHEN st.transaction_type = 'STOCK_OUT'
                    THEN -st.quantity
                ELSE 0
            END
        ), 0) AS current_stock,
    p.reorder_level,
    p.unit_cost
FROM products p
LEFT JOIN stock_transactions st
    ON p.product_id = st.product_id
GROUP BY
    p.product_id,
    p.sku,
    p.product_name,
    p.category,
    p.opening_stock,
    p.reorder_level,
    p.unit_cost;


-- Report 2: Products that need restocking
CREATE OR REPLACE VIEW low_stock_report AS
SELECT *
FROM current_stock_report
WHERE current_stock <= reorder_level;


-- Report 3: Stock-in and stock-out totals per product
CREATE OR REPLACE VIEW stock_movement_report AS
SELECT
    p.product_id,
    p.sku,
    p.product_name,
    COALESCE(SUM(
        CASE
            WHEN st.transaction_type = 'STOCK_IN'
                THEN st.quantity
            ELSE 0
        END
    ), 0) AS total_stock_in,
    COALESCE(SUM(
        CASE
            WHEN st.transaction_type = 'STOCK_OUT'
                THEN st.quantity
            ELSE 0
        END
    ), 0) AS total_stock_out,
    COUNT(st.transaction_id) AS transaction_count
FROM products p
LEFT JOIN stock_transactions st
    ON p.product_id = st.product_id
GROUP BY
    p.product_id,
    p.sku,
    p.product_name;


-- Report 4: Estimated inventory value per product
CREATE OR REPLACE VIEW inventory_valuation_report AS
SELECT
    product_id,
    sku,
    product_name,
    current_stock,
    unit_cost,
    current_stock * unit_cost AS inventory_value
FROM current_stock_report;


-- Report 5: Daily stock movement
CREATE OR REPLACE VIEW daily_stock_movement_report AS
SELECT
    DATE(transaction_date) AS movement_date,
    SUM(
        CASE
            WHEN transaction_type = 'STOCK_IN'
                THEN quantity
            ELSE 0
        END
    ) AS total_stock_in,
    SUM(
        CASE
            WHEN transaction_type = 'STOCK_OUT'
                THEN quantity
            ELSE 0
        END
    ) AS total_stock_out,
    SUM(
        CASE
            WHEN transaction_type = 'STOCK_IN'
                THEN quantity
            WHEN transaction_type = 'STOCK_OUT'
                THEN -quantity
            ELSE 0
        END
    ) AS net_movement
FROM stock_transactions
GROUP BY DATE(transaction_date);
