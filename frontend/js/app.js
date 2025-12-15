/**
 * Таможенный калькулятор - Frontend JavaScript
 */

const API_BASE = '/api';

// DOM Elements
const form = document.getElementById('calculatorForm');
const codeInput = document.getElementById('tnvedCode');
const autocompleteList = document.getElementById('codeAutocomplete');
const resultsDiv = document.getElementById('results');
const errorDiv = document.getElementById('error');
const submitBtn = form.querySelector('button[type="submit"]');

// Debounce helper
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

// Format number with spaces
function formatNumber(num, decimals = 0) {
    return num.toLocaleString('ru-RU', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

// Show error message
function showError(message) {
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
    resultsDiv.classList.add('hidden');
}

// Hide error
function hideError() {
    errorDiv.classList.add('hidden');
}

// Search TN VED codes
async function searchCodes(query) {
    if (query.length < 2) {
        autocompleteList.classList.remove('active');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}&limit=10`);
        const data = await response.json();

        if (data.results && data.results.length > 0) {
            autocompleteList.innerHTML = data.results.map(item => `
                <div class="autocomplete-item" data-code="${item.code}">
                    <div class="code">${item.code}</div>
                    <div class="desc">${item.description}</div>
                </div>
            `).join('');
            autocompleteList.classList.add('active');
        } else {
            autocompleteList.classList.remove('active');
        }
    } catch (error) {
        console.error('Search error:', error);
        autocompleteList.classList.remove('active');
    }
}

// Handle autocomplete item click
function handleAutocompleteClick(event) {
    const item = event.target.closest('.autocomplete-item');
    if (item) {
        codeInput.value = item.dataset.code;
        autocompleteList.classList.remove('active');
    }
}

// Calculate customs payments
async function calculate(formData) {
    const requestBody = {
        code: formData.get('code'),
        price: parseFloat(formData.get('price')),
        currency: formData.get('currency'),
    };

    // Optional fields
    const weight = formData.get('weight');
    if (weight) requestBody.weight = parseFloat(weight);

    const quantity = formData.get('quantity');
    if (quantity) requestBody.quantity = parseInt(quantity);

    const deliveryCost = formData.get('delivery_cost');
    if (deliveryCost) requestBody.delivery_cost = parseFloat(deliveryCost);

    const insuranceCost = formData.get('insurance_cost');
    if (insuranceCost) requestBody.insurance_cost = parseFloat(insuranceCost);

    const countryOrigin = formData.get('country_origin');
    if (countryOrigin) requestBody.country_origin = countryOrigin;

    requestBody.has_origin_certificate = formData.get('has_origin_certificate') === 'on';

    try {
        const response = await fetch(`${API_BASE}/calculate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Ошибка расчета');
        }

        return await response.json();
    } catch (error) {
        throw error;
    }
}

// Display results in the new compact format
function displayResults(data) {
    // Basic info
    document.getElementById('resultCode').textContent = data.tn_ved_code;
    document.getElementById('resultDescription').textContent = data.tn_ved_description;
    document.getElementById('resultTradeRegime').textContent = data.trade_regime;

    // Map payment types to display elements
    const paymentMap = {
        'customs_duty': { el: 'customsDuty', block: 'customsDutyBlock', label: 'Таможенная пошлина' },
        'excise': { el: 'excise', block: 'exciseBlock', label: 'Акциз' },
        'vat': { el: 'vat', block: 'vatBlock', label: 'НДС' },
        'customs_fee': { el: 'customsFee', block: 'customsFeeBlock', label: 'Сбор за оформление' }
    };

    // Reset all values
    Object.values(paymentMap).forEach(({ el, block }) => {
        document.getElementById(el).textContent = '-';
        document.getElementById(block).style.display = 'block';
    });

    // Update payment values
    data.payments.forEach(payment => {
        const mapping = paymentMap[payment.type];
        if (mapping) {
            const valueEl = document.getElementById(mapping.el);
            valueEl.textContent = `${formatNumber(payment.amount_uzs)} сум`;
        }
    });

    // Totals
    document.getElementById('totalUzs').textContent = `${formatNumber(data.total_uzs)} сум`;
    document.getElementById('totalUsd').textContent = `≈ ${formatNumber(data.total_usd, 2)} USD`;

    // Notes
    const notesDiv = document.getElementById('resultNotes');
    if (data.notes) {
        notesDiv.textContent = data.notes;
        notesDiv.classList.remove('hidden');
    } else {
        notesDiv.classList.add('hidden');
    }

    // Show results
    resultsDiv.classList.remove('hidden');

    // Scroll to results
    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Form submit handler
async function handleSubmit(event) {
    event.preventDefault();
    hideError();

    const formData = new FormData(form);

    // Validate code
    const code = formData.get('code');
    if (!code || code.length < 4) {
        showError('Введите код ТН ВЭД (минимум 4 цифры)');
        return;
    }

    // Validate price
    const price = parseFloat(formData.get('price'));
    if (!price || price <= 0) {
        showError('Введите стоимость товара');
        return;
    }

    // Show loading state
    submitBtn.disabled = true;
    submitBtn.classList.add('loading');

    try {
        const result = await calculate(formData);
        displayResults(result);
    } catch (error) {
        showError(error.message || 'Произошла ошибка при расчете');
    } finally {
        submitBtn.disabled = false;
        submitBtn.classList.remove('loading');
    }
}

// Event listeners
form.addEventListener('submit', handleSubmit);

// Autocomplete
const debouncedSearch = debounce(searchCodes, 300);
codeInput.addEventListener('input', (e) => debouncedSearch(e.target.value));
codeInput.addEventListener('focus', (e) => {
    if (e.target.value.length >= 2) {
        debouncedSearch(e.target.value);
    }
});

// Close autocomplete on click outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.field')) {
        autocompleteList.classList.remove('active');
    }
});

// Autocomplete item click
autocompleteList.addEventListener('click', handleAutocompleteClick);

// Keyboard navigation for autocomplete
codeInput.addEventListener('keydown', (e) => {
    const items = autocompleteList.querySelectorAll('.autocomplete-item');
    const activeItem = autocompleteList.querySelector('.autocomplete-item.active');
    let currentIndex = Array.from(items).indexOf(activeItem);

    if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (currentIndex < items.length - 1) {
            if (activeItem) activeItem.classList.remove('active');
            items[currentIndex + 1].classList.add('active');
        }
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (currentIndex > 0) {
            if (activeItem) activeItem.classList.remove('active');
            items[currentIndex - 1].classList.add('active');
        }
    } else if (e.key === 'Enter' && activeItem) {
        e.preventDefault();
        codeInput.value = activeItem.dataset.code;
        autocompleteList.classList.remove('active');
    } else if (e.key === 'Escape') {
        autocompleteList.classList.remove('active');
    }
});

// Initialize - fetch current exchange rates
async function initializeRates() {
    try {
        const response = await fetch(`${API_BASE}/rates`);
        if (response.ok) {
            const data = await response.json();
            console.log('Current rates loaded:', data);
        }
    } catch (error) {
        console.warn('Could not fetch initial rates:', error);
    }
}

// Run initialization
document.addEventListener('DOMContentLoaded', initializeRates);
