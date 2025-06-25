// about.js - About page specific JavaScript functionality

/**
 * About page initialization and functionality
 */
const AboutPage = {
    init() {
        this.setupStatsAnimation();
        this.setupContactForm();
        this.setupSmoothScrolling();
        this.setupCardsAnimation();
        this.setupModalHandlers();
    },

    setupStatsAnimation() {
        const observerOptions = {
            threshold: 0.5,
            rootMargin: '0px 0px -100px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.animateStats(entry.target);
                    observer.unobserve(entry.target); // Only animate once
                }
            });
        }, observerOptions);
        
        document.querySelectorAll('.stats-grid').forEach(el => {
            observer.observe(el);
        });
    },

    animateStats(statsContainer) {
        const statNumbers = statsContainer.querySelectorAll('.stat-number');
        
        statNumbers.forEach(statEl => {
            const finalValue = statEl.textContent;
            const isNumber = !isNaN(parseFloat(finalValue));
            
            if (isNumber) {
                const targetNum = parseFloat(finalValue);
                const hasPlus = finalValue.includes('+');
                let currentNum = 0;
                const increment = targetNum / 50;
                const duration = 30;
                
                const timer = setInterval(() => {
                    currentNum += increment;
                    if (currentNum >= targetNum) {
                        currentNum = targetNum;
                        clearInterval(timer);
                    }
                    statEl.textContent = Math.floor(currentNum) + (hasPlus ? '+' : '');
                }, duration);
            }
        });
    },

    setupContactForm() {
        const contactForm = document.querySelector('.contact-form');
        if (contactForm) {
            contactForm.addEventListener('submit', this.handleContactForm.bind(this));
        }

        // Alternative selector for feedback form
        const feedbackForm = document.querySelector('.feedback-form');
        if (feedbackForm) {
            feedbackForm.addEventListener('submit', this.handleContactForm.bind(this));
        }
    },

    async handleContactForm(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const data = Object.fromEntries(formData.entries());
        
        // Basic form validation
        if (!data.name || !data.email || !data.message) {
            showNotification('Please fill in all required fields.', 'warning');
            return;
        }

        if (!this.isValidEmail(data.email)) {
            showNotification('Please enter a valid email address.', 'warning');
            return;
        }
        
        try {
            showLoading('Sending your message...');
            
            // Simulate API call - replace with actual endpoint
            const response = await fetch('/api/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                showNotification('Thank you for your feedback! We\'ll get back to you soon.', 'success');
                event.target.reset();
            } else {
                throw new Error('Server error');
            }
            
        } catch (error) {
            console.error('Contact form error:', error);
            // For demo purposes - simulate success after delay
            await new Promise(resolve => setTimeout(resolve, 1500));
            showNotification('Thank you for your feedback! We\'ll get back to you soon.', 'success');
            event.target.reset();
        } finally {
            hideLoading();
        }
    },

    setupSmoothScrolling() {
        // Handle anchor links for smooth scrolling to sections
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                    
                    // Announce to screen readers
                    const targetHeading = target.querySelector('h2, h3, h4');
                    if (targetHeading) {
                        announceToScreenReader(`Navigated to ${targetHeading.textContent}`);
                    }
                }
            });
        });
    },

    setupCardsAnimation() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);
        
        // Observe cards for staggered animation
        document.querySelectorAll('.method-card, .source-card, .tech-category, .plan-category').forEach((el, index) => {
            // Add a delay class for staggered animation
            el.style.animationDelay = `${index * 0.1}s`;
            observer.observe(el);
        });
    },

    setupModalHandlers() {
        // Handle modal triggers for methodology details, source info, etc.
        document.querySelectorAll('[data-modal-trigger]').forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                const modalId = trigger.getAttribute('data-modal-trigger');
                this.openModal(modalId);
            });
        });

        // Handle modal close buttons
        document.querySelectorAll('[data-modal-close]').forEach(closeBtn => {
            closeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.closeModal();
            });
        });

        // Close modal on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });

        // Close modal on backdrop click
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-backdrop')) {
                this.closeModal();
            }
        });
    },

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
            
            // Focus first focusable element in modal
            const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (firstFocusable) {
                firstFocusable.focus();
            }
            
            announceToScreenReader('Modal opened');
        }
    },

    closeModal() {
        const activeModal = document.querySelector('.modal.active');
        if (activeModal) {
            activeModal.classList.remove('active');
            activeModal.classList.add('hidden');
            document.body.style.overflow = '';
            announceToScreenReader('Modal closed');
        }
    },

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    // Enhanced accessibility features
    setupAccessibilityFeatures() {
        // Add skip links for better keyboard navigation
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Skip to main content';
        skipLink.className = 'skip-link';
        document.body.insertBefore(skipLink, document.body.firstChild);

        // Enhance button feedback
        document.querySelectorAll('button, .btn').forEach(button => {
            button.addEventListener('click', () => {
                // Visual feedback for button clicks
                button.style.transform = 'scale(0.98)';
                setTimeout(() => {
                    button.style.transform = '';
                }, 150);
            });
        });

        // Add aria-live region for dynamic content announcements
        if (!document.getElementById('aria-live-region')) {
            const liveRegion = document.createElement('div');
            liveRegion.id = 'aria-live-region';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.style.position = 'absolute';
            liveRegion.style.left = '-10000px';
            liveRegion.style.width = '1px';
            liveRegion.style.height = '1px';
            liveRegion.style.overflow = 'hidden';
            document.body.appendChild(liveRegion);
        }
    },

    // Performance optimization
    setupPerformanceOptimizations() {
        // Lazy load heavy content
        const lazyElements = document.querySelectorAll('[data-lazy]');
        if (lazyElements.length > 0 && 'IntersectionObserver' in window) {
            const lazyObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const element = entry.target;
                        const src = element.getAttribute('data-lazy');
                        if (src) {
                            element.src = src;
                            element.removeAttribute('data-lazy');
                        }
                        lazyObserver.unobserve(element);
                    }
                });
            });

            lazyElements.forEach(el => lazyObserver.observe(el));
        }

        // Debounce scroll events for performance
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            if (scrollTimeout) {
                clearTimeout(scrollTimeout);
            }
            scrollTimeout = setTimeout(() => {
                this.handleScroll();
            }, 16); // ~60fps
        }, { passive: true });
    },

    handleScroll() {
        // Add scroll-based effects here if needed
        const scrollTop = window.pageYOffset;
        const documentHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPercent = scrollTop / documentHeight;

        // Example: Update progress indicator
        const progressBar = document.querySelector('.reading-progress');
        if (progressBar) {
            progressBar.style.width = `${scrollPercent * 100}%`;
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    AboutPage.init();
    AboutPage.setupAccessibilityFeatures();
    AboutPage.setupPerformanceOptimizations();
});

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AboutPage;
}