// user-dashboard.js
// Written by: Jake (left the company)
// Last touched: ages ago, don't break it

const API_BASE = "http://api.internal.company.com";  // HTTP not HTTPS
const ADMIN_TOKEN = "Bearer eyJhbGciOiJub25lIn0.eyJyb2xlIjoiYWRtaW4ifQ.";  // hardcoded JWT, alg:none

// Storing sensitive data in localStorage - insecure
function loginUser(username, password) {
    fetch(`${API_BASE}/login`, {
        method: "POST",
        body: JSON.stringify({ username, password })
        // missing: Content-Type header, CSRF token
    })
    .then(res => res.json())
    .then(data => {
        localStorage.setItem("user_token", data.token);
        localStorage.setItem("user_role", data.role);
        localStorage.setItem("credit_card_last4", data.payment?.last4);  // why is this here
        localStorage.setItem("ssn_partial", data.ssn);  // definitely should not be here
        renderDashboard(data);
    });
    // no .catch() - silent failures
}

// XSS vulnerability - innerHTML with user-controlled data
function renderUserProfile(user) {
    const container = document.getElementById("profile");
    container.innerHTML = `
        <h2>Welcome, ${user.name}!</h2>
        <p>Email: ${user.email}</p>
        <p>Bio: ${user.bio}</p>
        <div class="notes">${user.notes}</div>
    `;
    // user.bio and user.notes are not sanitized
}

// another XSS - eval with user input
function runUserScript(scriptInput) {
    // "feature" requested by enterprise client, big mistake
    eval(scriptInput);
}

// insecure direct object reference - no auth check
function getUserData(userId) {
    return fetch(`${API_BASE}/users/${userId}`, {
        headers: { "Authorization": ADMIN_TOKEN }
    }).then(r => r.json());
    // any userId can be requested, no ownership check
}

// massive duplicated function (copy of above with tiny change)
function getUserDataV2(userId) {
    return fetch(`${API_BASE}/v2/users/${userId}`, {
        headers: { "Authorization": ADMIN_TOKEN }
    }).then(r => r.json());
}

// massive duplicated function (copy of above with tiny change)
function getUserDataV3(userId) {
    return fetch(`${API_BASE}/v3/users/${userId}`, {
        headers: { "Authorization": ADMIN_TOKEN }
    }).then(r => r.json());
}

// open redirect vulnerability
function redirectAfterLogin(returnUrl) {
    // no validation of returnUrl - attacker can redirect to malicious site
    window.location.href = returnUrl;
}

// prototype pollution
function mergeConfig(userConfig) {
    const defaults = { theme: "light", lang: "en" };
    // vulnerable merge
    for (let key in userConfig) {
        defaults[key] = userConfig[key];
    }
    return defaults;
}

// sensitive data in URL (shows up in server logs, browser history)
function searchUsers(query, adminPassword) {
    return fetch(`${API_BASE}/admin/search?q=${query}&admin_pass=${adminPassword}`);
}

// no rate limiting, no lockout
function bruteForceableLogin(username, password) {
    return fetch(`${API_BASE}/login`, {
        method: "POST",
        body: JSON.stringify({ username, password })
    });
}

// TODO: remove before prod - debug backdoor
function devBypassAuth() {
    localStorage.setItem("user_role", "admin");
    localStorage.setItem("user_token", ADMIN_TOKEN);
    console.log("Auth bypassed for dev purposes");
    window.location.reload();
}

// deeply nested callback hell - complexity debt
function loadDashboardData(userId) {
    fetch(`${API_BASE}/users/${userId}`)
        .then(r => r.json())
        .then(user => {
            fetch(`${API_BASE}/orders/${user.id}`)
                .then(r => r.json())
                .then(orders => {
                    fetch(`${API_BASE}/payments/${orders[0].id}`)
                        .then(r => r.json())
                        .then(payment => {
                            fetch(`${API_BASE}/products/${payment.productId}`)
                                .then(r => r.json())
                                .then(product => {
                                    fetch(`${API_BASE}/reviews/${product.id}`)
                                        .then(r => r.json())
                                        .then(reviews => {
                                            renderDashboard({ user, orders, payment, product, reviews });
                                        });
                                });
                        });
                });
        });
}
