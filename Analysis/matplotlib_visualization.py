
import os
import sys
import textwrap
from datetime import timedelta

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap, to_rgb
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _find_db_folder():
    skip = {".venv", "__pycache__", ".git", "node_modules"}

    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in skip]

        if "db_connection.py" in files:
            return folder

    return None


_db_folder = _find_db_folder()

if _db_folder:
    sys.path.insert(0, _db_folder)

from db_connection import get_db_connection

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

BG = "#F7F6F0"
PANEL = "#FFFFFF"
TRACK = "#E3E9E2"
GRID = "#E6EBE5"
TEXT = "#254D3A"
MUTED = "#738276"

IN_COLOR = "#507A5A"
OUT_COLOR = "#C98570"

PALETTE = [
    "#507A5A",
    "#8FA995",
    "#C98570",
    "#B7C9B9",
    "#6B8E78",
    "#D9A08E",
    "#7F9C89",
    "#AEBDAE",
]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "text.color": TEXT,
    "axes.labelcolor": TEXT,
    "xtick.color": TEXT,
    "ytick.color": MUTED,
    "figure.facecolor": BG,
    "axes.facecolor": PANEL,
    "savefig.facecolor": BG,
    "legend.frameon": False,
})


def inr(value):
    if value >= 1e7:
        return f"₹{value / 1e7:.2f} Cr"

    if value >= 1e5:
        return f"₹{value / 1e5:.2f} L"

    if value >= 1e3:
        return f"₹{value / 1e3:.1f}K"

    return f"₹{value:,.0f}"


def cat_of(value):
    return value or "Uncategorized"


def wrap(names, width=13):
    return [
        "\n".join(textwrap.wrap(str(name), width=width)) or str(name)
        for name in names
    ]


def tone(color, amount):
    r, g, b = to_rgb(color)

    if amount >= 0:
        return (
            r + (1 - r) * amount,
            g + (1 - g) * amount,
            b + (1 - b) * amount,
        )

    k = 1 + amount

    return r * k, g * k, b * k


def gradient_bar(ax, x, width, height, color):
    if height <= 0:
        return

    ax.bar(
        x,
        height,
        width * 1.4,
        color=color,
        alpha=0.10,
        linewidth=0,
        zorder=2,
    )

    cmap = LinearSegmentedColormap.from_list(
        "bar",
        [tone(color, -0.25), tone(color, 0.20)],
    )

    ax.imshow(
        np.linspace(0, 1, 128).reshape(-1, 1),
        cmap=cmap,
        aspect="auto",
        origin="lower",
        extent=(
            x - width / 2,
            x + width / 2,
            0,
            height,
        ),
        zorder=3,
    )


def style_axes(ax):
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.set_axisbelow(True)

    ax.grid(
        axis="y",
        color=GRID,
        linewidth=0.8,
        linestyle=(0, (4, 4)),
    )

    ax.tick_params(length=0)


def finish_bars(ax, names, ymax, y_format=None):
    style_axes(ax)

    ax.set_xlim(-0.65, len(names) - 0.35)
    ax.set_ylim(0, ymax * 1.22)

    ax.set_xticks(np.arange(len(names)))

    ax.set_xticklabels(
        wrap(names),
        fontsize=10.5,
        color=TEXT,
    )

    ax.tick_params(axis="x", pad=10)
    ax.tick_params(axis="y", labelsize=9.5, pad=8)

    if y_format:
        ax.yaxis.set_major_formatter(
            FuncFormatter(lambda value, _: y_format(value))
        )


def legend_below(ax, handles):
    ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.2),
        ncol=min(len(handles), 5),
        fontsize=10.5,
        labelcolor=MUTED,
        handlelength=1,
        handleheight=1,
        columnspacing=1.8,
    )


def chip(color, label):
    return Patch(
        facecolor=color,
        edgecolor="none",
        label=label,
    )


def bar_axes(n):
    return plt.subplots(
        figsize=(max(9, n * 1.15), 5.2)
    )


def save_chart(fig, filename):
    fig.savefig(
        os.path.join(OUTPUT_DIR, filename),
        dpi=220,
        bbox_inches="tight",
        pad_inches=0.4,
        facecolor=BG,
    )

    plt.close(fig)


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


def category_colors():
    cats = sorted({
        cat_of(row[1])
        for row in get_inventory()
    })

    return {
        category: PALETTE[i % len(PALETTE)]
        for i, category in enumerate(cats)
    }


