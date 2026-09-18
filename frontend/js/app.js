// HomeBrain Main Application Logic

let currentUser = null;
let categories = [];
let userEmails = [];
let selectedFile = null;
let selectedCategoryId = null;
let currentInboxFilter = "pending";

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", async () => {
  setupEventListeners();
  await checkAuth();
});

// --- Auth Handling ---
async function checkAuth() {
  const token = api.getToken();
  if (!token) {
    showAuthView();
    return;
  }

  try {
    currentUser = await api.getMe();
    showAppView();
    await loadInitialData();
  } catch (err) {
    console.warn("Auth check failed:", err);
    showAuthView();
  }
}

function showAuthView() {
  document.getElementById("authView").classList.remove("hidden");
  document.getElementById("appContainer").classList.add("hidden");
  document.getElementById("userHeaderBar").classList.add("hidden");
  document.getElementById("mobileBottomNav").classList.add("hidden");
  lucide.createIcons();
}

function showAppView() {
  document.getElementById("authView").classList.add("hidden");
  document.getElementById("appContainer").classList.remove("hidden");
  document.getElementById("userHeaderBar").classList.remove("hidden");
  document.getElementById("mobileBottomNav").classList.remove("hidden");

  // Populate user header
  document.getElementById("userDisplayName").textContent = currentUser.display_name || currentUser.username;
  document.getElementById("userAvatar").textContent = (currentUser.display_name || currentUser.username).charAt(0).toUpperCase();

  const roleBadge = document.getElementById("userRoleBadge");
  const adminSection = document.getElementById("adminUserSection");
  if (currentUser.role === "admin") {
    roleBadge.classList.remove("hidden");
    adminSection.classList.remove("hidden");
  } else {
    roleBadge.classList.add("hidden");
    adminSection.classList.add("hidden");
  }

  lucide.createIcons();
}

function setQuickLogin(username, password) {
  document.getElementById("loginUsername").value = username;
  document.getElementById("loginPassword").value = password;
  document.getElementById("loginForm").dispatchEvent(new Event("submit"));
}

// --- Event Listeners Setup ---
function setupEventListeners() {
  // Login Form
  document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = document.getElementById("loginSubmitBtn");
    const u = document.getElementById("loginUsername").value.trim();
    const p = document.getElementById("loginPassword").value;

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span>Přihlašuji...</span>`;
      const res = await api.login(u, p);
      currentUser = res.user;
      showAppView();
      await loadInitialData();
      showToast("Vítejte v HomeBrain!", `Úspěšně přihlášen jako ${currentUser.display_name}`, "success");
    } catch (err) {
      showToast("Chyba přihlášení", err.message, "error");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<span>Přihlásit se</span><i data-lucide="arrow-right" class="w-4 h-4"></i>`;
      lucide.createIcons();
    }
  });

  // Logout Button
  document.getElementById("logoutBtn").addEventListener("click", () => {
    api.setToken(null);
    currentUser = null;
    showAuthView();
    showToast("Odhlášeno", "Byli jste úspěšně odhlášeni ze systému.", "info");
  });

  // Camera file input
  const cameraInput = document.getElementById("cameraInput");
  cameraInput.addEventListener("change", handleFileSelected);

  // Global custom event for auth required
  window.addEventListener("auth:required", () => {
    showAuthView();
  });
}

// --- Initial Data Loader ---
async function loadInitialData() {
  await Promise.all([
    loadCategories(),
    loadUserEmails(),
    loadInboxDocuments()
  ]);
  if (currentUser && currentUser.role === "admin") {
    await loadAdminUsers();
  }
}

// --- Tab Switching ---
function switchTab(tabName) {
  // Hide all contents
  document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
  document.getElementById(`tab-${tabName}`).classList.remove("hidden");

  // Update Desktop Tabs
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.classList.remove("active-tab");
    btn.classList.add("text-slate-400");
  });
  const activeDesktopBtn = document.getElementById(`desktopTabBtn-${tabName}`);
  if (activeDesktopBtn) {
    activeDesktopBtn.classList.add("active-tab");
    activeDesktopBtn.classList.remove("text-slate-400");
  }

  // Update Mobile Tabs
  const mobileButtons = ["capture", "inbox", "settings"];
  mobileButtons.forEach(name => {
    const btn = document.getElementById(`mobileTabBtn-${name}`);
    if (btn) {
      if (name === tabName) {
        btn.classList.add("text-indigo-400");
        btn.classList.remove("text-slate-400");
      } else {
        btn.classList.remove("text-indigo-400");
        btn.classList.add("text-slate-400");
      }
    }
  });

  if (tabName === "inbox") {
    loadInboxDocuments();
  } else if (tabName === "settings") {
    loadUserEmails();
    loadCategories();
    if (currentUser.role === "admin") loadAdminUsers();
  }

  lucide.createIcons();
}

