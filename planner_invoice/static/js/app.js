const state = {
  schedule: [],
  items: [],
  meta: {
    invoiceNumber: "",
    issueDate: "",
    dueDate: "",
    clientName: "",
    clientEmail: "",
    clientAddress: "",
    taxRate: 11,
    discountRate: 0,
  },
};

const scheduleForm = document.getElementById("schedule-form");
const scheduleTableBody = document.querySelector("#schedule-table tbody");
const schedulePreviewList = document.getElementById("schedule-preview");
const clearScheduleBtn = document.getElementById("clear-schedule");

const invoiceMetaForm = document.getElementById("invoice-meta");
const previewClient = document.getElementById("preview-client");
const previewNumber = document.getElementById("preview-number");
const previewIssue = document.getElementById("preview-issue");
const previewDue = document.getElementById("preview-due");

const itemForm = document.getElementById("item-form");
const itemsTableBody = document.querySelector("#items-table tbody");
const previewItemsBody = document.getElementById("preview-items");
const clearItemsBtn = document.getElementById("clear-items");

const subtotalCell = document.getElementById("subtotal");
const discountCell = document.getElementById("discount");
const taxCell = document.getElementById("tax");
const grandTotalCell = document.getElementById("grand-total");

const previewSubtotal = document.getElementById("preview-subtotal");
const previewDiscount = document.getElementById("preview-discount");
const previewTax = document.getElementById("preview-tax");
const previewGrand = document.getElementById("preview-grand");

const qrContainer = document.getElementById("qr-code");
let qrInstance = null;

const downloadPdfBtn = document.getElementById("download-pdf");
const downloadRawBtn = document.getElementById("download-raw");
const previewArea = document.getElementById("preview-area");

function formatCurrency(value) {
  return `Rp${Number(value || 0).toLocaleString("id-ID", {
    minimumFractionDigits: 0,
  })}`;
}

function formatDate(value) {
  if (!value) return "-";
  return dayjs(value).format("DD MMM YYYY");
}

function formatTime(value) {
  return value ? dayjs(`2000-01-01T${value}`).format("HH:mm") : "-";
}

function updateScheduleTable() {
  scheduleTableBody.innerHTML = "";
  schedulePreviewList.innerHTML = "";

  const sorted = [...state.schedule].sort((a, b) => {
    if (a.date === b.date) {
      return a.time.localeCompare(b.time);
    }
    return a.date.localeCompare(b.date);
  });

  sorted.forEach((entry) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${formatDate(entry.date)}</td>
      <td>${formatTime(entry.time)}</td>
      <td>${entry.activity}</td>
      <td>${entry.location || "-"}</td>
      <td>${entry.notes || "-"}</td>`;
    scheduleTableBody.appendChild(row);

    const listItem = document.createElement("li");
    listItem.innerHTML = `
      <strong>${formatDate(entry.date)} • ${formatTime(entry.time)}</strong>
      <span>${entry.activity}</span>
      ${entry.location ? `<small>Lokasi: ${entry.location}</small>` : ""}
      ${entry.notes ? `<small>Catatan: ${entry.notes}</small>` : ""}
    `;
    schedulePreviewList.appendChild(listItem);
  });

  if (!sorted.length) {
    const emptyRow = document.createElement("tr");
    emptyRow.innerHTML = `<td colspan="5" style="text-align:center;color:var(--muted)">Belum ada agenda</td>`;
    scheduleTableBody.appendChild(emptyRow);

    const emptyPreview = document.createElement("li");
    emptyPreview.textContent = "Belum ada agenda yang ditambahkan.";
    emptyPreview.style.color = "var(--muted)";
    schedulePreviewList.appendChild(emptyPreview);
  }
}

function calculateTotals() {
  const subtotal = state.items.reduce(
    (total, item) => total + item.quantity * item.rate,
    0,
  );
  const discount = subtotal * ((Number(state.meta.discountRate) || 0) / 100);
  const taxedBase = subtotal - discount;
  const tax = taxedBase * ((Number(state.meta.taxRate) || 0) / 100);
  const grand = taxedBase + tax;
  return { subtotal, discount, tax, grand };
}

function updateItemsTable() {
  itemsTableBody.innerHTML = "";
  previewItemsBody.innerHTML = "";

  state.items.forEach((item) => {
    const subtotal = item.quantity * item.rate;
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${item.description}</td>
      <td>${item.quantity}</td>
      <td>${formatCurrency(item.rate)}</td>
      <td>${formatCurrency(subtotal)}</td>`;
    itemsTableBody.appendChild(row);

    const previewRow = row.cloneNode(true);
    previewItemsBody.appendChild(previewRow);
  });

  if (!state.items.length) {
    const emptyRow = document.createElement("tr");
    emptyRow.innerHTML = `<td colspan="4" style="text-align:center;color:var(--muted)">Belum ada item</td>`;
    itemsTableBody.appendChild(emptyRow);

    const emptyPreview = document.createElement("tr");
    emptyPreview.innerHTML = `<td colspan="4" style="text-align:center;color:var(--muted)">Tambahkan item untuk menampilkan invoice.</td>`;
    previewItemsBody.appendChild(emptyPreview);
  }

  const totals = calculateTotals();
  subtotalCell.textContent = formatCurrency(totals.subtotal);
  discountCell.textContent = formatCurrency(totals.discount);
  taxCell.textContent = formatCurrency(totals.tax);
  grandTotalCell.textContent = formatCurrency(totals.grand);

  previewSubtotal.textContent = formatCurrency(totals.subtotal);
  previewDiscount.textContent = formatCurrency(totals.discount);
  previewTax.textContent = formatCurrency(totals.tax);
  previewGrand.textContent = formatCurrency(totals.grand);

  updateQRCode();
}

