const expressionEl = document.getElementById("calc-expression");
const displayEl = document.getElementById("calc-display");
const historyListEl = document.getElementById("history-list");
const memoryDisplay = document.getElementById("memory-display");
const vaultStatusPill = document.getElementById("vault-status-pill");
const vaultSetupCard = document.getElementById("vault-setup");
const vaultUnlockCard = document.getElementById("vault-unlock");
const vaultDashboard = document.getElementById("vault-dashboard");
const vaultEntriesEl = document.getElementById("vault-entries");
const toastContainer = document.getElementById("toast-container");
const entryEditIndicator = document.getElementById("entry-edit-indicator");
const entryCancelBtn = document.querySelector("[data-entry-action='cancel']");
const entryForm = document.querySelector("[data-form='entry']");
const setupForm = document.querySelector("[data-form='setup']");
const unlockForm = document.querySelector("[data-form='unlock']");

let expression = "";
let outputValue = "0";
let memoryValue = 0;
let editingEntryId = null;
let cachedVaultEntries = [];

const numberFormatter = new Intl.NumberFormat("id-ID", {
  maximumFractionDigits: 6,
});

const toastVariants = {
  success: "bg-emerald-500/90",
  error: "bg-rose-500/90",
  info: "bg-cyan-500/90",
};

function updateDisplay() {
  expressionEl.textContent = expression || "0";
  displayEl.textContent = outputValue;
}

function appendToExpression(value) {
  if (!expression && /[0-9.]/.test(value)) {
    expression = value;
  } else {
    expression += value;
  }
  outputValue = expression || "0";
  updateDisplay();
}

function clearExpression() {
  expression = "";
  outputValue = "0";
  updateDisplay();
}

function backspaceExpression() {
  expression = expression.slice(0, -1);
  outputValue = expression || "0";
  updateDisplay();
}

function negateExpression() {
  if (!expression) {
    if (outputValue && outputValue !== "0") {
      expression = outputValue.startsWith("-")
        ? outputValue.slice(1)
        : `-${outputValue}`;
    }
  } else if (expression.startsWith("-")) {
    expression = expression.slice(1);
  } else {
    expression = `-(${expression})`;
  }
  outputValue = expression || "0";
  updateDisplay();
}

async function evaluateCurrentExpression() {
  if (!expression) {
    return;
  }
  try {
    const response = await fetch("/api/calc", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ expression }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Gagal menghitung ekspresi");
    }
    outputValue = data.result;
    expression = data.result;
    showToast("Perhitungan berhasil", "success");
    updateDisplay();
    await loadHistory();
  } catch (error) {
    showToast(resolveErrorMessage(error, "Terjadi kesalahan"), "error");
  }
}

function attachCalculatorListeners() {
  document.querySelectorAll("[data-insert]").forEach((button) => {
    button.addEventListener("click", () => {
      appendToExpression(button.dataset.insert);
    });
  });
  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const action = button.dataset.action;
      if (action === "clear") {
        clearExpression();
      } else if (action === "backspace") {
        backspaceExpression();
      } else if (action === "evaluate") {
        evaluateCurrentExpression();
      } else if (action === "negate") {
        negateExpression();
      }
    });
  });
  document.addEventListener("keydown", (event) => {
    if (event.key.match(/[0-9()+\-*/%.]/)) {
      appendToExpression(event.key);
    } else if (event.key === "Enter") {
      event.preventDefault();
      evaluateCurrentExpression();
    } else if (event.key === "Backspace") {
      backspaceExpression();
    } else if (event.key === "Escape") {
      clearExpression();
    }
  });
}

