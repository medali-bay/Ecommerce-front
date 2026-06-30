import { useEffect, useMemo, useState } from "react";
import api from "./api/axios";
import "./App.css";

const formatPrice = (value) => `${Number(value || 0).toFixed(2)} €`;

const getProductStatus = (product) => {
  const text =
    `${product.name || ""} ${product.description || ""}`.toLowerCase();

  if (text.includes("coming soon") || text.includes("soon")) {
    return { label: "Coming soon", className: "status-soon", canBuy: false };
  }

  if (product.stock <= 0) {
    return { label: "Out of stock", className: "status-out", canBuy: false };
  }

  if (product.stock <= 5) {
    return { label: "Limited", className: "status-limited", canBuy: true };
  }

  return { label: "Available", className: "status-available", canBuy: true };
};

const emptyProductForm = {
  name: "",
  description: "",
  price: "",
  stock: "",
  category: "",
};

const emptyManualOrderForm = {
  customerName: "",
  city: "",
  phoneNumber: "",
  product: "",
  quantity: 1,
  notes: "",
};

function App() {
  const [orderSearch, setOrderSearch] = useState("");
  const [orderStatusFilter, setOrderStatusFilter] = useState("");

  const [productImage, setProductImage] = useState(null);

  const [editingProductId, setEditingProductId] = useState(null);
  const [editProductForm, setEditProductForm] = useState(emptyProductForm);
  const [editProductImage, setEditProductImage] = useState(null);

  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [orders, setOrders] = useState([]);
  const [adminStats, setAdminStats] = useState(null);
  const [lowStock, setLowStock] = useState([]);

  const [cart, setCart] = useState([]);
  const [activeView, setActiveView] = useState("shop");

  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [ordering, setOrdering] = useState("");

  const [loading, setLoading] = useState(true);
  const [pageMessage, setPageMessage] = useState("");
  const [pageError, setPageError] = useState("");

  const [showCheckout, setShowCheckout] = useState(false);
  const [customerName, setCustomerName] = useState("");
  const [city, setCity] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [notes, setNotes] = useState("");
  const [useSavedPhone, setUseSavedPhone] = useState(false);
  const [orderSuccess, setOrderSuccess] = useState("");
  const [orderError, setOrderError] = useState("");

  const [showAuth, setShowAuth] = useState(false);
  const [authMode, setAuthMode] = useState("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [loggedInUser, setLoggedInUser] = useState(
    localStorage.getItem("username") || "",
  );
  const [isAdmin, setIsAdmin] = useState(
    localStorage.getItem("isAdmin") === "true",
  );
  const [authMessage, setAuthMessage] = useState("");
  const [authError, setAuthError] = useState("");

  const [adminProductForm, setAdminProductForm] = useState(emptyProductForm);
  const [categoryMode, setCategoryMode] = useState("existing");
  const [newCategoryName, setNewCategoryName] = useState("");

  const [manualOrderForm, setManualOrderForm] = useState(emptyManualOrderForm);
  const [stockAdjustments, setStockAdjustments] = useState({});

  const cartItemsCount = useMemo(
    () => cart.reduce((total, item) => total + item.quantity, 0),
    [cart],
  );

  const cartTotal = useMemo(
    () => cart.reduce((total, item) => total + item.price * item.quantity, 0),
    [cart],
  );

  const visibleStats = useMemo(() => {
    const available = products.filter((product) => product.stock > 5).length;
    const limited = products.filter(
      (product) => product.stock > 0 && product.stock <= 5,
    ).length;

    return {
      products: products.length,
      available,
      limited,
      categories: categories.length,
    };
  }, [products, categories]);

  const filteredOrders = useMemo(() => {
    return orders.filter((order) => {
      const customer = (
        order.customer_name ||
        order.username ||
        "Guest customer"
      ).toLowerCase();

      const phone = (order.phone_number || "").toLowerCase();
      const cityValue = (order.city || "").toLowerCase();
      const searchValue = orderSearch.toLowerCase();

      const matchesSearch =
        customer.includes(searchValue) ||
        phone.includes(searchValue) ||
        cityValue.includes(searchValue) ||
        String(order.id).includes(searchValue);

      const matchesStatus =
        !orderStatusFilter || order.status === orderStatusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [orders, orderSearch, orderStatusFilter]);

  const loadProducts = async (overrideFilters = null) => {
    setLoading(true);
    setPageError("");

    const activeFilters = overrideFilters || {
      search,
      category,
      minPrice,
      maxPrice,
      ordering,
    };

    try {
      const response = await api.get("/products/", {
        params: {
          search: activeFilters.search || undefined,
          category: activeFilters.category || undefined,
          min_price: activeFilters.minPrice || undefined,
          max_price: activeFilters.maxPrice || undefined,
          ordering: activeFilters.ordering || undefined,
        },
      });

      setProducts(response.data.results || []);
    } catch {
      setPageError(
        "Products could not be loaded. Check that Django is running.",
      );
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const response = await api.get("/categories/");
      setCategories(response.data.results || []);
    } catch {
      setCategories([]);
    }
  };

  const loadOrders = async () => {
    if (!loggedInUser) return;

    try {
      const response = await api.get("/orders/");
      setOrders(response.data.results || []);
    } catch {
      setOrders([]);
    }
  };

  const loadAdminData = async () => {
    if (!isAdmin) return;

    try {
      const [statsResponse, lowStockResponse, ordersResponse] =
        await Promise.all([
          api.get("/dashboard/stats/"),
          api.get("/dashboard/low-stock/"),
          api.get("/orders/"),
        ]);

      setAdminStats(statsResponse.data);
      setLowStock(lowStockResponse.data || []);
      setOrders(ordersResponse.data.results || []);
    } catch {
      setPageError(
        "Admin data could not be loaded. Please login as admin again.",
      );
    }
  };

  const checkAdminAccess = async () => {
    try {
      await api.get("/dashboard/stats/");
      setIsAdmin(true);
      localStorage.setItem("isAdmin", "true");
    } catch {
      setIsAdmin(false);
      localStorage.removeItem("isAdmin");
    }
  };

  useEffect(() => {
    loadProducts();
    loadCategories();
  }, []);

  useEffect(() => {
    if (loggedInUser) {
      checkAdminAccess();
      loadOrders();
    }
  }, [loggedInUser]);

  useEffect(() => {
    if (activeView === "admin") loadAdminData();
    if (activeView === "orders") loadOrders();
  }, [activeView, isAdmin]);

  const handleFilterSubmit = (event) => {
    event.preventDefault();
    loadProducts();
  };

  const clearFilters = () => {
    setSearch("");
    setCategory("");
    setMinPrice("");
    setMaxPrice("");
    setOrdering("");

    loadProducts({
      search: "",
      category: "",
      minPrice: "",
      maxPrice: "",
      ordering: "",
    });
  };

  const addToCart = (product) => {
    if (isAdmin) {
      setActiveView("admin");
      setPageMessage(
        "Admin accounts use Manual order or Stock control from the admin dashboard.",
      );
      return;
    }

    const status = getProductStatus(product);
    if (!status.canBuy) return;

    setOrderSuccess("");
    setOrderError("");

    setCart((currentCart) => {
      const existingItem = currentCart.find((item) => item.id === product.id);

      if (existingItem) {
        if (existingItem.quantity >= product.stock) return currentCart;

        return currentCart.map((item) =>
          item.id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item,
        );
      }

      return [
        ...currentCart,
        {
          id: product.id,
          name: product.name,
          price: Number(product.price),
          stock: product.stock,
          image: product.image,
          quantity: 1,
        },
      ];
    });
  };

  const increaseQuantity = (productId) => {
    setCart((currentCart) =>
      currentCart.map((item) =>
        item.id === productId && item.quantity < item.stock
          ? { ...item, quantity: item.quantity + 1 }
          : item,
      ),
    );
  };

  const decreaseQuantity = (productId) => {
    setCart((currentCart) =>
      currentCart
        .map((item) =>
          item.id === productId
            ? { ...item, quantity: item.quantity - 1 }
            : item,
        )
        .filter((item) => item.quantity > 0),
    );
  };

  const removeFromCart = (productId) => {
    setCart((currentCart) =>
      currentCart.filter((item) => item.id !== productId),
    );
  };

  const clearCart = () => {
    setCart([]);
    setShowCheckout(false);
    setOrderSuccess("");
    setOrderError("");
  };

  const submitOrder = async (event) => {
    event.preventDefault();
    setOrderSuccess("");
    setOrderError("");

    if (cart.length === 0) {
      setOrderError("Your cart is empty.");
      return;
    }

    const orderData = {
      notes,
      order_items: cart.map((item) => ({
        product: item.id,
        quantity: item.quantity,
      })),
    };

    if (loggedInUser) {
      orderData.use_saved_phone = useSavedPhone;

      if (!useSavedPhone) {
        orderData.city = city;
        orderData.phone_number = phoneNumber;
      }
    } else {
      orderData.customer_name = customerName;
      orderData.city = city;
      orderData.phone_number = phoneNumber;
    }

    try {
      await api.post("/orders/", orderData);

      setOrderSuccess("Your order was created successfully.");
      setCart([]);
      setShowCheckout(false);
      setCustomerName("");
      setCity("");
      setPhoneNumber("");
      setNotes("");
      setUseSavedPhone(false);

      await loadProducts();
      await loadOrders();
    } catch (error) {
      const detail = error.response?.data;
      setOrderError(
        typeof detail === "string"
          ? detail
          : detail?.detail ||
              detail?.non_field_errors?.[0] ||
              "Order could not be created.",
      );
    }
  };

  const loginUser = async (event) => {
    event.preventDefault();
    setAuthError("");
    setAuthMessage("");

    try {
      const response = await api.post("/token/", { username, password });

      localStorage.setItem("accessToken", response.data.access);
      localStorage.setItem("refreshToken", response.data.refresh);
      localStorage.setItem("username", username);

      setLoggedInUser(username);
      setUsername("");
      setPassword("");
      setShowAuth(false);
      setAuthMessage("");
      await checkAdminAccess();
    } catch {
      setAuthError("Invalid username or password.");
    }
  };

  const registerUser = async (event) => {
    event.preventDefault();
    setAuthError("");
    setAuthMessage("");

    try {
      await api.post("/register/", {
        username,
        email,
        password,
        password_confirm: passwordConfirm,
      });

      setAuthMessage("Account created. Login to continue.");
      setAuthMode("login");
      setEmail("");
      setPassword("");
      setPasswordConfirm("");
    } catch (error) {
      const detail = error.response?.data;
      setAuthError(
        detail?.username?.[0] ||
          detail?.password?.[0] ||
          detail?.non_field_errors?.[0] ||
          "Account could not be created.",
      );
    }
  };

  const logoutUser = () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("username");
    localStorage.removeItem("isAdmin");

    setLoggedInUser("");
    setIsAdmin(false);
    setOrders([]);
    setActiveView("shop");
    setShowAuth(false);
  };

  const validateOrder = async (orderId) => {
    setPageError("");
    setPageMessage("");

    try {
      await api.post(`/orders/${orderId}/validate_order/`);
      setPageMessage("Order validated successfully.");
      await loadOrders();
      await loadAdminData();
    } catch {
      setPageError("Order could not be validated.");
    }
  };

  const deliverOrder = async (orderId) => {
    setPageError("");
    setPageMessage("");

    try {
      await api.post(`/orders/${orderId}/deliver_order/`);
      setPageMessage("Order delivered successfully.");
      await loadOrders();
      await loadAdminData();
    } catch {
      setPageError("Order could not be delivered. Validate it first.");
    }
  };

  const cancelOrder = async (orderId) => {
    const confirmed = window.confirm(
      "Cancel this order? Stock will be restored.",
    );

    if (!confirmed) return;

    setPageError("");
    setPageMessage("");

    try {
      await api.post(`/orders/${orderId}/cancel_order/`);
      setPageMessage("Order cancelled successfully.");
      await loadOrders();
      await loadProducts();
      await loadAdminData();
    } catch {
      setPageError("Order could not be cancelled.");
    }
  };

  const createCategory = async () => {
    if (!newCategoryName.trim()) {
      setPageError("Enter a new category name.");
      return null;
    }

    try {
      const response = await api.post("/categories/", {
        name: newCategoryName.trim(),
      });

      await loadCategories();

      setNewCategoryName("");
      setCategoryMode("existing");

      return response.data.id;
    } catch {
      setPageError("Category could not be created.");
      return null;
    }
  };

  const createProduct = async (event) => {
    event.preventDefault();
    setPageError("");
    setPageMessage("");

    try {
      let categoryId = adminProductForm.category;

      if (categoryMode === "new") {
        categoryId = await createCategory();

        if (!categoryId) return;
      }

      const formData = new FormData();

      formData.append("name", adminProductForm.name);
      formData.append("description", adminProductForm.description);
      formData.append("price", adminProductForm.price);
      formData.append("stock", Number(adminProductForm.stock));
      formData.append("category", Number(categoryId));

      if (productImage) {
        formData.append("image", productImage);
      }

      await api.post("/products/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setAdminProductForm(emptyProductForm);
      setCategoryMode("existing");
      setNewCategoryName("");
      setProductImage(null);
      setPageMessage("Product created successfully.");

      await loadProducts();
      await loadCategories();
      await loadAdminData();
    } catch {
      setPageError("Product could not be created.");
    }
  };

  const startEditProduct = (product) => {
    setEditingProductId(product.id);
    setEditProductForm({
      name: product.name || "",
      description: product.description || "",
      price: product.price || "",
      stock: product.stock || "",
      category: product.category || "",
    });
    setEditProductImage(null);
    setActiveView("admin");
  };

  const cancelEditProduct = () => {
    setEditingProductId(null);
    setEditProductForm(emptyProductForm);
    setEditProductImage(null);
  };

  const updateProduct = async (event) => {
    event.preventDefault();
    setPageError("");
    setPageMessage("");

    if (!editingProductId) return;

    try {
      const formData = new FormData();

      formData.append("name", editProductForm.name);
      formData.append("description", editProductForm.description);
      formData.append("price", editProductForm.price);
      formData.append("category", Number(editProductForm.category));

      if (editProductImage) {
        formData.append("image", editProductImage);
      }

      await api.patch(`/products/${editingProductId}/`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setEditingProductId(null);
      setEditProductForm(emptyProductForm);
      setEditProductImage(null);
      setPageMessage("Product updated successfully.");

      await loadProducts();
      await loadAdminData();
    } catch {
      setPageError(
        "Product could not be updated. Stock must be changed only from Stock control.",
      );
    }
  };

  const createManualOrder = async (event) => {
    event.preventDefault();
    setPageError("");
    setPageMessage("");

    if (!manualOrderForm.product || Number(manualOrderForm.quantity) < 1) {
      setPageError("Select a product and enter a valid quantity.");
      return;
    }

    try {
      await api.post("/orders/", {
        customer_name: manualOrderForm.customerName,
        city: manualOrderForm.city,
        phone_number: manualOrderForm.phoneNumber,
        notes: manualOrderForm.notes || "Manual order created by admin.",
        use_saved_phone: false,
        order_items: [
          {
            product: Number(manualOrderForm.product),
            quantity: Number(manualOrderForm.quantity),
          },
        ],
      });

      setManualOrderForm(emptyManualOrderForm);
      setPageMessage("Manual order created successfully.");

      await loadProducts();
      await loadOrders();
      await loadAdminData();
    } catch (error) {
      const detail = error.response?.data;
      setPageError(
        typeof detail === "string"
          ? detail
          : detail?.detail ||
              detail?.non_field_errors?.[0] ||
              "Manual order could not be created.",
      );
    }
  };

  const adjustStock = async (productId) => {
    const adjustment = stockAdjustments[productId] || {};
    const quantityChange = Number(adjustment.quantity || 0);

    if (!quantityChange) {
      setPageError("Enter a stock change first.");
      return;
    }

    try {
      await api.post(`/products/${productId}/adjust_stock/`, {
        quantity_change: quantityChange,
        note: adjustment.note || "Stock updated from admin dashboard.",
      });

      setStockAdjustments((current) => ({
        ...current,
        [productId]: { quantity: "", note: "" },
      }));

      setPageMessage("Stock updated successfully.");

      await loadProducts();
      await loadAdminData();
    } catch {
      setPageError("Stock could not be updated.");
    }
  };

  const renderProductCard = (product) => {
    const status = getProductStatus(product);

    return (
      <article className="product-card" key={product.id}>
        <div className="product-media">
          {product.image ? (
            <img src={product.image} alt={product.name} />
          ) : (
            <div className="product-placeholder">E</div>
          )}
          <span className={`status-badge ${status.className}`}>
            {status.label}
          </span>
        </div>

        <div className="product-body">
          <div className="product-meta-row">
            <span>{product.category_name || "Collection"}</span>
            <strong>{formatPrice(product.price)}</strong>
          </div>

          <h3>{product.name}</h3>
          <p>{product.description || "Designed for everyday performance."}</p>

          <button
            type="button"
            className="product-cta"
            disabled={!isAdmin && !status.canBuy}
            onClick={() =>
              isAdmin ? startEditProduct(product) : addToCart(product)
            }
          >
            {isAdmin
              ? "Manage product"
              : status.canBuy
                ? "Add to cart"
                : status.label}
          </button>
        </div>
      </article>
    );
  };

  return (
    <div className="app-shell">
      <header className="site-header">
        <button
          type="button"
          className="brand-mark"
          onClick={() => setActiveView("shop")}
        >
          <span>E</span>
          Ecommerce
        </button>

        <nav className="main-nav">
          <button
            type="button"
            className={activeView === "shop" ? "active" : ""}
            onClick={() => setActiveView("shop")}
          >
            Shop
          </button>

          {loggedInUser && (
            <button
              type="button"
              className={activeView === "orders" ? "active" : ""}
              onClick={() => setActiveView("orders")}
            >
              {isAdmin ? "Orders" : "My orders"}
            </button>
          )}

          {isAdmin && (
            <button
              type="button"
              className={activeView === "admin" ? "active" : ""}
              onClick={() => setActiveView("admin")}
            >
              Admin
            </button>
          )}
        </nav>

        <div className="header-actions">
          {!isAdmin && (
            <button
              type="button"
              className="cart-chip"
              onClick={() => setActiveView("shop")}
            >
              Cart · {cartItemsCount}
            </button>
          )}

          {loggedInUser ? (
            <>
              <span className="user-chip">
                {isAdmin ? "Admin" : "Hi"}, {loggedInUser}
              </span>
              <button
                type="button"
                className="outline-button"
                onClick={logoutUser}
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                className="outline-button"
                onClick={() => {
                  setAuthMode("login");
                  setShowAuth(true);
                }}
              >
                Login
              </button>
              <button
                type="button"
                className="solid-button"
                onClick={() => {
                  setAuthMode("register");
                  setShowAuth(true);
                }}
              >
                Register
              </button>
            </>
          )}
        </div>
      </header>

      {showAuth && (
        <section className="auth-card">
          <div>
            <p className="section-kicker">Account</p>
            <h2>
              {authMode === "login" ? "Welcome back" : "Create your account"}
            </h2>
          </div>

          <form
            className="auth-form"
            onSubmit={authMode === "login" ? loginUser : registerUser}
          >
            {authError && <p className="alert error">{authError}</p>}
            {authMessage && <p className="alert success">{authMessage}</p>}

            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />

            {authMode === "register" && (
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            )}

            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />

            {authMode === "register" && (
              <input
                type="password"
                placeholder="Confirm password"
                value={passwordConfirm}
                onChange={(event) => setPasswordConfirm(event.target.value)}
                required
              />
            )}

            <div className="auth-actions">
              <button type="submit" className="solid-button full">
                {authMode === "login" ? "Login" : "Create account"}
              </button>
              <button
                type="button"
                className="text-button"
                onClick={() => setShowAuth(false)}
              >
                Close
              </button>
            </div>
          </form>

          <button
            type="button"
            className="switch-auth"
            onClick={() => {
              setAuthError("");
              setAuthMessage("");
              setAuthMode(authMode === "login" ? "register" : "login");
            }}
          >
            {authMode === "login"
              ? "Need an account? Register"
              : "Already registered? Login"}
          </button>
        </section>
      )}

      {pageMessage && <p className="global-message success">{pageMessage}</p>}
      {pageError && <p className="global-message error">{pageError}</p>}

      {activeView === "shop" && (
        <>
          <section className="hero-section">
            <div className="hero-copy">
              <p className="section-kicker">Blue drop collection</p>
              <h1>Clean essentials. Fast checkout. Built to convert.</h1>
              <p>
                A premium storefront inspired by global performance brands:
                focused, fast, and easy to shop.
              </p>
              <div className="hero-cta-row">
                <a href="#products" className="solid-link">
                  Shop products
                </a>
                <button
                  type="button"
                  className="outline-button dark"
                  onClick={clearFilters}
                >
                  Reset filters
                </button>
              </div>
            </div>

            <div className="hero-panel">
              <span>Cart total</span>
              <strong>{formatPrice(cartTotal)}</strong>
              <p>
                {cartItemsCount} selected item{cartItemsCount === 1 ? "" : "s"}
              </p>
            </div>
          </section>

          <section className="store-stats">
            <div>
              <span>Products</span>
              <strong>{visibleStats.products}</strong>
            </div>
            <div>
              <span>Available</span>
              <strong>{visibleStats.available}</strong>
            </div>
            <div>
              <span>Limited</span>
              <strong>{visibleStats.limited}</strong>
            </div>
            <div>
              <span>Categories</span>
              <strong>{visibleStats.categories}</strong>
            </div>
          </section>

          <main
            className={
              isAdmin ? "shop-layout admin-shop-layout" : "shop-layout"
            }
            id="products"
          >
            <section className="catalog-area">
              <div className="section-title">
                <div>
                  <p className="section-kicker">Catalog</p>
                  <h2>Products</h2>
                </div>
                <p>
                  Stock numbers stay private. Customers only see clear
                  availability labels.
                </p>
              </div>

              <form className="filter-bar" onSubmit={handleFilterSubmit}>
                <input
                  type="text"
                  placeholder="Search products"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />

                <select
                  value={category}
                  onChange={(event) => setCategory(event.target.value)}
                >
                  <option value="">All categories</option>
                  {categories.map((categoryItem) => (
                    <option key={categoryItem.id} value={categoryItem.id}>
                      {categoryItem.name}
                    </option>
                  ))}
                </select>

                <input
                  type="number"
                  placeholder="Min price"
                  value={minPrice}
                  onChange={(event) => setMinPrice(event.target.value)}
                />

                <input
                  type="number"
                  placeholder="Max price"
                  value={maxPrice}
                  onChange={(event) => setMaxPrice(event.target.value)}
                />

                <select
                  value={ordering}
                  onChange={(event) => setOrdering(event.target.value)}
                >
                  <option value="">Featured</option>
                  <option value="price">Price low to high</option>
                  <option value="-price">Price high to low</option>
                  <option value="name">Name A to Z</option>
                  <option value="-name">Name Z to A</option>
                </select>

                <button type="submit" className="solid-button">
                  Apply
                </button>
                <button
                  type="button"
                  className="ghost-light"
                  onClick={clearFilters}
                >
                  Clear
                </button>
              </form>

              {loading ? (
                <div className="state-card">Loading products...</div>
              ) : pageError ? (
                <div className="state-card error">{pageError}</div>
              ) : products.length === 0 ? (
                <div className="state-card">No products found.</div>
              ) : (
                <div className="product-grid">
                  {products.map(renderProductCard)}
                </div>
              )}
            </section>

            {!isAdmin && (
              <aside className="cart-card">
                <div className="cart-title">
                  <div>
                    <p className="section-kicker">Checkout</p>
                    <h2>Cart</h2>
                  </div>
                  {cart.length > 0 && !orderSuccess && (
                    <button
                      type="button"
                      className="text-button danger"
                      onClick={clearCart}
                    >
                      Clear
                    </button>
                  )}
                </div>

                {orderSuccess ? (
                  <div className="confirmation-card">
                    <span>✓</span>
                    <h3>Order confirmed</h3>
                    <p>{orderSuccess}</p>
                    <button
                      type="button"
                      className="solid-button full"
                      onClick={() => setOrderSuccess("")}
                    >
                      Continue shopping
                    </button>
                  </div>
                ) : cart.length === 0 ? (
                  <div className="empty-cart-card">
                    <strong>Your cart is empty</strong>
                    <p>Add a product to start checkout.</p>
                  </div>
                ) : (
                  <>
                    <div className="cart-items">
                      {cart.map((item) => (
                        <div className="cart-item" key={item.id}>
                          <div className="mini-image">
                            {item.image ? (
                              <img src={item.image} alt={item.name} />
                            ) : (
                              <span>E</span>
                            )}
                          </div>
                          <div>
                            <h4>{item.name}</h4>
                            <p>{formatPrice(item.price)}</p>
                            <div className="quantity-row">
                              <button
                                type="button"
                                onClick={() => decreaseQuantity(item.id)}
                              >
                                -
                              </button>
                              <span>{item.quantity}</span>
                              <button
                                type="button"
                                onClick={() => increaseQuantity(item.id)}
                                disabled={item.quantity >= item.stock}
                              >
                                +
                              </button>
                            </div>
                          </div>
                          <button
                            type="button"
                            className="remove-item"
                            onClick={() => removeFromCart(item.id)}
                          >
                            ×
                          </button>
                        </div>
                      ))}
                    </div>

                    <div className="cart-summary">
                      <div>
                        <span>Items</span>
                        <strong>{cartItemsCount}</strong>
                      </div>
                      <div>
                        <span>Total</span>
                        <strong>{formatPrice(cartTotal)}</strong>
                      </div>
                      {!showCheckout && (
                        <button
                          type="button"
                          className="solid-button full"
                          onClick={() => {
                            setOrderError("");
                            setShowCheckout(true);
                          }}
                        >
                          Checkout
                        </button>
                      )}
                    </div>

                    {showCheckout && (
                      <form className="checkout-form" onSubmit={submitOrder}>
                        <h3>Delivery details</h3>
                        {orderError && (
                          <p className="alert error">{orderError}</p>
                        )}

                        {loggedInUser && (
                          <label className="check-row">
                            <input
                              type="checkbox"
                              checked={useSavedPhone}
                              onChange={(event) =>
                                setUseSavedPhone(event.target.checked)
                              }
                            />
                            Use saved phone and city
                          </label>
                        )}

                        {!loggedInUser && (
                          <input
                            type="text"
                            placeholder="Full name"
                            value={customerName}
                            onChange={(event) =>
                              setCustomerName(event.target.value)
                            }
                            required
                          />
                        )}

                        {!useSavedPhone && (
                          <>
                            <input
                              type="text"
                              placeholder="City"
                              value={city}
                              onChange={(event) => setCity(event.target.value)}
                              required
                            />
                            <input
                              type="text"
                              placeholder="Phone number"
                              value={phoneNumber}
                              onChange={(event) =>
                                setPhoneNumber(event.target.value)
                              }
                              required
                            />
                          </>
                        )}

                        <textarea
                          placeholder="Notes"
                          value={notes}
                          onChange={(event) => setNotes(event.target.value)}
                        />

                        <div className="checkout-actions">
                          <button type="submit" className="solid-button full">
                            Submit order
                          </button>
                          <button
                            type="button"
                            className="ghost-light"
                            onClick={() => setShowCheckout(false)}
                          >
                            Cancel
                          </button>
                        </div>
                      </form>
                    )}
                  </>
                )}
              </aside>
            )}
          </main>
        </>
      )}

      {activeView === "orders" && (
        <main className="panel-page">
          <div className="section-title">
            <div>
              <p className="section-kicker">
                {isAdmin ? "Order management" : "Customer area"}
              </p>
              <h2>{isAdmin ? "Orders" : "My orders"}</h2>
            </div>
            <button
              type="button"
              className="outline-button dark"
              onClick={loadOrders}
            >
              Refresh
            </button>
          </div>

          <div className="order-filter-bar">
            <input
              type="text"
              placeholder="Search by order ID, customer, phone, or city"
              value={orderSearch}
              onChange={(event) => setOrderSearch(event.target.value)}
            />

            <select
              value={orderStatusFilter}
              onChange={(event) => setOrderStatusFilter(event.target.value)}
            >
              <option value="">All statuses</option>
              <option value="pending">Pending</option>
              <option value="validated">Validated</option>
              <option value="delivered">Delivered</option>
              <option value="cancelled">Cancelled</option>
            </select>

            <button
              type="button"
              className="ghost-light"
              onClick={() => {
                setOrderSearch("");
                setOrderStatusFilter("");
              }}
            >
              Clear
            </button>
          </div>

          {filteredOrders.length === 0 ? (
            <div className="state-card">No orders found.</div>
          ) : (
            <div className="table-card">
              <table>
                <thead>
                  <tr>
                    <th>Order</th>
                    <th>Phone</th>
                    <th>City</th>
                    <th>Total</th>
                    <th>Status</th>
                    <th>Date</th>
                    {isAdmin && <th>Actions</th>}
                  </tr>
                </thead>

                <tbody>
                  {filteredOrders.map((order) => (
                    <tr key={order.id}>
                      <td>
                        <strong>#{order.id}</strong>

                        <span className="order-owner">
                          Customer:{" "}
                          {order.customer_name ||
                            order.username ||
                            "Guest customer"}
                        </span>

                        <div className="order-items-list">
                          {order.items && order.items.length > 0 ? (
                            order.items.map((item) => (
                              <span className="order-item-pill" key={item.id}>
                                {item.product_name ||
                                  `Product #${item.product}`}{" "}
                                × {item.quantity}
                              </span>
                            ))
                          ) : (
                            <span className="order-item-empty">No items</span>
                          )}
                        </div>
                      </td>

                      <td>{order.phone_number || "No phone"}</td>
                      <td>{order.city || "No city"}</td>

                      <td>
                        <strong>{formatPrice(order.total_price)}</strong>
                      </td>

                      <td>
                        <span className={`order-status ${order.status}`}>
                          {order.status}
                        </span>
                      </td>

                      <td>
                        {order.created_at
                          ? new Date(order.created_at).toLocaleDateString()
                          : "No date"}
                      </td>

                      {isAdmin && (
                        <td>
                          <div className="admin-actions">
                            {order.status === "pending" && (
                              <>
                                <button
                                  type="button"
                                  className="mini-action-button approve"
                                  onClick={() => validateOrder(order.id)}
                                >
                                  Validate
                                </button>

                                <button
                                  type="button"
                                  className="mini-action-button danger"
                                  onClick={() => cancelOrder(order.id)}
                                >
                                  Cancel
                                </button>
                              </>
                            )}

                            {order.status === "validated" && (
                              <>
                                <button
                                  type="button"
                                  className="mini-action-button approve"
                                  onClick={() => deliverOrder(order.id)}
                                >
                                  Deliver
                                </button>

                                <button
                                  type="button"
                                  className="mini-action-button danger"
                                  onClick={() => cancelOrder(order.id)}
                                >
                                  Cancel
                                </button>
                              </>
                            )}

                            {order.status === "delivered" && (
                              <span className="action-muted">—</span>
                            )}

                            {order.status === "cancelled" && (
                              <span className="action-muted">—</span>
                            )}
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </main>
      )}

      {activeView === "admin" && isAdmin && (
        <main className="panel-page">
          <div className="section-title">
            <div>
              <p className="section-kicker">Admin workspace</p>
              <h2>Dashboard</h2>
            </div>
            <button
              type="button"
              className="outline-button dark"
              onClick={loadAdminData}
            >
              Refresh admin data
            </button>
          </div>

          <section className="admin-stats">
            <div>
              <span>Total orders</span>
              <strong>{adminStats?.total_orders ?? "—"}</strong>
            </div>
            <div>
              <span>Pending</span>
              <strong>{adminStats?.pending_orders ?? "—"}</strong>
            </div>
            <div>
              <span>Delivered</span>
              <strong>{adminStats?.delivered_orders ?? "—"}</strong>
            </div>
            <div>
              <span>Low stock</span>
              <strong>{lowStock.length}</strong>
            </div>
          </section>

          <section className="admin-grid">
            {editingProductId && (
              <div className="admin-card wide">
                <h3>Edit product</h3>
                <p className="admin-hint">
                  Edit product details here. Stock is managed separately from
                  Stock control.
                </p>

                <form className="admin-form" onSubmit={updateProduct}>
                  <input
                    type="text"
                    placeholder="Product name"
                    value={editProductForm.name}
                    onChange={(event) =>
                      setEditProductForm({
                        ...editProductForm,
                        name: event.target.value,
                      })
                    }
                    required
                  />

                  <textarea
                    placeholder="Description"
                    value={editProductForm.description}
                    onChange={(event) =>
                      setEditProductForm({
                        ...editProductForm,
                        description: event.target.value,
                      })
                    }
                  />

                  <input
                    type="number"
                    placeholder="Price"
                    value={editProductForm.price}
                    onChange={(event) =>
                      setEditProductForm({
                        ...editProductForm,
                        price: event.target.value,
                      })
                    }
                    required
                  />

                  <select
                    value={editProductForm.category}
                    onChange={(event) =>
                      setEditProductForm({
                        ...editProductForm,
                        category: event.target.value,
                      })
                    }
                    required
                  >
                    <option value="">Select category</option>
                    {categories.map((categoryItem) => (
                      <option value={categoryItem.id} key={categoryItem.id}>
                        {categoryItem.name}
                      </option>
                    ))}
                  </select>

                  <input
                    type="file"
                    accept="image/*"
                    onChange={(event) =>
                      setEditProductImage(event.target.files[0] || null)
                    }
                  />

                  <div className="form-actions">
                    <button type="submit" className="solid-button full">
                      Save product
                    </button>

                    <button
                      type="button"
                      className="ghost-light"
                      onClick={cancelEditProduct}
                    >
                      Cancel edit
                    </button>
                  </div>
                </form>
              </div>
            )}
            <div className="admin-card">
              <h3>Create product</h3>
              <form className="admin-form" onSubmit={createProduct}>
                <input
                  type="text"
                  placeholder="Product name"
                  value={adminProductForm.name}
                  onChange={(event) =>
                    setAdminProductForm({
                      ...adminProductForm,
                      name: event.target.value,
                    })
                  }
                  required
                />

                <textarea
                  placeholder="Description. Add 'coming soon' to show Coming soon."
                  value={adminProductForm.description}
                  onChange={(event) =>
                    setAdminProductForm({
                      ...adminProductForm,
                      description: event.target.value,
                    })
                  }
                />

                <input
                  type="number"
                  placeholder="Price"
                  value={adminProductForm.price}
                  onChange={(event) =>
                    setAdminProductForm({
                      ...adminProductForm,
                      price: event.target.value,
                    })
                  }
                  required
                />

                <input
                  type="number"
                  placeholder="Stock quantity"
                  value={adminProductForm.stock}
                  onChange={(event) =>
                    setAdminProductForm({
                      ...adminProductForm,
                      stock: event.target.value,
                    })
                  }
                  required
                />

                <div className="category-mode">
                  <button
                    type="button"
                    className={
                      categoryMode === "existing"
                        ? "mode-button active"
                        : "mode-button"
                    }
                    onClick={() => setCategoryMode("existing")}
                  >
                    Existing category
                  </button>

                  <button
                    type="button"
                    className={
                      categoryMode === "new"
                        ? "mode-button active"
                        : "mode-button"
                    }
                    onClick={() => setCategoryMode("new")}
                  >
                    New category
                  </button>
                </div>

                {categoryMode === "existing" ? (
                  <select
                    value={adminProductForm.category}
                    onChange={(event) =>
                      setAdminProductForm({
                        ...adminProductForm,
                        category: event.target.value,
                      })
                    }
                    required
                  >
                    <option value="">Select category</option>
                    {categories.map((categoryItem) => (
                      <option value={categoryItem.id} key={categoryItem.id}>
                        {categoryItem.name}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    placeholder="New category name"
                    value={newCategoryName}
                    onChange={(event) => setNewCategoryName(event.target.value)}
                    required
                  />
                )}

                <input
                  type="file"
                  accept="image/*"
                  onChange={(event) =>
                    setProductImage(event.target.files[0] || null)
                  }
                />

                <button type="submit" className="solid-button full">
                  Create product
                </button>
              </form>
            </div>

            <div className="admin-card">
              <h3>Manual order</h3>
              <p className="admin-hint">
                Create an order for a customer. This is the correct admin way to
                place an order without using the customer cart.
              </p>

              <form className="admin-form" onSubmit={createManualOrder}>
                <input
                  type="text"
                  placeholder="Customer name"
                  value={manualOrderForm.customerName}
                  onChange={(event) =>
                    setManualOrderForm({
                      ...manualOrderForm,
                      customerName: event.target.value,
                    })
                  }
                  required
                />

                <input
                  type="text"
                  placeholder="City"
                  value={manualOrderForm.city}
                  onChange={(event) =>
                    setManualOrderForm({
                      ...manualOrderForm,
                      city: event.target.value,
                    })
                  }
                  required
                />

                <input
                  type="text"
                  placeholder="Phone number"
                  value={manualOrderForm.phoneNumber}
                  onChange={(event) =>
                    setManualOrderForm({
                      ...manualOrderForm,
                      phoneNumber: event.target.value,
                    })
                  }
                  required
                />

                <select
                  value={manualOrderForm.product}
                  onChange={(event) =>
                    setManualOrderForm({
                      ...manualOrderForm,
                      product: event.target.value,
                    })
                  }
                  required
                >
                  <option value="">Select product</option>
                  {products.map((product) => (
                    <option value={product.id} key={product.id}>
                      {product.name} · stock {product.stock}
                    </option>
                  ))}
                </select>

                <input
                  type="number"
                  min="1"
                  placeholder="Quantity"
                  value={manualOrderForm.quantity}
                  onChange={(event) =>
                    setManualOrderForm({
                      ...manualOrderForm,
                      quantity: event.target.value,
                    })
                  }
                  required
                />

                <textarea
                  placeholder="Internal note"
                  value={manualOrderForm.notes}
                  onChange={(event) =>
                    setManualOrderForm({
                      ...manualOrderForm,
                      notes: event.target.value,
                    })
                  }
                />

                <button type="submit" className="solid-button full">
                  Create manual order
                </button>
              </form>
            </div>
          </section>

          <section className="admin-card">
            <h3>Stock control</h3>

            <div className="stock-grid">
              {products.map((product) => (
                <div className="stock-row" key={product.id}>
                  <div>
                    <strong>{product.name}</strong>
                    <p>Current stock: {product.stock}</p>
                  </div>

                  <input
                    type="number"
                    placeholder="+10 or -3"
                    value={stockAdjustments[product.id]?.quantity || ""}
                    onChange={(event) =>
                      setStockAdjustments((current) => ({
                        ...current,
                        [product.id]: {
                          ...(current[product.id] || {}),
                          quantity: event.target.value,
                        },
                      }))
                    }
                  />

                  <input
                    type="text"
                    placeholder="Note"
                    value={stockAdjustments[product.id]?.note || ""}
                    onChange={(event) =>
                      setStockAdjustments((current) => ({
                        ...current,
                        [product.id]: {
                          ...(current[product.id] || {}),
                          note: event.target.value,
                        },
                      }))
                    }
                  />

                  <button
                    type="button"
                    className="solid-button"
                    onClick={() => adjustStock(product.id)}
                  >
                    Update
                  </button>
                </div>
              ))}
            </div>
          </section>
        </main>
      )}
    </div>
  );
}

export default App;
