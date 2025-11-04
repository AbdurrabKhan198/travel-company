// Main JavaScript for Safar Zone Travels

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        if (mobileMenu && !mobileMenu.contains(event.target) && 
            mobileMenuButton && !mobileMenuButton.contains(event.target)) {
            mobileMenu.classList.add('hidden');
        }
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-auto-hide');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // Date picker - only enable dates from inventory
    const dateInput = document.getElementById('travel-date');
    if (dateInput && window.availableDates) {
        dateInput.addEventListener('focus', function() {
            // This would be enhanced with a proper date picker library
            // For now, HTML5 date input with min/max constraints
            const today = new Date().toISOString().split('T')[0];
            dateInput.setAttribute('min', today);
        });
    }

    // Form validation
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const inputs = form.querySelectorAll('input[required], select[required]');
            let valid = true;
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    valid = false;
                    input.classList.add('border-red-500');
                } else {
                    input.classList.remove('border-red-500');
                }
            });
            
            if (!valid) {
                e.preventDefault();
                alert('Please fill in all required fields');
            }
        });
    });

    // Booking confirmation modal
    window.showBookingConfirmation = function(bookingRef) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-xl p-8 max-w-md mx-4 animate-slide-in">
                <div class="text-center">
                    <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                    </div>
                    <h3 class="text-2xl font-bold text-gray-800 mb-2">Booking Confirmed!</h3>
                    <p class="text-gray-600 mb-4">Your booking reference: <strong>${bookingRef}</strong></p>
                    <button onclick="this.closest('.fixed').remove()" 
                            class="btn-primary w-full">
                        Close
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    };

    // Cancel booking confirmation
    window.confirmCancelBooking = function(bookingId) {
        if (confirm('Are you sure you want to cancel this booking?')) {
            document.getElementById(`cancel-form-${bookingId}`).submit();
        }
    };

    // Search form enhancement
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        const fromInput = document.getElementById('from-location');
        const toInput = document.getElementById('to-location');
        
        if (fromInput && toInput) {
            // Prevent same from/to locations
            fromInput.addEventListener('change', function() {
                if (toInput.value === fromInput.value && fromInput.value !== '') {
                    alert('Destination cannot be the same as origin');
                    fromInput.value = '';
                }
            });
            
            toInput.addEventListener('change', function() {
                if (toInput.value === fromInput.value && toInput.value !== '') {
                    alert('Destination cannot be the same as origin');
                    toInput.value = '';
                }
            });
        }
    }
});

// Airplane animation on homepage
if (document.querySelector('.hero-section')) {
    const plane = document.querySelector('.plane-icon');
    if (plane) {
        setInterval(() => {
            plane.classList.add('animate-float');
        }, 100);
    }
}

// Print booking function
window.printBooking = function() {
    window.print();
};