function attachMemoryControls() {
  document.querySelectorAll("[data-memory]").forEach((button) => {
    button.addEventListener("click", () => {
      const currentValue = parseFloat(outputValue);
      if (Number.isNaN(currentValue)) {
        showToast("Nilai tidak valid untuk memori", "error");
        return;
      }
      switch (button.dataset.memory) {
        case "save":
          memoryValue += currentValue;
          showToast("Memori ditambahkan", "info");
          break;
        case "subtract":
          memoryValue -= currentValue;
          showToast("Memori dikurangi", "info");
          break;
        case "recall":
          expression = memoryValue.toString();
          outputValue = expression;
          showToast("Memori dipanggil", "success");
          break;
        case "clear":
          memoryValue = 0;
          showToast("Memori dibersihkan", "info");
          break;
        case "toVault":
          pushMemoryToVault();
          return;
        default:
          break;
      }
      memoryDisplay.textContent = numberFormatter.format(memoryValue);
      updateDisplay();
    });
  });
}

async function loadHistory() {
  try {
    const response = await fetch("/api/history");
    const data = await response.json();
    renderHistory(data.history || []);
  } catch (error) {
    showToast("Gagal memuat histori", "error");
  }
}

function renderHistory(history) {
  historyListEl.innerHTML = "";
  if (!history.length) {
    historyListEl.innerHTML =
      '<p class="text-sm text-slate-400">Histori kosong. Hitung sesuatu!</p>';
    return;
  }
  history.forEach((item) => {
    const wrapper = document.createElement("article");
    wrapper.className =
      "rounded-xl border border-slate-700/60 bg-slate-900/70 p-3 text-sm shadow-inner";
    wrapper.innerHTML = `
      <div class="flex items-start justify-between gap-3">
        <div>
          <p class="text-xs uppercase tracking-wide text-slate-400">${formatTimestamp(
            item.created_at
          )}</p>
          <p class="mt-1 font-semibold text-cyan-200">${escapeHtml(
            item.expression
          )}</p>
          <p class="text-lg font-semibold text-white">${escapeHtml(
            item.result
          )}</p>
        </div>
        <button
          class="btn-mini"
          data-history-id="${item.id}"
          title="Hapus catatan"
        >
          ✕
        </button>
      </div>
    `;
    historyListEl.appendChild(wrapper);
  });
}

function attachHistoryControls() {
  document.querySelectorAll("[data-history]").forEach((button) => {
    button.addEventListener("click", async () => {
      if (button.dataset.history === "refresh") {
        await loadHistory();
      } else if (button.dataset.history === "clear") {
        await fetch("/api/history", { method: "DELETE" });
        await loadHistory();
        showToast("Histori dibersihkan", "info");
      }
    });
  });
  historyListEl.addEventListener("click", async (event) => {
    const target = event.target.closest("[data-history-id]");
    if (!target) return;
    const historyId = target.dataset.historyId;
    await fetch(`/api/history/${historyId}`, { method: "DELETE" });
    await loadHistory();
    showToast("Catatan histori dihapus", "info");
  });
}

function showToast(message, variant = "info") {
  const toast = document.createElement("div");
  toast.className = `${
    toastVariants[variant] || toastVariants.info
  } pointer-events-auto rounded-2xl px-4 py-3 text-sm font-semibold text-slate-900 shadow-lg shadow-slate-900/40`;
  toast.textContent = message;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.classList.add("opacity-0", "translate-y-2", "transition", "duration-500");
    setTimeout(() => toast.remove(), 500);
  }, 2800);
}

