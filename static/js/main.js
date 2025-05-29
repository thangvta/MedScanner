// main.js - Main JavaScript functionality for MedScanner application

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Setup mobile navigation
    setupMobileNavigation();
    
    // Setup form validation
    setupFormValidation();
    
    // Initialize page-specific functions based on the page identifier
    initPageSpecificFunctions();
});

/**
 * Set up the mobile navigation menu
 */
function setupMobileNavigation() {
    const navToggle = document.getElementById('navbarToggle');
    if (navToggle) {
        navToggle.addEventListener('click', function() {
            const navbarCollapse = document.getElementById('navbarContent');
            if (navbarCollapse) {
                navbarCollapse.classList.toggle('show');
            }
        });
    }
}

/**
 * Setup form validation for all forms with the 'needs-validation' class
 */
function setupFormValidation() {
    // Fetch all forms that need validation
    const forms = document.querySelectorAll('.needs-validation');
    
    // Loop over them and prevent submission
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Initialize page-specific functions based on data-page attribute
 */
function initPageSpecificFunctions() {
    const pageContainer = document.getElementById('page-container');
    if (!pageContainer) return;
    
    const pageName = pageContainer.getAttribute('data-page');
    
    switch(pageName) {
        case 'scan':
            // Initialize prescription scanner if on scan page
            if (typeof initScanner === 'function') {
                initScanner();
            }
            break;
            
        case 'dosage':
            // Setup dosage verification form
            setupDosageVerificationForm();
            break;
            
        case 'inventory':
            // Setup inventory management functions
            setupInventoryFunctions();
            break;
            
        case 'interactions':
            // Setup interaction visualization
            setupInteractionVisuals();
            break;
            
        case 'reports':
            // Setup report filtering
            setupReportFilters();
            break;
    }
}

/**
 * Shows an alert message
 * @param {string} message - The message to display
 * @param {string} type - Alert type (success, danger, warning, info)
 * @param {string} containerId - ID of the container to add the alert to
 */
function showAlert(message, type = 'info', containerId = 'alert-container') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    container.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 5000);
}

/**
 * Setup the dosage verification form
 */
function setupDosageVerificationForm() {
    const dosageForm = document.getElementById('dosage-verification-form');
    if (!dosageForm) return;
    
    dosageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(dosageForm);
        const resultContainer = document.getElementById('dosage-results');
        
        fetch('/verify-dosage', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showAlert(data.error, 'danger', 'dosage-alert-container');
                return;
            }
            
            // Display results
            let resultHTML = '<div class="card mt-3">';
            resultHTML += '<div class="card-header bg-primary text-white">Dosage Verification Results</div>';
            resultHTML += '<div class="card-body">';
            
            if (data.is_appropriate) {
                resultHTML += '<div class="alert alert-success">✓ Dosage appears to be appropriate</div>';
            } else {
                resultHTML += '<div class="alert alert-danger">⚠ Dosage may not be appropriate</div>';
            }
            
            if (data.warnings && data.warnings.length > 0) {
                resultHTML += '<h5 class="mt-3">Warnings:</h5>';
                resultHTML += '<ul class="list-group">';
                data.warnings.forEach(warning => {
                    resultHTML += `<li class="list-group-item list-group-item-warning">${warning}</li>`;
                });
                resultHTML += '</ul>';
            }
            
            if (data.recommendations && data.recommendations.length > 0) {
                resultHTML += '<h5 class="mt-3">Recommendations:</h5>';
                resultHTML += '<ul class="list-group">';
                data.recommendations.forEach(rec => {
                    resultHTML += `<li class="list-group-item list-group-item-info">${rec}</li>`;
                });
                resultHTML += '</ul>';
            }
            
            resultHTML += '</div></div>';
            
            resultContainer.innerHTML = resultHTML;
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('An error occurred while verifying the dosage', 'danger', 'dosage-alert-container');
        });
    });
}

/**
 * Setup inventory management functions
 */