// --- Camera & Photo Capture ---
function triggerCamera() {
  document.getElementById("cameraInput").click();
}

function handleFileSelected(e) {
  const file = e.target.files[0];
  if (!file) return;

  selectedFile = file;
  document.getElementById("capturePrompt").classList.add("hidden");
  const previewContainer = document.getElementById("previewContainer");
  previewContainer.classList.remove("hidden");

  if (file.type.startsWith("image/")) {
    const reader = new FileReader();
    reader.onload = (event) => {
      const img = document.getElementById("imagePreview");
      img.src = event.target.result;
      img.classList.remove("hidden");
      document.getElementById("pdfPreview").classList.add("hidden");
    };
    reader.readAsDataURL(file);
  } else {
    // PDF or other document
    document.getElementById("imagePreview").classList.add("hidden");
    const pdfPreview = document.getElementById("pdfPreview");
    pdfPreview.classList.remove("hidden");
    document.getElementById("pdfFilename").textContent = file.name;
  }
}

function removePhoto() {
  selectedFile = null;
  document.getElementById("cameraInput").value = "";
  document.getElementById("previewContainer").classList.add("hidden");
  document.getElementById("capturePrompt").classList.remove("hidden");
}

// --- Categories Handling ---
async function loadCategories() {
  try {
    categories = await api.getCategories();
    renderCategoriesCapture();
    renderCategoriesSettings();
  } catch (err) {
    console.error("Failed to load categories:", err);
  }
}

function getIconEmoji(icon) {
  const map = {
    "receipt": "🧾",
    "heart-pulse": "🩺",
    "file-text": "📄",
    "car": "🚗",
    "home": "🏠",
    "folder": "📁"
  };
  return map[icon] || "📁";
}

function renderCategoriesCapture() {
  const container = document.getElementById("categoriesList");
  container.innerHTML = "";

  if (categories.length === 0) {
    container.innerHTML = `<p class="text-xs text-slate-400 col-span-3">Žádné kategorie. Přidejte první tlačítkem výše.</p>`;
    return;
  }

  categories.forEach((cat, idx) => {
    const isSelected = selectedCategoryId === cat.id || (!selectedCategoryId && idx === 0);
    if (isSelected && !selectedCategoryId) {
      selectedCategoryId = cat.id;
    }

    const card = document.createElement("button");
    card.type = "button";
    card.className = `cat-card p-3 rounded-xl border text-left transition flex items-center gap-2.5 ${
      isSelected
        ? "active-cat border-indigo-500 bg-indigo-500/10 text-white"
        : "border-slate-700 bg-slate-900/60 text-slate-300 hover:border-slate-600 hover:bg-slate-900"
    }`;
    card.onclick = () => selectCategory(cat.id);

    card.innerHTML = `
      <span class="text-xl">${getIconEmoji(cat.icon)}</span>
      <div class="overflow-hidden">
        <p class="font-semibold text-xs truncate">${cat.name}</p>
        <p class="text-[10px] text-slate-400 truncate">${cat.target_folder_name || 'Dokumenty'}</p>
      </div>
    `;
    container.appendChild(card);
  });
}

function selectCategory(catId) {
  selectedCategoryId = catId;
  renderCategoriesCapture();

  // If category has a default email configured, select it in the dropdown
  const cat = categories.find(c => c.id === catId);
  if (cat && cat.default_email) {
    const select = document.getElementById("targetEmailSelect");
    for (let opt of select.options) {
      if (opt.value === cat.default_email) {
        select.value = cat.default_email;
        break;
      }
    }
  }
}

// --- User Emails Handling ---
async function loadUserEmails() {
  try {
    userEmails = await api.getEmails();
    renderEmailsDropdown();
    renderEmailsSettings();
  } catch (err) {
    console.error("Failed to load user emails:", err);
  }
}

