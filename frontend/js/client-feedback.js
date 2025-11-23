/**
 * Client Feedback Form
 * Structured feedback collection for galleries
 */

/**
 * Show feedback form modal
 */
function showFeedbackForm(galleryId) {
    // Close any existing modals
    const existingModal = document.getElementById('feedbackModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create modal
    const modal = document.createElement('div');
    modal.id = 'feedbackModal';
    modal.className = 'feedback-modal';
    modal.innerHTML = `
        <div class="feedback-modal-content">
            <div class="feedback-modal-header">
                <h2>Share Your Feedback</h2>
                <button class="feedback-modal-close" onclick="closeFeedbackModal()" aria-label="Close feedback form">&times;</button>
            </div>
            <form id="feedbackForm" onsubmit="submitFeedback(event, '${galleryId}')">
                <div class="feedback-section">
                    <label>Your Name *</label>
                    <input type="text" id="clientName" name="client_name" required placeholder="Enter your name">
                </div>
                
                <div class="feedback-section">
                    <label>Your Email *</label>
                    <input type="email" id="clientEmail" name="client_email" required placeholder="your@email.com">
                </div>
                
                <div class="feedback-section">
                    <label>Overall Rating *</label>
                    <div class="rating-input">
                        ${[1, 2, 3, 4, 5].map(i => `
                            <button type="button" class="rating-star" data-rating="${i}" onclick="setRating('overall', ${i})" aria-label="Rate ${i} stars">
                                <span class="star">☆</span>
                            </button>
                        `).join('')}
                    </div>
                    <input type="hidden" id="overallRating" name="overall_rating" required>
                </div>
                
                <div class="feedback-section">
                    <label>Photo Quality</label>
                    <div class="rating-input">
                        ${[1, 2, 3, 4, 5].map(i => `
                            <button type="button" class="rating-star" data-rating="${i}" onclick="setRating('photoQuality', ${i})" aria-label="Rate ${i} stars">
                                <span class="star">☆</span>
                            </button>
                        `).join('')}
                    </div>
                    <input type="hidden" id="photoQualityRating" name="photo_quality_rating">
                </div>
                
                <div class="feedback-section">
                    <label>Delivery Time</label>
                    <div class="rating-input">
                        ${[1, 2, 3, 4, 5].map(i => `
                            <button type="button" class="rating-star" data-rating="${i}" onclick="setRating('delivery', ${i})" aria-label="Rate ${i} stars">
                                <span class="star">☆</span>
                            </button>
                        `).join('')}
                    </div>
                    <input type="hidden" id="deliveryRating" name="delivery_time_rating">
                </div>
                
                <div class="feedback-section">
                    <label>Communication</label>
                    <div class="rating-input">
                        ${[1, 2, 3, 4, 5].map(i => `
                            <button type="button" class="rating-star" data-rating="${i}" onclick="setRating('communication', ${i})" aria-label="Rate ${i} stars">
                                <span class="star">☆</span>
                            </button>
                        `).join('')}
                    </div>
                    <input type="hidden" id="communicationRating" name="communication_rating">
                </div>
                
                <div class="feedback-section">
                    <label>Value for Money</label>
                    <div class="rating-input">
                        ${[1, 2, 3, 4, 5].map(i => `
                            <button type="button" class="rating-star" data-rating="${i}" onclick="setRating('value', ${i})" aria-label="Rate ${i} stars">
                                <span class="star">☆</span>
                            </button>
                        `).join('')}
                    </div>
                    <input type="hidden" id="valueRating" name="value_rating">
                </div>
                
                <div class="feedback-section">
                    <label>
                        <input type="checkbox" id="wouldRecommend" name="would_recommend">
                        Would you recommend this photographer?
                    </label>
                </div>
                
                <div class="feedback-section">
                    <label>Additional Comments</label>
                    <textarea id="comments" name="comments" rows="4" placeholder="Tell us more about your experience..."></textarea>
                </div>
                
                <div class="feedback-actions">
                    <button type="button" class="feedback-btn-cancel" onclick="closeFeedbackModal()">Cancel</button>
                    <button type="submit" class="feedback-btn-submit">
                        <span>Submit Feedback</span>
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M6 12L10 8L6 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                </div>
            </form>
        </div>
    `;
    
    // Add styles
    const style = document.createElement('style');
    style.textContent = `
        .feedback-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            padding: 20px;
            box-sizing: border-box;
        }
        
        .feedback-modal-content {
            background: white;
            border-radius: 12px;
            max-width: 600px;
            width: 100%;
            max-height: calc(100vh - 40px);
            overflow-y: auto;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
        }
        
        .feedback-modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 24px;
            border-bottom: 1px solid #eee;
        }
        
        .feedback-modal-header h2 {
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }
        
        .feedback-modal-close {
            background: none;
            border: none;
            font-size: 32px;
            cursor: pointer;
            color: #999;
            padding: 0;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 4px;
        }
        
        .feedback-modal-close:hover {
            background: #f5f5f5;
            color: #333;
        }
        
        #feedbackForm {
            padding: 24px;
        }
        
        .feedback-section {
            margin-bottom: 24px;
        }
        
        .feedback-section label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #333;
        }
        
        .feedback-section input[type="text"],
        .feedback-section input[type="email"],
        .feedback-section textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            box-sizing: border-box;
        }
        
        .feedback-section textarea {
            resize: vertical;
            font-family: inherit;
        }
        
        .rating-input {
            display: flex;
            gap: 8px;
        }
        
        .rating-star {
            background: none;
            border: none;
            font-size: 32px;
            cursor: pointer;
            padding: 0;
            color: #ddd;
            transition: color 0.2s;
        }
        
        .rating-star:hover,
        .rating-star.active {
            color: #ffc107;
        }
        
        .rating-star .star {
            display: block;
        }
        
        .feedback-section input[type="checkbox"] {
            margin-right: 8px;
        }
        
        .feedback-actions {
            display: flex;
            gap: 12px;
            justify-content: flex-end;
            margin-top: 32px;
        }
        
        .feedback-btn-cancel,
        .feedback-btn-submit {
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            border: none;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s;
        }
        
        .feedback-btn-cancel {
            background: #f5f5f5;
            color: #333;
        }
        
        .feedback-btn-cancel:hover {
            background: #e0e0e0;
        }
        
        .feedback-btn-submit {
            background: #007bff;
            color: white;
        }
        
        .feedback-btn-submit:hover {
            background: #0056b3;
        }
        
        .feedback-btn-submit:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        @media (max-width: 640px) {
            .feedback-modal-content {
                max-height: calc(100vh - 20px);
            }
            
            .feedback-modal-header,
            #feedbackForm {
                padding: 16px;
            }
            
            .rating-star {
                font-size: 24px;
            }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(modal);
    document.body.style.overflow = 'hidden';
    
    // Focus first input
    setTimeout(() => {
        document.getElementById('clientName').focus();
    }, 100);
    
    // Close on Escape key
    modal.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeFeedbackModal();
        }
    });
}

/**
 * Set rating for a category
 */
function setRating(category, rating) {
    const inputMap = {
        'overall': 'overallRating',
        'photoQuality': 'photoQualityRating',
        'delivery': 'deliveryRating',
        'communication': 'communicationRating',
        'value': 'valueRating'
    };
    
    const inputId = inputMap[category];
    if (!inputId) return;
    
    // Set hidden input value
    document.getElementById(inputId).value = rating;
    
    // Update star display
    const stars = document.querySelectorAll(`[onclick*="${category}"]`);
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('active');
            star.querySelector('.star').textContent = '★';
        } else {
            star.classList.remove('active');
            star.querySelector('.star').textContent = '☆';
        }
    });
}

/**
 * Submit feedback form
 */
async function submitFeedback(event, galleryId) {
    event.preventDefault();
    
    const form = event.target;
    const submitBtn = form.querySelector('.feedback-btn-submit');
    const originalText = submitBtn.innerHTML;
    
    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>Submitting...</span>';
    
    // Collect form data
    const formData = {
        client_name: document.getElementById('clientName').value.trim(),
        client_email: document.getElementById('clientEmail').value.trim().toLowerCase(),
        overall_rating: parseInt(document.getElementById('overallRating').value),
        photo_quality_rating: document.getElementById('photoQualityRating').value ? parseInt(document.getElementById('photoQualityRating').value) : undefined,
        delivery_time_rating: document.getElementById('deliveryRating').value ? parseInt(document.getElementById('deliveryRating').value) : undefined,
        communication_rating: document.getElementById('communicationRating').value ? parseInt(document.getElementById('communicationRating').value) : undefined,
        value_rating: document.getElementById('valueRating').value ? parseInt(document.getElementById('valueRating').value) : undefined,
        would_recommend: document.getElementById('wouldRecommend').checked,
        comments: document.getElementById('comments').value.trim()
    };
    
    // Remove undefined values
    Object.keys(formData).forEach(key => {
        if (formData[key] === undefined || formData[key] === '') {
            delete formData[key];
        }
    });
    
    try {
        const apiUrl = window.GalerlyConfig?.API_BASE_URL || window.API_BASE_URL || 'https://api.galerly.com';
        const response = await fetch(`${apiUrl}/api/v1/client/feedback/${galleryId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || data.message || 'Failed to submit feedback');
        }
        
        // Show success message
        showFeedbackNotification('Thank you for your feedback!', 'success');
        
        // Close modal after delay
        setTimeout(() => {
            closeFeedbackModal();
        }, 1500);
        
    } catch (error) {
        console.error('Error submitting feedback:', error);
        showFeedbackNotification(error.message || 'Failed to submit feedback. Please try again.', 'error');
        
        // Re-enable submit button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

/**
 * Close feedback modal
 */
function closeFeedbackModal() {
    const modal = document.getElementById('feedbackModal');
    if (modal) {
        modal.remove();
        document.body.style.overflow = '';
    }
}

/**
 * Show feedback notification
 */
function showFeedbackNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `feedback-notification feedback-notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? '#4caf50' : '#f44336'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 10001;
        animation: slideIn 0.3s ease-out;
    `;
    
    // Add animation
    if (!document.getElementById('feedbackNotificationStyle')) {
        const style = document.createElement('style');
        style.id = 'feedbackNotificationStyle';
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Export functions to window
window.showFeedbackForm = showFeedbackForm;
window.closeFeedbackModal = closeFeedbackModal;
window.setRating = setRating;
window.submitFeedback = submitFeedback;