function syncMetaPreview() {
  const {
    invoiceNumber,
    issueDate,
    dueDate,
    clientName,
    clientEmail,
    clientAddress,
  } = state.meta;

  previewNumber.textContent = invoiceNumber || "INV-XXXX";
  previewIssue.textContent = formatDate(issueDate);
  previewDue.textContent = formatDate(dueDate);

  const clientLines = [clientName, clientEmail, clientAddress]
    .filter(Boolean)
    .join(" • ");
  previewClient.textContent = clientLines || "Isi detail klien untuk menampilkan informasi";

  updateQRCode();
}

function updateQRCode() {
  const totals = calculateTotals();
  const payload = {
    invoice: state.meta.invoiceNumber || "INV-DRAFT",
    client: state.meta.clientName || "",
    due: state.meta.dueDate || "",
    total: totals.grand,
    items: state.items.map((item) => ({
      description: item.description,
      quantity: item.quantity,
      rate: item.rate,
    })),
  };

  if (qrInstance) {
    qrInstance.clear();
    qrInstance.makeCode(JSON.stringify(payload));
  } else {
    qrInstance = new QRCode(qrContainer, {
      text: JSON.stringify(payload),
      width: 180,
      height: 180,
      colorDark: "#0ea5e9",
      colorLight: "#ffffff",
      correctLevel: QRCode.CorrectLevel.M,
    });
  }
}

scheduleForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const formData = new FormData(scheduleForm);
  const entry = {
    date: formData.get("date"),
    time: formData.get("time"),
    activity: formData.get("activity"),
    location: formData.get("location"),
    notes: formData.get("notes"),
  };
  state.schedule.push(entry);
  scheduleForm.reset();
  updateScheduleTable();
});

clearScheduleBtn.addEventListener("click", () => {
  if (state.schedule.length && confirm("Hapus semua agenda?")) {
    state.schedule = [];
    updateScheduleTable();
  }
});

invoiceMetaForm.addEventListener("input", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement)) {
    return;
  }
  state.meta[target.name] = target.value;
  if (target.name === "taxRate" || target.name === "discountRate") {
    updateItemsTable();
  }
  syncMetaPreview();
});

itemForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const formData = new FormData(itemForm);
  const quantity = Number(formData.get("quantity"));
  const rate = Number(formData.get("rate"));
  state.items.push({
    description: formData.get("description"),
    quantity,
    rate,
  });
  itemForm.reset();
  itemForm.querySelector('input[name="quantity"]').value = "1";
  itemForm.querySelector('input[name="rate"]').value = "150000";
  updateItemsTable();
});

clearItemsBtn.addEventListener("click", () => {
  if (state.items.length && confirm("Hapus semua item invoice?")) {
    state.items = [];
    updateItemsTable();
  }
});

async function downloadPdf() {
  const { jsPDF } = window.jspdf;
  const canvas = await html2canvas(previewArea, {
    scale: 2,
    backgroundColor: "#0f172a",
    useCORS: true,
  });
  const imageData = canvas.toDataURL("image/png");
  const pdf = new jsPDF("p", "pt", "a4");
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const ratio = Math.min(pageWidth / canvas.width, pageHeight / canvas.height);
  const imgWidth = canvas.width * ratio;
  const imgHeight = canvas.height * ratio;
  pdf.addImage(imageData, "PNG", (pageWidth - imgWidth) / 2, 20, imgWidth, imgHeight);
  const fileName = state.meta.invoiceNumber ? `${state.meta.invoiceNumber}.pdf` : "invoice.pdf";
  pdf.save(fileName);
}

downloadPdfBtn.addEventListener("click", () => {
  downloadPdf().catch((error) => {
    console.error("Gagal membuat PDF", error);
    alert("Terjadi kesalahan saat membuat PDF. Silakan coba lagi.");
  });
});

downloadRawBtn.addEventListener("click", () => {
  const totals = calculateTotals();
  const payload = {
    generatedAt: new Date().toISOString(),
    schedule: state.schedule,
    invoice: {
      meta: state.meta,
      items: state.items,
      totals,
    },
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = state.meta.invoiceNumber ? `${state.meta.invoiceNumber}.json` : "invoice-data.json";
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
});

updateScheduleTable();
updateItemsTable();
syncMetaPreview();