function renderEmailsDropdown() {
  const select = document.getElementById("targetEmailSelect");
  select.innerHTML = "";

  if (userEmails.length === 0) {
    select.innerHTML = `<option value="">(Žádný e-mail není nastaven v profilu)</option>`;
    return;
  }

  userEmails.forEach(e => {
    const opt = document.createElement("option");
    opt.value = e.email_address;
    opt.textContent = `${e.label} (${e.email_address})${e.is_default ? ' ★' : ''}`;
    if (e.is_default) {
      opt.selected = true;
    }
    select.appendChild(opt);
  });
}

// --- Submit Document ---
async function submitDocument() {
  if (!selectedFile) {
    showToast("Chybí dokument", "Nejprve vyfoťte nebo vyberte dokument.", "error");
    return;
  }

  const targetEmail = document.getElementById("targetEmailSelect").value;
  if (!targetEmail) {
    showToast("Chybí e-mail", "Zvolte cílový e-mail pro odeslání.", "error");
    return;
  }

  const note = document.getElementById("documentNote").value;
  const submitBtn = document.getElementById("submitDocumentBtn");
  const submitText = document.getElementById("submitBtnText");

  try {
    submitBtn.disabled = true;
    submitText.textContent = "Odesílám e-mailem a ukládám...";

    const formData = new FormData();
    formData.append("file", selectedFile);
    if (selectedCategoryId) {
      formData.append("category_id", selectedCategoryId);
    }
    formData.append("target_email", targetEmail);
    if (note) {
      formData.append("note", note);
    }

    const doc = await api.uploadDocument(formData);

    showToast(
      "Úspěšně zpracováno!",
      `E-mail byl odeslán na ${targetEmail} a dokument byl zařazen do Inboxu.`,
      "success"
    );

    // Reset capture form
    removePhoto();
    document.getElementById("documentNote").value = "";

    // Refresh inbox count
    await loadInboxDocuments();
  } catch (err) {
    showToast("Chyba při odesílání", err.message, "error");
  } finally {
    submitBtn.disabled = false;
    submitText.textContent = "Odeslat mailem a uložit do Inboxu";
    lucide.createIcons();
  }
}

// --- Web Inbox Handling (PC / Mac) ---
async function loadInboxDocuments() {
  try {
    const docs = await api.getInboxDocuments(currentInboxFilter);
    renderInbox(docs);

    // Update pending badge
    const allPending = await api.getInboxDocuments("pending");
    const count = allPending.length;
    document.getElementById("inboxBadgeCount").textContent = count;
    const mobileBadge = document.getElementById("mobileInboxBadge");
    if (count > 0) {
      mobileBadge.classList.remove("hidden");
    } else {
      mobileBadge.classList.add("hidden");
    }
  } catch (err) {
    console.error("Failed to load inbox:", err);
  }
}

function filterInbox(status) {
  currentInboxFilter = status;
  document.querySelectorAll(".inbox-filter-btn").forEach(btn => {
    btn.classList.remove("bg-indigo-600", "text-white");
    btn.classList.add("bg-slate-800", "text-slate-400");
  });
  const activeBtn = document.getElementById(`filter-${status}`);
  if (activeBtn) {
    activeBtn.classList.remove("bg-slate-800", "text-slate-400");
    activeBtn.classList.add("bg-indigo-600", "text-white");
  }
  loadInboxDocuments();
}

