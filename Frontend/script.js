
const API_BASE = "";

const state = {
    products: [],
    suppliers: [],
    transactions: [],
    lowStock: [],
    chart: null
};

const $ = (id) => document.getElementById(id);

const money = (value) =>
    new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2
    }).format(Number(value) || 0);

const number = (value) =>
    new Intl.NumberFormat("en-IN").format(Number(value) || 0);

const escapeHTML = (value) =>
    String(value ?? "").replace(/[&<>"']/g, (character) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);

async function api(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: {
            ...(options.body ? { "Content-Type": "application/json" } : {}),
            ...options.headers
        }
    });

    const text = await response.text();
    let data = {};

    try {
        data = text ? JSON.parse(text) : {};
    } catch {
        data = { message: text };
    }

    if (!response.ok) {
        throw new Error(
            data.error || data.message || `Request failed (${response.status})`
        );
    }

    return data;
}

function showToast(message, isError = false) {
    const container = $("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast${isError ? " error" : ""}`;
    toast.textContent = message;
    container.appendChild(toast);

    window.setTimeout(() => toast.remove(), 3500);
}

function setMessage(id, message, isError = false) {
    const element = $(id);
    if (!element) return;

    element.textContent = message;
    element.classList.toggle("error", isError);
}

function formatDate(value) {
    if (!value) return "—";

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);

    return date.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric"
    });
}

function currentStock(product) {
    const value = product.current_stock;
    return Number(value ?? product.opening_stock ?? 0);
}

function isLowStock(product) {
    return currentStock(product) <= Number(product.reorder_level ?? 10);
}

function productName(productId) {
    const product = state.products.find(
        (item) => Number(item.product_id) === Number(productId)
    );

    return product?.product_name || "Unknown product";
}

function productBySku(sku) {
    return state.products.find((item) => item.sku === sku);
}

function statusBadge(product) {
    const low = isLowStock(product);

    return `<span class="status-badge${low ? " low" : ""}">
        ${low ? "Low stock" : "In stock"}
    </span>`;
}

async function loadDashboard() {
    const sidebarStatus = $("sidebarConnection");

    try {
        const [productsData, suppliersData, transactionsData, lowStockData] =
            await Promise.all([
                api("/products"),
                api("/suppliers"),
                api("/transactions"),
                api("/low-stock")
            ]);

        state.products = Array.isArray(productsData)
            ? productsData
            : productsData.products || [];

        state.suppliers = Array.isArray(suppliersData)
            ? suppliersData
            : suppliersData.suppliers || [];

        state.transactions = Array.isArray(transactionsData)
            ? transactionsData
            : transactionsData.transactions || [];

        state.lowStock = Array.isArray(lowStockData)
            ? lowStockData
            : lowStockData.low_stock_products || [];

        if (sidebarStatus) {
            sidebarStatus.textContent = "Connected to API";
        }

        renderDashboard();
        renderProducts();
        renderSuppliers();
        renderTransactions();
        renderLowStock();
        renderStockOptions();
        renderChart();

    } catch (error) {
        if (sidebarStatus) {
            sidebarStatus.textContent = "Connection failed";
        }

        showToast(
            `Could not load inventory: ${error.message}. Check Flask and the API routes.`,
            true
        );

        console.error("Dashboard loading error:", error);
    }
}

