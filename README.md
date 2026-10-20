# Inventory and Stock Analysis System

A Python-based inventory management and analysis system that tracks stock movements, monitors inventory levels, identifies low-stock products, and generates useful reports to support better inventory decisions.

## About the Project

Managing inventory manually can make it difficult to track available stock, monitor incoming and outgoing products, and identify items that need restocking.

The **Inventory and Stock Analysis System** aims to simplify these tasks by maintaining product records, recording stock transactions, calculating current stock levels, and analyzing inventory data.

The project combines Python, Flask, MySQL, Pandas, NumPy, and Matplotlib to build a backend-focused inventory management and reporting application.

## Project Objectives

- Manage product and supplier information.
- Record stock-in and stock-out transactions.
- Calculate current stock based on opening stock and recorded movements.
- Identify products that have reached or fallen below their reorder levels.
- Analyze product movement and inventory trends.
- Estimate the value of available inventory.
- Generate reports and charts for easier interpretation of inventory data.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application logic, validation, and calculations |
| Flask | REST API development and request handling |
| MySQL | Relational database and persistent storage |
| Pandas | Data cleaning, filtering, grouping, and reporting |
| NumPy | Numerical calculations and statistical analysis |
| Matplotlib | Data visualization and chart generation |
| Git and GitHub | Version control and team collaboration |

## Key Features

### 1. Product Management
- Add new products with unique SKUs.
- View existing product details.
- Update product information.
- Delete products when database constraints permit.

### 2. Stock Movement Tracking
- Record incoming stock using stock-in transactions.
- Record outgoing stock using stock-out transactions.
- Maintain transaction history.
- Associate stock transactions with the relevant products.

### 3. Current Stock Calculation

Current stock is calculated using the opening stock and recorded stock movements.

**Formula:**

Current Stock = Opening Stock + Total Stock In − Total Stock Out

### 4. Low-Stock Identification

Compare current stock against each product's configured reorder level to identify products that need attention.

### 5. Inventory Analysis

Use inventory and transaction data to prepare summaries, analyze product movements, identify fast-moving products, and estimate inventory value.

### 6. Reports and Visualization

Generate inventory reports and visualizations, including stock comparisons and product movement trends.

## System Workflow

1. Product and transaction data are stored in MySQL.
2. Python backend functions retrieve and update inventory records.
3. Flask API endpoints expose the available application operations.
4. Pandas organizes and analyzes inventory and transaction data.
5. NumPy supports numerical calculations and statistical analysis.
6. Matplotlib generates charts from the analyzed data.
7. Reports and API responses provide useful inventory information.

## Project Structure

```text
Inventory_and_stock_analysis_system/
│
├── Backend/
│   ├── app.py
│   ├── db_connection.py
│   └── inventory_logic.py
│
├── .env
├── .gitignore
├── README.md
└── requirements.txt
```

The database SQL scripts may be maintained in a separate folder or at the repository root, depending on the current repository structure. Analysis modules can be added as they are implemented.

**File responsibilities:**

- `app.py` — Flask application and API routes.
- `db_connection.py` — MySQL database connection.
- `inventory_logic.py` — Product operations and stock transaction logic.
- `.env` — Local database configuration; must not be committed.
- `requirements.txt` — Python dependencies.
- `README.md` — Project documentation.

## Database Design

The system uses a relational MySQL database.

### Main Tables

**Products**
- Product ID
- SKU
- Product name
- Category
- Opening stock
- Reorder level
- Unit cost
- Creation timestamp

**Suppliers**
- Supplier ID
- Supplier name
- Phone number
- Email
- Creation timestamp

**Stock Transactions**
- Transaction ID
- Product ID
- Transaction date
- Transaction type
- Quantity
- Supplier ID, when applicable
- Notes

Primary keys, foreign keys, constraints, and appropriate data validation help maintain data integrity.

### Database Views

The database includes reporting views for information such as:

- Current stock.
- Low-stock products.
- Daily stock movements.
- Stock movement summaries.
- Inventory valuation.

## Flask REST API Endpoints

The Flask application provides the following endpoints.

