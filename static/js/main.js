// Enhanced Event Management System JavaScript

// Global variables
let isLoading = false;
const ANIMATION_DURATION = 300;

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Initialize the application
function initializeApp() {
    initializeNavigation();
    initializeAlerts();
    initializeForms();
    initializeCards();
    initializeModals();
    initializeTooltips();
    initializeScrollEffects();
    setupEventListeners();
}

// Navigation enhancements
function initializeNavigation() {
    const navbar = document.querySelector('.navbar');
    let lastScrollTop = 0;

    // Navbar scroll effect
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > lastScrollTop && scrollTop > 100) {
            // Scrolling down
            navbar.style.transform = 'translateY(-100%)';
        } else {
            // Scrolling up
            navbar.style.transform = 'translateY(0)';
        }
        
        lastScrollTop = scrollTop;
    });

    // Mobile menu toggle enhancement
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        navbarToggler.addEventListener('click', function() {
            // Add smooth animation
            navbarCollapse.style.transition = 'height 0.3s ease-in-out';
        });
    }

    // Active link highlighting
    highlightActiveNavLink();
}

// Highlight active navigation link
function highlightActiveNavLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const linkPath = new URL(link.href).pathname;
        if (linkPath === currentPath || (currentPath.startsWith(linkPath) && linkPath !== '/')) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// Alert system enhancements
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(alert => {
        // Add icons to alerts
        addAlertIcon(alert);
        
        // Auto-dismiss alerts after 5 seconds
        if (alert.classList.contains('alert-dismissible')) {
            setTimeout(() => {
                dismissAlert(alert);
            }, 5000);
        }
    });
}

// Add appropriate icon to alerts
function addAlertIcon(alert) {
    let icon = '';
    
    if (alert.classList.contains('alert-success')) {
        icon = '<i class="fas fa-check-circle me-2"></i>';
    } else if (alert.classList.contains('alert-danger')) {
        icon = '<i class="fas fa-exclamation-circle me-2"></i>';
    } else if (alert.classList.contains('alert-warning')) {
        icon = '<i class="fas fa-exclamation-triangle me-2"></i>';
    } else if (alert.classList.contains('alert-info')) {
        icon = '<i class="fas fa-info-circle me-2"></i>';
    }
    
    if (icon && !alert.querySelector('i')) {
        alert.innerHTML = icon + alert.innerHTML;
    }
}

// Dismiss alert with animation
function dismissAlert(alert) {
    alert.style.opacity = '0';
    alert.style.transform = 'translateX(100%)';
    
    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, ANIMATION_DURATION);
}

// Form enhancements
function initializeForms() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Add loading states to submit buttons
        setupFormSubmission(form);
        
        // Enhanced validation
        setupFormValidation(form);
        
        // Floating labels
        setupFloatingLabels(form);
    });
    
    // Date/time inputs enhancement
    setupDateTimeInputs();
}

// Setup form submission with loading state
function setupFormSubmission(form) {
    const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
    
    if (submitBtn) {
        form.addEventListener('submit', function() {
            if (!isLoading) {
                isLoading = true;
                setButtonLoading(submitBtn, true);
                
                // Reset loading state after 10 seconds as fallback
                setTimeout(() => {
                    setButtonLoading(submitBtn, false);
                    isLoading = false;
                }, 10000);
            }
        });
    }
}

// Set button loading state
function setButtonLoading(button, loading) {
    const originalText = button.getAttribute('data-original-text') || button.textContent;
    
    if (loading) {
        button.setAttribute('data-original-text', originalText);
        button.innerHTML = '<span class="spinner me-2"></span>Loading...';
        button.disabled = true;
    } else {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

// Enhanced form validation
function setupFormValidation(form) {
    const inputs = form.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(input);
        });
        
        input.addEventListener('input', function() {
            // Clear validation errors on input
            clearFieldValidation(input);
        });
    });
}

// Validate individual field
function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    let isValid = true;
    let message = '';
    
    // Check required fields
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        message = 'This field is required.';
    }
    
    // Email validation
    if (type === 'email' && value && !isValidEmail(value)) {
        isValid = false;
        message = 'Please enter a valid email address.';
    }
    
    // Password validation
    if (type === 'password' && value && value.length < 8) {
        isValid = false;
        message = 'Password must be at least 8 characters long.';
    }
    
    // Update field validation state
    updateFieldValidation(field, isValid, message);
    
    return isValid;
}