function renderDashboard() {
    const totalUnits = state.products.reduce(
        (sum, product) => sum + currentStock(product),
        0
    );

    const totalValue = state.products.reduce(
        (sum, product) =>
            sum + currentStock(product) * Number(product.unit_cost || 0),
        0
    );

    $("totalProducts").textContent = number(state.products.length);
    $("totalUnits").textContent = number(totalUnits);
    $("inventoryValue").textContent = money(totalValue);
    $("lowStockCount").textContent = number(state.lowStock.length);

    const recent = [...state.transactions]
        .sort((a, b) =>
            new Date(b.transaction_date || 0) -
            new Date(a.transaction_date || 0)
        )
        .slice(0, 5);

    $("overviewTransactionsTable").innerHTML = recent.length
        ? recent.map((transaction) => `
            <tr>
                <td>${escapeHTML(transaction.product_name || productName(transaction.product_id))}</td>
                <td>${transactionTypeBadge(transaction.transaction_type)}</td>
                <td>${number(transaction.quantity)}</td>
                <td>${escapeHTML(formatDate(transaction.transaction_date))}</td>
            </tr>
        `).join("")
        : `<tr><td colspan="4" class="empty-state">No transactions recorded yet.</td></tr>`;

    $("overviewLowStockList").innerHTML = state.lowStock.length
        ? state.lowStock.slice(0, 5).map((product) => `
            <div class="low-stock-item">
                <div>
                    <strong>${escapeHTML(product.product_name)}</strong>
                    <small>${escapeHTML(product.sku || "")}</small>
                </div>
                <span class="status-badge low">
                    ${number(currentStock(product))} left
                </span>
            </div>
        `).join("")
        : `<p class="empty-state">All products are above their reorder levels.</p>`;
}

function transactionTypeBadge(type) {
    const incoming = String(type).toUpperCase() === "STOCK_IN";

    return `<span class="status-badge${incoming ? "" : " low"}">
        ${incoming ? "Stock in" : "Stock out"}
    </span>`;
}

function renderProducts() {
    const search = ($("productSearch")?.value || "").trim().toLowerCase();

    const products = state.products.filter((product) =>
        [product.product_name, product.sku, product.category]
            .some((value) => String(value || "").toLowerCase().includes(search))
    );

    $("productCount").textContent =
        `${products.length} product${products.length === 1 ? "" : "s"}`;

    $("productsTable").innerHTML = products.length
        ? products.map((product) => `
            <tr>
                <td><strong>${escapeHTML(product.product_name)}</strong></td>
                <td>${escapeHTML(product.sku)}</td>
                <td>${escapeHTML(product.category || "—")}</td>
                <td>${number(currentStock(product))}</td>
                <td>${money(product.unit_cost)}</td>
                <td>${statusBadge(product)}</td>
                <td>
                    <div class="action-group">
                        <button class="table-action" data-edit="${Number(product.product_id)}">Edit</button>
                        <button class="table-action danger" data-delete="${Number(product.product_id)}">Delete</button>
                    </div>
                </td>
            </tr>
        `).join("")
        : `<tr><td colspan="7" class="empty-state">No matching products found.</td></tr>`;
}

function renderSuppliers() {
    const select = $("stockInSupplier");
    if (!select) return;

    const selected = select.value;

    select.innerHTML = `<option value="">Select a supplier</option>` +
        state.suppliers.map((supplier) => `
            <option value="${Number(supplier.supplier_id)}">
                ${escapeHTML(supplier.supplier_name)}
            </option>
        `).join("");

    if (state.suppliers.some(
        (supplier) => String(supplier.supplier_id) === selected
    )) {
        select.value = selected;
    }

    renderSupplierDetails();
}

function renderSupplierDetails() {
    const select = $("stockInSupplier");
    const details = $("supplierDetails");
    if (!select || !details) return;

    const supplier = state.suppliers.find(
        (item) => String(item.supplier_id) === select.value
    );

    if (!supplier) {
        details.textContent = "Select a supplier to view contact details.";
        return;
    }

    const phone = supplier.phone_number || "No phone number";
    const email = supplier.email || "No email address";

    details.innerHTML =
        `<span>${escapeHTML(phone)}</span><span>${escapeHTML(email)}</span>`;
}

function openSupplierModal() {
    const form = $("supplierForm");
    const modal = $("supplierModal");
    if (!form || !modal) return;

    form.reset();
    setMessage("supplierFormMessage", "");
    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
    $("supplierName")?.focus();
}

function closeSupplierModal() {
    const modal = $("supplierModal");
    if (!modal) return;

    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
}

