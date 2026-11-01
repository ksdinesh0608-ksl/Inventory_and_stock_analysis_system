
import os
import sys
import traceback

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from Backend.db_connection import get_db_connection

OUTPUT_DIR = CURRENT_DIR

CHART_FILES = [
    "low_stock_products.png",
    "fast_moving_products.png",
    "stock_by_category.png",
    "stock_movement_over_time.png",
    "inventory_value_by_product.png"
]

BG = "#f5f7f2"
GREEN = "#49634d"
DARK = "#304936"
SAGE = "#91a78f"
LIGHT_GREEN = "#c8d5c3"
GOLD = "#c5a76b"
GRID = "#e5eae1"
TEXT = "#657267"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "axes.edgecolor": BG,
    "axes.labelcolor": TEXT,
    "axes.titlecolor": DARK,
    "xtick.color": TEXT,
    "ytick.color": TEXT,
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 9,
    "savefig.facecolor": BG,
    "savefig.edgecolor": BG
})


def fetch_data(query):
    connection = get_db_connection()

    try:
        return pd.read_sql_query(query, connection)
    finally:
        if connection.is_connected():
            connection.close()


def style_axis(ax, horizontal=False):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(GRID)

    ax.set_axisbelow(True)
    ax.grid(
        axis="x" if horizontal else "y",
        color=GRID,
        linewidth=0.8
    )

    ax.tick_params(length=0, pad=7)


def save_chart(fig, filename):
    output_path = os.path.join(OUTPUT_DIR, filename)

    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
        pad_inches=0.25,
        facecolor=BG
    )

    plt.close(fig)

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise RuntimeError(f"Chart was not saved correctly: {filename}")

    print(f"Saved {filename}: {os.path.getsize(output_path)} bytes")


def show_empty(ax, message="No data available"):
    ax.text(
        0.5, 0.5,
        message,
        transform=ax.transAxes,
        ha="center",
        va="center",
        color=TEXT,
        fontsize=11
    )
    ax.set_axis_off()


def low_stock_chart():
    query = """
        SELECT product_name, current_stock, reorder_level
        FROM current_stock_report
        WHERE current_stock < reorder_level
        ORDER BY current_stock ASC
    """

    df = fetch_data(query)

    fig, ax = plt.subplots(figsize=(8, 4.2))

    ax.set_title("Low Stock Products", loc="left", pad=18)

    if df.empty:
        show_empty(ax)
    else:
        df = df.head(10)
        bars = ax.barh(
            df["product_name"],
            df["current_stock"],
            color=SAGE,
            height=0.55
        )

        for bar, value in zip(bars, df["current_stock"]):
            ax.text(
                bar.get_width() + 0.2,
                bar.get_y() + bar.get_height() / 2,
                str(value),
                va="center",
                color=DARK,
                fontsize=9
            )

        ax.invert_yaxis()
        ax.set_xlabel("Current Stock")
        style_axis(ax, horizontal=True)

    fig.tight_layout()
    save_chart(fig, "low_stock_products.png")


def fast_moving_chart():
    query = """
        SELECT p.product_name,
               SUM(st.quantity) AS total_sold
        FROM stock_transactions st
        JOIN products p ON st.product_id = p.product_id
        WHERE st.transaction_type = 'STOCK_OUT'
        GROUP BY p.product_id, p.product_name
        ORDER BY total_sold DESC
        LIMIT 10
    """

    df = fetch_data(query)

    fig, ax = plt.subplots(figsize=(8, 4.2))

    ax.set_title("Fast Moving Products", loc="left", pad=18)

    if df.empty:
        show_empty(ax)
    else:
        bars = ax.bar(
            df["product_name"],
            df["total_sold"],
            color=GREEN,
            width=0.58
        )

        for bar, value in zip(bars, df["total_sold"]):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                str(value),
                ha="center",
                va="bottom",
                color=DARK,
                fontsize=9
            )

        ax.set_ylabel("Quantity Sold")
        ax.tick_params(axis="x", rotation=20)
        style_axis(ax)

    fig.tight_layout()
    save_chart(fig, "fast_moving_products.png")


