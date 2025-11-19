/**
 * Galerly - Photographers Directory
 * Search and discover photographers by city
 */

let debounceTimeout = null;

// Load photographers on page load
document.addEventListener('DOMContentLoaded', function() {
    loadPhotographers();
    initializeCityAutocomplete();
});

// Fetch city suggestions from API
async function fetchCitySuggestions(query) {
    if (query.length < 2) return [];
    
    try {
        const apiUrl = `${window.GalerlyConfig.API_BASE_URL}/cities/search?q=${encodeURIComponent(query)}`;
        
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
            console.error('City search API error:', response.status);
            return [];
        }
        
        const data = await response.json();
        return data.cities || [];
    } catch (error) {
        console.error('City search error:', error);
        return [];
    }
}

// Show city suggestions
function showCitySuggestions(suggestions) {
    const dropdown = document.getElementById('citySuggestions');
    
    if (!dropdown) return;
    
    if (suggestions.length === 0) {
        dropdown.style.display = 'none';
        return;
    }
    
    dropdown.innerHTML = suggestions.map((city) => `
        <div class="city-suggestion-item" data-city="${city.display}" style="
            padding: 14px 18px;
            cursor: pointer;
            transition: background 0.2s ease;
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
            font-size: 1rem;
            color: var(--primary-900);
        " onmouseover="this.style.background='rgba(0, 0, 0, 0.03)'" 
           onmouseout="this.style.background='white'">
            ${city.display}
        </div>
    `).join('');
    
    dropdown.style.display = 'block';
    
    // Add click handlers to suggestions
    dropdown.querySelectorAll('.city-suggestion-item').forEach(item => {
        item.addEventListener('click', function() {
            const cityInput = document.getElementById('citySearch');
            if (cityInput) {
                cityInput.value = this.dataset.city;
                dropdown.style.display = 'none';
                // Trigger search with selected city
                searchPhotographers();
            }
        });
    });
}

// Initialize city autocomplete
function initializeCityAutocomplete() {
    const cityInput = document.getElementById('citySearch');
    const citySuggestions = document.getElementById('citySuggestions');
    
    if (!cityInput) {
        console.error('City search input not found!');
        return;
    }
    
    
    // Handle input with debouncing
    cityInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        
        // Clear previous timeout
        if (debounceTimeout) {
            clearTimeout(debounceTimeout);
        }
        
        // Hide suggestions if query is too short
        if (query.length < 2) {
            if (citySuggestions) citySuggestions.style.display = 'none';
            return;
        }
        
        // Debounce API calls (wait 300ms after user stops typing)
        debounceTimeout = setTimeout(async () => {
            const suggestions = await fetchCitySuggestions(query);
            showCitySuggestions(suggestions);
        }, 300);
    });
    
    // Close suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (citySuggestions && !cityInput.contains(e.target) && !citySuggestions.contains(e.target)) {
            citySuggestions.style.display = 'none';
        }
    });
    
    // Handle keyboard navigation (Escape to close, Enter to search)
    cityInput.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && citySuggestions) {
            citySuggestions.style.display = 'none';
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (citySuggestions) citySuggestions.style.display = 'none';
            searchPhotographers();
        }
    });
}

