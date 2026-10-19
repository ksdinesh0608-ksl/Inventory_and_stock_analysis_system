
USE inventory_management;

-- Check all tables
SHOW TABLES;

-- Check table structures
DESCRIBE suppliers;
DESCRIBE products;
DESCRIBE stock_transactions;
DESCRIBE users;

-- Check all views
SHOW FULL TABLES
WHERE Table_type = 'VIEW';

-- Check the trigger
SHOW TRIGGERS;

-- Check that no sample records were inserted
SELECT COUNT(*) AS supplier_count
FROM suppliers;

SELECT COUNT(*) AS product_count
FROM products;

SELECT COUNT(*) AS transaction_count
FROM stock_transactions;

SELECT COUNT(*) AS user_count
FROM users;

-- Preview reports
SELECT * FROM current_stock_report;
SELECT * FROM low_stock_report;
SELECT * FROM stock_movement_report;
SELECT * FROM inventory_valuation_report;
SELECT * FROM daily_stock_movement_report;
