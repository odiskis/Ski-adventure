// main.js - Global JavaScript functionality for Ski Touring Web App

/**
 * Global application state and configuration
 */
window.SkiApp = {
    config: {
        apiTimeout: 30000,
        retryAttempts: 3,
        debounceDelay: 300,
        animationDuration: 300,
        toastDuration: 5000
    },
    state: {
        isLoading: false,
        currentPage: document.body.className.split(' ')[0] || 'unknown',
        userPreferences: {},
        sessionData: {}
    },
    cache: new Map(),
    timers: new Map()
};

/**
 * Utility Functions
 */
const Utils = {
    // Debounce function for search inputs
    debounce(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    },

    // Throttle function for scroll events
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // Format numbers for display
    formatNumber(num, decimals = 0) {
        return Number(num).toFixed(decimals);
    },

    // Format distance
    formatDistance(km) {
        return `${Math.round(km)}km`;
    },

    // Format duration
    formatDuration(hours) {
        if (hours < 1) {
            return `${Math.round(hours * 60)}min`;
        } else if (hours < 2) {
            const minutes = Math.round((hours % 1) * 60);
            return minutes > 0 ? `${Math.floor(hours)}h ${minutes}min` : `${Math.floor(hours)}h`;
        } else {
            return `${Math.round(hours * 10) / 10}h`;
        }
    },

    // Get cookie value
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    },

    // Set cookie
    setCookie(name, value, days = 30) {
        const expires = new Date();
        expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
    },

    // Local storage with error handling
    getLocalStorage(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.warn('localStorage get error:', error);
            return defaultValue;
        }
    },

    setLocalStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.warn('localStorage set error:', error);
            return false;
        }
    },

    // Validate email
    isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    // Generate unique ID
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },

    // Escape HTML
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
};

/**
 * Loading Overlay Management
 */
const LoadingManager = {
    show(message = 'Loading...') {
        const loading = document.getElementById('loading');
        if (loading) {
            const messageEl = loading.querySelector('p');
            if (messageEl) messageEl.textContent = message;
            loading.style.display = 'flex';
            SkiApp.state.isLoading = true;
            
            // Prevent body scroll
            document.body.style.overflow = 'hidden';
        }
    },

    hide() {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = 'none';
            SkiApp.state.isLoading = false;
            
            // Restore body scroll
            document.body.style.overflow = '';
        }
    },

    isShowing() {
        return SkiApp.state.isLoading;
    }
};

/**
 * Notification System
 */
const NotificationManager = {
    show(message, type = 'info', duration = null) {
        const notification = document.getElementById('notification');
        if (!notification) return;

        const messageEl = notification.querySelector('.notification-message');
        if (messageEl) messageEl.textContent = message;

        // Remove existing type classes
        notification.className = 'notification';
        notification.classList.add(type);
        notification.style.display = 'block';

        // Auto-hide after duration
        const hideAfter = duration || SkiApp.config.toastDuration;
        setTimeout(() => {
            this.hide();
        }, hideAfter);

        // Announce to screen readers
        this.announceToScreenReader(message);
    },

    hide() {
        const notification = document.getElementById('notification');
        if (notification) {
            notification.style.display = 'none';
            notification.className = 'notification hidden';
        }
    },

    success(message, duration) {
        this.show(message, 'success', duration);
    },

    error(message, duration) {
        this.show(message, 'error', duration);
    },

    warning(message, duration) {
        this.show(message, 'warning', duration);
    },

    info(message, duration) {
        this.show(message, 'info', duration);
    },

    announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            if (document.body.contains(announcement)) {
                document.body.removeChild(announcement);
            }
        }, 1000);
    }
};

/**
 * API Communication
 */