function escapeHtml(unsafe) {
  const safe = unsafe == null ? "" : String(unsafe);
  return safe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatTimestamp(timestamp) {
  if (!timestamp) return "";
  const date = new Date(timestamp);
  return new Intl.DateTimeFormat("id-ID", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

async function fetchVaultStatus() {
  try {
    const response = await fetch("/api/vault/status");
    const data = await response.json();
    updateVaultUI(data);
    return data;
  } catch (error) {
    showToast("Gagal memuat status vault", "error");
    return { configured: false, unlocked: false };
  }
}

function updateVaultUI(status) {
  if (!status.configured) {
    setVisibility(vaultSetupCard, true);
    setVisibility(vaultUnlockCard, false);
    setVisibility(vaultDashboard, false);
    updateStatusPill("Belum dikonfigurasi", "border-amber-400/60 text-amber-200");
  } else if (!status.unlocked) {
    setVisibility(vaultSetupCard, false);
    setVisibility(vaultUnlockCard, true);
    setVisibility(vaultDashboard, false);
    updateStatusPill("Terkunci", "border-emerald-400/60 text-emerald-200");
  } else {
    setVisibility(vaultSetupCard, false);
    setVisibility(vaultUnlockCard, false);
    setVisibility(vaultDashboard, true);
    updateStatusPill("Terbuka", "border-cyan-400/60 text-cyan-200");
    loadVaultEntries();
  }
}

function updateStatusPill(text, classes) {
  vaultStatusPill.textContent = text;
  vaultStatusPill.className = `rounded-full px-3 py-1 text-xs uppercase tracking-wide ${classes}`;
}

function setVisibility(element, shouldShow) {
  if (!element) return;
  element.classList.toggle("hidden", !shouldShow);
}

if (setupForm) {
  setupForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(setupForm);
    const password = formData.get("password");
    const confirm = formData.get("confirm");
    if (password !== confirm) {
      showToast("Password dan konfirmasi tidak sama", "error");
      return;
    }
    try {
      const response = await fetch("/api/vault/setup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Gagal menyimpan password");
      }
      setupForm.reset();
      showToast("Vault berhasil dikonfigurasi", "success");
      await fetchVaultStatus();
  } catch (error) {
    showToast(resolveErrorMessage(error, "Terjadi kesalahan"), "error");
  }
});
}

if (unlockForm) {
  unlockForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(unlockForm);
    const password = formData.get("password");
    try {
      const response = await fetch("/api/vault/unlock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Password salah");
      }
      unlockForm.reset();
      showToast("Vault terbuka", "success");
      await fetchVaultStatus();
  } catch (error) {
    showToast(resolveErrorMessage(error, "Terjadi kesalahan"), "error");
  }
});
}

if (entryForm) {
  entryForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(entryForm);
    const payload = {
      title: formData.get("title"),
      content: formData.get("content"),
    };
    const url = editingEntryId
      ? `/api/vault/entries/${editingEntryId}`
      : "/api/vault/entries";
    const method = editingEntryId ? "PUT" : "POST";
    try {
      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.error || "Gagal menyimpan entri");
      }
      showToast(data.message || "Data vault tersimpan", "success");
      entryForm.reset();
      cancelEditing();
      await loadVaultEntries();
    } catch (error) {
      showToast(resolveErrorMessage(error, "Terjadi kesalahan"), "error");
    }
  });
}

if (entryCancelBtn) {
  entryCancelBtn.addEventListener("click", (event) => {
    event.preventDefault();
    cancelEditing();
  });
}

function cancelEditing() {
  editingEntryId = null;
  setVisibility(entryCancelBtn, false);
  if (entryCancelBtn) {
    entryCancelBtn.classList.remove("flex", "items-center", "justify-center");
    entryCancelBtn.classList.add("hidden");
  }
  if (entryEditIndicator) {
    entryEditIndicator.classList.add("hidden");
    entryEditIndicator.textContent = "";
  }
  entryForm?.reset();
}

async function loadVaultEntries() {
  try {
    const response = await fetch("/api/vault/entries");
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Vault terkunci");
    }
    renderVaultEntries(data.entries || []);
  } catch (error) {
    const message = resolveErrorMessage(error, "Gagal memuat data vault");
    if (message.toLowerCase().includes("locked")) {
      showToast("Vault masih terkunci", "error");
    } else {
      showToast(message, "error");
    }
  }
}

