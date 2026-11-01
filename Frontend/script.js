
const API_BASE = "";

const state = {
    user: null,
    products: [],
    suppliers: [],
    transactions: [],
    lowStock: [],
    pendingUsers: [],
    chart: null,
    currentPage: "overview",
    editingProduct: false
};

const $ = id => document.getElementById(id);

const money = value =>
    new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2
    }).format(Number(value) || 0);

const escapeHTML = value =>
    String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[char]);

async function api(path, options = {}) {
    const response = await fetch(API_BASE + path, {
        ...options,
        credentials: "include",
        headers: {
            ...(options.body instanceof FormData ? {} : {
                "Content-Type": "application/json"
            }),
            ...options.headers
        }
    });

    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
        ? await response.json()
        : await response.text();

    if (!response.ok) {
        throw new Error(data.message || data.error || data || "Request failed");
    }

    return data;
}

function isAdmin() {
    return state.user?.user_role === "ADMIN";
}

function showToast(message, isError = false) {
    const container = $("toastContainer");
    if (!container) {
        alert(message);
        return;
    }

    const toast = document.createElement("div");
    toast.className = `toast ${isError ? "error" : "success"}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => toast.remove(), 3500);
}

function showMessage(id, message, isError = false) {
    const element = $(id);
    if (!element) return;

    element.textContent = message;
    element.classList.toggle("error", isError);
    element.classList.toggle("success", !isError);
}

function showPage(page) {
    state.currentPage = page;

    document.querySelectorAll(".page-section").forEach(section => {
        section.classList.toggle("active", section.id === page);
        section.classList.toggle("hidden", section.id !== page);
    });

    document.querySelectorAll(".nav-link").forEach(link => {
        link.classList.toggle("active", link.dataset.page === page);
    });

    const titles = {
        overview: "Overview",
        products: "Products",
        "stock-in": "Stock In",
        "stock-out": "Stock Out",
        transactions: "Transactions",
        "low-stock": "Low Stock",
        analysis: "Stock Analysis",
        users: "User Management",
        suppliers: "Suppliers"
    };

    if ($("pageTitle")) {
        $("pageTitle").textContent = titles[page] || "Overview";
    }

    if (page === "users" && isAdmin()) loadPendingUsers();
    if (page === "analysis") loadAnalysisImages();
}

function applyRolePermissions() {
    const admin = isAdmin();

    document.querySelectorAll("[data-admin-only]").forEach(element => {
        element.classList.toggle("hidden", !admin);
    });

    document.querySelectorAll("[data-staff-only]").forEach(element => {
        element.classList.toggle("hidden", admin);
    });

    const roleLabel = $("userRole");
    if (roleLabel) {
        roleLabel.textContent = admin ? "Administrator" : "Staff";
    }

    const nameLabel = $("userName");
    if (nameLabel) {
        nameLabel.textContent = state.user?.full_name || state.user?.username || "";
    }

    document.querySelectorAll(".nav-link").forEach(link => {
        if (link.dataset.adminOnly === "true") {
            link.classList.toggle("hidden", !admin);
        }
    });

    if (!admin && ["stock-in", "stock-out", "users"].includes(state.currentPage)) {
        showPage("overview");
    }
}

function showAuthPage(page) {
    ["landingPage", "loginPage", "signupPage", "appLayout"].forEach(id => {
        const element = $(id);
        if (element) element.classList.add("hidden");
    });

    const selected = $(page);
    if (selected) selected.classList.remove("hidden");
}

async function checkSession() {
    try {
        const data = await api("/me");
        state.user = data.user || data;

        if (!state.user || !state.user.user_id) {
            showAuthPage("landingPage");
            return;
        }

        await enterDashboard();
    } catch {
        state.user = null;
        showAuthPage("landingPage");
    }
}

async function enterDashboard() {
    showAuthPage("appLayout");
    applyRolePermissions();
    bindDashboardEvents();

    if ($("todayDate")) {
        $("todayDate").textContent = new Date().toLocaleDateString("en-IN", {
            weekday: "long",
            day: "numeric",
            month: "long",
            year: "numeric"
        });
    }

    await loadDashboard();
}

async function login(event) {
    event?.preventDefault();

    const identifier = $("loginIdentifier")?.value.trim();
    const password = $("loginPassword")?.value;

    if (!identifier || !password) {
        showMessage("loginMessage", "Enter your username/email and password.", true);
        return;
    }

    try {
        const data = await api("/login", {
            method: "POST",
            body: JSON.stringify({
                identifier,
                password
            })
        });

        if (data.status === "PENDING") {
            showMessage("loginMessage", "Your account is waiting for admin approval.", true);
            return;
        }

        if (data.status === "REJECTED") {
            showMessage("loginMessage", "Your account request was rejected.", true);
            return;
        }

        if (data.status !== "SUCCESS" && !data.user) {
            showMessage("loginMessage", data.message || "Invalid login details.", true);
            return;
        }

        state.user = data.user;
        await enterDashboard();
    } catch (error) {
        showMessage("loginMessage", error.message, true);
    }
}

async function signup(event) {
    event?.preventDefault();

    const fullName = $("signupFullName")?.value.trim();
    const username = $("signupUsername")?.value.trim();
    const email = $("signupEmail")?.value.trim();
    const password = $("signupPassword")?.value;
    const confirmPassword = $("signupConfirmPassword")?.value;

    if (!fullName || !username || !email || !password || !confirmPassword) {
        showMessage("signupMessage", "Please fill in all fields.", true);
        return;
    }

    if (password !== confirmPassword) {
        showMessage("signupMessage", "Passwords do not match.", true);
        return;
    }

    try {
        const data = await api("/signup", {
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
            data.message || "Account created. Wait for administrator approval."
        );

        $("signupForm")?.reset();
    } catch (error) {
        showMessage("signupMessage", error.message, true);
    }
}

async function logout() {
    try {
        await api("/logout", { method: "POST" });
    } catch (error) {
        console.error(error);
    }

    state.user = null;
    state.products = [];
    state.suppliers = [];
    state.transactions = [];
    state.lowStock = [];

    showAuthPage("landingPage");
}

async function loadDashboard() {
    try {
        const results = await Promise.all([
            api("/products"),
            api("/suppliers"),
            api("/transactions"),
            api("/low-stock")
        ]);

        state.products = Array.isArray(results[0])
            ? results[0]
            : results[0].products || [];

        state.suppliers = Array.isArray(results[1])
            ? results[1]
            : results[1].suppliers || [];

        state.transactions = Array.isArray(results[2])
            ? results[2]
            : results[2].transactions || [];

        state.lowStock = Array.isArray(results[3])
            ? results[3]
            : results[3].low_stock_products || [];

        renderDashboard();
        renderProducts();
        renderSuppliers();
        renderTransactions();
        renderLowStock();
        renderStockProductOptions();
        renderMovementChart();
    } catch (error) {
        showToast(error.message, true);
    }
}

function getStock(product) {
    return Number(
        product.current_stock ??
        product.stock ??
        product.opening_stock ??
        0
    );
}

function getProductValue(product) {
    return getStock(product) * Number(product.unit_cost || 0);
}

function renderDashboard() {
    const totalUnits = state.products.reduce(
        (sum, product) => sum + getStock(product), 0
    );

    const totalValue = state.products.reduce(
        (sum, product) => sum + getProductValue(product), 0
    );

    if ($("totalProducts")) $("totalProducts").textContent = state.products.length;
    if ($("totalUnits")) $("totalUnits").textContent = totalUnits.toLocaleString("en-IN");
    if ($("inventoryValue")) $("inventoryValue").textContent = money(totalValue);
    if ($("lowStockCount")) $("lowStockCount").textContent = state.lowStock.length;

    const recent = [...state.transactions].reverse().slice(0, 5);
    const table = $("overviewTransactionsTable");

    if (table) {
        table.innerHTML = recent.length
            ? recent.map(transaction => transactionRow(transaction)).join("")
            : `<tr><td colspan="6">No transactions available.</td></tr>`;
    }

    const lowList = $("overviewLowStockList");

    if (lowList) {
        lowList.innerHTML = state.lowStock.length
            ? state.lowStock.slice(0, 5).map(product => `
                <div class="low-stock-item">
                    <div>
                        <strong>${escapeHTML(product.product_name)}</strong>
                        <small>${escapeHTML(product.sku)}</small>
                    </div>
                    <span>${getStock(product)} left</span>
                </div>
            `).join("")
            : `<p>No low-stock products.</p>`;
    }
}

function renderProducts() {
    const table = $("productsTable");
    if (!table) return;

    const search = $("productSearch")?.value.toLowerCase() || "";

    const products = state.products.filter(product =>
        `${product.product_name} ${product.sku} ${product.category || ""}`
            .toLowerCase().includes(search)
    );

    if ($("productCount")) {
        $("productCount").textContent = products.length;
    }

    table.innerHTML = products.length
        ? products.map(product => `
            <tr>
                <td>${escapeHTML(product.sku)}</td>
                <td>${escapeHTML(product.product_name)}</td>
                <td>${escapeHTML(product.category || "-")}</td>
                <td>${getStock(product)}</td>
                <td>${product.reorder_level ?? 0}</td>
                <td>${money(product.unit_cost)}</td>
                <td>
                    ${isAdmin() ? `
                        <button class="table-action" data-edit-product="${product.product_id}">Edit</button>
                        <button class="table-action danger" data-delete-product="${product.product_id}">Delete</button>
                    ` : `<span class="read-only-label">View only</span>`}
                </td>
            </tr>
        `).join("")
        : `<tr><td colspan="7">No products found.</td></tr>`;
}

function renderSuppliers() {
    const select = $("stockInSupplier");

    if (select) {
        select.innerHTML = `<option value="">Select supplier (optional)</option>` +
            state.suppliers.map(supplier => `
                <option value="${supplier.supplier_id}">
                    ${escapeHTML(supplier.supplier_name)}
                </option>
            `).join("");
    }

    const table = $("suppliersTable");

    if (table) {
        table.innerHTML = state.suppliers.length
            ? state.suppliers.map(supplier => `
                <tr>
                    <td>${escapeHTML(supplier.supplier_name)}</td>
                    <td>${escapeHTML(supplier.phone_number || "-")}</td>
                    <td>${escapeHTML(supplier.email || "-")}</td>
                </tr>
            `).join("")
            : `<tr><td colspan="3">No suppliers available.</td></tr>`;
    }
}

function transactionRow(transaction) {
    const type = String(transaction.transaction_type || "").toUpperCase();

    return `
        <tr>
            <td>${escapeHTML(transaction.transaction_date || transaction.created_at || "-")}</td>
            <td>${escapeHTML(transaction.product_name || transaction.sku || "-")}</td>
            <td><span class="status-pill ${type === "STOCK_IN" ? "positive" : "negative"}">${escapeHTML(type.replace("_", " "))}</span></td>
            <td>${Number(transaction.quantity || 0)}</td>
            <td>${escapeHTML(transaction.supplier_name || "-")}</td>
            <td>${escapeHTML(transaction.notes || "-")}</td>
        </tr>
    `;
}

function renderTransactions() {
    const table = $("transactionsTable");
    if (!table) return;

    table.innerHTML = state.transactions.length
        ? [...state.transactions].reverse().map(transactionRow).join("")
        : `<tr><td colspan="6">No transactions available.</td></tr>`;
}

function renderLowStock() {
    const table = $("lowStockTable");
    if (!table) return;

    table.innerHTML = state.lowStock.length
        ? state.lowStock.map(product => `
            <tr>
                <td>${escapeHTML(product.sku)}</td>
                <td>${escapeHTML(product.product_name)}</td>
                <td>${getStock(product)}</td>
                <td>${product.reorder_level ?? 0}</td>
                <td><span class="status-pill negative">Low stock</span></td>
            </tr>
        `).join("")
        : `<tr><td colspan="5">All products are sufficiently stocked.</td></tr>`;
}

function renderStockProductOptions() {
    ["stockInProduct", "stockOutProduct"].forEach(id => {
        const select = $(id);
        if (!select) return;

        select.innerHTML = `<option value="">Select product</option>` +
            state.products.map(product => `
                <option value="${escapeHTML(product.sku)}">
                    ${escapeHTML(product.product_name)} (${escapeHTML(product.sku)})
                </option>
            `).join("");
    });
}

function renderMovementChart() {
    const canvas = $("movementChart");
    if (!canvas || typeof Chart === "undefined") return;

    const labels = state.transactions.slice(-7).map(item =>
        item.transaction_date || item.created_at || ""
    );

    const stockIn = state.transactions.slice(-7).map(item =>
        String(item.transaction_type).toUpperCase() === "STOCK_IN"
            ? Number(item.quantity)
            : 0
    );

    const stockOut = state.transactions.slice(-7).map(item =>
        String(item.transaction_type).toUpperCase() === "STOCK_OUT"
            ? Number(item.quantity)
            : 0
    );

    if (state.chart) state.chart.destroy();

    state.chart = new Chart(canvas, {
        type: "bar",
        data: {
            labels,
            datasets: [
                { label: "Stock In", data: stockIn },
                { label: "Stock Out", data: stockOut }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "bottom" }
            }
        }
    });
}

function loadAnalysisImages() {
    document.querySelectorAll(".analysis-chart").forEach(image => {
        const original = image.dataset.src || image.getAttribute("src");
        if (original) {
            image.src = original + (original.includes("?") ? "&" : "?") + "t=" + Date.now();
        }
    });
}

function openProductModal(product = null) {
    if (!isAdmin()) return;

    $("productForm")?.reset();
    $("productModalTitle").textContent = product ? "Edit Product" : "Add Product";

    $("editProductId").value = product?.product_id || "";
    $("productSku").value = product?.sku || "";
    $("productName").value = product?.product_name || "";
    $("productCategory").value = product?.category || "";
    $("productOpeningStock").value = product?.opening_stock ?? "";
    $("productReorderLevel").value = product?.reorder_level ?? 10;
    $("productUnitCost").value = product?.unit_cost ?? "";

    $("productModal")?.classList.remove("hidden");
}

function closeProductModal() {
    $("productModal")?.classList.add("hidden");
}

async function saveProduct(event) {
    event.preventDefault();
    if (!isAdmin()) return;

    const id = $("editProductId").value;

    const product = {
        sku: $("productSku").value.trim(),
        product_name: $("productName").value.trim(),
        category: $("productCategory").value.trim(),
        opening_stock: Number($("productOpeningStock").value),
        reorder_level: Number($("productReorderLevel").value),
        unit_cost: Number($("productUnitCost").value)
    };

    try {
        await api(id ? `/products/${id}` : "/products", {
            method: id ? "PUT" : "POST",
            body: JSON.stringify(product)
        });

        closeProductModal();
        showToast(id ? "Product updated successfully." : "Product added successfully.");
        await loadDashboard();
    } catch (error) {
        showMessage("productFormMessage", error.message, true);
    }
}

async function deleteProduct(id) {
    if (!isAdmin() || !confirm("Are you sure you want to delete this product?")) return;

    try {
        await api(`/products/${id}`, { method: "DELETE" });
        showToast("Product deleted successfully.");
        await loadDashboard();
    } catch (error) {
        showToast(error.message, true);
    }
}

function openSupplierModal() {
    if (!isAdmin()) return;
    $("supplierForm")?.reset();
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

    try {
        await api("/suppliers", {
            method: "POST",
            body: JSON.stringify(supplier)
        });

        closeSupplierModal();
        showToast("Supplier added successfully.");
        const data = await api("/suppliers");
        state.suppliers = Array.isArray(data) ? data : data.suppliers || [];
        renderSuppliers();
    } catch (error) {
        showMessage("supplierFormMessage", error.message, true);
    }
}

async function submitStock(event, type) {
    event.preventDefault();
    if (!isAdmin()) return;

    const isIn = type === "stock-in";
    const product = $(isIn ? "stockInProduct" : "stockOutProduct").value;
    const quantity = Number($(isIn ? "stockInQuantity" : "stockOutQuantity").value);
    const notes = $(isIn ? "stockInNotes" : "stockOutNotes")?.value.trim() || "";

    if (!product || quantity <= 0) {
        showMessage(isIn ? "stockInMessage" : "stockOutMessage", "Select a product and enter a valid quantity.", true);
        return;
    }

    const payload = { sku: product, quantity, notes };

    if (isIn) {
        const supplierId = $("stockInSupplier")?.value;
        if (supplierId) payload.supplier_id = Number(supplierId);
    }

    try {
        await api(isIn ? "/stock-in" : "/stock-out", {
            method: "POST",
            body: JSON.stringify(payload)
        });

        $(isIn ? "stockInForm" : "stockOutForm")?.reset();
        showMessage(
            isIn ? "stockInMessage" : "stockOutMessage",
            isIn ? "Stock added successfully." : "Stock removed successfully."
        );

        await loadDashboard();
    } catch (error) {
        showMessage(isIn ? "stockInMessage" : "stockOutMessage", error.message, true);
    }
}

async function loadPendingUsers() {
    if (!isAdmin()) return;

    try {
        const data = await api("/admin/pending-users");
        state.pendingUsers = Array.isArray(data)
            ? data
            : data.users || data.pending_users || [];

        const table = $("pendingUsersTable");
        if (!table) return;

        table.innerHTML = state.pendingUsers.length
            ? state.pendingUsers.map(user => `
                <tr>
                    <td>${escapeHTML(user.full_name)}</td>
                    <td>${escapeHTML(user.username)}</td>
                    <td>${escapeHTML(user.email)}</td>
                    <td>
                        <button class="table-action" data-approve-user="${user.user_id}">Approve</button>
                        <button class="table-action danger" data-reject-user="${user.user_id}">Reject</button>
                    </td>
                </tr>
            `).join("")
            : `<tr><td colspan="4">No pending account requests.</td></tr>`;
    } catch (error) {
        showToast(error.message, true);
    }
}

async function updateUserApproval(id, status) {
    if (!isAdmin()) return;

    try {
        await api(`/admin/users/${id}/approval`, {
            method: "PUT",
            body: JSON.stringify({ approval_status: status })
        });

        showToast(`User ${status.toLowerCase()} successfully.`);
        await loadPendingUsers();
    } catch (error) {
        showToast(error.message, true);
    }
}

async function downloadTransactions() {
    try {
        const response = await fetch(API_BASE + "/transactions/download", {
            credentials: "include"
        });

        if (!response.ok) {
            throw new Error("Unable to download transactions.");
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");

        link.href = url;
        link.download = "inventory_transactions.csv";
        link.click();

        URL.revokeObjectURL(url);
    } catch (error) {
        showToast(error.message, true);
    }
}

async function refreshCharts() {
    if (!isAdmin()) return;

    try {
        await api("/refresh-charts", { method: "POST" });
        loadAnalysisImages();
        showToast("Charts refreshed successfully.");
    } catch (error) {
        showToast(error.message, true);
    }
}

function bindDashboardEvents() {
    document.querySelectorAll(".nav-link").forEach(link => {
        link.onclick = event => {
            event.preventDefault();
            showPage(link.dataset.page);
        };
    });

    $("headerAddProduct")?.addEventListener("click", () => openProductModal());
    $("addProductBtn")?.addEventListener("click", () => openProductModal());

    $("closeProductModal")?.addEventListener("click", closeProductModal);
    $("cancelProductModal")?.addEventListener("click", closeProductModal);
    $("productForm")?.addEventListener("submit", saveProduct);

    $("addSupplierBtn")?.addEventListener("click", openSupplierModal);
    $("closeSupplierModal")?.addEventListener("click", closeSupplierModal);
    $("cancelSupplierModal")?.addEventListener("click", closeSupplierModal);
    $("supplierForm")?.addEventListener("submit", saveSupplier);

    $("stockInForm")?.addEventListener("submit", event => submitStock(event, "stock-in"));
    $("stockOutForm")?.addEventListener("submit", event => submitStock(event, "stock-out"));

    $("productSearch")?.addEventListener("input", renderProducts);
    $("refreshDataBtn")?.addEventListener("click", loadDashboard);
    $("refreshChartsBtn")?.addEventListener("click", refreshCharts);

    $("downloadTransactionsBtn")?.addEventListener("click", downloadTransactions);
    $("exportTransactionsBtn")?.addEventListener("click", downloadTransactions);

    $("logoutBtn")?.addEventListener("click", logout);

    $("productsTable")?.addEventListener("click", event => {
        const editButton = event.target.closest("[data-edit-product]");
        const deleteButton = event.target.closest("[data-delete-product]");

        if (editButton && isAdmin()) {
            const product = state.products.find(item =>
                String(item.product_id) === editButton.dataset.editProduct
            );
            if (product) openProductModal(product);
        }

        if (deleteButton && isAdmin()) {
            deleteProduct(deleteButton.dataset.deleteProduct);
        }
    });

    $("pendingUsersTable")?.addEventListener("click", event => {
        const approve = event.target.closest("[data-approve-user]");
        const reject = event.target.closest("[data-reject-user]");

        if (approve) updateUserApproval(approve.dataset.approveUser, "APPROVED");
        if (reject) updateUserApproval(reject.dataset.rejectUser, "REJECTED");
    });
}

function bindAuthEvents() {
    $("loginForm")?.addEventListener("submit", login);
    $("signupForm")?.addEventListener("submit", signup);

    $("showLoginBtn")?.addEventListener("click", () => showAuthPage("loginPage"));
    $("showSignupBtn")?.addEventListener("click", () => showAuthPage("signupPage"));
    $("backToLanding")?.addEventListener("click", () => showAuthPage("landingPage"));
    $("backToLandingSignup")?.addEventListener("click", () => showAuthPage("landingPage"));

    $("landingLoginBtn")?.addEventListener("click", () => showAuthPage("loginPage"));
    $("landingSignupBtn")?.addEventListener("click", () => showAuthPage("signupPage"));
}

document.addEventListener("DOMContentLoaded", () => {
    bindAuthEvents();
    checkSession();
});