function renderInbox(docs) {
  const grid = document.getElementById("inboxGrid");
  const emptyState = document.getElementById("inboxEmptyState");
  grid.innerHTML = "";

  if (docs.length === 0) {
    emptyState.classList.remove("hidden");
    return;
  }
  emptyState.classList.add("hidden");

  docs.forEach(doc => {
    const card = document.createElement("div");
    card.className = "bg-slate-800/90 border border-slate-700/70 rounded-2xl overflow-hidden shadow-lg hover:border-slate-600 transition flex flex-col";

    const isImage = doc.content_type.startsWith("image/");
    const previewHtml = isImage
      ? `<img src="/api/documents/${doc.id}/file" class="w-full h-44 object-cover cursor-pointer hover:opacity-95 transition" onclick="window.open('/api/documents/${doc.id}/file', '_blank')" alt="${doc.category_name}">`
      : `<div class="w-full h-44 bg-slate-900/80 flex items-center justify-center text-indigo-400"><i data-lucide="file-text" class="w-16 h-16"></i></div>`;

    const statusBadge = doc.status === "pending"
      ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">Čeká na uložení</span>`
      : `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Uloženo v PC</span>`;

    const emailStatus = doc.email_status === "sent"
      ? `<span class="text-emerald-400" title="E-mail úspěšně odeslán">✉️ Odesláno</span>`
      : doc.email_status === "mock_sent"
        ? `<span class="text-amber-400" title="Uloženo v testovacím náhledu">✉️ Test náhled</span>`
        : `<span class="text-rose-400" title="Chyba odeslání">❌ Neodesláno</span>`;

    const createdDate = new Date(doc.created_at).toLocaleString("cs-CZ", {
      day: "numeric",
      month: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });

    card.innerHTML = `
      ${previewHtml}
      <div class="p-4 flex-1 flex flex-col justify-between space-y-3">
        <div>
          <div class="flex items-center justify-between gap-2 mb-1.5">
            <span class="font-bold text-sm text-white flex items-center gap-1.5">
              📁 ${doc.category_name}
            </span>
            ${statusBadge}
          </div>
          ${doc.note ? `<p class="text-xs text-slate-300 bg-slate-900/60 p-2 rounded-lg border border-slate-700/50 mb-2 font-medium">„${doc.note}“</p>` : ''}
          <div class="text-[11px] text-slate-400 space-y-0.5">
            <p>👤 Nahrál: <span class="text-slate-200">${doc.user_name}</span></p>
            <p>🕒 ${createdDate}</p>
            <p>📬 ${emailStatus} <span class="text-slate-300">(${doc.sent_to_email || '—'})</span></p>
          </div>
        </div>

        <div class="pt-3 border-t border-slate-700/60 flex items-center justify-between gap-2">
          <a href="/api/documents/${doc.id}/file?download=true" class="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-xs font-semibold inline-flex items-center gap-1 transition">
            <i data-lucide="download" class="w-3.5 h-3.5"></i>
            <span>Stáhnout</span>
          </a>
          ${doc.status === "pending" ? `
            <button onclick="markAsSaved(${doc.id})" class="px-3 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 rounded-lg text-xs font-semibold transition">
              ✓ Označit jako uloženo
            </button>
          ` : `
            <button onclick="markAsPending(${doc.id})" class="text-slate-400 hover:text-white text-xs underline">
              Vrátit do čekajících
            </button>
          `}
        </div>
      </div>
    `;
    grid.appendChild(card);
  });

  lucide.createIcons();
}

async function markAsSaved(docId) {
  try {
    await api.updateDocumentStatus(docId, "saved_to_pc");
    showToast("Uloženo", "Dokument byl označen jako uložený.", "success");
    loadInboxDocuments();
  } catch (err) {
    showToast("Chyba", err.message, "error");
  }
}

async function markAsPending(docId) {
  try {
    await api.updateDocumentStatus(docId, "pending");
    loadInboxDocuments();
  } catch (err) {
    showToast("Chyba", err.message, "error");
  }
}

// --- Browser File System Access API (Save to PC / Mac Disk) ---
async function saveAllToLocalDisk() {
  const docs = await api.getInboxDocuments("pending");
  if (docs.length === 0) {
    showToast("Žádné dokumenty", "V inboxu momentálně nečekají žádné nové dokumenty.", "info");
    return;
  }

  // Check if browser supports File System Access API
  if ("showDirectoryPicker" in window) {
    try {
      showToast("Výběr cílové složky", "Vyberte složku na vašem PC nebo Macu, kam chcete dokumenty uložit.", "info");
      const dirHandle = await window.showDirectoryPicker({
        mode: "readwrite"
      });

      let savedCount = 0;

      for (const doc of docs) {
        try {
          // Subfolder by category (e.g. "Paragony", "Lekarske_zpravy")
          const folderName = doc.category_name.replace(/[^a-zA-Z0-9_\u00C0-\u017F-]/g, "_");
          const subDirHandle = await dirHandle.getDirectoryHandle(folderName, { create: true });

          // Fetch file bytes
          const res = await fetch(`/api/documents/${doc.id}/file`, {
            headers: { "Authorization": `Bearer ${api.getToken()}` }
          });
          const blob = await res.blob();

          // Filename
          const fileHandle = await subDirHandle.getFileHandle(doc.original_filename, { create: true });
          const writable = await fileHandle.createWritable();
          await writable.write(blob);
          await writable.close();

          // Mark as saved in backend
          await api.updateDocumentStatus(doc.id, "saved_to_pc");
          savedCount++;
        } catch (err) {
          console.error(`Error saving doc ${doc.id}:`, err);
        }
      }

      showToast(
        "Dokumenty uloženy!",
        `Úspěšně uloženo ${savedCount} dokumentů do zvolené složky na vašem disku.`,
        "success"
      );
      loadInboxDocuments();
    } catch (err) {
      if (err.name !== "AbortError") {
        showToast("Chyba při ukládání", err.message, "error");
      }
    }
  } else {
    // Fallback: Download ZIP
    showToast("Stahuji ZIP", "Váš prohlížeč nepodporuje přímý zápis na disk. Stahuji uspořádaný ZIP archiv.", "info");
    downloadZipExport();
  }
}

