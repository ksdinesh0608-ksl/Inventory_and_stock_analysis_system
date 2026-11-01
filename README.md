# Stockwise – Inventory and Stock Analysis System

A web-based inventory management system developed to simplify product management, track stock movements, monitor low-stock items, and analyse inventory data.

The application provides a centralised dashboard where administrators and staff can manage inventory operations and view useful reports.

---

## Project Overview

Stockwise helps shopkeepers and inventory teams maintain accurate stock records and make better inventory decisions.

The system combines a web-based frontend, a Python Flask backend, a MySQL database, and data analysis tools.

### Main Objectives

- Manage products and their details.
- Record stock-in and stock-out transactions.
- Maintain supplier information.
- Monitor current stock levels.
- Identify products that need restocking.
- Analyse inventory movement and valuation.
- Provide role-based access to the application.

---

## Features

### 1. User Authentication and Management

- User registration and login.
- Admin and staff roles.
- New staff accounts require administrator approval.
- Admin can view pending registration requests.
- Admin can approve or reject staff accounts.
- Approved staff members can access the application according to their role.
- Session-based authentication.

### 2. Dashboard

- Overview of inventory information.
- Total products.
- Current stock information.
- Inventory valuation.
- Low-stock product count.
- Quick access to important inventory operations.

### 3. Product Management

- Add new products.
- View all available products.
- Edit existing product details.
- Delete products where permitted.
- Maintain SKU, product name, category, opening stock, reorder level, and unit cost.

### 4. Supplier Management

- Add new suppliers.
- View supplier information.
- Maintain supplier contact details.
- Select existing suppliers while recording stock-in transactions.

### 5. Stock Management

**Stock In**
- Record newly received stock.
- Select an existing supplier.
- Store transaction details and optional notes.

**Stock Out**
- Record stock issued or sold.
- Validate available stock before processing.
- Prevent stock from becoming negative.

### 6. Transaction History

- Maintain stock-in and stock-out records.
- View transaction details.
- Track transaction dates and quantities.
- Download transaction records.

### 7. Low-Stock Monitoring

- Identify products below their reorder level.
- Display current stock and reorder level.
- Help users identify products that require attention.

### 8. Inventory Analysis and Charts

The system generates visual reports using Matplotlib.

Available charts include:

1. Low-stock products.
2. Fast-moving products.
3. Stock by category.
4. Stock movement over time.
5. Inventory value by product.

These visualisations help users understand inventory conditions and make informed decisions.

---

## Technologies Used

| Technology | Purpose |
|---|---|
| HTML5 | Webpage structure |
| CSS3 | Styling and responsive layout |
| JavaScript | Frontend interactions and API requests |
| Python | Backend programming |
| Flask | Web framework and REST API |
| MySQL | Database management |
| Pandas | Data processing and analysis |
| NumPy | Numerical operations |
| Matplotlib | Data visualisation |
| Gunicorn | Production WSGI server |
| Render | Application deployment |
| Aiven | Hosted MySQL database |

---

## System Architecture

The application follows a three-layer architecture.

### 1. Frontend
HTML, CSS and JavaScript provide the user interface, forms, dashboard, tables and visual reports.

### 2. Backend
Python and Flask handle authentication, API requests, validation, inventory operations and database communication.

### 3. Database
MySQL stores user details, products, suppliers and stock transactions.

### Application Workflow

1. The user interacts with the frontend.
2. JavaScript sends a request to the Flask backend.
3. Flask processes the request and validates the information.
4. The backend communicates with MySQL.
5. MySQL stores or retrieves the required information.
6. The frontend displays the updated result.

---

## Database Design

The project uses a MySQL database named:

`inventory_management`

### Main Tables

| Table | Description |
|---|---|
| users | Stores user information, roles and approval status |
| products | Stores product details and inventory settings |
| suppliers | Stores supplier information |
| stock_transactions | Stores stock-in and stock-out records |

### Database Views

The database also uses views for inventory reporting:

- `current_stock_report`
- `daily_stock_movement_report`
- `inventory_valuation_report`
- `low_stock_report`
- `stock_movement_report`

### Important Inventory Calculations

**Current Stock**

Current Stock = Opening Stock + Stock In − Stock Out

**Low Stock Condition**

Current Stock < Reorder Level

**Inventory Valuation**

Inventory Value = Current Stock × Unit Cost

Stock-out operations are validated to prevent issuing more quantity than is available.

---

## Data Analysis

The project uses Python data analysis libraries to generate inventory reports.

### Pandas
Used for processing, filtering, grouping and summarising inventory data.

### NumPy
Used for numerical calculations and data operations.

### Matplotlib
Used to create visual charts for inventory analysis.

The generated reports provide information about low-stock products, fast-moving items, category-wise stock, stock movement and inventory valuation.

---

## Project Folder Structure

```text
Inventory_and_stock_analysis_system/
│
├── Backend/
│   ├── app.py
│   ├── db_connection.py
│   └── inventory_logic.py
│
├── Frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── Analysis/
│   └── matplotlib_visualization.py
│
├── requirements.txt
└── README.md
```

---

## Installation and Setup

### Prerequisites

Install the following before running the project locally:

- Python
- MySQL
- Git
- A code editor such as Visual Studio Code

### Step 1: Clone the Repository

```bash
git clone https://github.com/ksdinesh0608-ksl/Inventory_and_stock_analysis_system.git
```

### Step 2: Open the Project

```bash
cd Inventory_and_stock_analysis_system
```

### Step 3: Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Configure Database Credentials

Create a `.env` file in the project root and configure your MySQL connection:

```env
DB_HOST=your_database_host
DB_USER=your_database_username
DB_PORT=3306
DB_PASSWORD=your_database_password
DB_NAME=inventory_management
```

Use your own database credentials. Do not upload the `.env` file or expose database passwords on GitHub.

### Step 6: Run the Application

From the project root:

```bash
cd Backend
python app.py
```

Open the local URL displayed in the terminal.

---

## Deployment

The project is deployed using Render, with a hosted MySQL database on Aiven.

**Application URL:**

https://inventory-and-stock-analysis-system-coc4.onrender.com

The backend uses Gunicorn as the production server.

Database credentials are configured through environment variables in the deployment environment.

---

## Future Enhancements

Possible improvements include:

- Exporting inventory reports in PDF and Excel formats.
- Adding advanced search and filtering.
- Introducing barcode scanning.
- Adding automated email notifications for low-stock products.
- Improving analytics with additional inventory trends.
- Adding more detailed user activity logs.

---

## Project Information

**Project Name:** Inventory and Stock Analysis System

**Application Name:** Stockwise

**Domain:** Inventory Management and Data Analysis

**Backend:** Python Flask

**Database:** MySQL

**Frontend:** HTML, CSS and JavaScript

**Academic Programme:** B.Tech – Computer Science and Engineering

---

## Conclusion

Stockwise provides a simple and organised way to manage inventory operations. It brings product management, supplier records, stock transactions, user management and data visualisation together in one application.

The project demonstrates how frontend technologies, backend development, database management and data analysis can be combined to build a practical inventory management solution.
