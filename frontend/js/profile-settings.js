/**
 * Profile Settings - City Autocomplete
 */
let debounceTimeout = null;
// Load current profile data
async function loadProfileData() {
    try {
        const response = await fetch(`${window.GalerlyConfig.API_BASE_URL}/auth/me`, {
            credentials: 'include',  // Send HttpOnly cookie
            headers: {
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) {
            console.error('Failed to load profile, redirecting to login...');
            localStorage.removeItem('galerly_user_data');
            window.location.href = 'auth';
            return;
        }
        const user = await response.json();
        // Populate form
        const nameInput = document.getElementById('name');
        const usernameInput = document.getElementById('username');
        const bioInput = document.getElementById('bio');
        const cityInput = document.getElementById('city');
        if (nameInput) nameInput.value = user.name || '';
        if (usernameInput) usernameInput.value = user.username || '';
        if (bioInput) bioInput.value = user.bio || '';
        if (cityInput) cityInput.value = user.city || '';
        // Enable scrollbar after data loads
        const formWrapper = document.querySelector('.profile-form-wrapper');
        if (formWrapper) {
            formWrapper.classList.add('loaded');
        }
    } catch (error) {
        console.error('Error loading profile:', error);
        showMessage('Failed to load profile data. Please try again.', 'error');
        // Still enable scrollbar even on error
        const formWrapper = document.querySelector('.profile-form-wrapper');
        if (formWrapper) {
            formWrapper.classList.add('loaded');
        }
    }
}
// Fetch city suggestions from API
async function fetchCitySuggestions(query) {
    if (query.length < 2) return [];
    try {
        const apiUrl = `${window.GalerlyConfig.API_BASE_URL}/cities/search?q=${encodeURIComponent(query)}`;
        const response = await fetch(apiUrl);
        if (!response.ok) {
            console.error('[Profile] City search API error:', response.status);
            return [];
        }
        const data = await response.json();
        return data.cities || [];
    } catch (error) {
        console.error('[Profile] City search error:', error);
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
    dropdown.innerHTML = suggestions.map((city, index) => `
        <div class="city-suggestion-item" data-city="${city.display}" style="
            padding: 12px 16px;
            cursor: pointer;
            transition: background 0.2s ease;
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
            font-size: 14px;
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
            const cityInput = document.getElementById('city');
            if (cityInput) {
                cityInput.value = this.dataset.city;
                dropdown.style.display = 'none';
            }
        });
    });
}
// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Check if config is loaded
    if (!window.GalerlyConfig) {
        console.error('❌ GalerlyConfig not loaded!');
    } else {
    }
    // Load profile data
    loadProfileData();
    // Setup city autocomplete
    const cityInput = document.getElementById('city');
    const citySuggestions = document.getElementById('citySuggestions');
    if (!cityInput) {
        console.error('❌ City input not found!');
    } else {
    }
    if (!citySuggestions) {
        console.error('❌ City suggestions dropdown not found!');
    } else {
    }
    if (cityInput) {
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
        // Handle keyboard navigation (Escape to close)
        cityInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && citySuggestions) {
                citySuggestions.style.display = 'none';
            }
        });
    }
    // Setup form submission
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const name = document.getElementById('name').value.trim();
            const username = document.getElementById('username').value.trim();
            const bio = document.getElementById('bio').value.trim();
            const city = document.getElementById('city').value.trim();
            if (!name || !username) {
                showMessage('Please fill in your name and username', 'error');
                return;
            }
            if (!city) {
                showMessage('Please add your city', 'error');
                return;
            }
            try {
                const response = await fetch(`${window.GalerlyConfig.API_BASE_URL}/profile`, {
                    method: 'PUT',
                    credentials: 'include',  // Send HttpOnly cookie
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        name: name,
                        username: username,
                        bio: bio,
                        city: city
                    })
                });
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to update profile');
                }
                showMessage('Profile updated successfully!', 'success');
            } catch (error) {
                console.error('Error updating profile:', error);
                showMessage(error.message || 'Failed to update profile. Please try again.', 'error');
            }
        });
    }
});
// Show status message
function showMessage(message, type) {
    const statusDiv = document.getElementById('statusMessage');
    if (statusDiv) {
        // Remove any existing classes
        statusDiv.className = '';
        // Set the message
        statusDiv.textContent = message;
        // Add the appropriate class
        if (type === 'success') {
            statusDiv.classList.add('success');
        } else if (type === 'error') {
            statusDiv.classList.add('error');
        }
        // Show the message
        statusDiv.style.display = 'block';
        // Auto-hide after 5 seconds
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    } else {
        // Fallback to console
        console.error(`Status message error - ${type}: ${message}`);
    }
}