function downloadZipExport() {
  window.open(api.getExportZipUrl(currentInboxFilter), "_blank");
}

// --- Settings Section ---
function renderEmailsSettings() {
  const list = document.getElementById("settingsEmailList");
  list.innerHTML = "";

  if (userEmails.length === 0) {
    list.innerHTML = `<p class="text-xs text-slate-400">Zatím nemáte nastavený žádný e-mail.</p>`;
    return;
  }

  userEmails.forEach(e => {
    const item = document.createElement("div");
    item.className = "flex items-center justify-between p-3 bg-slate-900/70 border border-slate-700/60 rounded-xl text-xs";
    item.innerHTML = `
      <div>
        <span class="font-bold text-white">${e.label}</span>
        <span class="text-slate-400 ml-2 font-mono">${e.email_address}</span>
        ${e.is_default ? '<span class="ml-2 text-[10px] bg-indigo-500/20 text-indigo-300 px-1.5 py-0.5 rounded border border-indigo-500/30">Výchozí</span>' : ''}
      </div>
      <button onclick="handleDeleteEmail(${e.id})" class="text-slate-400 hover:text-rose-400 transition p-1">
        <i data-lucide="trash-2" class="w-4 h-4"></i>
      </button>
    `;
    list.appendChild(item);
  });
  lucide.createIcons();
}

async function handleAddEmail(e) {
  e.preventDefault();
  const label = document.getElementById("newEmailLabel").value.trim();
  const email = document.getElementById("newEmailAddress").value.trim();

  try {
    await api.addEmail({
      label,
      email_address: email,
      is_default: userEmails.length === 0
    });
    document.getElementById("newEmailLabel").value = "";
    document.getElementById("newEmailAddress").value = "";
    showToast("Přidáno", "E-mail byl úspěšně přidán do profilu.", "success");
    await loadUserEmails();
  } catch (err) {
    showToast("Chyba", err.message, "error");
  }
}

async function handleDeleteEmail(id) {
  if (!confirm("Opravdu chcete tento e-mail smazat?")) return;
  try {
    await api.deleteEmail(id);
    showToast("Smazáno", "E-mail byl odstraněn.", "success");
    await loadUserEmails();
  } catch (err) {
    showToast("Chyba", err.message, "error");
  }
}

function renderCategoriesSettings() {
  const list = document.getElementById("settingsCategoryList");
  list.innerHTML = "";

  categories.forEach(cat => {
    const item = document.createElement("div");
    item.className = "flex items-center justify-between p-3 bg-slate-900/70 border border-slate-700/60 rounded-xl text-xs";
    item.innerHTML = `
      <div class="flex items-center gap-2.5">
        <span class="text-lg">${getIconEmoji(cat.icon)}</span>
        <div>
          <span class="font-bold text-white">${cat.name}</span>
          <p class="text-[10px] text-slate-400">Předmět: <span class="font-mono text-slate-300">${cat.subject_template}</span> | Složka: <span class="font-mono text-slate-300">${cat.target_folder_name}</span></p>
        </div>
      </div>
      <button onclick="handleDeleteCategory(${cat.id})" class="text-slate-400 hover:text-rose-400 transition p-1">
        <i data-lucide="trash-2" class="w-4 h-4"></i>
      </button>
    `;
    list.appendChild(item);
  });
  lucide.createIcons();
}

function openNewCategoryModal() {
  document.getElementById("categoryModal").classList.remove("hidden");
  document.getElementById("catModalName").focus();
}

function closeNewCategoryModal() {
  document.getElementById("categoryModal").classList.add("hidden");
  document.getElementById("createCategoryForm").reset();
}

async function handleCreateCategory(e) {
  e.preventDefault();
  const name = document.getElementById("catModalName").value.trim();
  const icon = document.getElementById("catModalIcon").value;
  const folder = document.getElementById("catModalFolder").value.trim();

  try {
    await api.createCategory({
      name,
      icon,
      target_folder_name: folder || name.replace(/\s+/g, "_")
    });
    closeNewCategoryModal();
    showToast("Složka vytvořena", `Kategorie „${name}“ byla úspěšně přidána.`, "success");
    await loadCategories();
  } catch (err) {
    showToast("Chyba", err.message, "error");
  }
}