const ApiClient = {
    async request(url, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            timeout: SkiApp.config.apiTimeout
        };

        const config = { ...defaultOptions, ...options };
        
        // Add CSRF token if available
        const csrfToken = Utils.getCookie('csrf_token');
        if (csrfToken) {
            config.headers['X-CSRFToken'] = csrfToken;
        }

        try {
            LoadingManager.show();
            
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }

        } catch (error) {
            console.error('API request failed:', error);
            
            if (error.name === 'AbortError') {
                throw new Error('Request timed out. Please try again.');
            } else if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
                throw new Error('Network error. Please check your connection and try again.');
            } else {
                throw error;
            }
        } finally {
            LoadingManager.hide();
        }
    },

    async get(url, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        return this.request(fullUrl);
    },

    async post(url, data = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async put(url, data = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async delete(url) {
        return this.request(url, {
            method: 'DELETE'
        });
    }
};

/**
 * Form Enhancement
 */
const FormManager = {
    init() {
        // Auto-submit prevention
        document.addEventListener('submit', this.handleSubmit.bind(this));
        
        // Real-time validation
        document.addEventListener('input', this.handleInput.bind(this));
        
        // Form state management
        this.setupFormStateManagement();
    },

    handleSubmit(event) {
        const form = event.target;
        if (!form.matches('form')) return;

        // Prevent double submission
        if (form.dataset.submitting === 'true') {
            event.preventDefault();
            return;
        }

        // Mark as submitting
        form.dataset.submitting = 'true';
        
        // Show loading if specified
        const loadingMessage = form.dataset.loading;
        if (loadingMessage) {
            LoadingManager.show(loadingMessage);
        }

        // Reset submission flag after delay
        setTimeout(() => {
            form.dataset.submitting = 'false';
        }, 3000);
    },

    handleInput(event) {
        const input = event.target;
        if (!input.matches('input, select, textarea')) return;

        // Clear previous error states
        this.clearFieldError(input);
        
        // Real-time validation
        this.validateField(input);
    },

    validateField(field) {
        const value = field.value.trim();
        const type = field.type;
        const required = field.hasAttribute('required');
        
        let isValid = true;
        let errorMessage = '';

        // Required field validation
        if (required && !value) {
            isValid = false;
            errorMessage = 'This field is required.';
        }
        
        // Type-specific validation
        if (value && type === 'email' && !Utils.isValidEmail(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address.';
        }

        if (value && field.name === 'location' && value.length < 2) {
            isValid = false;
            errorMessage = 'Location must be at least 2 characters.';
        }

        // Update field state
        if (!isValid) {
            this.setFieldError(field, errorMessage);
        } else {
            this.clearFieldError(field);
        }

        return isValid;
    },

    setFieldError(field, message) {
        field.classList.add('error');
        
        let errorEl = field.parentNode.querySelector('.form-error');
        if (!errorEl) {
            errorEl = document.createElement('div');
            errorEl.className = 'form-error';
            field.parentNode.appendChild(errorEl);
        }
        
        errorEl.textContent = message;
        errorEl.classList.remove('hidden');
    },

    clearFieldError(field) {
        field.classList.remove('error');
        
        const errorEl = field.parentNode.querySelector('.form-error');
        if (errorEl) {
            errorEl.classList.add('hidden');
        }
    },

    setupFormStateManagement() {
        // Save form data to session storage for recovery
        const forms = document.querySelectorAll('form[data-persist]');
        
        forms.forEach(form => {
            const formId = form.id || Utils.generateId();
            
            // Load saved data
            this.loadFormData(form, formId);
            
            // Save data on input
            form.addEventListener('input', Utils.debounce(() => {
                this.saveFormData(form, formId);
            }, SkiApp.config.debounceDelay));
        });
    },

    saveFormData(form, formId) {
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        Utils.setLocalStorage(`form_${formId}`, data);
    },

    loadFormData(form, formId) {
        const savedData = Utils.getLocalStorage(`form_${formId}`);
        if (!savedData) return;

        Object.entries(savedData).forEach(([name, value]) => {
            const field = form.querySelector(`[name="${name}"]`);
            if (field && !field.value) {
                field.value = value;
            }
        });
    },

    clearFormData(formId) {
        localStorage.removeItem(`form_${formId}`);
    }
};

/**
 * Navigation Enhancement
 */
const NavigationManager = {
    init() {
        this.setupMobileMenu();
        this.setupActiveLinks();
        this.setupSmoothScrolling();
    },

    setupMobileMenu() {
        const navToggle = document.getElementById('navToggle');
        const navMenu = document.getElementById('navMenu');
        
        if (!navToggle || !navMenu) return;

        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('active');
            navToggle.setAttribute('aria-expanded', 
                navToggle.classList.contains('active').toString()
            );
        });

        // Close menu when clicking outside
        document.addEventListener('click', (event) => {
            if (!navToggle.contains(event.target) && !navMenu.contains(event.target)) {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
                navToggle.setAttribute('aria-expanded', 'false');
            }
        });

        // Close menu on escape key
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && navMenu.classList.contains('active')) {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
                navToggle.setAttribute('aria-expanded', 'false');
                navToggle.focus();
            }
        });
    },

    setupActiveLinks() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
                link.setAttribute('aria-current', 'page');
            }
        });
    },

    setupSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    const headerOffset = 80;
                    const elementPosition = target.offsetTop;
                    const offsetPosition = elementPosition - headerOffset;

                    window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        });
    }
};

