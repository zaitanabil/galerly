/**
 * City Autocomplete Component
 * Provides fast city search with autocomplete dropdown
 * Uses the /v1/cities/search API endpoint with prefix indexing
 */

/**
 * Initialize city autocomplete on an input field
 * @param {string} inputId - The ID of the input element
 * @param {function} onSelect - Callback when a city is selected: (city) => void
 * @param {string} placeholder - Optional placeholder text
 * @param {string} dropdownId - Optional ID of existing dropdown container (if not provided, creates one)
 */
function initCityAutocomplete(inputId, onSelect, placeholder = 'Start typing a city name...', dropdownId = null) {
    const input = document.getElementById(inputId);
    if (!input) {
        console.error(`City autocomplete: Input element #${inputId} not found`);
        return;
    }

    // Set placeholder if provided
    if (placeholder && placeholder !== 'Start typing a city name...') {
        input.placeholder = placeholder;
    }

    // Use existing dropdown or create new one
    let dropdown;
    if (dropdownId) {
        dropdown = document.getElementById(dropdownId);
        if (!dropdown) {
            console.error(`City autocomplete: Dropdown element #${dropdownId} not found`);
            return;
        }
        console.log(`🔍 Using existing dropdown: #${dropdownId}`);
    } else {
        // Create dropdown container
        dropdown = document.createElement('div');
        dropdown.className = 'city-autocomplete-dropdown';
        dropdown.style.display = 'none';
        input.parentNode.style.position = 'relative';
        input.parentNode.appendChild(dropdown);
        console.log('🔍 Created new dropdown container');
    }

    let currentRequest = null;
    let selectedIndex = -1;

    // Search cities with debouncing
    let debounceTimer;
    input.addEventListener('input', async function() {
        const query = this.value.trim();

        // Clear previous timer
        clearTimeout(debounceTimer);

        // Hide dropdown if query is too short
        if (query.length < 1) {
            dropdown.style.display = 'none';
            return;
        }

        // Debounce: wait 200ms after user stops typing
        debounceTimer = setTimeout(async () => {
            try {
                // Cancel previous request if it exists
                if (currentRequest) {
                    currentRequest.abort();
                }

                // Create new request with AbortController
                const controller = new AbortController();
                currentRequest = controller;

                const apiUrl = window.GalerlyConfig?.API_BASE_URL || window.API_BASE_URL || 'http://localhost:5001/v1';
                console.log(`🔍 City search API URL: ${apiUrl}/cities/search?q=${encodeURIComponent(query)}`);
                const response = await fetch(`${apiUrl}/cities/search?q=${encodeURIComponent(query)}`, {
                    signal: controller.signal
                });

                if (!response.ok) {
                    throw new Error(`City search failed: ${response.status}`);
                }

                const data = await response.json();
                console.log('🔍 City search response:', data);
                console.log('🔍 First city:', data.cities?.[0]);
                console.log('🔍 First city display_name:', data.cities?.[0]?.display_name);
                displayResults(data.cities || []);
            } catch (error) {
                if (error.name !== 'AbortError') {
                    console.error('City search error:', error);
                    dropdown.style.display = 'none';
                }
            }
        }, 200);
    });

    // Display search results
    function displayResults(cities) {
        console.log('🔍 displayResults called with:', cities.length, 'cities');
        console.log('🔍 First city in displayResults:', cities[0]);
        
        dropdown.innerHTML = '';
        selectedIndex = -1;

        if (cities.length === 0) {
            dropdown.style.display = 'none';
            return;
        }

        cities.forEach((city, index) => {
            console.log(`🔍 Processing city ${index}:`, city);
            console.log(`🔍 display_name value:`, city.display_name);
            console.log(`🔍 display_name type:`, typeof city.display_name);
            
            const item = document.createElement('div');
            item.className = 'city-autocomplete-item';
            
            // Fallback if display_name is undefined
            const displayText = city.display_name || `${city.city_ascii || city.city}, ${city.country}`;
            console.log(`🔍 Using display text:`, displayText);
            
            item.textContent = displayText;
            item.dataset.index = index;
            
            // Add inline styles for compatibility with existing dropdowns
            item.style.cssText = `
                padding: 12px 16px;
                cursor: pointer;
                transition: background 0.2s;
                font-size: 15px;
                color: #1D1D1F;
                border-bottom: 1px solid rgba(0, 0, 0, 0.05);
            `;

            // Store full city data
            item.dataset.cityData = JSON.stringify(city);

            // Hover effect
            item.addEventListener('mouseenter', function() {
                removeActiveClass();
                this.classList.add('active');
                this.style.background = '#F5F5F7';
                selectedIndex = index;
            });
            
            item.addEventListener('mouseleave', function() {
                if (!this.classList.contains('active')) {
                    this.style.background = 'transparent';
                }
            });

            // Click handler
            item.addEventListener('click', function() {
                selectCity(JSON.parse(this.dataset.cityData));
            });

            dropdown.appendChild(item);
        });

        dropdown.style.display = 'block';
    }

    // Select a city
    function selectCity(city) {
        console.log('🔍 selectCity called with:', city);
        const displayText = city.display_name || `${city.city_ascii || city.city}, ${city.country}`;
        console.log('🔍 Setting input value to:', displayText);
        input.value = displayText;
        dropdown.style.display = 'none';
        if (onSelect) {
            onSelect(city);
        }
    }

    // Remove active class from all items
    function removeActiveClass() {
        const items = dropdown.querySelectorAll('.city-autocomplete-item');
        items.forEach(item => item.classList.remove('active'));
    }

    // Keyboard navigation
    input.addEventListener('keydown', function(e) {
        const items = dropdown.querySelectorAll('.city-autocomplete-item');
        
        if (items.length === 0) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
            removeActiveClass();
            items[selectedIndex].classList.add('active');
            items[selectedIndex].scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, 0);
            removeActiveClass();
            items[selectedIndex].classList.add('active');
            items[selectedIndex].scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (selectedIndex >= 0 && items[selectedIndex]) {
                const cityData = JSON.parse(items[selectedIndex].dataset.cityData);
                selectCity(cityData);
            }
        } else if (e.key === 'Escape') {
            dropdown.style.display = 'none';
            selectedIndex = -1;
        }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!input.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.style.display = 'none';
        }
    });

    // Close dropdown when input loses focus (delayed to allow clicks)
    input.addEventListener('blur', function() {
        setTimeout(() => {
            dropdown.style.display = 'none';
        }, 200);
    });
}

// Add CSS styles for autocomplete dropdown
if (!document.getElementById('city-autocomplete-styles')) {
    const style = document.createElement('style');
    style.id = 'city-autocomplete-styles';
    style.textContent = `
        .city-autocomplete-dropdown {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-radius: 12px;
            margin-top: 4px;
            max-height: 300px;
            overflow-y: auto;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 1000;
        }

        .city-autocomplete-item {
            padding: 12px 16px;
            cursor: pointer;
            transition: background 0.2s;
            font-size: 15px;
            color: #1D1D1F;
        }

        .city-autocomplete-item:hover,
        .city-autocomplete-item.active {
            background: #F5F5F7;
        }

        .city-autocomplete-item:first-child {
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
        }

        .city-autocomplete-item:last-child {
            border-bottom-left-radius: 12px;
            border-bottom-right-radius: 12px;
        }
    `;
    document.head.appendChild(style);
}