def value_label(ax, x, y, text, size=10.5):
    ax.text(
        x,
        y,
        text,
        ha="center",
        va="bottom",
        fontsize=size,
        fontweight="bold",
        color=TEXT,
        zorder=5,
    )



def low_stock_chart():
    rows = [
        row
        for row in get_inventory()
        if float(row[2]) <= float(row[3])
    ]

    if not rows:
        fig, ax = plt.subplots(figsize=(10, 5))

        ax.text(
            0.5,
            0.5,
            "No low-stock products",
            ha="center",
            va="center",
            fontsize=16,
            color=MUTED,
            transform=ax.transAxes,
        )

        ax.set_title("Low-Stock Products")
        ax.set_xticks([])
        ax.set_yticks([])

        for spine in ax.spines.values():
            spine.set_visible(False)

        fig.tight_layout()
        save_chart(fig, "low_stock_products.png")
        plt.close(fig)

        print("No low-stock products found.")
        return

    rows.sort(
        key=lambda row: float(row[2]) / max(float(row[3]), 1)
    )

    rows = rows[:10]

    colors = category_colors()

    names = [row[0] for row in rows]
    cats = [cat_of(row[1]) for row in rows]

    current = np.array([
        float(row[2])
        for row in rows
    ])

    reorder = np.array([
        float(row[3])
        for row in rows
    ])

    x = np.arange(len(rows))

    fig, ax = bar_axes(len(rows))

    ax.bar(
        x,
        reorder,
        0.78,
        color=TRACK,
        edgecolor=MUTED,
        linewidth=1,
        linestyle=(0, (3, 3)),
        zorder=2,
    )

    for i in range(len(rows)):
        gradient_bar(
            ax,
            x[i],
            0.46,
            current[i],
            colors[cats[i]],
        )

        value_label(
            ax,
            x[i],
            reorder[i] + reorder.max() * 0.02,
            f"{current[i]:,.0f} / {reorder[i]:,.0f}",
        )

    finish_bars(ax, names, reorder.max())

    used = [
        category
        for category in colors
        if category in set(cats)
    ]

    legend_below(
        ax,
        [chip(colors[category], category) for category in used]
        + [
            Patch(
                facecolor=TRACK,
                edgecolor=MUTED,
                linestyle=(0, (3, 3)),
                label="Reorder level",
            )
        ],
    )

    save_chart(fig, "low_stock_products.png")
    plt.close(fig)


