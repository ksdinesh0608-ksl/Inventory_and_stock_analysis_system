
import os
import textwrap
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import timedelta
from Backend.db_connection import get_db_connection


# ==============================
# CHART THEME
# ==============================

NAVY = "#24364B"
TEAL = "#20A39E"
BLUE = "#527DAA"
CORAL = "#E76F51"
AMBER = "#E9B44C"
GRID = "#E8EDF2"
GREY = "#68788D"

OUTPUT_DIR = "Analysis"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "font.weight": "bold",
    "axes.titleweight": "bold",
    "axes.labelweight": "bold",
    "axes.labelcolor": NAVY,
    "xtick.color": NAVY,
    "ytick.color": NAVY,
    "text.color": NAVY,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white"
})


# ==============================
# COMMON CHART FUNCTIONS
# ==============================

def save_chart(fig, filename):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fig.tight_layout(pad=2)
    fig.savefig(
        os.path.join(OUTPUT_DIR, filename),
        dpi=220,
        bbox_inches="tight"
    )
    plt.close(fig)
    print(f"Saved: {filename}")


def style_chart(ax):
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0, pad=8)


def format_names(names, width=16):
    """Keep labels horizontal and wrap long names onto multiple lines."""
    return [
        "\n".join(textwrap.wrap(str(name), width=width))
        for name in names
    ]


def add_labels(ax, bars, currency=False):
    for bar in bars:
        value = bar.get_height()
        label = f"₹{value:,.0f}" if currency else f"{value:,.0f}"

        ax.annotate(
            label,
            (bar.get_x() + bar.get_width() / 2, value),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color=NAVY
        )


# ==============================
# GET INVENTORY DATA
# ==============================