/**
 * Accessibility Enhancements
 */
const AccessibilityManager = {
    init() {
        this.setupKeyboardNavigation();
        this.setupFocusManagement();
        this.setupScreenReaderSupport();
    },

    setupKeyboardNavigation() {
        // Add keyboard support for custom interactive elements
        document.addEventListener('keydown', (event) => {
            // Global keyboard shortcuts
            switch (event.key) {
                case 'Escape':
                    this.handleEscapeKey();
                    break;
                case '/':
                    if (event.ctrlKey || event.metaKey) {
                        event.preventDefault();
                        this.focusSearchInput();
                    }
                    break;
            }
        });

        // Tab navigation enhancement
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });

        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });
    },

    setupFocusManagement() {
        // Focus trapping for modals
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Tab') {
                const activeModal = document.querySelector('.modal:not(.hidden)');
                if (activeModal) {
                    this.trapFocus(event, activeModal);
                }
            }
        });
    },

    setupScreenReaderSupport() {
        // Announce page changes
        this.announcePageLoad();
        
        // Announce dynamic content changes
        this.setupContentChangeAnnouncements();
    },

    handleEscapeKey() {
        // Close open modals
        const openModal = document.querySelector('.modal:not(.hidden)');
        if (openModal) {
            const closeButton = openModal.querySelector('.modal-close');
            if (closeButton) closeButton.click();
            return;
        }

        // Close notifications
        NotificationManager.hide();
        
        // Close mobile menu
        const navMenu = document.getElementById('navMenu');
        if (navMenu && navMenu.classList.contains('active')) {
            const navToggle = document.getElementById('navToggle');
            if (navToggle) navToggle.click();
        }
    },

    focusSearchInput() {
        const searchInput = document.querySelector('input[type="search"], input[name="location"]');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    },

    trapFocus(event, modal) {
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (event.shiftKey && document.activeElement === firstElement) {
            event.preventDefault();
            lastElement.focus();
        } else if (!event.shiftKey && document.activeElement === lastElement) {
            event.preventDefault();
            firstElement.focus();
        }
    },

    announcePageLoad() {
        const pageTitle = document.title;
        const announcement = `Page loaded: ${pageTitle}`;
        
        setTimeout(() => {
            NotificationManager.announceToScreenReader(announcement);
        }, 1000);
    },

    setupContentChangeAnnouncements() {
        // Monitor for dynamic content changes
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            const announcement = node.getAttribute('data-announce');
                            if (announcement) {
                                NotificationManager.announceToScreenReader(announcement);
                            }
                        }
                    });
                }
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
};

/**
 * Animation and Visual Effects
 */