function setupInventoryFunctions() {
    // Setup low stock alerts
    const lowStockItems = document.querySelectorAll('.low-stock-item');
    lowStockItems.forEach(item => {
        item.classList.add('text-danger', 'fw-bold');
    });
    
    // Setup inventory adjustment modal
    const adjustmentModal = document.getElementById('inventory-adjustment-modal');
    if (adjustmentModal) {
        adjustmentModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const medicationId = button.getAttribute('data-medication-id');
            const medicationName = button.getAttribute('data-medication-name');
            
            const modalTitle = adjustmentModal.querySelector('.modal-title');
            const medicationIdInput = adjustmentModal.querySelector('#medication_id');
            
            modalTitle.textContent = `Adjust Inventory: ${medicationName}`;
            medicationIdInput.value = medicationId;
        });
    }
}

/**
 * Setup interaction visualization elements
 */
function setupInteractionVisuals() {
    // Highlight severe interactions
    const severeInteractions = document.querySelectorAll('.interaction-severe');
    severeInteractions.forEach(item => {
        item.classList.add('bg-danger', 'text-white');
    });
    
    // Highlight moderate interactions
    const moderateInteractions = document.querySelectorAll('.interaction-moderate');
    moderateInteractions.forEach(item => {
        item.classList.add('bg-warning');
    });
    
    // Highlight mild interactions
    const mildInteractions = document.querySelectorAll('.interaction-mild');
    mildInteractions.forEach(item => {
        item.classList.add('bg-info', 'text-white');
    });
    
    // Setup interaction details modal
    const interactionModal = document.getElementById('interaction-details-modal');
    if (interactionModal) {
        interactionModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const interactionId = button.getAttribute('data-interaction-id');
            const drug1 = button.getAttribute('data-drug1');
            const drug2 = button.getAttribute('data-drug2');
            const severity = button.getAttribute('data-severity');
            const description = button.getAttribute('data-description');
            
            const modalTitle = interactionModal.querySelector('.modal-title');
            const modalBody = interactionModal.querySelector('.modal-body');
            
            modalTitle.textContent = `Interaction: ${drug1} & ${drug2}`;
            
            let severityClass = '';
            switch(severity) {
                case 'severe':
                    severityClass = 'text-danger';
                    break;
                case 'moderate':
                    severityClass = 'text-warning';
                    break;
                case 'mild':
                    severityClass = 'text-info';
                    break;
            }
            
            modalBody.innerHTML = `
                <p><strong>Severity:</strong> <span class="${severityClass} fw-bold">${severity.toUpperCase()}</span></p>
                <p><strong>Description:</strong> ${description}</p>
            `;
        });
    }
}

/**
 * Setup report filtering functionality
 */
function setupReportFilters() {
    const filterForm = document.getElementById('report-filter-form');
    if (!filterForm) return;
    
    const reportItems = document.querySelectorAll('.report-item');
    
    filterForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const fromDate = document.getElementById('filter-from-date').value;
        const toDate = document.getElementById('filter-to-date').value;
        const severityFilter = document.getElementById('filter-severity').value;
        const typeFilter = document.getElementById('filter-type').value;
        
        // Simple client-side filtering
        reportItems.forEach(item => {
            let showItem = true;
            
            // Date filtering
            if (fromDate) {
                const itemDate = item.getAttribute('data-date');
                if (itemDate < fromDate) showItem = false;
            }
            
            if (toDate) {
                const itemDate = item.getAttribute('data-date');
                if (itemDate > toDate) showItem = false;
            }
            
            // Severity filtering
            if (severityFilter && severityFilter !== 'all') {
                const itemSeverity = item.getAttribute('data-severity');
                if (itemSeverity !== severityFilter) showItem = false;
            }
            
            // Type filtering
            if (typeFilter && typeFilter !== 'all') {
                const itemType = item.getAttribute('data-type');
                if (itemType !== typeFilter) showItem = false;
            }
            
            // Show or hide the item
            if (showItem) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    });
    
    // Reset button
    const resetButton = document.getElementById('filter-reset');
    if (resetButton) {
        resetButton.addEventListener('click', function() {
            filterForm.reset();
            reportItems.forEach(item => {
                item.style.display = '';
            });
        });
    }
}