| HTTP Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Check application status |
| GET | `/test-db` | Test database connectivity |
| GET | `/products` | Retrieve all products |
| POST | `/products` | Add a product |
| PUT | `/products/<product_id>` | Update a product |
| DELETE | `/products/<product_id>` | Delete a product when permitted |
| POST | `/stock-in` | Record incoming stock |
| POST | `/stock-out` | Record outgoing stock |
| GET | `/low-stock` | Retrieve low-stock products |
| GET | `/transactions` | Retrieve stock transaction history |

### API Handling

- Accepts JSON request data where required.
- Validates input before processing requests.
- Returns JSON responses.
- Uses suitable HTTP status codes for success and error conditions.
- Handles errors such as invalid input, duplicate SKUs, missing products, and insufficient stock.
- Uses parameterized SQL queries for database operations.

## Data Analysis and Visualization

The project uses three Python libraries for inventory analysis.

### Pandas
- Organizes product and transaction records into tabular data.
- Filters low-stock products.
- Groups transactions by product.
- Prepares inventory summaries and reports.

### NumPy
- Performs numerical calculations.
- Calculates statistics such as averages, totals, and other useful measurements.
- Supports quantitative analysis of inventory data.

### Matplotlib
- Creates bar charts for stock comparisons.
- Visualizes product movement and inventory trends.
- Generates charts with appropriate titles, labels, and legends.

These analysis capabilities will be integrated with the existing backend as the relevant modules are completed.

## Installation and Setup

### Prerequisites

Install the following software:

- Python
- MySQL Server
- MySQL Workbench
- Git
- Visual Studio Code (recommended)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Inventory_and_stock_analysis_system
```

Replace `<repository-url>` with the actual GitHub repository URL.

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

If `requirements.txt` is available:

```bash
python -m pip install -r requirements.txt
```

Otherwise, install the required packages:

```bash
python -m pip install flask mysql-connector-python python-dotenv pandas numpy matplotlib
```

### 4. Configure the Database

1. Start the MySQL server.
2. Open MySQL Workbench and connect to the server.
3. Execute the project's SQL scripts in the documented order.
4. Run the database verification script.
5. Confirm that the required tables, views, and triggers have been created.

### 5. Configure Environment Variables

Create a local `.env` file in the project root:

```env
DB_HOST=localhost
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=your_database_name
```

Replace the example values with your actual local database configuration. Do not commit credentials to GitHub.

### 6. Run the Application

From the project root, run:

```bash
python Backend/app.py
```

Use the host and port printed by Flask to access the running application.

### 7. Test the API

Use an API testing tool, such as Thunder Client or Postman, to send requests to the available endpoints.

For example, send a GET request to:

```text
http://127.0.0.1:5000/products
```

The port shown in your terminal may differ if you configured another port.

## Expected Outputs

The system is designed to provide:

- Product and stock records.
- Current stock reports.
- Low-stock product lists.
- Stock-in and stock-out transaction history.
- Stock movement summaries.
- Estimated inventory valuation.
- Charts comparing stock levels and visualizing product movements.

## Validation and Data Integrity

The application incorporates validation and error handling to help ensure reliable inventory records.

Examples include:

- Preventing duplicate product SKUs.
- Rejecting invalid or missing input.
- Checking product availability before stock-out transactions.
- Rejecting stock-out quantities that exceed available stock.
- Respecting database relationships when deleting products.
- Handling database errors without silently treating failed operations as successful.

## Security and Configuration

- Database credentials are stored in environment variables.
- The `.env` file is excluded from version control.
- SQL statements use parameters rather than directly inserting user input into query strings.
- Database constraints help protect the integrity of stored records.

## Project Scope

The project focuses on inventory tracking, stock movement analysis, low-stock identification, and reporting.

Reorder recommendations are based on configured stock thresholds. The system does not automatically place purchase orders with suppliers.

## Future Enhancements

- Add a dashboard for inventory summaries.
- Provide date-range filters for stock movement analysis.
- Generate downloadable inventory reports.
- Add user authentication and role-based access.
- Improve demand analysis and reorder recommendations.
- Add automated alerts for low-stock products.

## Team Collaboration

The project is developed collaboratively using Git and GitHub.

Team members can work on separate modules, commit their changes, and integrate their work through the shared repository.

## Conclusion

The Inventory and Stock Analysis System demonstrates how Python, Flask, MySQL, and data analysis libraries can work together to simplify inventory management.

By tracking stock movements, calculating current stock, identifying low-stock products, and preparing reports, the system aims to support more organized and informed inventory decisions.