// Load all photographers from the backend
async function loadPhotographers(city = '') {
    const grid = document.getElementById('photographersGrid');
    const searchResults = document.getElementById('searchResults');
    
    try {
        // Build query parameters
        const params = city ? `?city=${encodeURIComponent(city)}` : '';
        
        // Fetch photographers from backend
        const response = await fetch(window.GalerlyConfig.API_BASE_URL + '/photographers' + params);
        
        if (!response.ok) {
            throw new Error('Failed to load photographers');
        }
        
        const data = await response.json();
        const photographers = data.photographers || [];
        
        // Update search results text
        if (city) {
            searchResults.textContent = photographers.length > 0 
                ? `Found ${photographers.length} photographer${photographers.length !== 1 ? 's' : ''} in ${city}`
                : `No photographers found in ${city}. Try another city.`;
        } else {
            searchResults.textContent = `Showing ${photographers.length} photographer${photographers.length !== 1 ? 's' : ''}`;
        }
        
        // Clear grid
        grid.innerHTML = '';
        
        if (photographers.length === 0) {
            grid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 60px; opacity: 0.6;">
                    <p style="font-size: 18px; margin-bottom: 12px;">No photographers found</p>
                    <p style="font-size: 14px;">${city ? 'Try searching for another city.' : 'Be the first photographer in your city!'}</p>
                </div>
            `;
            return;
        }
        
        // Render photographer cards
        photographers.forEach(photographer => {
            const card = createPhotographerCard(photographer);
            grid.appendChild(card);
        });
        
    } catch (error) {
        console.error('Error loading photographers:', error);
        grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 60px; opacity: 0.6;">
                <p style="font-size: 18px; margin-bottom: 12px; color: var(--color-error);">Failed to load photographers</p>
                <p style="font-size: 14px;">Please try again later.</p>
            </div>
        `;
    }
}

// Search photographers by city
function searchPhotographers() {
    const searchInput = document.getElementById('citySearch');
    const city = searchInput.value.trim();
    loadPhotographers(city);
}

// Create photographer card element
function createPhotographerCard(photographer) {
    const card = document.createElement('div');
    card.className = 'card-18 hero-10 animation-11 textarea-7';
    card.style.cursor = 'pointer';
    card.onclick = () => window.location.href = `portfolio?id=${photographer.id}`;
    
    // Get cover image (first gallery's first photo or placeholder)
    const coverImage = photographer.cover_image || 
                      (photographer.galleries && photographer.galleries[0] && photographer.galleries[0].photos && photographer.galleries[0].photos[0] && photographer.galleries[0].photos[0].url) ||
                      'https://via.placeholder.com/400x300?text=No+Cover+Image';
    
    card.innerHTML = `
        <div class="button-18 list-7" style="height: 100%;">
            <!-- Cover Image -->
            <div style="width: 100%; height: 240px; overflow: hidden; border-radius: var(--border-radius-m); margin-bottom: var(--size-l);">
                <img 
                    src="${coverImage}" 
                    alt="${photographer.name || photographer.username}'s work" 
                    style="width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s ease;"
                    onmouseover="this.style.transform='scale(1.05)'"
                    onmouseout="this.style.transform='scale(1)'"
                    onerror="this.src='https://via.placeholder.com/400x300?text=No+Cover+Image'"
                />
            </div>
            
            <!-- Photographer Info -->
            <div class="container-15 item-7">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: var(--size-m);">
                    <div style="flex: 1;">
                        <h3 class="grid-15 animation-7" style="margin-bottom: var(--size-xs);">
                            ${photographer.name || photographer.username || 'Anonymous'}
                        </h3>
                        <p style="color: var(--color-text-secondary); font-size: 0.9375rem; margin-bottom: var(--size-xs);">
                            ${photographer.city || 'Unknown City'}
                        </p>
                        ${photographer.specialties && photographer.specialties.length > 0 ? `
                            <p style="color: var(--color-text-secondary); font-size: 0.875rem;">
                                ${photographer.specialties.slice(0, 3).join(' • ')}
                            </p>
                        ` : ''}
                    </div>
                </div>
                
                <div class="input-15 background-7">
                    ${photographer.bio ? `
                        <p style="margin-bottom: var(--size-m); line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">
                            ${photographer.bio}
                        </p>
                    ` : ''}
                    
                    <div style="display: flex; gap: var(--size-l); color: var(--color-text-secondary); font-size: 0.875rem;">
                        <div>
                            <span style="font-weight: 600; color: var(--color-text-primary);">${photographer.gallery_count || 0}</span>
                            <span> galleries</span>
                        </div>
                        <div>
                            <span style="font-weight: 600; color: var(--color-text-primary);">${photographer.photo_count || 0}</span>
                            <span> photos</span>
                        </div>
                    </div>
                    
                    <div style="margin-top: var(--size-l);">
                        <a 
                            href="portfolio?id=${photographer.id}" 
                            onclick="event.stopPropagation();"
                            style="display: inline-flex; align-items: center; gap: var(--size-xs); color: var(--color-primary); font-weight: 600; text-decoration: none; transition: gap 0.2s ease;"
                            onmouseover="this.style.gap='var(--size-s)'"
                            onmouseout="this.style.gap='var(--size-xs)'"
                        >
                            View Portfolio
                            <svg width="17" height="14" viewBox="0 0 17 14" fill="none">
                                <path d="M10.6862 13.1281L16.1072 7.70711C16.4977 7.31658 16.4977 6.68342 16.1072 6.29289L10.6862 0.871896" stroke="currentColor" stroke-linecap="round"></path>
                                <path d="M1 7L16 7" stroke="currentColor" stroke-linecap="round"></path>
                            </svg>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    return card;
}

