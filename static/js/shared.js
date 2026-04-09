/**
 * SBB Weichenheizung - Shared JavaScript Functions
 * Gemeinsame Funktionen für alle Seiten
 */

// ===== Fetch Helper mit Status-Anzeige =====
async function fetchWithStatus(url, options = {}) {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

// ===== Auto-Save Status Anzeige (für einfache inline Status) =====
function showInlineSaveStatus(elementId, status) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.classList.remove('saving', 'saved', 'error');
    element.classList.add(status);

    if (status === 'saved') {
        element.textContent = '✓ Gespeichert';
        setTimeout(() => {
            element.textContent = '';
            element.classList.remove('saved');
        }, 2000);
    } else if (status === 'saving') {
        element.textContent = 'Speichern...';
    } else if (status === 'error') {
        element.textContent = '✗ Fehler beim Speichern';
    }
}

// ===== Auto-Save Popup Status Anzeige =====
let _saveStatusTimeout = null;

function showSaveStatus(status, message = '') {
    const statusElement = document.getElementById('save-status');

    if (!statusElement) {
        console.warn('save-status Element nicht gefunden');
        return;
    }

    if (_saveStatusTimeout) {
        clearTimeout(_saveStatusTimeout);
    }

    // Entferne alle Status-Klassen
    statusElement.classList.remove('saving', 'saved', 'error');

    if (status === 'saving') {
        statusElement.classList.add('saving');
        statusElement.innerHTML = '💾 Speichert...';
        statusElement.style.display = 'block';
    } else if (status === 'saved') {
        statusElement.classList.add('saved');
        const displayMessage = message || 'Gespeichert';
        statusElement.innerHTML = `✓ ${displayMessage}`;
        statusElement.style.display = 'block';

        _saveStatusTimeout = setTimeout(() => {
            statusElement.style.display = 'none';
        }, 2000);
    } else if (status === 'error') {
        statusElement.classList.add('error');
        statusElement.innerHTML = `⚠ Fehler: ${message}`;
        statusElement.style.display = 'block';

        _saveStatusTimeout = setTimeout(() => {
            statusElement.style.display = 'none';
        }, 5000);
    }
}

// ===== Debounce Funktion =====
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ===== Live-Suche =====
function initLiveSearch(inputId, itemSelector, textSelector = null) {
    const searchInput = document.getElementById(inputId);
    if (!searchInput) return;

    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const items = document.querySelectorAll(itemSelector);

        items.forEach(item => {
            const text = textSelector
                ? (item.querySelector(textSelector)?.textContent.toLowerCase() || '')
                : item.textContent.toLowerCase();
            item.style.display = text.includes(searchTerm) ? '' : 'none';
        });
    });
}

// ===== Modal Funktionen =====
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// ===== Checkbox Radio-Verhalten =====
// Wenn eine Checkbox in einer Gruppe aktiviert wird, andere deaktivieren
function handleCheckboxRadio(checkbox, otherCheckboxId) {
    if (checkbox.checked) {
        const other = document.getElementById(otherCheckboxId);
        if (other) other.checked = false;
    }
}

// ===== Row Highlight basierend auf Checkbox-Status =====
function updateRowHighlight(row, checkedClass, uncheckedClass) {
    row.classList.remove('row-success', 'row-muted');
    if (checkedClass) {
        row.classList.add(checkedClass);
    }
}

// ===== Format Datum/Zeit =====
function formatDateTime(date) {
    if (!date) return '';
    const d = new Date(date);
    return d.toLocaleDateString('de-CH') + ' ' + d.toLocaleTimeString('de-CH', {hour: '2-digit', minute: '2-digit'});
}

// ===== Console Log für Debug =====
const DEBUG = false;
function debugLog(...args) {
    if (DEBUG) console.log('[DEBUG]', ...args);
}

console.log('shared.js loaded');