def fast_moving_chart():
    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                p.product_name,
                c.category,
                SUM(t.quantity) AS total_out
            FROM products p
            JOIN stock_transactions t
                ON p.product_id = t.product_id
            JOIN current_stock_report c
                ON c.product_name = p.product_name
            WHERE t.transaction_type = %s
            GROUP BY
                p.product_id,
                p.product_name,
                c.category
            ORDER BY total_out DESC
            LIMIT %s
        """, ("STOCK_OUT", 10))

        data = cursor.fetchall()

    finally:
        connection.close()

    if not data:
        print("No stock-out transactions found.")
        return

    colors = category_colors()

    names = [row[0] for row in data]
    cats = [cat_of(row[1]) for row in data]

    qty = np.array([
        float(row[2])
        for row in data
    ])

    x = np.arange(len(data))

    fig, ax = bar_axes(len(data))

    for i in range(len(data)):
        gradient_bar(
            ax,
            x[i],
            0.58,
            qty[i],
            colors[cats[i]],
        )

        value_label(
            ax,
            x[i],
            qty[i] + qty.max() * 0.02,
            f"{qty[i]:,.0f}",
            11,
        )

    finish_bars(ax, names, qty.max())

    used = [
        category
        for category in colors
        if category in set(cats)
    ]

    legend_below(
        ax,
        [chip(colors[category], category) for category in used],
    )

    save_chart(fig, "fast_moving_products.png")


def category_chart():
    data = get_inventory()

    if not data:
        print("No inventory data found.")
        return

    colors = category_colors()
    totals = {}

    for row in data:
        category = cat_of(row[1])

        totals[category] = (
            totals.get(category, 0)
            + float(row[2])
        )

    items = sorted(
        totals.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    names = [name for name, _ in items]

    values = np.array([
        value
        for _, value in items
    ])

    grand = values.sum()

    if grand <= 0:
        print("No stock available for category analysis.")
        return

    x = np.arange(len(names))

    fig, ax = plt.subplots(
        figsize=(max(8, len(names) * 1.6), 5.2)
    )

    for i, name in enumerate(names):
        gradient_bar(
            ax,
            x[i],
            0.54,
            values[i],
            colors[name],
        )

        value_label(
            ax,
            x[i],
            values[i] + values.max() * 0.02,
            f"{values[i]:,.0f}",
            12,
        )

        ax.text(
            x[i],
            values[i] + values.max() * 0.11,
            f"{values[i] / grand * 100:.0f}%",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color=colors[name],
            zorder=5,
            bbox=dict(
                boxstyle="round,pad=0.35,rounding_size=0.8",
                facecolor=tone(colors[name], 0.75),
                edgecolor="none",
            ),
        )

    finish_bars(
        ax,
        names,
        values.max() * 1.1,
    )

    save_chart(fig, "stock_by_category.png")


def stock_movement_chart():
    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                DATE(t.transaction_date),
                c.category,
                t.transaction_type,
                SUM(t.quantity)
            FROM stock_transactions t
            JOIN products p
                ON p.product_id = t.product_id
            JOIN current_stock_report c
                ON c.product_name = p.product_name
            GROUP BY
                DATE(t.transaction_date),
                c.category,
                t.transaction_type
            ORDER BY DATE(t.transaction_date)
        """)

        data = cursor.fetchall()

    finally:
        connection.close()

    data = [
        row
        for row in data
        if row[2] in ("STOCK_IN", "STOCK_OUT")
    ]

    if not data:
        print("No stock movement data found.")
        return

    active_dates = sorted({
        row[0]
        for row in data
    })

    if len(active_dates) < 5:
        totals = {}

        for date, cat, kind, qty in data:
            bucket = totals.setdefault(
                cat_of(cat),
                {
                    "STOCK_IN": 0,
                    "STOCK_OUT": 0,
                },
            )

            bucket[kind] += float(qty)

        names = sorted(
            totals,
            key=lambda category: (
                totals[category]["STOCK_IN"]
                + totals[category]["STOCK_OUT"]
            ),
            reverse=True,
        )

        stock_in = np.array([
            totals[name]["STOCK_IN"]
            for name in names
        ])

        stock_out = np.array([
            totals[name]["STOCK_OUT"]
            for name in names
        ])

        x = np.arange(len(names))
        width = 0.34

        peak = max(
            stock_in.max(),
            stock_out.max(),
            1,
        )

        fig, ax = plt.subplots(
            figsize=(max(8, len(names) * 1.9), 5.2)
        )

        for i in range(len(names)):
            gradient_bar(
                ax,
                x[i] - width / 2 - 0.02,
                width,
                stock_in[i],
                IN_COLOR,
            )

            gradient_bar(
                ax,
                x[i] + width / 2 + 0.02,
                width,
                stock_out[i],
                OUT_COLOR,
            )

            value_label(
                ax,
                x[i] - width / 2 - 0.02,
                stock_in[i] + peak * 0.02,
                f"{stock_in[i]:,.0f}",
                11,
            )

            value_label(
                ax,
                x[i] + width / 2 + 0.02,
                stock_out[i] + peak * 0.02,
                f"{stock_out[i]:,.0f}",
                11,
            )

        finish_bars(ax, names, peak)

        legend_below(
            ax,
            [
                chip(IN_COLOR, "Stock in"),
                chip(OUT_COLOR, "Stock out"),
            ],
        )

        save_chart(
            fig,
            "stock_movement_over_time.png",
        )

        return

    colors = category_colors()

    latest = active_dates[-1]

    start = max(
        active_dates[0],
        latest - timedelta(days=29),
    )

    dates = [
        start + timedelta(days=i)
        for i in range((latest - start).days + 1)
    ]

    per_cat = {}
    overall = {}

    for date, cat, kind, qty in data:
        if not (start <= date <= latest):
            continue

        for bucket in (
            per_cat.setdefault(cat_of(cat), {}),
            overall,
        ):
            bucket.setdefault(
                date,
                {
                    "STOCK_IN": 0,
                    "STOCK_OUT": 0,
                },
            )

            bucket[date][kind] += float(qty)

    volume = {
        category: sum(
            values["STOCK_IN"] + values["STOCK_OUT"]
            for values in category_data.values()
        )
        for category, category_data in per_cat.items()
    }

    ordered = sorted(
        volume,
        key=volume.get,
        reverse=True,
    )[:7]

    panels = (
        [("All categories", overall, TEXT)]
        + [
            (category, per_cat[category], colors[category])
            for category in ordered
        ]
    )

    ncols = 2
    nrows = int(np.ceil(len(panels) / ncols))

    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(11.5, 3.3 * nrows),
        squeeze=False,
    )

    axes = axes.flatten()

    for ax, (title, bucket, title_color) in zip(axes, panels):
        for key, color in (
            ("STOCK_IN", IN_COLOR),
            ("STOCK_OUT", OUT_COLOR),
        ):
            series = [
                bucket.get(date, {}).get(key, 0)
                for date in dates
            ]

            ax.fill_between(
                dates,
                series,
                color=color,
                alpha=0.12,
                linewidth=0,
            )

            ax.plot(
                dates,
                series,
                color=color,
                linewidth=2.6,
                solid_capstyle="round",
            )

            ax.scatter(
                dates,
                series,
                s=26,
                color=PANEL,
                edgecolor=color,
                linewidth=1.8,
                zorder=4,
            )

        style_axes(ax)

        ax.set_title(
            title,
            loc="left",
            fontsize=13,
            fontweight="bold",
            color=title_color,
            pad=12,
        )

        top = max(
            [
                bucket.get(date, {}).get(key, 0)
                for date in dates
                for key in ("STOCK_IN", "STOCK_OUT")
            ] + [1]
        )

        ax.set_ylim(0, top * 1.18)
        ax.set_xlim(dates[0], dates[-1])

        ax.xaxis.set_major_locator(
            mdates.AutoDateLocator(
                minticks=3,
                maxticks=5,
            )
        )

        ax.xaxis.set_major_formatter(
            mdates.DateFormatter("%d %b")
        )

        ax.tick_params(
            axis="x",
            labelsize=9.5,
            pad=8,
            colors=TEXT,
        )

        ax.tick_params(
            axis="y",
            labelsize=9,
            pad=6,
        )

    for ax in axes[len(panels):]:
        ax.axis("off")

    fig.legend(
        handles=[
            Line2D(
                [0],
                [0],
                color=IN_COLOR,
                linewidth=4,
                label="Stock in",
            ),
            Line2D(
                [0],
                [0],
                color=OUT_COLOR,
                linewidth=4,
                label="Stock out",
            ),
        ],
        loc="upper right",
        ncol=2,
        fontsize=11,
        labelcolor=MUTED,
        bbox_to_anchor=(0.97, 1.0),
    )

    fig.subplots_adjust(
        top=0.88,
        hspace=0.65,
        wspace=0.18,
    )

    save_chart(
        fig,
        "stock_movement_over_time.png",
    )


