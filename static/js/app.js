/* ============================================
   FLOWZEN ERP - GLOBAL JAVASCRIPT UTILITIES
   ============================================ */

// Theme Management
const themeToggle = document.getElementById('themeToggle');
if (themeToggle) {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Update icon
    const sunIcon = themeToggle.querySelector('.fa-sun');
    const moonIcon = themeToggle.querySelector('.fa-moon');
    if (sunIcon && moonIcon) {
        if (savedTheme === 'dark') {
            sunIcon.style.display = 'none';
            moonIcon.style.display = 'inline-block';
            themeToggle.querySelector('span').textContent = 'Light Mode';
        } else {
            sunIcon.style.display = 'inline-block';
            moonIcon.style.display = 'none';
            themeToggle.querySelector('span').textContent = 'Dark Mode';
        }
    }
    
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        if (sunIcon && moonIcon) {
            if (newTheme === 'dark') {
                sunIcon.style.display = 'none';
                moonIcon.style.display = 'inline-block';
                themeToggle.querySelector('span').textContent = 'Light Mode';
            } else {
                sunIcon.style.display = 'inline-block';
                moonIcon.style.display = 'none';
                themeToggle.querySelector('span').textContent = 'Dark Mode';
            }
        }
    });
}

// Modal Functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('open');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('open');
        document.body.style.overflow = '';
    }
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
    if (e.target.classList && e.target.classList.contains('modal-overlay')) {
        closeModal(e.target.id);
    }
});

// Toast Notification
function toast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${type === 'success' ? '✓' : type === 'error' ? '✕' : '⚠'}</span><span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.25s ease forwards';
        setTimeout(() => toast.remove(), 250);
    }, 3500);
}

// Escape HTML
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// Format Currency
function formatCurrency(value, currency = 'TND') {
    return new Intl.NumberFormat('fr-TN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value || 0) + ` ${currency}`;
}

// Format Date
function formatDate(dateString) {
    if (!dateString) return '—';
    return new Date(dateString).toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
}

// Get Initials
function getInitials(name) {
    if (!name) return '?';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

// Export to window
window.openModal = openModal;
window.closeModal = closeModal;
window.toast = toast;
window.escapeHtml = escapeHtml;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.getInitials = getInitials;