async function saveSupplier(event) {
    event.preventDefault();

    const payload = {
        supplier_name: $("supplierName").value.trim(),
        phone_number: $("supplierPhone").value.trim(),
        email: $("supplierEmail").value.trim()
    };

    if (!payload.supplier_name) {
        setMessage("supplierFormMessage", "Supplier name is required.", true);
        return;
    }

    try {
        const result = await api("/suppliers", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        const newSupplierId = result.supplier_id;

        closeSupplierModal();
        await loadDashboard();

        if (newSupplierId) {
            $("stockInSupplier").value = String(newSupplierId);
            renderSupplierDetails();
        }

        showToast("Supplier added successfully.");

    } catch (error) {
        setMessage("supplierFormMessage", error.message, true);
    }
}

function renderStockOptions() {
    ["stockInProduct", "stockOutProduct"].forEach((id) => {
        const select = $(id);
        if (!select) return;

        const selected = select.value;

        select.innerHTML = `<option value="">Select a product</option>` +
            state.products.map((product) => `
                <option value="${escapeHTML(product.sku)}">
                    ${escapeHTML(product.product_name)} (${escapeHTML(product.sku)})
                </option>
            `).join("");

        if (state.products.some((product) => product.sku === selected)) {
            select.value = selected;
        }
    });
}

function renderTransactions() {
    const transactions = [...state.transactions].sort((a, b) =>
        new Date(b.transaction_date || 0) -
        new Date(a.transaction_date || 0)
    );

    $("transactionsTable").innerHTML = transactions.length
        ? transactions.map((transaction) => `
            <tr>
                <td>${escapeHTML(transaction.product_name || productName(transaction.product_id))}</td>
                <td>${transactionTypeBadge(transaction.transaction_type)}</td>
                <td>${number(transaction.quantity)}</td>
                <td>${escapeHTML(transaction.supplier_name || "—")}</td>
                <td>${escapeHTML(formatDate(transaction.transaction_date))}</td>
            </tr>
        `).join("")
        : `<tr><td colspan="5" class="empty-state">No transactions recorded yet.</td></tr>`;
}

function renderLowStock() {
    $("lowStockTable").innerHTML = state.lowStock.length
        ? state.lowStock.map((product) => `
            <tr>
                <td><strong>${escapeHTML(product.product_name)}</strong></td>
                <td>${escapeHTML(product.sku || "—")}</td>
                <td>${number(currentStock(product))}</td>
                <td>${number(product.reorder_level)}</td>
                <td><span class="status-badge low">Reorder needed</span></td>
            </tr>
        `).join("")
        : `<tr><td colspan="5" class="empty-state">No products currently need reordering.</td></tr>`;
}

function renderChart() {
    const canvas = $("movementChart");
    if (!canvas || typeof Chart === "undefined") return;

    const days = [];

    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setHours(0, 0, 0, 0);
        date.setDate(date.getDate() - i);

        days.push({
            key: date.toLocaleDateString("en-CA"),
            label: date.toLocaleDateString("en-IN", {
                day: "2-digit",
                month: "short"
            }),
            incoming: 0,
            outgoing: 0
        });
    }

    state.transactions.forEach((transaction) => {
        const date = new Date(transaction.transaction_date);
        if (Number.isNaN(date.getTime())) return;

        const key = date.toLocaleDateString("en-CA");
        const day = days.find((item) => item.key === key);
        if (!day) return;

        const type = String(transaction.transaction_type).toUpperCase();

        if (type === "STOCK_IN") {
            day.incoming += Number(transaction.quantity || 0);
        } else if (type === "STOCK_OUT") {
            day.outgoing += Number(transaction.quantity || 0);
        }
    });

    if (state.chart) {
        state.chart.destroy();
    }

    state.chart = new Chart(canvas, {
        type: "bar",
        data: {
            labels: days.map((day) => day.label),
            datasets: [
                {
                    label: "Stock in",
                    data: days.map((day) => day.incoming),
                    backgroundColor: "#8da78a",
                    borderRadius: 4,
                    maxBarThickness: 20
                },
                {
                    label: "Stock out",
                    data: days.map((day) => day.outgoing),
                    backgroundColor: "#d8a18b",
                    borderRadius: 4,
                    maxBarThickness: 20
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "index",
                intersect: false
            },
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        usePointStyle: true,
                        boxWidth: 7,
                        padding: 16,
                        color: "#7a8178",
                        font: { size: 10 }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: {
                        color: "#7a8178",
                        font: { size: 10 }
                    },
                    border: { display: false }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: "#edf0e9" },
                    ticks: {
                        precision: 0,
                        color: "#7a8178",
                        font: { size: 10 }
                    },
                    border: { display: false }
                }
            }
        }
    });
}

