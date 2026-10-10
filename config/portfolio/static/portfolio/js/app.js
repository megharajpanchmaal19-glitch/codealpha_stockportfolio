/**
 * app.js — Stock Portfolio Tracker frontend logic.
 *
 * Uses plain fetch() — no external libraries.
 * CSRF token is read from the Django cookie and sent as a request header.
 * All monetary calculations are ONLY displayed from backend JSON responses;
 * the frontend never performs authoritative financial arithmetic.
 */

'use strict';

// ─────────────────────────────────────────────────────────────────
// Utility helpers
// ─────────────────────────────────────────────────────────────────

/** Read the Django CSRF token from the cookie. */
function getCsrfToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : '';
}

/** Format a numeric string as USD currency. */
function formatUSD(value) {
  return '$' + parseFloat(value).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/** Show an element (remove 'hidden' class). */
function show(el) { el.classList.remove('hidden'); }

/** Hide an element (add 'hidden' class). */
function hide(el) { el.classList.add('hidden'); }

/**
 * Display a status message inside a message container element.
 * @param {HTMLElement} el  - The message div
 * @param {string} text     - Message text
 * @param {'success'|'error'} type
 * @param {number} [duration] - Auto-hide after ms (0 = persistent)
 */
function showMessage(el, text, type, duration = 4000) {
  el.textContent = text;
  el.className = `form-message ${type}`;
  show(el);
  if (duration > 0) {
    setTimeout(() => { hide(el); }, duration);
  }
}

// ─────────────────────────────────────────────────────────────────
// DOM references
// ─────────────────────────────────────────────────────────────────

const form             = document.getElementById('add-stock-form');
const symbolSelect     = document.getElementById('stock-symbol');
const priceDisplay     = document.getElementById('stock-price-display');
const quantityInput    = document.getElementById('quantity');
const investPreview    = document.getElementById('investment-preview');
const addBtn           = document.getElementById('add-btn');
const refreshBtn       = document.getElementById('refresh-btn');
const formMessage      = document.getElementById('form-message');
const loadingEl        = document.getElementById('loading');

const navTotalStocks   = document.getElementById('nav-total-stocks');
const totalInvestment  = document.getElementById('total-investment');
const totalStocksEl    = document.getElementById('total-stocks');
const totalQuantityEl  = document.getElementById('total-quantity');

const emptyState       = document.getElementById('empty-state');
const tableWrapper     = document.getElementById('table-wrapper');
const holdingsTbody    = document.getElementById('holdings-tbody');
const tableTotal       = document.getElementById('table-total');

const editModal        = document.getElementById('edit-modal');
const modalTitle       = document.getElementById('modal-title');
const modalSymbolLabel = document.getElementById('modal-symbol-label');
const modalQuantity    = document.getElementById('modal-quantity');
const modalSaveBtn     = document.getElementById('modal-save-btn');
const modalCancelBtn   = document.getElementById('modal-cancel-btn');
const modalMessage     = document.getElementById('modal-message');

// ─────────────────────────────────────────────────────────────────
// Form interactions — price display & investment preview
// ─────────────────────────────────────────────────────────────────

symbolSelect.addEventListener('change', updatePriceAndPreview);
quantityInput.addEventListener('input', updatePriceAndPreview);

function updatePriceAndPreview() {
  const selectedOption = symbolSelect.options[symbolSelect.selectedIndex];
  const price = selectedOption ? selectedOption.dataset.price : null;

  if (price && parseFloat(price) > 0) {
    priceDisplay.value = formatUSD(price);
  } else {
    priceDisplay.value = '';
  }

  const qty = parseInt(quantityInput.value, 10);
  if (price && qty > 0 && Number.isInteger(qty)) {
    investPreview.value = formatUSD(parseFloat(price) * qty);
  } else {
    investPreview.value = '—';
  }
}

// ─────────────────────────────────────────────────────────────────
// Add stock — form submit
// ─────────────────────────────────────────────────────────────────

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  hide(formMessage);

  const symbol = symbolSelect.value.trim();
  const qtyRaw = quantityInput.value.trim();

  // Client-side pre-validation (backend validates authoritatively)
  if (!symbol) {
    showMessage(formMessage, 'Please select a stock symbol.', 'error');
    return;
  }
  if (!qtyRaw || isNaN(qtyRaw) || parseInt(qtyRaw, 10) <= 0 || qtyRaw.includes('.')) {
    showMessage(formMessage, 'Quantity must be a positive whole number.', 'error');
    return;
  }

  show(loadingEl);
  addBtn.disabled = true;

  try {
    const response = await fetch('/api/portfolio/', {
      method:  'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken':  getCsrfToken(),
      },
      body: JSON.stringify({
        stock_symbol: symbol,
        quantity:     parseInt(qtyRaw, 10),
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      showMessage(formMessage, data.error || 'An error occurred.', 'error');
      return;
    }

    showMessage(formMessage, data.message, 'success');
    form.reset();
    priceDisplay.value  = '';
    investPreview.value = '—';
    await loadPortfolio();

  } catch (err) {
    showMessage(formMessage, 'Network error. Please check your connection.', 'error');
    console.error(err);
  } finally {
    hide(loadingEl);
    addBtn.disabled = false;
  }
});

// ─────────────────────────────────────────────────────────────────
// Load & render portfolio
// ─────────────────────────────────────────────────────────────────

async function loadPortfolio() {
  try {
    const response = await fetch('/api/portfolio/');
    if (!response.ok) throw new Error('Failed to load portfolio');
    const data = await response.json();
    renderPortfolio(data);
  } catch (err) {
    console.error('loadPortfolio error:', err);
    showMessage(formMessage, 'Could not load portfolio. Is the server running?', 'error', 0);
  }
}

function renderPortfolio(data) {
  const { holdings, total_investment, total_stocks, total_quantity } = data;

  // Summary cards
  totalInvestment.textContent = formatUSD(total_investment);
  totalStocksEl.textContent   = total_stocks;
  totalQuantityEl.textContent = total_quantity;
  navTotalStocks.textContent  = `${total_stocks} stock${total_stocks !== 1 ? 's' : ''}`;

  // Table footer total
  tableTotal.textContent = formatUSD(total_investment);

  // Empty / filled state
  if (holdings.length === 0) {
    show(emptyState);
    hide(tableWrapper);
    return;
  }

  hide(emptyState);
  show(tableWrapper);

  // Build table rows
  holdingsTbody.innerHTML = '';
  holdings.forEach((h, idx) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${idx + 1}</td>
      <td><span class="symbol-badge">${escHtml(h.stock_symbol)}</span></td>
      <td>${escHtml(h.company_name)}</td>
      <td>${formatUSD(h.stock_price)}</td>
      <td>${h.quantity.toLocaleString()}</td>
      <td class="inv-value">${formatUSD(h.investment_value)}</td>
      <td>${escHtml(h.created_at)}</td>
      <td class="actions-cell">
        <button
          class="btn btn-edit"
          data-id="${h.id}"
          data-symbol="${escHtml(h.stock_symbol)}"
          data-qty="${h.quantity}"
          aria-label="Edit ${escHtml(h.stock_symbol)}"
        >✏ Edit</button>
        <button
          class="btn btn-del"
          data-id="${h.id}"
          data-symbol="${escHtml(h.stock_symbol)}"
          aria-label="Delete ${escHtml(h.stock_symbol)}"
        >✕ Delete</button>
      </td>
    `;
    holdingsTbody.appendChild(tr);
  });

  // Wire edit / delete buttons
  holdingsTbody.querySelectorAll('.btn-edit').forEach(btn => {
    btn.addEventListener('click', () => openEditModal(
      parseInt(btn.dataset.id, 10),
      btn.dataset.symbol,
      parseInt(btn.dataset.qty, 10),
    ));
  });

  holdingsTbody.querySelectorAll('.btn-del').forEach(btn => {
    btn.addEventListener('click', () => confirmDelete(
      parseInt(btn.dataset.id, 10),
      btn.dataset.symbol,
    ));
  });
}

/** Simple HTML escaping to prevent XSS in table cells. */
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ─────────────────────────────────────────────────────────────────
// Delete holding
// ─────────────────────────────────────────────────────────────────

async function confirmDelete(holdingId, symbol) {
  const ok = confirm(
    `Delete holding for ${symbol}?\n\nThis action cannot be undone.`
  );
  if (!ok) return;

  try {
    const response = await fetch(`/api/portfolio/${holdingId}/`, {
      method:  'DELETE',
      headers: { 'X-CSRFToken': getCsrfToken() },
    });
    const data = await response.json();
    if (!response.ok) {
      showMessage(formMessage, data.error || 'Delete failed.', 'error');
      return;
    }
    showMessage(formMessage, data.message, 'success');
    await loadPortfolio();
  } catch (err) {
    showMessage(formMessage, 'Network error during delete.', 'error');
    console.error(err);
  }
}

// ─────────────────────────────────────────────────────────────────
// Edit holding (modal)
// ─────────────────────────────────────────────────────────────────

let _activeEditId = null;

function openEditModal(holdingId, symbol, currentQty) {
  _activeEditId       = holdingId;
  modalTitle.textContent      = 'Update Quantity';
  modalSymbolLabel.textContent = `Editing: ${symbol} (current qty: ${currentQty})`;
  modalQuantity.value          = currentQty;
  hide(modalMessage);
  show(editModal);
  modalQuantity.focus();
}

function closeEditModal() {
  hide(editModal);
  _activeEditId = null;
}

modalCancelBtn.addEventListener('click', closeEditModal);

// Close on overlay click
editModal.addEventListener('click', (e) => {
  if (e.target === editModal) closeEditModal();
});

// Close on Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && !editModal.classList.contains('hidden')) {
    closeEditModal();
  }
});

modalSaveBtn.addEventListener('click', async () => {
  const qtyRaw = modalQuantity.value.trim();

  if (!qtyRaw || isNaN(qtyRaw) || parseInt(qtyRaw, 10) <= 0 || qtyRaw.includes('.')) {
    showMessage(modalMessage, 'Please enter a positive whole number.', 'error', 0);
    return;
  }

  modalSaveBtn.disabled = true;
  hide(modalMessage);

  try {
    const response = await fetch(`/api/portfolio/${_activeEditId}/`, {
      method:  'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken':  getCsrfToken(),
      },
      body: JSON.stringify({ quantity: parseInt(qtyRaw, 10) }),
    });

    const data = await response.json();

    if (!response.ok) {
      showMessage(modalMessage, data.error || 'Update failed.', 'error', 0);
      return;
    }

    closeEditModal();
    showMessage(formMessage, data.message, 'success');
    await loadPortfolio();

  } catch (err) {
    showMessage(modalMessage, 'Network error during update.', 'error', 0);
    console.error(err);
  } finally {
    modalSaveBtn.disabled = false;
  }
});

// ─────────────────────────────────────────────────────────────────
// Refresh button
// ─────────────────────────────────────────────────────────────────

refreshBtn.addEventListener('click', async () => {
  refreshBtn.disabled = true;
  refreshBtn.textContent = '↺ Refreshing…';
  await loadPortfolio();
  refreshBtn.disabled = false;
  refreshBtn.textContent = '↺ Refresh Portfolio';
});

// ─────────────────────────────────────────────────────────────────
// Initial load
// ─────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', loadPortfolio);
