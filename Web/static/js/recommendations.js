/* recommendations.js - Recommendations page functionality */

// Global variables
let currentRecommendations = [];
let savedDestinations = [];
let currentFilters = {};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeRecommendationsPage();
});

function initializeRecommendationsPage() {
    setupFilters();
    setupRecommendationCards();
    setupModifySearch();
    loadSavedDestinations();
    setupAccessibility();
}

// ===== FILTER FUNCTIONALITY =====

function setupFilters() {
    const filterInputs = document.querySelectorAll('.filter-range, .filter-checkbox');
    
    filterInputs.forEach(input => {
        input.addEventListener('change', handleFilterChange);
    });
    
    const resetButton = document.querySelector('.filters-reset');
    if (resetButton) {
        resetButton.addEventListener('click', resetFilters);
    }
}

function handleFilterChange(event) {
    const filterName = event.target.name;
    const filterValue = event.target.value;
    const filterType = event.target.type;
    
    if (filterType === 'range') {
        currentFilters[filterName] = parseFloat(filterValue);
        updateRangeDisplay(event.target);
    } else if (filterType === 'checkbox') {
        currentFilters[filterName] = event.target.checked;
    }
    
    // Debounce filter application
    clearTimeout(window.filterTimeout);
    window.filterTimeout = setTimeout(() => {
        applyFilters();
    }, 300);
}

function updateRangeDisplay(rangeInput) {
    const valueDisplay = rangeInput.parentNode.querySelector('.filter-current-value');
    if (valueDisplay) {
        valueDisplay.textContent = rangeInput.value;
    }
    
    // Update range background
    const percent = ((rangeInput.value - rangeInput.min) / (rangeInput.max - rangeInput.min)) * 100;
    rangeInput.style.background = `linear-gradient(to right, var(--accent-orange) 0%, var(--accent-orange) ${percent}%, #ddd ${percent}%, #ddd 100%)`;
}

function applyFilters() {
    const cards = document.querySelectorAll('.recommendation-card');
    let visibleCount = 0;
    
    cards.forEach(card => {
        const shouldShow = matchesFilters(card);
        card.style.display = shouldShow ? 'block' : 'none';
        if (shouldShow) visibleCount++;
    });
    
    updateResultsCount(visibleCount);
    
    // Show no results message if needed
    if (visibleCount === 0) {
        showNoResultsMessage();
    } else {
        hideNoResultsMessage();
    }
}

function matchesFilters(card) {
    // Extract data attributes from card
    const cardData = {
        score: parseFloat(card.dataset.score || 0),
        distance: parseFloat(card.dataset.distance || 0),
        elevation: parseFloat(card.dataset.elevation || 0),
        difficulty: parseInt(card.dataset.difficulty || 1),
        snowDepth: parseFloat(card.dataset.snowDepth || 0),
        avalancheRisk: parseInt(card.dataset.avalancheRisk || 1)
    };
    
    // Check each filter
    for (const [filterName, filterValue] of Object.entries(currentFilters)) {
        if (!checkFilter(filterName, filterValue, cardData)) {
            return false;
        }
    }
    
    return true;
}

function checkFilter(filterName, filterValue, cardData) {
    switch (filterName) {
        case 'minScore':
            return cardData.score >= filterValue;
        case 'maxDistance':
            return cardData.distance <= filterValue;
        case 'maxElevation':
            return cardData.elevation <= filterValue;
        case 'maxDifficulty':
            return cardData.difficulty <= filterValue;
        case 'minSnowDepth':
            return cardData.snowDepth >= filterValue;
        case 'maxAvalancheRisk':
            return cardData.avalancheRisk <= filterValue;
        case 'beginner_friendly':
            return !filterValue || cardData.difficulty <= 2;
        case 'powder_focus':
            return !filterValue || cardData.snowDepth >= 40;
        default:
            return true;
    }
}