def category_chart():
    query = """
        SELECT p.category,
               SUM(c.current_stock) AS total_stock
        FROM products p
        JOIN current_stock_report c
        ON p.product_id = c.product_id
        GROUP BY p.category
        ORDER BY total_stock DESC
    """

    df = fetch_data(query)

    fig, ax = plt.subplots(figsize=(8, 4.2))

    ax.set_title("Stock by Category", loc="left", pad=18)

    if df.empty:
        show_empty(ax)
    else:
        colors = [GREEN, SAGE, LIGHT_GREEN, GOLD, "#a7b5a1"]

        wedges, _, _ = ax.pie(
            df["total_stock"],
            labels=None,
            colors=colors[:len(df)],
            startangle=90,
            autopct=lambda p: f"{p:.0f}%" if p >= 5 else "",
            pctdistance=0.72,
            wedgeprops={
                "width": 0.42,
                "edgecolor": BG,
                "linewidth": 3
            },
            textprops={"color": DARK, "fontsize": 9}
        )

        ax.legend(
            wedges,
            df["category"].astype(str),
            loc="center left",
            bbox_to_anchor=(0.85, 0.5),
            frameon=False,
            fontsize=9
        )

        ax.set_aspect("equal")

    fig.tight_layout()
    save_chart(fig, "stock_by_category.png")


def stock_movement_chart():
    query = """
        SELECT DATE(transaction_date) AS movement_date,
               SUM(CASE
                   WHEN transaction_type = 'STOCK_IN'
                   THEN quantity ELSE 0
               END) AS stock_in,
               SUM(CASE
                   WHEN transaction_type = 'STOCK_OUT'
                   THEN quantity ELSE 0
               END) AS stock_out
        FROM stock_transactions
        GROUP BY DATE(transaction_date)
        ORDER BY movement_date
    """

    df = fetch_data(query)

    fig, ax = plt.subplots(figsize=(8, 4.2))

    ax.set_title("Stock Movement Over Time", loc="left", pad=18)

    if df.empty:
        show_empty(ax)
    else:
        df["movement_date"] = pd.to_datetime(df["movement_date"])

        ax.plot(
            df["movement_date"],
            df["stock_in"],
            color=GREEN,
            linewidth=2.5,
            marker="o",
            markersize=5,
            label="Stock In"
        )

        ax.plot(
            df["movement_date"],
            df["stock_out"],
            color=GOLD,
            linewidth=2.5,
            marker="o",
            markersize=5,
            label="Stock Out"
        )

        ax.fill_between(
            df["movement_date"],
            df["stock_in"],
            color=GREEN,
            alpha=0.08
        )

        ax.set_ylabel("Quantity")
        ax.legend(frameon=False, loc="upper left")
        ax.tick_params(axis="x", rotation=20)
        style_axis(ax)

    fig.tight_layout()
    save_chart(fig, "stock_movement_over_time.png")


def inventory_value_chart():
    query = """
        SELECT p.product_name,
               c.current_stock * p.unit_cost AS inventory_value
        FROM products p
        JOIN current_stock_report c
        ON p.product_id = c.product_id
        ORDER BY inventory_value DESC
        LIMIT 10
    """

    df = fetch_data(query)

    fig, ax = plt.subplots(figsize=(8, 4.2))

    ax.set_title("Inventory Value by Product", loc="left", pad=18)

    if df.empty:
        show_empty(ax)
    else:
        bars = ax.barh(
            df["product_name"],
            df["inventory_value"],
            color=SAGE,
            height=0.55
        )

        for bar, value in zip(bars, df["inventory_value"]):
            ax.text(
                bar.get_width(),
                bar.get_y() + bar.get_height() / 2,
                f"  ₹{value:,.0f}",
                va="center",
                color=DARK,
                fontsize=8
            )

        ax.invert_yaxis()
        ax.set_xlabel("Inventory Value (₹)")
        ax.xaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"₹{x:,.0f}")
        )
        style_axis(ax, horizontal=True)

    fig.tight_layout()
    save_chart(fig, "inventory_value_by_product.png")


def generate_all_charts():
    chart_functions = [
        low_stock_chart,
        fast_moving_chart,
        category_chart,
        stock_movement_chart,
        inventory_value_chart
    ]

    for filename in CHART_FILES:
        path = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(path):
            os.remove(path)

    for function in chart_functions:
        function()

    for filename in CHART_FILES:
        path = os.path.join(OUTPUT_DIR, filename)

        if not os.path.exists(path) or os.path.getsize(path) == 0:
            raise RuntimeError(f"Missing or empty chart: {filename}")

    print("All five charts generated successfully.")


if __name__ == "__main__":
    try:
        generate_all_charts()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
