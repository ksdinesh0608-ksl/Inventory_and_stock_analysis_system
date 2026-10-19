# Inventory and Stock Analysis System

## About the Project

The Inventory and Stock Analysis System is a Python-based project designed to help a shop manage its products and keep track of stock movements.

In a shop, it is important to know how much stock is available, which products need to be restocked, and which products are moving quickly. Keeping track of all these details manually can be difficult.

This project aims to make inventory management easier by recording stock transactions, calculating current stock, and generating useful reports for better decision-making.

## Project Objectives

- Manage product and supplier details.
- Record stock coming into and going out of the shop.
- Calculate current stock using opening stock and stock transactions.
- Identify products that have reached or fallen below their reorder level.
- Analyze product movement and inventory trends.
- Calculate the estimated value of available stock.
- Display inventory information through reports and charts.

## Technologies Used

- **Python** – Application logic and calculations.
- **Flask** – Handles application routes and API requests.
- **MySQL** – Stores product, supplier, and stock transaction details.
- **Pandas** – Organizes and analyzes inventory data.
- **NumPy** – Performs numerical calculations and statistical analysis.
- **Matplotlib** – Creates charts to visualize stock levels and product movements.

## Main Features

### Product and Supplier Management
Stores product information, including product name, SKU, category, opening stock, reorder level, and unit cost, along with supplier details.

### Stock Movement Tracking
Records stock-in and stock-out transactions so that inventory changes can be tracked.

### Current Stock Calculation
Calculates available stock using the opening stock and recorded stock movements.

### Low-Stock Identification
Identifies products that need attention based on their configured reorder levels.

### Inventory Analysis
Summarizes product movements, helps identify fast-moving products, and estimates the value of available inventory.

### Reports and Visualization
Generates inventory reports and charts to make stock information easier to understand.

## Database Setup

1. Install MySQL and open MySQL Workbench.
2. Connect to your MySQL server.
3. Open the SQL files in the project repository.
4. Execute the scripts in the correct order, starting with database creation, followed by the required tables, triggers, and reports.
5. Run the database verification script to check whether the required tables, views, and triggers have been created successfully.

Make sure the database setup is completed before connecting the Python application.

## Expected Outputs

- Current stock report.
- Low-stock product list.
- Stock movement summary.
- Estimated inventory valuation.
- Charts showing stock levels and product movement.

## Project Scope

This project focuses on inventory tracking and analysis. Reorder recommendations are based on configurable stock thresholds. The system does not automatically purchase products from suppliers.
