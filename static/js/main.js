// Main JavaScript for Corporate Event Hub
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Smooth scrolling for anchor links
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

    // Form validation enhancement
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Search functionality enhancement
    const searchInput = document.getElementById('search');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function() {
                // Could add live search functionality here
            }, 300);
        });
    }

    // Event registration confirmation
    const registerButtons = document.querySelectorAll('.btn-register');
    registerButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to register for this event?')) {
                e.preventDefault();
            }
        });
    });

    // Event deletion confirmation
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this event? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // File upload preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Show preview if it's an image
                    if (file.type.startsWith('image/')) {
                        let preview = document.getElementById('file-preview');
                        if (!preview) {
                            preview = document.createElement('div');
                            preview.id = 'file-preview';
                            preview.className = 'mt-2';
                            input.parentNode.appendChild(preview);
                        }
                        preview.innerHTML = `
                            <img src="${e.target.result}" alt="Preview" 
                                 style="max-width: 200px; max-height: 200px; border-radius: 8px;">
                            <p class="text-muted mt-1">${file.name}</p>
                        `;
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    });

    // Loading states for buttons
    const loadingButtons = document.querySelectorAll('.btn-loading');
    loadingButtons.forEach(button => {
        button.addEventListener('click', function() {
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
            this.disabled = true;
            
            // Re-enable after 5 seconds (fallback)
            setTimeout(() => {
                this.innerHTML = originalText;
                this.disabled = false;
            }, 5000);
        });
    });

    // Dynamic form fields
    const addFieldButtons = document.querySelectorAll('.add-field');
    addFieldButtons.forEach(button => {
        button.addEventListener('click', function() {
            const template = this.dataset.template;
            const container = document.getElementById(this.dataset.container);
            if (template && container) {
                const newField = document.createElement('div');
                newField.innerHTML = template;
                container.appendChild(newField.firstElementChild);
            }
        });
    });

    // Countdown timers for events
    const countdownElements = document.querySelectorAll('.countdown');
    countdownElements.forEach(element => {
        const eventDate = new Date(element.dataset.date);
        
        function updateCountdown() {
            const now = new Date();
            const timeLeft = eventDate - now;
            
            if (timeLeft > 0) {
                const days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
                const hours = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
                
                element.innerHTML = `${days}d ${hours}h ${minutes}m`;
            } else {
                element.innerHTML = 'Event Started';
                element.classList.add('text-success');
            }
        }
        
        updateCountdown();
        setInterval(updateCountdown, 60000); // Update every minute
    });

    // Copy to clipboard functionality
    const copyButtons = document.querySelectorAll('.copy-to-clipboard');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const text = this.dataset.text || this.textContent;
            navigator.clipboard.writeText(text).then(() => {
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-check"></i> Copied!';
                setTimeout(() => {
                    this.innerHTML = originalText;
                }, 2000);
            });
        });
    });

    // Dark mode toggle (if implemented)
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-mode');
            localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
        });

        // Load saved dark mode preference
        if (localStorage.getItem('darkMode') === 'true') {
            document.body.classList.add('dark-mode');
        }
    }

    // Infinite scroll for event lists (if needed)
    let page = 1;
    let loading = false;
    
    function loadMoreEvents() {
        if (loading) return;
        loading = true;
        
        // Implementation would depend on backend pagination
        // This is a placeholder for future enhancement
        
        loading = false;
    }

    // Check if we're near the bottom of the page
    window.addEventListener('scroll', function() {
        if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 1000) {
            // loadMoreEvents(); // Uncomment when pagination is implemented
        }
    });

    // Enhanced form validation messages
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('invalid', function() {
            this.setCustomValidity('');
            if (!this.validity.valid) {
                if (this.validity.valueMissing) {
                    this.setCustomValidity('This field is required.');
                } else if (this.validity.typeMismatch) {
                    this.setCustomValidity('Please enter a valid ' + this.type + '.');
                } else if (this.validity.tooShort) {
                    this.setCustomValidity('Please enter at least ' + this.minLength + ' characters.');
                } else if (this.validity.tooLong) {
                    this.setCustomValidity('Please enter no more than ' + this.maxLength + ' characters.');
                }
            }
        });

        input.addEventListener('input', function() {
            this.setCustomValidity('');
        });
    });

    // Animation observer for fade-in effects
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe elements for animation
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    animatedElements.forEach(element => {
        observer.observe(element);
    });
});

// Utility functions
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '1100';
    document.body.appendChild(container);
    return container;
}

function formatDate(date) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(date));
}

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