
const API_BASE = "";

const state = {
    user: null,
    products: [],
    suppliers: [],
    transactions: [],
    lowStock: [],
    pendingUsers: [],
    approvedUsers: [],
    chart: null,
    currentPage: "overview",
    eventsBound: false
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
    String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);

async function apiRequest(url, options = {}) {
    const config = {
        credentials: "include",
        ...options,
        headers: {
            ...(options.body instanceof FormData ? {} : {
                "Content-Type": "application/json"
            }),
            ...options.headers
        }
    };

    const response = await fetch(API_BASE + url, config);
    const contentType = response.headers.get("content-type") || "";

    let data = {};

    if (contentType.includes("application/json")) {
        data = await response.json();
    } else {
        data.message = await response.text();
    }

    if (!response.ok) {
        throw new Error(data.message || data.error || `Request failed (${response.status})`);
    }

    return data;
}

function showToast(message, type = "success") {
    const container = $("toastContainer");

    if (!container) {
        alert(message);
        return;
    }

    const toast = document.createElement("div");
    toast.className = `toast ${type === "error" ? "error" : ""}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => toast.remove(), 3500);
}

function showMessage(elementId, message, type = "error") {
    const element = $(elementId);
    if (!element) return;

    element.textContent = message;
    element.classList.toggle("success", type === "success");
    element.classList.toggle("error", type === "error");
}

function clearMessage(elementId) {
    showMessage(elementId, "");
}

/* AUTHENTICATION PAGES */

function showAuthPage(page) {
    [
        "landingPage",
        "loginPage",
        "signupPage",
        "pendingPage",
        "appLayout"
    ].forEach((id) => {
        $(id)?.classList.add("hidden");
    });

    $(page)?.classList.remove("hidden");
}

function showLanding() {
    showAuthPage("landingPage");
}

function showLogin() {
    showAuthPage("loginPage");
    clearMessage("loginMessage");
}

function showSignup() {
    showAuthPage("signupPage");
    clearMessage("signupMessage");
}

function showPending() {
    showAuthPage("pendingPage");
}

function getUserName() {
    return state.user?.full_name ||
        state.user?.username ||
        state.user?.name ||
        "User";
}

function isAdmin() {
    return String(state.user?.user_role || state.user?.role || "")
        .toUpperCase() === "ADMIN";
}

/* ROLE PERMISSIONS */

function applyRolePermissions() {
    const admin = isAdmin();

    document.querySelectorAll("[data-admin-only]").forEach((element) => {
        element.classList.toggle("hidden", !admin);
    });

    document.querySelectorAll(".nav-link[data-page]").forEach((element) => {
        const page = element.dataset.page;
        const adminPage = ["stock-in", "stock-out", "users"].includes(page);

        element.classList.toggle("hidden", adminPage && !admin);
    });

    if ($("sidebarUserName")) {
        $("sidebarUserName").textContent = getUserName();
    }

    if ($("sidebarUserRole")) {
        $("sidebarUserRole").textContent = admin ? "Administrator" : "Staff";
    }

    if ($("welcomeName")) {
        $("welcomeName").textContent = `Welcome back, ${getUserName()}`;
    }

    if ($("rolePill")) {
        $("rolePill").textContent = admin ? "ADMIN" : "STAFF";
    }
}

/* SIDEBAR NAVIGATION */
function showPage(page) {
    const pageSections = {
        overview: "overview",
        products: "products",
        suppliers: "suppliers",
        "stock-in": "stock-in",
        "stock-out": "stock-out",
        transactions: "transactions",
        "low-stock": "low-stock",
        analysis: "analysis",
        users: "users"
    };

    const sectionId = pageSections[page];

    if (!sectionId) {
        console.error("Invalid page:", page);
        showToast("Page not found", "error");
        return;
    }

    const section = document.getElementById(sectionId);

    if (!section) {
        console.error("Section not found:", sectionId);
        showToast("Page not found: " + page, "error");
        return;
    }

    document.querySelectorAll(".page-section").forEach(item => {
        item.classList.add("hidden");
        item.classList.remove("active");
    });

    section.classList.remove("hidden");
    section.classList.add("active");

    document.querySelectorAll(".nav-link").forEach(link => {
        link.classList.toggle("active", link.dataset.page === page);
    });

    const pageTitles = {
        overview: "Overview",
        products: "Products",
        suppliers: "Suppliers",
        "stock-in": "Stock In",
        "stock-out": "Stock Out",
        transactions: "Transactions",
        "low-stock": "Low Stock",
        analysis: "Stock Analysis",
        users: "User Management"
    };

    const title = document.getElementById("pageTitle");
    if (title) title.textContent = pageTitles[page];

    if (typeof loadPageData === "function") {
        loadPageData(page);
    }
    if (page === "analysis") {
        loadAnalysisImages();
    }

    if (page === "users") {
    loadUserManagement();
}
}

function bindNavigationEvents() {
    document.addEventListener("click", (event) => {
        const navLink = event.target.closest(".nav-link[data-page]");

        if (navLink) {
            event.preventDefault();
            showPage(navLink.dataset.page);
            return;
        }

        const pageButton = event.target.closest("[data-go-page]");

        if (pageButton) {
            event.preventDefault();
            showPage(pageButton.dataset.goPage);
        }
    });
}

/* DATA HELPERS */

function getStock(product) {
    return Number(
        product.current_stock ??
        product.stock ??
        product.available_stock ??
        product.opening_stock ??
        0
    );
}

function getProductId(product) {
    return product.product_id ?? product.id;
}

function getProductName(product) {
    return product.product_name ?? product.name ?? "Unnamed product";
}

function getProductValue(product) {
    return getStock(product) * Number(product.unit_cost || 0);
}

function isLowStock(product) {
    return getStock(product) <= Number(product.reorder_level || 0);
}

function getTransactionDate(transaction) {
    const value = transaction.transaction_date ||
        transaction.created_at ||
        transaction.date;

    if (!value) return "—";

    const date = new Date(value);

    return Number.isNaN(date.getTime())
        ? String(value)
        : date.toLocaleDateString("en-IN");
}

function getTransactionType(transaction) {
    return String(transaction.transaction_type || transaction.type || "")
        .toUpperCase();
}

function getArray(data, key) {
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.[key])) return data[key];
    return [];
}

/* AUTHENTICATION EVENTS */

function bindAuthEvents() {
    $("landingLogin")?.addEventListener("click", showLogin);
    $("landingSignup")?.addEventListener("click", showSignup);

    $("loginToSignup")?.addEventListener("click", showSignup);
    $("signupToLogin")?.addEventListener("click", showLogin);

    $("backToLanding")?.addEventListener("click", showLanding);
    $("backToLandingSignup")?.addEventListener("click", showLanding);

    $("pendingLogin")?.addEventListener("click", showLogin);

    $("loginForm")?.addEventListener("submit", handleLogin);
    $("signupForm")?.addEventListener("submit", handleSignup);

    $("logoutBtn")?.addEventListener("click", handleLogout);
}

async function handleLogin(event) {
    event.preventDefault();

    const identifier = $("loginIdentifier")?.value.trim();
    const password = $("loginPassword")?.value;

    if (!identifier || !password) {
        showMessage("loginMessage", "Enter your username/email and password.");
        return;
    }

    const button = $("loginSubmit");
    if (button) button.disabled = true;

    try {
        const data = await apiRequest("/login", {
            method: "POST",
            body: JSON.stringify({ identifier, password })
        });

        if (data.status === "PENDING") {
            showPending();
            return;
        }

        if (data.status === "REJECTED") {
            showMessage("loginMessage", "Your account registration was rejected.");
            return;
        }

        if (data.status === "INACTIVE") {
            showMessage("loginMessage", "Your account is inactive. Contact the administrator.");
            return;
        }

        if (data.status && data.status !== "SUCCESS") {
            showMessage("loginMessage", data.message || "Login failed.");
            return;
        }

        state.user = data.user || data;

        await enterDashboard();
    } catch (error) {
        showMessage("loginMessage", error.message || "Unable to login.");
    } finally {
        if (button) button.disabled = false;
    }
}

async function handleSignup(event) {
    event.preventDefault();

    const fullName = $("signupFullName")?.value.trim();
    const username = $("signupUsername")?.value.trim();
    const email = $("signupEmail")?.value.trim();
    const password = $("signupPassword")?.value;

    if (!fullName || !username || !email || !password) {
        showMessage("signupMessage", "Please fill in all fields.");
        return;
    }

    if (password.length < 6) {
        showMessage("signupMessage", "Password must contain at least 6 characters.");
        return;
    }

    const button = $("signupSubmit");
    if (button) button.disabled = true;

    try {
        const data = await apiRequest("/signup", {
            method: "POST",
            body: JSON.stringify({
                full_name: fullName,
                username,
                email,
                password
            })
        });

        showMessage(
            "signupMessage",
            data.message || "Registration submitted. Wait for administrator approval.",
            "success"
        );

        $("signupForm")?.reset();

        setTimeout(showPending, 1400);
    } catch (error) {
        showMessage("signupMessage", error.message || "Registration failed.");
    } finally {
        if (button) button.disabled = false;
    }
}

async function handleLogout() {
    try {
        await apiRequest("/logout", { method: "POST" });
    } catch (error) {
        console.error("Logout error:", error);
    }

    state.user = null;
    state.products = [];
    state.suppliers = [];
    state.transactions = [];
    state.lowStock = [];
    state.pendingUsers = [];

    if (state.chart) {
        state.chart.destroy();
        state.chart = null;
    }

    showLanding();
}

async function checkSession() {
    try {
        const data = await apiRequest("/me");
        state.user = data.user || data;

        if (!state.user || !(state.user.user_id || state.user.id || state.user.username)) {
            showLanding();
            return;
        }

        await enterDashboard();
    } catch (error) {
        showLanding();
    }
}

/* ENTER DASHBOARD */

async function enterDashboard() {
    showAuthPage("appLayout");

    applyRolePermissions();
    bindDashboardEvents();
    showPage("overview");

    if ($("todayDate")) {
        $("todayDate").textContent = new Date().toLocaleDateString("en-IN", {
            day: "numeric",
            month: "short",
            year: "numeric"
        });
    }

    await loadDashboardData();
}

/* DASHBOARD EVENTS */

function bindDashboardEvents() {
    if (state.eventsBound) return;

    state.eventsBound = true;

    bindNavigationEvents();

    $("refreshDataBtn")?.addEventListener("click", loadDashboardData);

    $("headerAddProduct")?.addEventListener("click", () => {
        if (isAdmin()) openProductModal();
    });

    $("addProductBtn")?.addEventListener("click", openProductModal);

    $("addSupplierPageBtn")?.addEventListener("click", openSupplierModal);
    $("addSupplierBtn")?.addEventListener("click", openSupplierModal);

    $("closeProductModal")?.addEventListener("click", closeProductModal);
    $("cancelProductModal")?.addEventListener("click", closeProductModal);

    $("closeSupplierModal")?.addEventListener("click", closeSupplierModal);
    $("cancelSupplierModal")?.addEventListener("click", closeSupplierModal);

    $("productForm")?.addEventListener("submit", saveProduct);
    $("supplierForm")?.addEventListener("submit", saveSupplier);

    $("stockInForm")?.addEventListener("submit", handleStockIn);
    $("stockOutForm")?.addEventListener("submit", handleStockOut);

    $("productSearch")?.addEventListener("input", renderProducts);

    $("stockInSupplier")?.addEventListener("change", updateSupplierDetails);

    $("transactionsDownloadBtn")?.addEventListener("click", downloadTransactions);
    $("downloadTransactionsBtn")?.addEventListener("click", downloadTransactions);

    $("refreshChartsBtn")?.addEventListener("click", refreshCharts);

    $("productsTable")?.addEventListener("click", handleProductTableClick);
    $("pendingUsersTable")?.addEventListener("click", handlePendingUserClick);
}

/* LOAD DASHBOARD DATA */

async function loadDashboardData() {
    try {
        const results = await Promise.allSettled([
            apiRequest("/products"),
            apiRequest("/suppliers"),
            apiRequest("/transactions"),
            apiRequest("/low-stock")
        ]);

        if (results[0].status === "fulfilled") {
            state.products = getArray(results[0].value, "products");
        }

        if (results[1].status === "fulfilled") {
            state.suppliers = getArray(results[1].value, "suppliers");
        }

        if (results[2].status === "fulfilled") {
            state.transactions = getArray(results[2].value, "transactions");
        }

        if (results[3].status === "fulfilled") {
            state.lowStock = getArray(results[3].value, "low_stock_products");

            if (!state.lowStock.length) {
                state.lowStock = getArray(results[3].value, "products");
            }
        }

        renderDashboard();

        const failed = results.filter((result) => result.status === "rejected");

        if (failed.length) {
            console.error("Some dashboard data could not be loaded:", failed);
            showToast("Some dashboard information could not be loaded.", "error");
        }
    } catch (error) {
        showToast(error.message || "Unable to load dashboard.", "error");
    }
}

function renderDashboard() {
    renderStats();
    renderProducts();
    renderSuppliers();
    renderTransactions();
    renderLowStock();
    renderStockDropdowns();
    renderMovementChart();
}

/* DASHBOARD STATISTICS */

function renderStats() {
    const totalProducts = state.products.length;

    const totalUnits = state.products.reduce(
        (sum, product) => sum + getStock(product),
        0
    );

    const inventoryValue = state.products.reduce(
        (sum, product) => sum + getProductValue(product),
        0
    );

    const lowStockCount = state.products.filter(isLowStock).length;

    if ($("totalProducts")) $("totalProducts").textContent = number(totalProducts);
    if ($("totalUnits")) $("totalUnits").textContent = number(totalUnits);
    if ($("inventoryValue")) $("inventoryValue").textContent = money(inventoryValue);
    if ($("lowStockCount")) $("lowStockCount").textContent = number(lowStockCount);

    if ($("productCount")) {
        $("productCount").textContent = `${totalProducts} products`;
    }
}

/* PRODUCTS */

function renderProducts() {
    const table = $("productsTable");
    if (!table) return;

    const search = ($("productSearch")?.value || "").toLowerCase();

    const filtered = state.products.filter((product) => {
        const text = [
            product.sku,
            getProductName(product),
            product.category
        ].join(" ").toLowerCase();

        return text.includes(search);
    });

    table.innerHTML = filtered.length
        ? filtered.map((product) => {
            const low = isLowStock(product);

            return `
                <tr>
                    <td>${escapeHTML(product.sku)}</td>
                    <td>${escapeHTML(getProductName(product))}</td>
                    <td>${escapeHTML(product.category || "—")}</td>
                    <td>${number(getStock(product))}</td>
                    <td>${number(product.reorder_level)}</td>
                    <td>${money(product.unit_cost)}</td>
                    <td>
                        <span class="stock-status ${low ? "low" : ""}">
                            ${low ? "Low Stock" : "In Stock"}
                        </span>
                    </td>
                    ${isAdmin() ? `
                    <td>
                        <button class="table-action" data-edit-product="${escapeHTML(getProductId(product))}">Edit</button>
                        <button class="table-action delete" data-delete-product="${escapeHTML(getProductId(product))}">Delete</button>
                    </td>` : ""}
                </tr>
            `;
        }).join("")
        : `<tr><td colspan="8">No products found.</td></tr>`;
}

function handleProductTableClick(event) {
    const editButton = event.target.closest("[data-edit-product]");
    const deleteButton = event.target.closest("[data-delete-product]");

    if (editButton) {
        const product = state.products.find(
            (item) => String(getProductId(item)) === editButton.dataset.editProduct
        );

        if (product) openProductModal(product);
    }

    if (deleteButton) {
        deleteProduct(deleteButton.dataset.deleteProduct);
    }
}

function openProductModal(product = null) {
    if (!isAdmin()) return;

    $("productForm")?.reset();
    clearMessage("productFormMessage");

    if ($("editProductId")) {
        $("editProductId").value = product ? getProductId(product) : "";
    }

    if ($("productModalTitle")) {
        $("productModalTitle").textContent = product ? "Edit Product" : "Add Product";
    }

    if (product) {
        $("productSku").value = product.sku || "";
        $("productName").value = getProductName(product);
        $("productCategory").value = product.category || "";
        $("productOpeningStock").value = product.opening_stock ?? 0;
        $("productReorderLevel").value = product.reorder_level ?? 10;
        $("productUnitCost").value = product.unit_cost ?? 0;
    }

    $("productModal")?.classList.remove("hidden");
}

function closeProductModal() {
    $("productModal")?.classList.add("hidden");
}

async function saveProduct(event) {
    event.preventDefault();

    if (!isAdmin()) return;

    const productId = $("editProductId")?.value;

    const product = {
        sku: $("productSku").value.trim(),
        product_name: $("productName").value.trim(),
        category: $("productCategory").value.trim(),
        opening_stock: Number($("productOpeningStock").value),
        reorder_level: Number($("productReorderLevel").value),
        unit_cost: Number($("productUnitCost").value)
    };

    if (!product.sku || !product.product_name) {
        showMessage("productFormMessage", "SKU and product name are required.");
        return;
    }

    if (Object.values(product).some((value) => value === "" || Number.isNaN(value))) {
        showMessage("productFormMessage", "Enter valid product details.");
        return;
    }

    const button = $("saveProductBtn");
    if (button) button.disabled = true;

    try {
        await apiRequest(productId ? `/products/${productId}` : "/products", {
            method: productId ? "PUT" : "POST",
            body: JSON.stringify(product)
        });

        closeProductModal();
        await loadDashboardData();

        showToast(productId ? "Product updated successfully." : "Product added successfully.");
    } catch (error) {
        showMessage("productFormMessage", error.message || "Unable to save product.");
    } finally {
        if (button) button.disabled = false;
    }
}

async function deleteProduct(productId) {
    if (!isAdmin()) return;

    if (!confirm("Are you sure you want to delete this product?")) return;

    try {
        await apiRequest(`/products/${productId}`, { method: "DELETE" });
        await loadDashboardData();

        showToast("Product deleted successfully.");
    } catch (error) {
        showToast(error.message || "Unable to delete product.", "error");
    }
}

/* SUPPLIERS */

function getSupplierId(supplier) {
    return supplier.supplier_id ?? supplier.id;
}

function getSupplierName(supplier) {
    return supplier.supplier_name ?? supplier.name ?? "Unnamed supplier";
}

function renderSuppliers() {
    const table = $("suppliersTable");
    if (!table) return;

    table.innerHTML = state.suppliers.length
        ? state.suppliers.map((supplier) => `
            <tr>
                <td>${escapeHTML(getSupplierName(supplier))}</td>
                <td>${escapeHTML(supplier.phone_number || supplier.phone || "—")}</td>
                <td>${escapeHTML(supplier.email || "—")}</td>
            </tr>
        `).join("")
        : `<tr><td colspan="3">No suppliers added yet.</td></tr>`;
}

function renderStockDropdowns() {
    const productOptions = `
        <option value="">Select product</option>
        ${state.products.map((product) => `
            <option value="${escapeHTML(product.sku)}">
                ${escapeHTML(getProductName(product))} (${escapeHTML(product.sku)})
            </option>
        `).join("")}
    `;

    ["stockInProduct", "stockOutProduct"].forEach((id) => {
        const select = $(id);
        if (!select) return;

        const selected = select.value;
        select.innerHTML = productOptions;

        if (state.products.some((product) => product.sku === selected)) {
            select.value = selected;
        }
    });

    const supplierSelect = $("stockInSupplier");

    if (supplierSelect) {
        const selected = supplierSelect.value;

        supplierSelect.innerHTML = `
            <option value="">Select supplier</option>
            ${state.suppliers.map((supplier) => `
                <option value="${escapeHTML(getSupplierId(supplier))}">
                    ${escapeHTML(getSupplierName(supplier))}
                </option>
            `).join("")}
        `;

        if (state.suppliers.some((supplier) => String(getSupplierId(supplier)) === selected)) {
            supplierSelect.value = selected;
        }

        updateSupplierDetails();
    }
}

function updateSupplierDetails() {
    const supplierId = $("stockInSupplier")?.value;

    const supplier = state.suppliers.find(
        (item) => String(getSupplierId(item)) === String(supplierId)
    );

    if ($("supplierDetails")) {
        $("supplierDetails").textContent = supplier
            ? `${supplier.phone_number || supplier.phone || "No phone"} · ${supplier.email || "No email"}`
            : "";
    }
}

function openSupplierModal() {
    if (!isAdmin()) return;

    $("supplierForm")?.reset();
    clearMessage("supplierFormMessage");

    $("supplierModal")?.classList.remove("hidden");
}

function closeSupplierModal() {
    $("supplierModal")?.classList.add("hidden");
}

async function saveSupplier(event) {
    event.preventDefault();

    if (!isAdmin()) return;

    const supplier = {
        supplier_name: $("supplierName").value.trim(),
        phone_number: $("supplierPhone").value.trim(),
        email: $("supplierEmail").value.trim()
    };

    if (!supplier.supplier_name) {
        showMessage("supplierFormMessage", "Supplier name is required.");
        return;
    }

    const button = $("saveSupplierBtn");
    if (button) button.disabled = true;

    try {
        await apiRequest("/suppliers", {
            method: "POST",
            body: JSON.stringify(supplier)
        });

        closeSupplierModal();
        await loadDashboardData();

        showToast("Supplier added successfully.");
    } catch (error) {
        showMessage("supplierFormMessage", error.message || "Unable to add supplier.");
    } finally {
        if (button) button.disabled = false;
    }
}

/* STOCK IN */

async function handleStockIn(event) {
    event.preventDefault();

    if (!isAdmin()) return;

    const sku = $("stockInProduct")?.value;
    const quantity = Number($("stockInQuantity")?.value);
    const supplierId = $("stockInSupplier")?.value;
    const notes = $("stockInNotes")?.value.trim() || "";

    if (!sku || !Number.isInteger(quantity) || quantity <= 0) {
        showMessage("stockInMessage", "Select a product and enter a valid quantity.");
        return;
    }

    if (!supplierId) {
        showMessage("stockInMessage", "Please select a supplier.");
        return;
    }

    try {
        await apiRequest("/stock-in", {
            method: "POST",
            body: JSON.stringify({
                sku,
                quantity,
                supplier_id: Number(supplierId),
                notes
            })
        });

        $("stockInForm")?.reset();
        clearMessage("stockInMessage");

        await loadDashboardData();

        showToast("Stock added successfully.");
    } catch (error) {
        showMessage("stockInMessage", error.message || "Unable to record stock in.");
    }
}

/* STOCK OUT */

async function handleStockOut(event) {
    event.preventDefault();

    if (!isAdmin()) return;

    const sku = $("stockOutProduct")?.value;
    const quantity = Number($("stockOutQuantity")?.value);
    const notes = $("stockOutNotes")?.value.trim() || "";

    if (!sku || !Number.isInteger(quantity) || quantity <= 0) {
        showMessage("stockOutMessage", "Select a product and enter a valid quantity.");
        return;
    }

    try {
        await apiRequest("/stock-out", {
            method: "POST",
            body: JSON.stringify({ sku, quantity, notes })
        });

        $("stockOutForm")?.reset();
        clearMessage("stockOutMessage");

        await loadDashboardData();

        showToast("Stock removed successfully.");
    } catch (error) {
        showMessage("stockOutMessage", error.message || "Unable to record stock out.");
    }
}

/* TRANSACTIONS */

function renderTransactions() {
    const table = $("transactionsTable");
    if (!table) return;

    const rows = state.transactions.slice().reverse();

    table.innerHTML = rows.length
        ? rows.map((transaction) => {
            const type = getTransactionType(transaction);
            const stockIn = type === "STOCK_IN";

            return `
                <tr>
                    <td>${escapeHTML(getTransactionDate(transaction))}</td>
                    <td>${escapeHTML(transaction.sku || "—")}</td>
                    <td>${escapeHTML(transaction.product_name || transaction.name || "—")}</td>
                    <td>
                        <span class="stock-status ${stockIn ? "" : "low"}">
                            ${escapeHTML(type || "—")}
                        </span>
                    </td>
                    <td>${number(transaction.quantity)}</td>
                    <td>${escapeHTML(transaction.supplier_name || "—")}</td>
                    <td>${escapeHTML(transaction.notes || "—")}</td>
                </tr>
            `;
        }).join("")
        : `<tr><td colspan="7">No transactions found.</td></tr>`;

    const overviewTable = $("overviewTransactionsTable");

    if (overviewTable) {
        overviewTable.innerHTML = rows.slice(0, 5).length
            ? rows.slice(0, 5).map((transaction) => `
                <tr>
                    <td>${escapeHTML(transaction.product_name || transaction.name || transaction.sku || "—")}</td>
                    <td>${escapeHTML(getTransactionType(transaction))}</td>
                    <td>${number(transaction.quantity)}</td>
                    <td>${escapeHTML(getTransactionDate(transaction))}</td>
                </tr>
            `).join("")
            : `<tr><td colspan="4">No recent transactions.</td></tr>`;
    }
}

async function downloadTransactions() {
    try {
        const response = await fetch("/transactions/download", {
            credentials: "include"
        });

        if (!response.ok) {
            throw new Error("Unable to download transactions.");
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");

        link.href = url;
        link.download = "stock_transactions.csv";

        document.body.appendChild(link);
        link.click();
        link.remove();

        URL.revokeObjectURL(url);
    } catch (error) {
        showToast(error.message || "Download failed.", "error");
    }
}

/* LOW STOCK */

function renderLowStock() {
    const lowProducts = state.products.filter(isLowStock);

    const table = $("lowStockTable");

    if (table) {
        table.innerHTML = lowProducts.length
            ? lowProducts.map((product) => `
                <tr>
                    <td>${escapeHTML(product.sku)}</td>
                    <td>${escapeHTML(getProductName(product))}</td>
                    <td>${number(getStock(product))}</td>
                    <td>${number(product.reorder_level)}</td>
                    <td><span class="stock-status low">Low Stock</span></td>
                </tr>
            `).join("")
            : `<tr><td colspan="5">No low-stock products. Everything looks good!</td></tr>`;
    }

    const overview = $("overviewLowStockList");

    if (overview) {
        overview.innerHTML = lowProducts.length
            ? lowProducts.slice(0, 5).map((product) => `
                <div class="low-stock-item">
                    <div>
                        <strong>${escapeHTML(getProductName(product))}</strong>
                        <small>${escapeHTML(product.sku)}</small>
                    </div>
                    <span>${number(getStock(product))} left</span>
                </div>
            `).join("")
            : `<p>No low-stock products.</p>`;
    }
}

/* MOVEMENT CHART */

function renderMovementChart() {
    const canvas = $("movementChart");

    if (!canvas || typeof Chart === "undefined") return;

    const daily = {};

    state.transactions.forEach((transaction) => {
        const date = getTransactionDate(transaction);
        if (date === "—") return;

        if (!daily[date]) {
            daily[date] = { stockIn: 0, stockOut: 0 };
        }

        const type = getTransactionType(transaction);
        const quantity = Number(transaction.quantity) || 0;

        if (type === "STOCK_IN") {
            daily[date].stockIn += quantity;
        } else if (type === "STOCK_OUT") {
            daily[date].stockOut += quantity;
        }
    });

    const labels = Object.keys(daily).slice(-7);

    if (state.chart) {
        state.chart.destroy();
    }

    state.chart = new Chart(canvas, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: "Stock In",
                    data: labels.map((date) => daily[date].stockIn),
                    backgroundColor: "#78967d",
                    borderRadius: 5
                },
                {
                    label: "Stock Out",
                    data: labels.map((date) => daily[date].stockOut),
                    backgroundColor: "#c8d6c4",
                    borderRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        usePointStyle: true,
                        boxWidth: 7,
                        font: { size: 10 }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 10 } }
                },
                y: {
                    beginAtZero: true,
                    ticks: { precision: 0, font: { size: 10 } }
                }
            }
        }
    });
}

/* ANALYSIS CHART IMAGES */

function loadAnalysisImages() {
    document.querySelectorAll(".analysis-chart[data-src]").forEach((image) => {
        const source = image.dataset.src;

        if (source) {
            image.src = `${source}?t=${Date.now()}`;
        }
    });
}

async function refreshCharts() {
    if (!isAdmin()) return;

    const button = $("refreshChartsBtn");
    if (button) button.disabled = true;

    try {
        await apiRequest("/refresh-charts", { method: "POST" });

        loadAnalysisImages();

        showToast("Analysis charts refreshed.");
    } catch (error) {
        showToast(error.message || "Unable to refresh charts.", "error");
    } finally {
        if (button) button.disabled = false;
    }
}


/* USER MANAGEMENT */

async function loadUserManagement() {
    if (!isAdmin()) return;

    const pendingTable = $("pendingUsersTable");
    const approvedTable = $("approvedUsersTable");

    if (pendingTable) {
        pendingTable.innerHTML = `<tr><td colspan="4">Loading requests...</td></tr>`;
    }

    if (approvedTable) {
        approvedTable.innerHTML = `<tr><td colspan="4">Loading approved users...</td></tr>`;
    }

    await Promise.all([
        loadPendingUsers(),
        loadApprovedUsers()
    ]);
}

async function loadPendingUsers() {
    if (!isAdmin()) return;

    try {
        const data = await apiRequest("/admin/pending-users");

        state.pendingUsers = getArray(data, "users");

        renderPendingUsers();
    } catch (error) {
        console.error("Pending users:", error);

        if ($("pendingUsersTable")) {
            $("pendingUsersTable").innerHTML =
                `<tr><td colspan="4">Unable to load pending requests.</td></tr>`;
        }

        showToast(error.message || "Unable to load pending users.", "error");
    }
}

async function loadApprovedUsers() {
    if (!isAdmin()) return;

    try {
        const data = await apiRequest("/admin/approved-users");

        state.approvedUsers = getArray(data, "users");

        renderApprovedUsers();
    } catch (error) {
        console.error("Approved users:", error);

        if ($("approvedUsersTable")) {
            $("approvedUsersTable").innerHTML =
                `<tr><td colspan="4">Unable to load approved users.</td></tr>`;
        }

        showToast(error.message || "Unable to load approved users.", "error");
    }
}

function renderPendingUsers() {
    const table = $("pendingUsersTable");

    if (!table) return;

    if ($("pendingCount")) {
        $("pendingCount").textContent =
            `${state.pendingUsers.length} Pending`;
    }

    if (!state.pendingUsers.length) {
        table.innerHTML = `
            <tr>
                <td colspan="4">No pending requests.</td>
            </tr>
        `;
        return;
    }

    table.innerHTML = state.pendingUsers.map(user => `
        <tr>
            <td>${escapeHTML(user.full_name)}</td>
            <td>${escapeHTML(user.username)}</td>
            <td>${escapeHTML(user.email)}</td>
            <td>
                <button
                    type="button"
                    class="approve-user-btn"
                    data-id="${escapeHTML(user.user_id)}">
                    Approve
                </button>

                <button
                    type="button"
                    class="reject-user-btn"
                    data-id="${escapeHTML(user.user_id)}">
                    Reject
                </button>
            </td>
        </tr>
    `).join("");
}

function renderApprovedUsers() {
    const table = $("approvedUsersTable");

    if (!table) return;

    if ($("approvedCount")) {
        $("approvedCount").textContent =
            `${state.approvedUsers.length} Approved`;
    }

    if (!state.approvedUsers.length) {
        table.innerHTML = `
            <tr>
                <td colspan="4">No approved staff members yet.</td>
            </tr>
        `;
        return;
    }

    table.innerHTML = state.approvedUsers.map(user => `
        <tr>
            <td>${escapeHTML(user.full_name)}</td>
            <td>${escapeHTML(user.username)}</td>
            <td>${escapeHTML(user.email)}</td>
            <td>
                <span class="stock-status">Approved</span>
            </td>
        </tr>
    `).join("");
}

async function handlePendingUserClick(event) {
    const approveButton = event.target.closest(".approve-user-btn");
    const rejectButton = event.target.closest(".reject-user-btn");

    if (!approveButton && !rejectButton) return;

    if (!isAdmin()) return;

    const button = approveButton || rejectButton;
    const userId = button.dataset.id;

    const approvalStatus = approveButton ? "APPROVED" : "REJECTED";

    const action = approveButton ? "approve" : "reject";

    if (!userId) {
        showToast("Invalid user ID.", "error");
        return;
    }

    if (!confirm(`Are you sure you want to ${action} this account?`)) {
        return;
    }

    const row = button.closest("tr");

    if (row) {
        row.querySelectorAll("button").forEach(item => {
            item.disabled = true;
        });
    }

    try {
        const data = await apiRequest(
            `/admin/users/${encodeURIComponent(userId)}/approval`,
            {
                method: "PUT",
                body: JSON.stringify({
                    approval_status: approvalStatus
                })
            }
        );

        showToast(
            data.message ||
            (approveButton
                ? "Staff account approved successfully."
                : "Staff account rejected successfully.")
        );

        await loadUserManagement();

    } catch (error) {
        showToast(
            error.message || `Unable to ${action} this account.`,
            "error"
        );

        if (row) {
            row.querySelectorAll("button").forEach(item => {
                item.disabled = false;
            });
        }
    }
}

/* INITIALIZATION */

document.addEventListener("DOMContentLoaded", () => {
    bindAuthEvents();
    checkSession();
});