const AnimationManager = {
    init() {
        this.setupScrollAnimations();
        this.setupHoverEffects();
        this.setupParallaxEffects();
    },

    setupScrollAnimations() {
        if (window.IntersectionObserver) {
            const observerOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };

            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animate-in');
                        
                        // Stagger animations for children
                        const children = entry.target.querySelectorAll('.stagger-child');
                        children.forEach((child, index) => {
                            setTimeout(() => {
                                child.classList.add('animate-in');
                            }, index * 100);
                        });
                    }
                });
            }, observerOptions);

            // Observe elements with animation classes
            document.querySelectorAll('.animate-on-scroll').forEach(el => {
                observer.observe(el);
            });
        }
    },

    setupHoverEffects() {
        // Enhanced hover effects for interactive elements
        document.querySelectorAll('.card, .recommendation-card, .tour-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-5px)';
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = '';
            });
        });
    },

    setupParallaxEffects() {
        const parallaxElements = document.querySelectorAll('.parallax');
        
        if (parallaxElements.length > 0) {
            const handleScroll = Utils.throttle(() => {
                const scrolled = window.pageYOffset;
                
                parallaxElements.forEach(element => {
                    const speed = element.dataset.speed || 0.5;
                    const yPos = scrolled * speed;
                    element.style.transform = `translateY(${yPos}px)`;
                });
            }, 10);

            window.addEventListener('scroll', handleScroll);
        }
    },

    fadeIn(element, duration = 300) {
        element.style.opacity = '0';
        element.style.display = 'block';
        
        const start = performance.now();
        
        const animate = (timestamp) => {
            const elapsed = timestamp - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.opacity = progress;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    },

    fadeOut(element, duration = 300) {
        const start = performance.now();
        const startOpacity = parseFloat(window.getComputedStyle(element).opacity);
        
        const animate = (timestamp) => {
            const elapsed = timestamp - start;
            const progress = Math.min(elapsed / duration, 1);
            
            element.style.opacity = startOpacity * (1 - progress);
            
            if (progress >= 1) {
                element.style.display = 'none';
            } else {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }
};

/**
 * Performance Monitoring
 */
const PerformanceManager = {
    init() {
        this.setupLazyLoading();
        this.setupImageOptimization();
        this.monitorPagePerformance();
    },

    setupLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        observer.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    },

    setupImageOptimization() {
        // Preload critical images
        const criticalImages = document.querySelectorAll('img[data-critical]');
        criticalImages.forEach(img => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = 'image';
            link.href = img.src || img.dataset.src;
            document.head.appendChild(link);
        });
    },

    monitorPagePerformance() {
        if ('performance' in window) {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const perfData = performance.getEntriesByType('navigation')[0];
                    
                    const metrics = {
                        loadTime: perfData.loadEventEnd - perfData.loadEventStart,
                        domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                        totalTime: perfData.loadEventEnd - perfData.fetchStart
                    };

                    // Log performance metrics (could send to analytics)
                    console.log('Page Performance:', metrics);
                    
                    // Store in app state
                    SkiApp.state.performance = metrics;
                }, 0);
            });
        }
    }
};

/**
 * Error Handling
 */
const ErrorManager = {
    init() {
        this.setupGlobalErrorHandling();
        this.setupUnhandledPromiseRejection();
    },

    setupGlobalErrorHandling() {
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            
            // Don't show user-facing errors for minor issues
            if (!this.isCriticalError(event.error)) {
                return;
            }

            NotificationManager.error(
                'Something went wrong. Please refresh the page and try again.',
                10000
            );
        });
    },

    setupUnhandledPromiseRejection() {
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            
            // Prevent default browser behavior
            event.preventDefault();
            
            // Show user-friendly error
            NotificationManager.error(
                'A network error occurred. Please check your connection and try again.',
                8000
            );
        });
    },

    isCriticalError(error) {
        const criticalErrors = [
            'Network error',
            'Failed to fetch',
            'TypeError',
            'ReferenceError'
        ];

        return criticalErrors.some(critical => 
            error.message && error.message.includes(critical)
        );
    },

    logError(error, context = 'Unknown') {
        const errorData = {
            message: error.message,
            stack: error.stack,
            context: context,
            userAgent: navigator.userAgent,
            url: window.location.href,
            timestamp: new Date().toISOString()
        };

        console.error('Application Error:', errorData);
        
        // Could send to error tracking service
        // this.sendToErrorService(errorData);
    }
};