function resetFilters() {
    currentFilters = {};
    
    // Reset all form inputs
    const filterInputs = document.querySelectorAll('.filter-range, .filter-checkbox');
    filterInputs.forEach(input => {
        if (input.type === 'range') {
            input.value = input.defaultValue || input.min;
            updateRangeDisplay(input);
        } else if (input.type === 'checkbox') {
            input.checked = false;
        }
    });
    
    // Show all cards
    const cards = document.querySelectorAll('.recommendation-card');
    cards.forEach(card => {
        card.style.display = 'block';
    });
    
    hideNoResultsMessage();
    updateResultsCount(cards.length);
}

function updateResultsCount(count) {
    const countElement = document.querySelector('.results-count');
    if (countElement) {
        countElement.textContent = `${count} destination${count !== 1 ? 's' : ''} found`;
    }
}

function showNoResultsMessage() {
    let noResultsEl = document.querySelector('.no-results');
    if (!noResultsEl) {
        noResultsEl = createNoResultsMessage();
        const grid = document.querySelector('.recommendations-grid');
        if (grid) {
            grid.parentNode.insertBefore(noResultsEl, grid.nextSibling);
        }
    }
    noResultsEl.style.display = 'block';
}

function hideNoResultsMessage() {
    const noResultsEl = document.querySelector('.no-results');
    if (noResultsEl) {
        noResultsEl.style.display = 'none';
    }
}

function createNoResultsMessage() {
    const noResults = document.createElement('div');
    noResults.className = 'no-results';
    noResults.innerHTML = `
        <div class="no-results-icon">🔍</div>
        <h3 class="no-results-title">No destinations match your filters</h3>
        <p class="no-results-text">
            Try adjusting your filters or modify your search criteria to find more options.
        </p>
        <div class="no-results-actions">
            <button class="btn btn-primary" onclick="resetFilters()">
                Clear All Filters
            </button>
            <button class="btn btn-outline" onclick="modifySearch()">
                Modify Search
            </button>
        </div>
    `;
    return noResults;
}

// ===== RECOMMENDATION CARDS =====

function setupRecommendationCards() {
    const cards = document.querySelectorAll('.recommendation-card');
    
    cards.forEach(card => {
        setupCardInteractions(card);
        setupSaveButton(card);
        setupDetailsButton(card);
    });
}

function setupCardInteractions(card) {
    // Add keyboard navigation
    card.setAttribute('tabindex', '0');
    
    card.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            const detailsButton = card.querySelector('.btn-details');
            if (detailsButton) {
                detailsButton.click();
            }
        }
    });
    
    // Add hover effects
    card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-8px)';
    });
    
    card.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
    });
}

function setupSaveButton(card) {
    const saveButton = card.querySelector('.btn-save');
    if (!saveButton) return;
    
    const destinationId = card.dataset.destinationId;
    
    // Check if already saved
    if (savedDestinations.includes(destinationId)) {
        saveButton.classList.add('saved');
        saveButton.innerHTML = '💾';
        saveButton.title = 'Remove from saved destinations';
    }
    
    saveButton.addEventListener('click', function(event) {
        event.stopPropagation();
        toggleSaveDestination(destinationId, saveButton);
    });
}

function setupDetailsButton(card) {
    const detailsButton = card.querySelector('.btn-details');
    if (!detailsButton) return;
    
    const destinationId = card.dataset.destinationId;
    
    detailsButton.addEventListener('click', function() {
        showDestinationDetails(destinationId);
    });
}

function toggleSaveDestination(destinationId, button) {
    const isSaved = savedDestinations.includes(destinationId);
    
    if (isSaved) {
        // Remove from saved
        savedDestinations = savedDestinations.filter(id => id !== destinationId);
        button.classList.remove('saved');
        button.innerHTML = '🤍';
        button.title = 'Save destination';
        showNotification('Destination removed from saved list', 'info');
    } else {
        // Add to saved
        savedDestinations.push(destinationId);
        button.classList.add('saved');
        button.innerHTML = '💾';
        button.title = 'Remove from saved destinations';
        showNotification('Destination saved!', 'success');
    }
    
    // Save to local storage
    saveSavedDestinations();
}