async function handleDeleteCategory(id) {
  if (!confirm("Opravdu chcete tuto kategorii smazat?")) return;
  try {
    await api.deleteCategory(id);
    showToast("Smazáno", "Kategorie byla odstraněna.", "success");
    await loadCategories();
  } catch (err) {
    showToast("Chyba", err.message, "error");
  }
}

// --- Admin: Users Management ---
async function loadAdminUsers() {
  try {
    const users = await api.listUsers();
    renderAdminUsers(users);
  } catch (err) {
    console.error("Failed to load admin users:", err);
  }
}

function renderAdminUsers(users) {
  const list = document.getElementById("adminUsersList");
  list.innerHTML = "";

  users.forEach(u => {
    const item = document.createElement("div");
    item.className = "flex items-center justify-between p-3 bg-slate-900/70 border border-slate-700/60 rounded-xl text-xs";
    item.innerHTML = `
      <div class="flex items-center gap-2">
        <div class="w-6 h-6 rounded-full bg-purple-600 text-white font-bold flex items-center justify-center text-[10px]">
          ${u.display_name.charAt(0).toUpperCase()}
        </div>
        <div>
          <span class="font-bold text-white">${u.display_name}</span>
          <span class="text-slate-400 font-mono text-[11px] ml-1">(@${u.username})</span>
          ${u.role === 'admin' ? '<span class="ml-2 text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded border border-amber-500/30">Admin</span>' : ''}
        </div>
      </div>
      ${u.id !== currentUser.id ? `
        <button onclick="handleDeleteUser(${u.id})" class="text-slate-400 hover:text-rose-400 transition p-1">
          <i data-lucide="trash-2" class="w-4 h-4"></i>
        </button>
      ` : ''}
    `;
    list.appendChild(item);
  });
  lucide.createIcons();
}

async function handleAddUser(e) {
  e.preventDefault();
  const username = document.getElementById("newUsername").value.trim();
  const displayName = document.getElementById("newDisplayName").value.trim();
  const password = document.getElementById("newUserPassword").value;
  const initialEmail = document.getElementById("newUserEmail").value.trim();

  try {
    await api.createUser({
      username,
      display_name: displayName,
      password,
      initial_email: initialEmail || null
    });
    document.getElementById("addUserForm").reset();
    showToast("Uživatel vytvořen", `Uživatel ${displayName} byl úspěšně přidán.`, "success");
    await loadAdminUsers();
  } catch (err) {
    showToast("Chyba", err.message, "error");
  }
}

async function handleDeleteUser(userId) {
  if (!confirm("Opravdu chcete tohoto uživatele smazat?")) return;
  try {
    await api.deleteUser(userId);
    showToast("Smazáno", "Uživatel byl odstraněn.", "success");
    await loadAdminUsers();
  } catch (err) {
    showToast("Chyba", err.message, "error");
  }
}

// --- Notification Toast Utility ---
let toastTimer = null;
function showToast(title, message, type = "success") {
  const toast = document.getElementById("toastNotification");
  const icon = document.getElementById("toastIcon");
  const titleEl = document.getElementById("toastTitle");
  const msgEl = document.getElementById("toastMessage");

  if (type === "success") {
    toast.className = "mb-6 p-4 rounded-xl border flex items-center justify-between shadow-lg transition-all animate-fade-in bg-emerald-950/80 border-emerald-500/50 text-emerald-200";
    icon.textContent = "✅";
  } else if (type === "error") {
    toast.className = "mb-6 p-4 rounded-xl border flex items-center justify-between shadow-lg transition-all animate-fade-in bg-rose-950/80 border-rose-500/50 text-rose-200";
    icon.textContent = "⚠️";
  } else {
    toast.className = "mb-6 p-4 rounded-xl border flex items-center justify-between shadow-lg transition-all animate-fade-in bg-indigo-950/80 border-indigo-500/50 text-indigo-200";
    icon.textContent = "ℹ️";
  }

  titleEl.textContent = title;
  msgEl.textContent = message;
  toast.classList.remove("hidden");

  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    hideToast();
  }, 5000);
}

function hideToast() {
  document.getElementById("toastNotification").classList.add("hidden");
}