function renderVaultEntries(entries) {
  cachedVaultEntries = entries;
  vaultEntriesEl.innerHTML = "";
  if (!entries.length) {
    vaultEntriesEl.innerHTML =
      '<p class="text-sm text-slate-400">Belum ada data. Tambahkan catatan rahasia pertama Anda.</p>';
    return;
  }
  entries.forEach((entry) => {
    const article = document.createElement("article");
    article.className =
      "group rounded-2xl border border-slate-700/60 bg-slate-900/70 p-4 transition hover:border-cyan-400/50";
    article.innerHTML = `
      <div class="flex items-start justify-between gap-3">
        <div>
          <h4 class="text-lg font-semibold text-white">${escapeHtml(entry.title)}</h4>
          <p class="mt-1 text-sm text-slate-300 whitespace-pre-wrap">${escapeHtml(
            entry.content
          )}</p>
          <p class="mt-2 text-xs uppercase tracking-wide text-slate-500">
            Dibuat: ${formatTimestamp(entry.created_at)} · Diperbarui: ${formatTimestamp(
      entry.updated_at
    )}
          </p>
        </div>
        <div class="flex flex-col gap-2">
          <button class="btn-mini" data-entry-edit="${entry.id}">Edit</button>
          <button class="btn-mini" data-entry-delete="${entry.id}">Hapus</button>
        </div>
      </div>
    `;
    vaultEntriesEl.appendChild(article);
  });
}

vaultEntriesEl.addEventListener("click", async (event) => {
  const editBtn = event.target.closest("[data-entry-edit]");
  const deleteBtn = event.target.closest("[data-entry-delete]");
  if (editBtn) {
    const entryId = Number(editBtn.dataset.entryEdit);
    const targetEntry = cachedVaultEntries.find((item) => item.id === entryId);
    if (targetEntry) {
      editingEntryId = targetEntry.id;
      entryForm.querySelector('[name="title"]').value = targetEntry.title;
      entryForm.querySelector('[name="content"]').value = targetEntry.content;
      if (entryEditIndicator) {
        entryEditIndicator.textContent = `Mengedit \"${targetEntry.title}\"`;
        entryEditIndicator.classList.remove("hidden");
      }
      if (entryCancelBtn) {
        setVisibility(entryCancelBtn, true);
        entryCancelBtn.classList.remove("hidden");
        entryCancelBtn.classList.add("flex", "items-center", "justify-center");
      }
      showToast("Mode edit aktif", "info");
    }
  } else if (deleteBtn) {
    const entryId = deleteBtn.dataset.entryDelete;
    const confirmed = confirm("Hapus catatan ini dari vault?");
    if (!confirmed) return;
    await fetch(`/api/vault/entries/${entryId}`, { method: "DELETE" });
    showToast("Catatan dihapus", "info");
    await loadVaultEntries();
  }
});

function pushMemoryToVault() {
  if (vaultDashboard.classList.contains("hidden")) {
    showToast("Buka vault terlebih dahulu", "error");
    return;
  }
  if (!entryForm) return;
  entryForm.querySelector('[name="title"]').value = `Snapshot Memori ${new Date().toLocaleString("id-ID")}`;
  entryForm.querySelector('[name="content"]').value = `Nilai memori kalkulator: ${memoryValue}`;
  showToast("Memori siap disimpan, tekan Simpan ke Vault", "info");
}

function attachVaultControls() {
  document.querySelectorAll("[data-vault]").forEach((button) => {
    button.addEventListener("click", async () => {
      const action = button.dataset.vault;
      if (action === "lock") {
        await fetch("/api/vault/lock", { method: "POST" });
        cancelEditing();
        await fetchVaultStatus();
        showToast("Vault dikunci", "info");
      } else if (action === "refresh") {
        await loadVaultEntries();
      }
    });
  });
}

function resolveErrorMessage(error, fallback) {
  if (error && typeof error === "object" && "message" in error) {
    const message = error.message;
    if (typeof message === "string" && message.trim()) {
      return message;
    }
  }
  if (typeof error === "string" && error.trim()) {
    return error;
  }
  return fallback;
}

async function bootstrap() {
  updateDisplay();
  attachCalculatorListeners();
  attachHistoryControls();
  attachMemoryControls();
  attachVaultControls();
  await loadHistory();
  await fetchVaultStatus();
}

bootstrap();