// Update field validation state
function updateFieldValidation(field, isValid, message) {
    const feedbackElement = field.parentNode.querySelector('.invalid-feedback');
    
    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
        if (feedbackElement) {
            feedbackElement.textContent = '';
        }
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
        if (feedbackElement) {
            feedbackElement.textContent = message;
        }
    }
}

// Clear field validation
function clearFieldValidation(field) {
    field.classList.remove('is-valid', 'is-invalid');
    const feedbackElement = field.parentNode.querySelector('.invalid-feedback');
    if (feedbackElement) {
        feedbackElement.textContent = '';
    }
}

// Email validation helper
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Setup floating labels
function setupFloatingLabels(form) {
    const floatingGroups = form.querySelectorAll('.form-floating');
    
    floatingGroups.forEach(group => {
        const input = group.querySelector('input, select, textarea');
        const label = group.querySelector('label');
        
        if (input && label) {
            // Set placeholder for floating effect
            if (!input.placeholder) {
                input.placeholder = ' ';
            }
            
            // Handle initial state
            updateFloatingLabel(input, label);
            
            // Handle focus/blur events
            input.addEventListener('focus', () => updateFloatingLabel(input, label));
            input.addEventListener('blur', () => updateFloatingLabel(input, label));
            input.addEventListener('input', () => updateFloatingLabel(input, label));
        }
    });
}

// Update floating label state
function updateFloatingLabel(input, label) {
    const hasValue = input.value.length > 0;
    const isFocused = document.activeElement === input;
    
    if (hasValue || isFocused) {
        label.classList.add('active');
    } else {
        label.classList.remove('active');
    }
}

// Setup date/time inputs
function setupDateTimeInputs() {
    const dateInputs = document.querySelectorAll('input[type="datetime-local"]');
    
    dateInputs.forEach(input => {
        // Set minimum date to today
        const now = new Date();
        const minDate = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
        input.min = minDate.toISOString().slice(0, 16);
    });
}

// Card enhancements
function initializeCards() {
    const cards = document.querySelectorAll('.card');
    
    cards.forEach(card => {
        // Add hover effects
        addCardHoverEffect(card);
        
        // Lazy load images in cards
        lazyLoadCardImages(card);
    });
}

// Add hover effects to cards
function addCardHoverEffect(card) {
    card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-4px)';
        this.style.boxShadow = 'var(--shadow-xl)';
    });
    
    card.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
        this.style.boxShadow = 'var(--shadow)';
    });
}

// Lazy load images in cards
function lazyLoadCardImages(card) {
    const images = card.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Modal enhancements
function initializeModals() {
    const modalTriggers = document.querySelectorAll('[data-bs-toggle="modal"]');
    
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function() {
            const targetModal = document.querySelector(this.getAttribute('data-bs-target'));
            if (targetModal) {
                // Add custom modal animations
                targetModal.style.display = 'block';
                targetModal.classList.add('show');
                setTimeout(() => {
                    targetModal.querySelector('.modal-dialog').style.transform = 'translateY(0)';
                }, 10);
            }
        });
    });
}

// Tooltip initialization
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Scroll effects
function initializeScrollEffects() {
    const elementsToAnimate = document.querySelectorAll('.card, .stat-card, .alert');
    
    const animationObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    elementsToAnimate.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
        animationObserver.observe(element);
    });
}

// Setup additional event listeners
function setupEventListeners() {
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
    
    // Copy to clipboard functionality
    document.querySelectorAll('[data-clipboard]').forEach(button => {
        button.addEventListener('click', function() {
            const text = this.getAttribute('data-clipboard');
            navigator.clipboard.writeText(text).then(() => {
                showToast('Copied to clipboard!', 'success');
            });
        });
    });
    
    // Confirmation dialogs
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} toast-notification`;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease-in-out;
    `;
    toast.innerHTML = message;
    
    document.body.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    }, 10);
    
    // Auto remove
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

// Utility functions
const utils = {
    // Format date
    formatDate: function(date) {
        return new Date(date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    },
    
    // Format currency
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },
    
    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Throttle function
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// Make utils globally available
window.eventManagementUtils = utils;

// Service Worker registration for PWA capabilities
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/js/sw.js').then(function(registration) {
            console.log('ServiceWorker registration successful');
        }, function(err) {
            console.log('ServiceWorker registration failed');
        });
    });
}

// Export functions for use in other modules
window.eventManagement = {
    showToast,
    setButtonLoading,
    validateField,
    utils
};