def inventory_value_chart():
    data = get_inventory()

    if not data:
        print("No inventory data found.")
        return

    valued = [
        (
            row[0],
            cat_of(row[1]),
            float(row[2]) * float(row[4]),
        )
        for row in data
    ]

    if sum(item[2] for item in valued) <= 0:
        print("No inventory value available.")
        return

    valued.sort(
        key=lambda item: item[2],
        reverse=True,
    )

    top = valued[:10]
    colors = category_colors()

    names = [item[0] for item in top]
    cats = [item[1] for item in top]

    values = np.array([
        item[2]
        for item in top
    ])

    x = np.arange(len(top))

    fig, ax = bar_axes(len(top))

    for i in range(len(top)):
        gradient_bar(
            ax,
            x[i],
            0.58,
            values[i],
            colors[cats[i]],
        )

        value_label(
            ax,
            x[i],
            values[i] + values.max() * 0.02,
            inr(values[i]),
        )

    finish_bars(
        ax,
        names,
        values.max(),
        y_format=inr,
    )

    used = [
        category
        for category in colors
        if category in set(cats)
    ]

    legend_below(
        ax,
        [chip(colors[category], category) for category in used],
    )

    save_chart(
        fig,
        "inventory_value_by_product.png",
    )


if __name__ == "__main__":
    low_stock_chart()
    fast_moving_chart()
    category_chart()
    stock_movement_chart()
    inventory_value_chart()

    print("Matplotlib chart generation finished.")
