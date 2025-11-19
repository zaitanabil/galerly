/**
 * Notification Preferences Handler
 * Manages email notification settings for photographers
 */
(function() {
    'use strict';
    // Default preferences
    const defaultPreferences = {
        client_notifications: {
            gallery_shared: true,
            new_photos_added: true,
            gallery_ready: true,
            selection_reminder: true,
            gallery_expiring: true,
            custom_messages: true
        },
        photographer_notifications: {
            client_selected_photos: true,
            client_feedback_received: true
        }
    };
    // Load notification preferences
    async function loadNotificationPreferences() {
        try {
            const response = await fetch(`${window.GalerlyConfig.API_BASE_URL}/notifications/preferences`, {
                method: 'GET',
                credentials: 'include',  // Send HttpOnly cookie
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            if (!response.ok) {
                throw new Error('Failed to load notification preferences');
            }
            const data = await response.json();
            if (data.success && data.preferences) {
                applyPreferencesToUI(data.preferences);
            }
        } catch (error) {
            console.error('Error loading notification preferences:', error);
            // Apply defaults if error
            applyPreferencesToUI({
                client_notifications: defaultPreferences.client_notifications,
                photographer_notifications: defaultPreferences.photographer_notifications
            });
        }
    }
    // Apply preferences to UI
    function applyPreferencesToUI(preferences) {
        const clientPrefs = preferences.client_notifications || {};
        const photographerPrefs = preferences.photographer_notifications || {};
        
        // Helper function to safely set checkbox
        const setCheckbox = (id, value) => {
            const element = document.getElementById(id);
            if (element) {
                element.checked = value !== false;
            }
        };
        
        // Client notifications (notify clients when...)
        setCheckbox('notify_gallery_shared', clientPrefs.gallery_shared);
        setCheckbox('notify_gallery_ready', clientPrefs.gallery_ready);
        setCheckbox('notify_selection_reminder', clientPrefs.selection_reminder);
        setCheckbox('notify_gallery_expiring', clientPrefs.gallery_expiring);
        setCheckbox('notify_custom_messages', clientPrefs.custom_messages);
        
        // Photographer notifications (notify me when...)
        setCheckbox('notify_client_selected_photos', photographerPrefs.client_selected_photos);
        setCheckbox('notify_client_feedback_received', photographerPrefs.client_feedback_received);
    }
    // Save notification preferences
    async function saveNotificationPreferences() {
        try {
            // Helper function to safely get checkbox value
            const getCheckbox = (id) => {
                const element = document.getElementById(id);
                return element ? element.checked : true; // Default to true if not found
            };
            
            // Gather current preferences from UI
            const preferences = {
                client_notifications: {
                    gallery_shared: getCheckbox('notify_gallery_shared'),
                    new_photos_added: true, // Always enabled (sent manually from gallery)
                    gallery_ready: getCheckbox('notify_gallery_ready'),
                    selection_reminder: getCheckbox('notify_selection_reminder'),
                    gallery_expiring: getCheckbox('notify_gallery_expiring'),
                    custom_messages: getCheckbox('notify_custom_messages')
                },
                photographer_notifications: {
                    client_selected_photos: getCheckbox('notify_client_selected_photos'),
                    client_feedback_received: getCheckbox('notify_client_feedback_received')
                }
            };
            const response = await fetch(`${window.GalerlyConfig.API_BASE_URL}/notifications/preferences`, {
                method: 'PUT',
                credentials: 'include',  // Send HttpOnly cookie
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(preferences)
            });
            if (!response.ok) {
                const errorData = await response.json();
                console.error('Failed to save notification preferences:', errorData);
                throw new Error('Failed to save notification preferences');
            }
            const data = await response.json();
            return data.success;
        } catch (error) {
            console.error('Error saving notification preferences:', error);
            return false;
        }
    }
    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {
        // Load preferences when page loads
        loadNotificationPreferences();
        // Add to profile form submit handler
        const profileForm = document.getElementById('profileForm');
        if (profileForm) {
            const originalSubmitHandler = profileForm.onsubmit;
            profileForm.onsubmit = async function(e) {
                e.preventDefault();
                // First, save notification preferences
                const prefsSuccess = await saveNotificationPreferences();
                // Then call original profile save handler if it exists
                if (originalSubmitHandler) {
                    originalSubmitHandler.call(profileForm, e);
                }
                return false;
            };
        }
    });
    // Export functions for external use
    window.NotificationPreferences = {
        load: loadNotificationPreferences,
        save: saveNotificationPreferences
    };
})();