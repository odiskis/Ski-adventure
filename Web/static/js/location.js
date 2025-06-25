/* location.js - Location page functionality */

// Global variables
let locationSuggestions = [];
let selectedLocation = null;
let debounceTimer = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeLocationPage();
});

function initializeLocationPage() {
    setupLocationInput();
    setupDistanceSelection();
    setupFormSubmission();
    setupExampleLocations();
    setupModalHandlers();
}

// ===== LOCATION INPUT FUNCTIONALITY =====

function setupLocationInput() {
    const locationInput = document.getElementById('locationInput');
    if (!locationInput) return;
    
    locationInput.addEventListener('input', handleLocationInput);
    locationInput.addEventListener('blur', handleLocationBlur);
    locationInput.addEventListener('focus', handleLocationFocus);
    locationInput.addEventListener('keydown', handleLocationKeydown);
}

function handleLocationInput(event) {
    clearTimeout(debounceTimer);
    const query = event.target.value.trim();
    
    clearLocationError();
    
    if (query.length < 2) {
        hideSuggestions();
        return;
    }
    
    debounceTimer = setTimeout(() => {
        searchLocations(query);
    }, 300);
}

function handleLocationBlur() {
    // Delay hiding suggestions to allow clicking
    setTimeout(hideSuggestions, 200);
}

function handleLocationFocus(event) {
    const query = event.target.value.trim();
    if (query.length >= 2) {
        searchLocations(query);
    }
}

function handleLocationKeydown(event) {
    const dropdown = document.getElementById('locationSuggestions');
    const suggestions = dropdown.querySelectorAll('.suggestion-item');
    
    if (suggestions.length === 0) return;
    
    const currentSelected = dropdown.querySelector('.suggestion-item.selected');
    let selectedIndex = currentSelected ? Array.from(suggestions).indexOf(currentSelected) : -1;
    
    switch (event.key) {
        case 'ArrowDown':
            event.preventDefault();
            selectedIndex = Math.min(selectedIndex + 1, suggestions.length - 1);
            updateSelectedSuggestion(suggestions, selectedIndex);
            break;
            
        case 'ArrowUp':
            event.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, -1);
            updateSelectedSuggestion(suggestions, selectedIndex);
            break;
            
        case 'Enter':
            event.preventDefault();
            if (currentSelected) {
                selectLocation(currentSelected.dataset.index);
            }
            break;
            
        case 'Escape':
            hideSuggestions();
            break;
    }
}

async function searchLocations(query) {
    try {
        // Mock location search for now - replace with real API call
        const mockSuggestions = generateMockSuggestions(query);
        
        if (mockSuggestions && mockSuggestions.length > 0) {
            showSuggestions(mockSuggestions);
        } else {
            hideSuggestions();
        }
        
    } catch (error) {
        console.error('Location search error:', error);
        hideSuggestions();
    }
}

function generateMockSuggestions(query) {
    const norwegianCities = [
        { name: 'Oslo', region: 'Oslo', lat: 59.9139, lon: 10.7522 },
        { name: 'Bergen', region: 'Vestland', lat: 60.3913, lon: 5.3221 },
        { name: 'Trondheim', region: 'Trøndelag', lat: 63.4305, lon: 10.3951 },
        { name: 'Stavanger', region: 'Rogaland', lat: 58.9700, lon: 5.7331 },
        { name: 'Tromsø', region: 'Troms og Finnmark', lat: 69.6496, lon: 18.9560 },
        { name: 'Drammen', region: 'Viken', lat: 59.7432, lon: 10.2045 },
        { name: 'Fredrikstad', region: 'Viken', lat: 59.2181, lon: 10.9298 },
        { name: 'Kristiansand', region: 'Agder', lat: 58.1467, lon: 7.9956 },
        { name: 'Sandnes', region: 'Rogaland', lat: 58.8518, lon: 5.7362 },
        { name: 'Ålesund', region: 'Møre og Romsdal', lat: 62.4722, lon: 6.1495 },
        { name: 'Bodø', region: 'Nordland', lat: 67.2804, lon: 14.4040 },
        { name: 'Molde', region: 'Møre og Romsdal', lat: 62.7378, lon: 7.1605 },
        { name: 'Lillehammer', region: 'Innlandet', lat: 61.1153, lon: 10.4662 },
        { name: 'Mo i Rana', region: 'Nordland', lat: 66.3142, lon: 14.1426 },
        { name: 'Narvik', region: 'Nordland', lat: 68.4385, lon: 17.4272 }
    ];
    
    const lowerQuery = query.toLowerCase();
    return norwegianCities
        .filter(city => city.name.toLowerCase().includes(lowerQuery))
        .slice(0, 5)
        .map((city, index) => ({
            id: index,
            name: city.name,
            region: city.region,
            country: 'Norway',
            lat: city.lat,
            lon: city.lon,
            display_name: `${city.name}, ${city.region}, Norway`
        }));
}

