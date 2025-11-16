// Admin Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Date range picker for reports
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    
    if (startDateInput && endDateInput) {
        // Set default date range (last 30 days)
        if (!startDateInput.value) {
            const endDate = new Date();
            const startDate = new Date();
            startDate.setDate(startDate.getDate() - 30);
            
            endDateInput.value = endDate.toISOString().split('T')[0];
            startDateInput.value = startDate.toISOString().split('T')[0];
        }

        // Validate date range
        const dateForm = document.querySelector('form[method="GET"]');
        if (dateForm) {
            dateForm.addEventListener('submit', function(e) {
                const start = new Date(startDateInput.value);
                const end = new Date(endDateInput.value);
                
                if (start > end) {
                    e.preventDefault();
                    alert('Start date must be before end date.');
                    return false;
                }
            });
        }
    }

    // Client verification form
    const verifyForms = document.querySelectorAll('[data-verify-form]');
    verifyForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const action = e.submitter?.value || form.querySelector('button[type="submit"]')?.value;
            
            if (action === 'approve') {
                const locationCode = form.querySelector('[name="location_code"]');
                if (!locationCode || !locationCode.value.trim()) {
                    e.preventDefault();
                    alert('Please enter a location code.');
                    locationCode.focus();
                }
            } else if (action === 'reject') {
                const reason = form.querySelector('[name="reason"]');
                if (!reason || !reason.value.trim()) {
                    e.preventDefault();
                    alert('Please provide a reason for rejection.');
                    reason.focus();
                }
            }
        });
    });

    // Auto-refresh statistics (optional)
    function refreshStats() {
        // This could be implemented with AJAX to refresh stats without page reload
        // For now, it's a placeholder
    }

    // Refresh stats every 5 minutes
    // setInterval(refreshStats, 300000);
});

// Export functions for reports
function exportReport(format) {
    // Placeholder for CSV/PDF export functionality
    alert('Export functionality coming soon!');
}

