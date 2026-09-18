// HomeBrain API Client

const API_BASE = "";

const api = {
  getToken() {
    return localStorage.getItem("homebrain_token");
  },

  setToken(token) {
    if (token) {
      localStorage.setItem("homebrain_token", token);
    } else {
      localStorage.removeItem("homebrain_token");
    }
  },

  async request(endpoint, options = {}) {
    const headers = options.headers || {};
    const token = this.getToken();

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (!options.isFormData && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    const config = {
      ...options,
      headers
    };

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, config);
      if (res.status === 401) {
        // Token expired or invalid
        this.setToken(null);
        window.dispatchEvent(new CustomEvent("auth:required"));
        throw new Error("Relace vypršela. Přihlaste se prosím znovu.");
      }

      if (!res.ok) {
        let errDetail = "Neznámá chyba serveru";
        try {
          const errData = await res.json();
          errDetail = errData.detail || errDetail;
        } catch (_) {}
        throw new Error(errDetail);
      }

      const contentType = res.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        return await res.json();
      }
      return res;
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  },

  // --- Auth ---
  async login(username, password) {
    const data = await this.request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password })
    });
    this.setToken(data.access_token);
    return data;
  },

  async getMe() {
    return await this.request("/api/auth/me");
  },

  async listUsers() {
    return await this.request("/api/auth/users");
  },

  async createUser(data) {
    return await this.request("/api/auth/users", {
      method: "POST",
      body: JSON.stringify(data)
    });
  },

  async deleteUser(userId) {
    return await this.request(`/api/auth/users/${userId}`, {
      method: "DELETE"
    });
  },

  // --- Settings: Emails ---
  async getEmails() {
    return await this.request("/api/settings/emails");
  },

  async addEmail(data) {
    return await this.request("/api/settings/emails", {
      method: "POST",
      body: JSON.stringify(data)
    });
  },

  async deleteEmail(emailId) {
    return await this.request(`/api/settings/emails/${emailId}`, {
      method: "DELETE"
    });
  },

  // --- Settings: Categories ---
  async getCategories() {
    return await this.request("/api/settings/categories");
  },

  async createCategory(data) {
    return await this.request("/api/settings/categories", {
      method: "POST",
      body: JSON.stringify(data)
    });
  },

  async deleteCategory(catId) {
    return await this.request(`/api/settings/categories/${catId}`, {
      method: "DELETE"
    });
  },

  // --- Documents ---
  async uploadDocument(formData) {
    return await this.request("/api/documents/upload", {
      method: "POST",
      body: formData,
      isFormData: true
    });
  },

  async getInboxDocuments(statusFilter = "pending") {
    return await this.request(`/api/documents/inbox?status_filter=${statusFilter}`);
  },

  async updateDocumentStatus(docId, status) {
    return await this.request(`/api/documents/${docId}/status`, {
      method: "PUT",
      body: JSON.stringify({ status })
    });
  },

  getExportZipUrl(statusFilter = "pending") {
    const token = this.getToken();
    return `/api/documents/export-zip?status_filter=${statusFilter}&token=${token || ''}`;
  }
};