function showSuggestions(suggestions) {
    const dropdown = document.getElementById('locationSuggestions');
    dropdown.innerHTML = '';
    
    suggestions.forEach((suggestion, index) => {
        const item = document.createElement('div');
        item.className = 'suggestion-item';
        item.dataset.index = index;
        item.innerHTML = `
            <div class="suggestion-main">${suggestion.name}</div>
            <div class="suggestion-detail">${suggestion.region}, ${suggestion.country}</div>
        `;
        
        item.addEventListener('click', () => selectLocation(index));
        dropdown.appendChild(item);
    });
    
    locationSuggestions = suggestions;
    dropdown.classList.remove('hidden');
}

function hideSuggestions() {
    const dropdown = document.getElementById('locationSuggestions');
    dropdown.classList.add('hidden');
    dropdown.innerHTML = '';
}

function updateSelectedSuggestion(suggestions, selectedIndex) {
    suggestions.forEach((item, index) => {
        item.classList.toggle('selected', index === selectedIndex);
    });
}

function selectLocation(index) {
    const suggestion = locationSuggestions[index];
    if (!suggestion) return;
    
    selectedLocation = suggestion;
    
    const locationInput = document.getElementById('locationInput');
    locationInput.value = suggestion.name;
    locationInput.classList.add('valid');
    
    hideSuggestions();
    showLocationPreview(suggestion);
    clearLocationError();
}

function showLocationPreview(location) {
    const preview = document.getElementById('locationPreview');
    if (!preview) return;
    
    preview.innerHTML = `
        <div class="preview-header">
            <span class="preview-icon">📍</span>
            <span class="preview-title">Selected Location</span>
        </div>
        <div class="preview-details">
            <strong>${location.name}</strong><br>
            ${location.region}, ${location.country}<br>
            <small>Coordinates: ${location.lat.toFixed(4)}, ${location.lon.toFixed(4)}</small>
        </div>
    `;
    
    preview.classList.add('show');
}

// ===== EXAMPLE LOCATIONS =====

function setupExampleLocations() {
    // This function is called from the HTML template
}

function selectExample(cityName) {
    const locationInput = document.getElementById('locationInput');
    locationInput.value = cityName;
    locationInput.focus();
    
    // Trigger search for this city
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        searchLocations(cityName);
    }, 100);
}

// ===== DISTANCE SELECTION =====

function setupDistanceSelection() {
    const radioButtons = document.querySelectorAll('input[name="max_hours"]');
    const distanceOptions = document.querySelectorAll('.distance-option');
    
    radioButtons.forEach(radio => {
        radio.addEventListener('change', function() {
            updateDistanceSelection(this.value);
        });
    });
    
    distanceOptions.forEach(option => {
        option.addEventListener('click', function() {
            const radio = option.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
                updateDistanceSelection(radio.value);
            }
        });
    });
    
    // Set default selection
    const defaultOption = document.querySelector('input[name="max_hours"][value="3"]');
    if (defaultOption) {
        defaultOption.checked = true;
        updateDistanceSelection('3');
    }
}