/**
 * Application Initialization
 */
const SkiTouringApp = {
    init() {
        console.log('🎿 Initializing Ski Touring Web App...');
        
        try {
            // Core managers
            ErrorManager.init();
            FormManager.init();
            NavigationManager.init();
            AccessibilityManager.init();
            AnimationManager.init();
            PerformanceManager.init();
            
            // Page-specific initialization
            this.initPageSpecific();
            
            // Setup global event listeners
            this.setupGlobalListeners();
            
            console.log('✅ Ski Touring Web App initialized successfully');
            
        } catch (error) {
            console.error('❌ Failed to initialize app:', error);
            ErrorManager.logError(error, 'App Initialization');
        }
    },

    initPageSpecific() {
        const currentPage = SkiApp.state.currentPage;
        
        switch (currentPage) {
            case 'landing-page':
                this.initLandingPage();
                break;
            case 'quiz-page':
                this.initQuizPage();
                break;
            case 'location-page':
                this.initLocationPage();
                break;
            case 'recommendations-page':
                this.initRecommendationsPage();
                break;
        }
    },

    initLandingPage() {
        // Landing page specific initialization
        if (typeof LandingPage !== 'undefined') {
            LandingPage.init();
        }
    },

    initQuizPage() {
        // Quiz page specific initialization
        if (typeof QuizPage !== 'undefined') {
            QuizPage.init();
        }
    },

    initLocationPage() {
        // Location page specific initialization
        if (typeof LocationPage !== 'undefined') {
            LocationPage.init();
        }
    },

    initRecommendationsPage() {
        // Recommendations page specific initialization
        if (typeof RecommendationsPage !== 'undefined') {
            RecommendationsPage.init();
        }
    },

    setupGlobalListeners() {
        // Page visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Page hidden - pause animations, etc.
                console.log('Page hidden');
            } else {
                // Page visible - resume functionality
                console.log('Page visible');
            }
        });

        // Window resize
        window.addEventListener('resize', Utils.throttle(() => {
            // Handle responsive adjustments
            this.handleResize();
        }, 250));

        // Before page unload
        window.addEventListener('beforeunload', () => {
            // Cleanup and save state
            this.cleanup();
        });
    },

    handleResize() {
        // Update viewport height for mobile browsers
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
        
        // Update app state
        SkiApp.state.viewport = {
            width: window.innerWidth,
            height: window.innerHeight
        };
    },

    cleanup() {
        // Clear timers
        SkiApp.timers.forEach(timer => clearTimeout(timer));
        SkiApp.timers.clear();
        
        // Clear cache if needed
        if (SkiApp.cache.size > 100) {
            SkiApp.cache.clear();
        }
    }
};

// Global utility functions (backwards compatibility)
window.showLoading = LoadingManager.show.bind(LoadingManager);
window.hideLoading = LoadingManager.hide.bind(LoadingManager);
window.showNotification = NotificationManager.show.bind(NotificationManager);
window.hideNotification = NotificationManager.hide.bind(NotificationManager);
window.makeApiCall = ApiClient.request.bind(ApiClient);
window.announceToScreenReader = NotificationManager.announceToScreenReader.bind(NotificationManager);

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', SkiTouringApp.init.bind(SkiTouringApp));
} else {
    SkiTouringApp.init();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        SkiTouringApp,
        Utils,
        LoadingManager,
        NotificationManager,
        ApiClient,
        FormManager,
        NavigationManager,
        AccessibilityManager,
        AnimationManager,
        PerformanceManager,
        ErrorManager
    };
}