async function refreshCharts() {
    try {
        const response = await fetch("/refresh-charts", {
            method: "POST"
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Could not refresh charts");
        }

        const timestamp = Date.now();

        document.querySelectorAll(".analysis-chart").forEach((img) => {
            const url = new URL(img.src, window.location.origin);
            url.searchParams.set("t", timestamp);
            img.src = url.toString();
        });

        showToast("Charts refreshed successfully");
    } catch (error) {
        showToast("Could not refresh charts: " + error.message, "error");
    }
}
function openProductModal(product = null) {
    $("productForm").reset();
    $("productFormMessage").textContent = "";
    $("editProductId").value = product?.product_id ?? "";
    $("productModalTitle").textContent = product ? "Edit product" : "Add product";
    $("saveProductBtn").textContent = product ? "Save changes" : "Save product";

    if (product) {
        $("productSku").value = product.sku || "";
        $("productName").value = product.product_name || "";
        $("productCategory").value = product.category || "";
        $("productOpeningStock").value = product.opening_stock ?? 0;
        $("productReorderLevel").value = product.reorder_level ?? 10;
        $("productUnitCost").value = product.unit_cost ?? 0;
    }

    $("productModal").classList.add("open");
    $("productModal").setAttribute("aria-hidden", "false");
    $("productSku").focus();
}

function closeProductModal() {
    $("productModal").classList.remove("open");
    $("productModal").setAttribute("aria-hidden", "true");
}

function navigate(page) {
    const section = $(page);
    if (!section || !section.classList.contains("page-section")) return;

    document.querySelectorAll(".page-section").forEach((item) =>
        item.classList.toggle("active", item.id === page)
    );

    document.querySelectorAll(".nav-link").forEach((link) =>
        link.classList.toggle("active", link.dataset.page === page)
    );

    const titles = {
        overview: "Overview",
        products: "Products",
        "stock-in": "Stock In",
        "stock-out": "Stock Out",
        transactions: "Transactions",
        "low-stock": "Low Stock"
    };

    $("pageTitle").textContent = titles[page] || "Overview";
    window.scrollTo({ top: 0, behavior: "smooth" });
}

async function saveProduct(event) {
    event.preventDefault();

    const id = $("editProductId").value;

    const payload = {
        sku: $("productSku").value.trim(),
        product_name: $("productName").value.trim(),
        category: $("productCategory").value.trim(),
        opening_stock: Number($("productOpeningStock").value),
        reorder_level: Number($("productReorderLevel").value),
        unit_cost: Number($("productUnitCost").value)
    };

    if (!payload.sku || !payload.product_name || !payload.category) {
        setMessage("productFormMessage", "Please complete all required fields.", true);
        return;
    }

    try {
        await api(id ? `/products/${id}` : "/products", {
            method: id ? "PUT" : "POST",
            body: JSON.stringify(payload)
        });

        closeProductModal();
        showToast(id ? "Product updated successfully." : "Product added successfully.");
        await loadDashboard();

    } catch (error) {
        setMessage("productFormMessage", error.message, true);
    }
}

async function deleteProduct(id) {
    const product = state.products.find(
        (item) => Number(item.product_id) === Number(id)
    );

    if (!product) return;

    const confirmed = window.confirm(
        `Delete "${product.product_name}"? Products referenced by stock transactions may not be deletable.`
    );

    if (!confirmed) return;

    try {
        await api(`/products/${id}`, { method: "DELETE" });
        showToast("Product deleted successfully.");
        await loadDashboard();
    } catch (error) {
        showToast(error.message, true);
    }
}

async function submitStock(event, type) {
    event.preventDefault();

    const incoming = type === "stock-in";
    const prefix = incoming ? "stockIn" : "stockOut";
    const messageId = incoming ? "stockInMessage" : "stockOutMessage";

    const sku = $(prefix + "Product").value;
    const quantity = Number($(prefix + "Quantity").value);
    const notes = $(prefix + "Notes").value.trim();

    if (!sku || !Number.isInteger(quantity) || quantity < 1) {
        setMessage(messageId, "Select a product and enter a positive whole-number quantity.", true);
        return;
    }

    const payload = { sku, quantity, notes };

    if (incoming) {
        const supplierId = $("stockInSupplier")?.value;

        if (!supplierId) {
            setMessage(messageId, "Select a supplier before recording stock in.", true);
            return;
        }

        payload.supplier_id = Number(supplierId);
    }

    try {
        await api(incoming ? "/stock-in" : "/stock-out", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        $(incoming ? "stockInForm" : "stockOutForm").reset();
        setMessage(messageId, incoming
            ? "Stock received successfully."
            : "Stock issued successfully.");

        showToast(incoming ? "Stock-in recorded." : "Stock-out recorded.");
        await loadDashboard();

    } catch (error) {
        setMessage(messageId, error.message, true);
    }
}

function bindEvents() {
    document.querySelectorAll("[data-page]").forEach((link) => {
        link.addEventListener("click", (event) => {
            event.preventDefault();
            const page = link.dataset.page;
            navigate(page);
            history.replaceState(null, "", `#${page}`);
        });
    });

    $("headerAddProduct").addEventListener("click", () => {
        navigate("products");
        openProductModal();
    });

    $("addProductBtn").addEventListener("click", () => openProductModal());

    $("closeProductModal").addEventListener("click", closeProductModal);
    $("cancelProductModal").addEventListener("click", closeProductModal);

    $("productModal").addEventListener("click", (event) => {
        if (event.target === $("productModal")) closeProductModal();
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeProductModal();
            closeSupplierModal();
        }
    });

    $("productForm").addEventListener("submit", saveProduct);

    $("addSupplierBtn")?.addEventListener("click", openSupplierModal);
    $("closeSupplierModal")?.addEventListener("click", closeSupplierModal);
    $("cancelSupplierModal")?.addEventListener("click", closeSupplierModal);
    $("supplierForm")?.addEventListener("submit", saveSupplier);

    $("supplierModal")?.addEventListener("click", (event) => {
        if (event.target === $("supplierModal")) closeSupplierModal();
    });

    $("stockInSupplier")?.addEventListener("change", renderSupplierDetails);

    $("productsTable").addEventListener("click", (event) => {
        const editButton = event.target.closest("[data-edit]");
        const deleteButton = event.target.closest("[data-delete]");

        if (editButton) {
            const product = state.products.find(
                (item) => Number(item.product_id) === Number(editButton.dataset.edit)
            );

            if (product) openProductModal(product);
        }

        if (deleteButton) {
            deleteProduct(Number(deleteButton.dataset.delete));
        }
    });

    $("productSearch").addEventListener("input", renderProducts);

    $("stockInForm").addEventListener("submit", (event) =>
        submitStock(event, "stock-in")
    );

    $("stockOutForm").addEventListener("submit", (event) =>
        submitStock(event, "stock-out")
    );

    $("refreshDataBtn")?.addEventListener("click", async () => {
        await loadDashboard();
        showToast("Inventory refresh completed.");
    });

    $("refreshChartsBtn")?.addEventListener("click", refreshCharts);
}

function initialize() {
    $("todayDate").textContent = new Date().toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric"
    });

    bindEvents();

    const initialPage = window.location.hash.slice(1);
    if ($(initialPage)?.classList.contains("page-section")) {
        navigate(initialPage);
    }

    loadDashboard();
}

document.addEventListener("DOMContentLoaded", initialize);