function updateDistanceSelection(selectedValue) {
    const options = document.querySelectorAll('.distance-option');
    
    options.forEach(option => {
        const radio = option.querySelector('input[type="radio"]');
        if (radio && radio.value === selectedValue) {
            option.classList.add('selected');
        } else {
            option.classList.remove('selected');
        }
    });
    
    // Show travel info for longer distances
    if (parseInt(selectedValue) >= 4) {
        showTravelInfo();
    }
}

// ===== FORM SUBMISSION =====

function setupFormSubmission() {
    const form = document.getElementById('locationForm');
    if (!form) return;
    
    form.addEventListener('submit', handleFormSubmit);
}

async function handleFormSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const locationInput = formData.get('location');
    const maxHours = formData.get('max_hours') || 3;
    
    // Validate location
    if (!locationInput || !locationInput.trim()) {
        showLocationError('Please enter a starting location.');
        return;
    }
    
    // Show loading state
    const submitButton = form.querySelector('.btn-primary');
    const originalText = submitButton.textContent;
    submitButton.textContent = 'Finding destinations...';
    submitButton.disabled = true;
    
    try {
        const locationData = {
            location: locationInput.trim(),
            max_hours: parseInt(maxHours)
        };
        
        const response = await fetch('/location', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(locationData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Navigate to recommendations
            window.location.href = result.redirect;
        } else {
            showLocationError(result.error || 'Please check your location and try again.');
        }
        
    } catch (error) {
        console.error('Location submission error:', error);
        showLocationError('Network error. Please check your connection and try again.');
    } finally {
        // Reset button state
        submitButton.textContent = originalText;
        submitButton.disabled = false;
    }
}

// ===== ERROR HANDLING =====

function showLocationError(message) {
    const errorEl = document.getElementById('locationError');
    const locationInput = document.getElementById('locationInput');
    
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.classList.remove('hidden');
    }
    
    if (locationInput) {
        locationInput.classList.add('error');
    }
}

function clearLocationError() {
    const errorEl = document.getElementById('locationError');
    const locationInput = document.getElementById('locationInput');
    
    if (errorEl) {
        errorEl.classList.add('hidden');
    }
    
    if (locationInput) {
        locationInput.classList.remove('error');
    }
}

// ===== MODAL HANDLERS =====

function setupModalHandlers() {
    // Close modal when clicking outside
    document.addEventListener('click', function(event) {
        const modal = event.target.closest('.modal');
        if (modal && event.target === modal) {
            modal.classList.add('hidden');
        }
    });
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const visibleModal = document.querySelector('.modal:not(.hidden)');
            if (visibleModal) {
                visibleModal.classList.add('hidden');
            }
        }
    });
}

function showTravelInfo() {
    const modal = document.getElementById('travelInfoModal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

function closeTravelInfo() {
    const modal = document.getElementById('travelInfoModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// ===== UTILITY FUNCTIONS =====

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Hide and remove notification
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 5000);
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
    const locationInput = document.getElementById('locationInput');
    const suggestionsDropdown = document.getElementById('locationSuggestions');
    
    if (locationInput && suggestionsDropdown) {
        locationInput.setAttribute('aria-expanded', 'false');
        locationInput.setAttribute('aria-haspopup', 'listbox');
        locationInput.setAttribute('aria-controls', 'locationSuggestions');
        
        suggestionsDropdown.setAttribute('role', 'listbox');
    }
    
    // Update ARIA states when suggestions are shown/hidden
    const originalShowSuggestions = showSuggestions;
    showSuggestions = function(suggestions) {
        originalShowSuggestions(suggestions);
        if (locationInput) {
            locationInput.setAttribute('aria-expanded', 'true');
        }
    };
    
    const originalHideSuggestions = hideSuggestions;
    hideSuggestions = function() {
        originalHideSuggestions();
        if (locationInput) {
            locationInput.setAttribute('aria-expanded', 'false');
        }
    };
}

// Initialize accessibility features
document.addEventListener('DOMContentLoaded', setupAccessibility);

// ===== EXPORT FOR GLOBAL ACCESS =====

// Make functions available globally for HTML event handlers
window.selectExample = selectExample;
window.showTravelInfo = showTravelInfo;
window.closeTravelInfo = closeTravelInfo;