def get_inventory():
    connection = get_db_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                product_name,
                category,
                current_stock,
                reorder_level,
                unit_cost
            FROM current_stock_report
        """)
        return cursor.fetchall()

    finally:
        connection.close()


# ==============================
# 1. LOW-STOCK PRODUCTS
# ==============================

def low_stock_chart():
    data = [
        row for row in get_inventory()
        if float(row[2]) <= float(row[3])
    ]

    if not data:
        print("No low-stock products found.")
        return

    data.sort(key=lambda row: float(row[2]) - float(row[3]))
    data = data[:10]

    names = [row[0] for row in data]
    current = [float(row[2]) for row in data]
    reorder = [float(row[3]) for row in data]

    x = np.arange(len(names))
    width = 0.36

    fig, ax = plt.subplots(
        figsize=(max(8, len(names) * 1.15), 5)
    )

    bars1 = ax.bar(
        x - width / 2, current, width,
        color=CORAL, label="Current Stock"
    )
    bars2 = ax.bar(
        x + width / 2, reorder, width,
        color=AMBER, label="Reorder Level"
    )

    ax.set_title(
        "Low-Stock Products",
        fontsize=16, loc="left", pad=16
    )
    ax.set_ylabel("Quantity (units)")
    ax.set_xlabel("Products", labelpad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(
        format_names(names),
        rotation=0,
        ha="center",
        fontweight="bold"
    )

    ax.legend(frameon=False, ncol=2)
    style_chart(ax)
    ax.set_ylim(0, max(current + reorder + [1]) * 1.25)

    add_labels(ax, bars1)
    add_labels(ax, bars2)

    save_chart(fig, "low_stock_products.png")


# ==============================
# 2. FAST-MOVING PRODUCTS
# ==============================

def fast_moving_chart():
    connection = get_db_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                p.product_name,
                SUM(t.quantity) AS total_out
            FROM products p
            JOIN stock_transactions t
                ON p.product_id = t.product_id
            WHERE t.transaction_type = %s
            GROUP BY p.product_id, p.product_name
            ORDER BY total_out DESC
            LIMIT %s
        """, ("STOCK_OUT", 10))

        data = cursor.fetchall()

    finally:
        connection.close()

    if not data:
        print("No stock-out transactions found.")
        return

    names = [row[0] for row in data]
    quantities = [float(row[1]) for row in data]
    x = np.arange(len(names))

    fig, ax = plt.subplots(
        figsize=(max(8, len(names) * 1.15), 5)
    )

    colors = [
        TEAL if i == 0 else BLUE
        for i in range(len(names))
    ]

    bars = ax.bar(
        x, quantities,
        color=colors,
        width=0.55,
        edgecolor="white",
        linewidth=1
    )

    ax.set_title(
        "Fast-Moving Products",
        fontsize=16, loc="left", pad=16
    )
    ax.set_ylabel("Stock-Out Quantity (units)")
    ax.set_xlabel("Products", labelpad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(
        format_names(names),
        rotation=0,
        ha="center",
        fontweight="bold"
    )

    style_chart(ax)
    ax.set_ylim(0, max(quantities + [1]) * 1.25)
    add_labels(ax, bars)

    save_chart(fig, "fast_moving_products.png")


# ==============================
# 3. STOCK BY CATEGORY
# ==============================

def category_chart():
    data = get_inventory()

    if not data:
        print("No inventory data found.")
        return

    totals = {}

    for row in data:
        category = row[1] or "Uncategorized"
        totals[category] = (
            totals.get(category, 0) + float(row[2])
        )

    items = sorted(
        totals.items(),
        key=lambda item: item[1],
        reverse=True
    )

    categories = [item[0] for item in items]
    quantities = [item[1] for item in items]

    palette = [NAVY, TEAL, BLUE, AMBER, CORAL]
    colors = [
        palette[i % len(palette)]
        for i in range(len(categories))
    ]

    x = np.arange(len(categories))

    fig, ax = plt.subplots(
        figsize=(max(8, len(categories) * 1.15), 5)
    )

    bars = ax.bar(
        x, quantities,
        color=colors,
        width=0.58
    )

    ax.set_title(
        "Inventory by Category",
        fontsize=16, loc="left", pad=16
    )
    ax.set_ylabel("Total Stock (units)")
    ax.set_xlabel("Categories", labelpad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(
        format_names(categories),
        rotation=0,
        ha="center",
        fontweight="bold"
    )

    style_chart(ax)
    ax.set_ylim(0, max(quantities + [1]) * 1.25)
    add_labels(ax, bars)

    save_chart(fig, "stock_by_category.png")


# ==============================
# 4. STOCK MOVEMENT OVER TIME
# ==============================

def stock_movement_chart():
    connection = get_db_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                DATE(transaction_date),
                transaction_type,
                SUM(quantity)
            FROM stock_transactions
            GROUP BY DATE(transaction_date), transaction_type
            ORDER BY DATE(transaction_date)
        """)
        data = cursor.fetchall()

    finally:
        connection.close()

    if not data:
        print("No stock movement data found.")
        return

    latest = max(row[0] for row in data)
    start = latest - timedelta(days=29)

    movement = {}

    for date, kind, quantity in data:
        if start <= date <= latest:
            movement.setdefault(
                date, {"STOCK_IN": 0, "STOCK_OUT": 0}
            )
            movement[date][kind] = float(quantity)

    if not movement:
        print("No transactions in the latest 30-day period.")
        return

    dates = sorted(movement)
    stock_in = [movement[d]["STOCK_IN"] for d in dates]
    stock_out = [movement[d]["STOCK_OUT"] for d in dates]

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.plot(
        dates, stock_in,
        color=TEAL, linewidth=2.5,
        marker="o", markersize=5,
        label="Stock In"
    )
    ax.plot(
        dates, stock_out,
        color=CORAL, linewidth=2.5,
        marker="o", markersize=5,
        label="Stock Out"
    )

    ax.set_title(
        "Stock Movement — Latest 30 Days",
        fontsize=16, loc="left", pad=16
    )
    ax.set_ylabel("Quantity (units)")
    ax.set_xlabel("Transaction Date", labelpad=12)

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%d %b")
    )
    ax.xaxis.set_major_locator(
        mdates.AutoDateLocator(minticks=3, maxticks=7)
    )

    ax.legend(frameon=False, ncol=2)
    style_chart(ax)
    ax.grid(axis="x", visible=False)

    for label in ax.get_xticklabels():
        label.set_rotation(0)
        label.set_fontweight("bold")

    save_chart(fig, "stock_movement_over_time.png")


# ==============================
# 5. INVENTORY VALUE BY PRODUCT
# ==============================

def inventory_value_chart():
    data = get_inventory()

    if not data:
        print("No inventory data found.")
        return

    data.sort(
        key=lambda row: float(row[2]) * float(row[4]),
        reverse=True
    )
    data = data[:10]

    names = [row[0] for row in data]
    values = [
        float(row[2]) * float(row[4])
        for row in data
    ]

    x = np.arange(len(names))

    fig, ax = plt.subplots(
        figsize=(max(8, len(names) * 1.15), 5)
    )

    bars = ax.bar(
        x, values,
        color=BLUE,
        width=0.55,
        edgecolor="white",
        linewidth=1
    )

    ax.set_title(
        "Inventory Value by Product",
        fontsize=16, loc="left", pad=16
    )
    ax.set_ylabel("Inventory Value (₹)")
    ax.set_xlabel("Products", labelpad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(
        format_names(names),
        rotation=0,
        ha="center",
        fontweight="bold"
    )

    style_chart(ax)
    ax.set_ylim(0, max(values + [1]) * 1.25)
    add_labels(ax, bars, currency=True)

    save_chart(fig, "inventory_value_by_product.png")


# ==============================
# GENERATE ALL FIVE CHARTS
# ==============================

if __name__ == "__main__":
    print("\nGenerating inventory charts...\n")

    low_stock_chart()
    fast_moving_chart()
    category_chart()
    stock_movement_chart()
    inventory_value_chart()

    print("\nAll charts generated successfully.")