function showDestinationDetails(destinationId) {
    // In a real app, this would open a modal or navigate to a details page
    const card = document.querySelector(`[data-destination-id="${destinationId}"]`);
    if (!card) return;
    
    const destinationName = card.querySelector('.destination-name').textContent;
    
    // Create modal or navigate to details page
    alert(`Would show detailed information for: ${destinationName}\n\nThis would include:\n- Detailed route information\n- Current conditions\n- Safety recommendations\n- Route maps\n- User reviews`);
}

// ===== MODIFY SEARCH =====

function setupModifySearch() {
    const modifyButton = document.querySelector('.modify-search');
    if (modifyButton) {
        modifyButton.addEventListener('click', modifySearch);
    }
}

function modifySearch() {
    // Navigate back to location page to modify search
    window.location.href = '/location';
}

// ===== SAVED DESTINATIONS =====

function loadSavedDestinations() {
    const saved = localStorage.getItem('savedDestinations');
    if (saved) {
        try {
            savedDestinations = JSON.parse(saved);
        } catch (error) {
            console.error('Error loading saved destinations:', error);
            savedDestinations = [];
        }
    }
}

function saveSavedDestinations() {
    try {
        localStorage.setItem('savedDestinations', JSON.stringify(savedDestinations));
    } catch (error) {
        console.error('Error saving destinations:', error);
    }
}

// ===== UTILITY FUNCTIONS =====

function showNotification(message, type = 'info') {
    // Remove existing notification
    const existing = document.querySelector('.notification');
    if (existing) {
        existing.remove();
    }
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Style notification
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        background: type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db',
        color: 'white',
        padding: '12px 20px',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        zIndex: '10000',
        transform: 'translateX(100%)',
        transition: 'transform 0.3s ease'
    });
    
    // Add to page
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Hide notification
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
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

// ===== ACCESSIBILITY =====

function setupAccessibility() {
    // Add ARIA labels and roles
    const recommendationsGrid = document.querySelector('.recommendations-grid');
    if (recommendationsGrid) {
        recommendationsGrid.setAttribute('role', 'list');
        recommendationsGrid.setAttribute('aria-label', 'Ski touring recommendations');
    }
    
    const cards = document.querySelectorAll('.recommendation-card');
    cards.forEach((card, index) => {
        card.setAttribute('role', 'listitem');
        card.setAttribute('aria-label', `Recommendation ${index + 1}`);
    });
    
    // Add keyboard navigation for filters
    const filterInputs = document.querySelectorAll('.filter-range');
    filterInputs.forEach(input => {
        input.addEventListener('keydown', function(event) {
            const step = parseFloat(this.step) || 1;
            let newValue = parseFloat(this.value);
            
            switch (event.key) {
                case 'ArrowLeft':
                case 'ArrowDown':
                    newValue = Math.max(parseFloat(this.min), newValue - step);
                    break;
                case 'ArrowRight':
                case 'ArrowUp':
                    newValue = Math.min(parseFloat(this.max), newValue + step);
                    break;
                case 'Home':
                    newValue = parseFloat(this.min);
                    break;
                case 'End':
                    newValue = parseFloat(this.max);
                    break;
                default:
                    return;
            }
            
            this.value = newValue;
            updateRangeDisplay(this);
            handleFilterChange({ target: this });
        });
    });
}

// ===== ANIMATION UTILITIES =====

function animateCards() {
    const cards = document.querySelectorAll('.recommendation-card');
    
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

// ===== EXPORT FOR GLOBAL ACCESS =====

// Make functions available globally for HTML event handlers
window.resetFilters = resetFilters;
window.modifySearch = modifySearch;
window.toggleSaveDestination = toggleSaveDestination;
window.showDestinationDetails = showDestinationDetails;

// Initialize animations when page loads
window.addEventListener('load', function() {
    // Add loading delay to see the effect
    setTimeout(animateCards, 200);
});