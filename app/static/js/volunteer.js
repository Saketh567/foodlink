// Volunteer Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Log pickup form enhancements
    const logPickupForm = document.getElementById('log-pickup-form');
    if (logPickupForm) {
        logPickupForm.addEventListener('submit', function(e) {
            const weightInput = document.getElementById('weight_kg');
            if (weightInput && parseFloat(weightInput.value) <= 0) {
                e.preventDefault();
                alert('Please enter a valid weight greater than 0.');
                weightInput.focus();
            }
        });
    }

    // Client sign-in form
    const clientSigninForm = document.getElementById('client-signin-form');
    if (clientSigninForm) {
        const clientNumberInput = document.getElementById('client_number');
        if (clientNumberInput) {
            clientNumberInput.addEventListener('input', function(e) {
                // Auto-uppercase and format client number
                e.target.value = e.target.value.toUpperCase().trim();
            });

            // Validate client number format (e.g., FL-001)
            clientSigninForm.addEventListener('submit', function(e) {
                const value = clientNumberInput.value;
                const pattern = /^[A-Z]{2,5}-\d{3,4}$/;
                if (!pattern.test(value)) {
                    e.preventDefault();
                    alert('Please enter a valid client number (e.g., FL-001).');
                    clientNumberInput.focus();
                }
            });
        }
    }

    // Calculate total weight for today
    function updateTodayTotal() {
        const weightCells = document.querySelectorAll('.today-weight');
        let total = 0;
        weightCells.forEach(function(cell) {
            total += parseFloat(cell.textContent) || 0;
        });
        const totalElement = document.getElementById('today-total');
        if (totalElement) {
            totalElement.textContent = total.toFixed(2) + ' kg';
        }
    }

    updateTodayTotal();
});

