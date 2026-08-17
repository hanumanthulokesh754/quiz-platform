const API_BASE = "http://localhost:5000/api";

function getToken() {
  return localStorage.getItem("token");
}

function getUser() {
  const raw = localStorage.getItem("user");
  return raw ? JSON.parse(raw) : null;
}

function setSession(token, user) {
  localStorage.setItem("token", token);
  localStorage.setItem("user", JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

async function api(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data = null;
  try {
    data = await res.json();
  } catch (_) {
    // no JSON body (e.g. 204)
  }

  if (res.status === 401 && auth) {
    clearSession();
    window.location.href = "/auth/login.html";
    return;
  }

  if (!res.ok) {
    throw new Error((data && data.error) || `Request failed (${res.status})`);
  }

  return data;
}

/** Redirects to login if there's no session. Call at the top of every
 * protected page. Pass "ADMIN" to also gate the page to admins only. */
function requireAuth(role) {
  const user = getUser();
  if (!user || !getToken()) {
    window.location.href = "/auth/login.html";
    return null;
  }
  if (role && user.role !== role) {
    window.location.href = user.role === "ADMIN" ? "/admin/dashboard.html" : "/student/dashboard.html";
    return null;
  }
  return user;
}
