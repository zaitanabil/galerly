/**
 * Enhanced Comments System
 * Supports threading, reactions, mentions, and moderation
 */

let currentEditingCommentId = null;
let currentReplyingToCommentId = null;
let commentsPollInterval = null;
let currentPhotoIdForPolling = null;

/**
 * Render comments - simplified: all replies at same level
 */
function renderEnhancedComments(comments, photoId, currentUserId, isGalleryOwner) {
    // CRITICAL: Preserve any textarea values if user is typing
    const preservedInputs = new Map();
    if (currentReplyingToCommentId) {
        const replyInput = document.getElementById(`reply-input-${currentReplyingToCommentId}`);
        if (replyInput) {
            preservedInputs.set(`reply-input-${currentReplyingToCommentId}`, replyInput.value);
        }
    }
    if (currentEditingCommentId) {
        const editInput = document.getElementById(`edit-input-${currentEditingCommentId}`);
        if (editInput) {
            preservedInputs.set(`edit-input-${currentEditingCommentId}`, editInput.value);
        }
    }
    
    const commentsList = document.getElementById('commentsList');
    if (!commentsList) return;
    
    commentsList.innerHTML = '';
    
    if (!comments || comments.length === 0) {
        commentsList.innerHTML = '<p style="text-align: center; opacity: 0.5; padding: 40px 20px;">No comments yet. Be the first to comment!</p>';
        return;
    }
    
    // Separate root comments and replies
    const rootComments = [];
    const replies = [];
    
    comments.forEach(comment => {
        if (comment.parent_id) {
            replies.push(comment);
        } else {
            rootComments.push(comment);
        }
    });
    
    // Sort root comments by date (newest first)
    rootComments.sort((a, b) => {
        const dateA = new Date(a.created_at || 0);
        const dateB = new Date(b.created_at || 0);
        return dateB - dateA;
    });
    
    // Sort replies by date (oldest first, so they appear right after their parent)
    replies.sort((a, b) => {
        const dateA = new Date(a.created_at || 0);
        const dateB = new Date(b.created_at || 0);
        return dateA - dateB;
    });
    
    // Create a map for quick parent lookup
    const commentMap = new Map();
    rootComments.forEach(c => commentMap.set(c.id, c));
    replies.forEach(c => commentMap.set(c.id, c));
    
    // Render root comments, and immediately after each root, render its replies
    rootComments.forEach(rootComment => {
        // Render root comment
        const rootEl = createCommentElement(rootComment, photoId, currentUserId, isGalleryOwner, 0);
        commentsList.appendChild(rootEl);
        
        // Find and render all replies to this root (flat, no nesting)
        const rootReplies = replies.filter(r => r.parent_id === rootComment.id);
        rootReplies.forEach(reply => {
            const replyEl = createCommentElement(reply, photoId, currentUserId, isGalleryOwner, 0);
            commentsList.appendChild(replyEl);
        });
    });
}

/**
 * Create a comment element with all features
 */
function createCommentElement(comment, photoId, currentUserId, isGalleryOwner, depth) {
    const isOwnComment = comment.user_id === currentUserId;
    const canEdit = isOwnComment || isGalleryOwner;
    const canDelete = isOwnComment || isGalleryOwner;
    const isReply = !!comment.parent_id;
    
    const commentEl = document.createElement('div');
    commentEl.className = 'comment-item-enhanced';
    commentEl.setAttribute('data-comment-id', comment.id);
    commentEl.setAttribute('data-depth', depth);
    
    if (isReply) {
        commentEl.classList.add('comment-reply');
    }
    
    // Parse mentions and highlight them
    const textWithMentions = parseMentions(comment.text);
    
    // Get reaction counts
    const reactions = comment.reactions || {};
    const likeCount = (reactions.like || []).length;
    const heartCount = (reactions.heart || []).length;
    const dislikeCount = (reactions.dislike || []).length;
    const hasLiked = currentUserId && (reactions.like || []).includes(currentUserId);
    const hasHearted = currentUserId && (reactions.heart || []).includes(currentUserId);
    const hasDisliked = currentUserId && (reactions.dislike || []).includes(currentUserId);
    
    commentEl.innerHTML = `
        <div class="comment-content">
            <div class="comment-header-enhanced">
                <div class="comment-author-info">
                    <span class="comment-author-enhanced">${escapeHtml(comment.author || 'Anonymous')}</span>
                    ${comment.is_edited ? '<span class="comment-edited-badge">(edited)</span>' : ''}
                </div>
                <div class="comment-actions-header">
                    <span class="comment-time-enhanced">${formatCommentTime(comment.is_edited ? comment.updated_at : comment.created_at)}</span>
                    ${canEdit ? `<button class="comment-action-btn edit-btn" onclick="startEditComment('${comment.id}', '${photoId}')" title="Edit comment">✏️</button>` : ''}
                    ${canDelete ? `<button class="comment-action-btn delete-btn" onclick="deleteComment('${comment.id}', '${photoId}')" title="Delete comment">🗑️</button>` : ''}
                </div>
            </div>
            <div class="comment-text-enhanced" id="comment-text-${comment.id}">
                ${textWithMentions}
            </div>
            <div class="comment-footer-enhanced">
                <div class="comment-reactions">
                    <button class="reaction-btn ${hasLiked ? 'active' : ''}" onclick="toggleReaction('${comment.id}', '${photoId}', 'like')" title="Like">
                        👍 <span class="reaction-count">${likeCount || ''}</span>
                    </button>
                    <button class="reaction-btn ${hasHearted ? 'active' : ''}" onclick="toggleReaction('${comment.id}', '${photoId}', 'heart')" title="Love">
                        ❤️ <span class="reaction-count">${heartCount || ''}</span>
                    </button>
                    <button class="reaction-btn ${hasDisliked ? 'active' : ''}" onclick="toggleReaction('${comment.id}', '${photoId}', 'dislike')" title="Dislike">
                        👎 <span class="reaction-count">${dislikeCount || ''}</span>
                    </button>
                </div>
                ${!isReply ? `<button class="reply-btn" onclick="startReply('${comment.id}')">Reply</button>` : ''}
            </div>
        </div>
        <div class="comment-reply-form" id="reply-form-${comment.id}" style="display: none;">
            <textarea class="reply-input" id="reply-input-${comment.id}" placeholder="Write a reply..."></textarea>
            <div class="reply-actions">
                <button class="reply-submit-btn" onclick="submitReply('${comment.id}', '${photoId}')">Post Reply</button>
                <button class="reply-cancel-btn" onclick="cancelReply('${comment.id}')">Cancel</button>
            </div>
        </div>
        <div class="comment-edit-form" id="edit-form-${comment.id}" style="display: none;">
            <textarea class="edit-input" id="edit-input-${comment.id}">${escapeHtml(comment.text)}</textarea>
            <div class="edit-actions">
                <button class="edit-submit-btn" onclick="submitEdit('${comment.id}', '${photoId}')">Save</button>
                <button class="edit-cancel-btn" onclick="cancelEdit('${comment.id}')">Cancel</button>
            </div>
        </div>
    `;
    
    return commentEl;
}

/**
 * Parse @mentions and highlight them
 */
function parseMentions(text) {
    if (!text) return '';
    
    const mentionPattern = /@(\w+)/g;
    return escapeHtml(text).replace(mentionPattern, '<span class="mention">@$1</span>');
}

/**
 * Toggle reaction on a comment
 */
async function toggleReaction(commentId, photoId, reactionType) {
    // Get current user for instant display
    const currentUser = getUserData();
    const currentUserId = currentUser ? currentUser.id : null;
    
    // Update local data IMMEDIATELY for instant feedback (before backend call)
    const photos = window.galleryPhotos || [];
    const photo = photos.find(p => p.id === photoId);
    let comment = null;
    let commentIndex = -1;
    
    if (photo && photo.comments) {
        commentIndex = photo.comments.findIndex(c => c.id === commentId);
        if (commentIndex >= 0) {
            comment = photo.comments[commentIndex];
            
            // Initialize reactions if not present
            if (!comment.reactions) {
                comment.reactions = {};
            }
            if (!comment.reactions[reactionType]) {
                comment.reactions[reactionType] = [];
            }
            
            // Toggle reaction locally
            const reactionsList = comment.reactions[reactionType];
            if (currentUserId && reactionsList.includes(currentUserId)) {
                // Remove reaction
                reactionsList.splice(reactionsList.indexOf(currentUserId), 1);
            } else if (currentUserId) {
                // Add reaction
                reactionsList.push(currentUserId);
            }
            
            // Re-render IMMEDIATELY with updated local data
            const gallery = window.currentGalleryData || {};
            const isGalleryOwner = currentUserId === gallery.user_id;
            renderEnhancedComments(photo.comments || [], photoId, currentUserId, isGalleryOwner);
        }
    }
    
    // Now call backend to sync
    try {
        const response = await apiRequest(`photos/${photoId}/comments/${commentId}`, {
            method: 'PUT',
            body: JSON.stringify({
                reaction: reactionType,
                action: 'toggle'
            })
        });
        
        // Update with backend response to ensure consistency
        if (photo && photo.comments && response && commentIndex >= 0) {
            photo.comments[commentIndex] = { ...photo.comments[commentIndex], ...response };
            
            // Re-render with backend data
            const gallery = window.currentGalleryData || {};
            const isGalleryOwner = currentUserId === gallery.user_id;
            renderEnhancedComments(photo.comments || [], photoId, currentUserId, isGalleryOwner);
        }
        
        // Reload comments AFTER reaction is clicked and backend responds
        // Use silent=true to prevent restarting polling immediately
        await reloadComments(photoId, true);
        
    } catch (error) {
        console.error('Error toggling reaction:', error);
        
        // Rollback: restore original reaction state on error
        if (photo && photo.comments && comment && commentIndex >= 0) {
            // Revert the toggle
            if (!comment.reactions) {
                comment.reactions = {};
            }
            if (!comment.reactions[reactionType]) {
                comment.reactions[reactionType] = [];
            }
            const reactionsList = comment.reactions[reactionType];
            if (currentUserId && reactionsList.includes(currentUserId)) {
                reactionsList.splice(reactionsList.indexOf(currentUserId), 1);
            } else if (currentUserId) {
                reactionsList.push(currentUserId);
            }
            
            // Re-render with original state
            const gallery = window.currentGalleryData || {};
            const isGalleryOwner = currentUserId === gallery.user_id;
            renderEnhancedComments(photo.comments || [], photoId, currentUserId, isGalleryOwner);
        }
        
        showNotification('Failed to update reaction. Please try again.', 'error');
    }
}

/**
 * Start replying to a comment
 */
function startReply(commentId) {
    // Stop polling immediately and prevent any reloads while user is writing
    stopCommentsPolling();
    
    // Set this BEFORE any DOM manipulation to prevent any reloads
    currentReplyingToCommentId = commentId;
    
    // Hide any other reply forms
    document.querySelectorAll('.comment-reply-form').forEach(form => {
        form.style.display = 'none';
    });
    
    // Show reply form for this comment
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    if (replyForm) {
        replyForm.style.display = 'block';
        const replyInput = document.getElementById(`reply-input-${commentId}`);
        if (replyInput) {
            replyInput.focus();
            // Store the current value to prevent it from being lost
            replyInput.dataset.originalValue = replyInput.value;
        }
    }
}

/**
 * Cancel reply
 */
function cancelReply(commentId) {
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    if (replyForm) {
        replyForm.style.display = 'none';
        const replyInput = document.getElementById(`reply-input-${commentId}`);
        if (replyInput) {
            replyInput.value = '';
        }
    }
    currentReplyingToCommentId = null;
    
    // Restart polling after canceling reply
    const photos = window.galleryPhotos || [];
    const currentPhotoIndex = window.currentPhotoIndex !== undefined ? window.currentPhotoIndex : 0;
    const photo = photos[currentPhotoIndex];
    if (photo && photo.id) {
        startCommentsPolling(photo.id);
    }
}

/**
 * Find root comment ID (if replying to a reply, find the root)
 */
function findRootCommentId(commentId, comments) {
    const comment = comments.find(c => c.id === commentId);
    if (!comment) return commentId;
    
    // If it's already a root comment (no parent_id), return it
    if (!comment.parent_id) {
        return commentId;
    }
    
    // If it's a reply, find the root by following parent_id chain
    let currentComment = comment;
    while (currentComment && currentComment.parent_id) {
        const parent = comments.find(c => c.id === currentComment.parent_id);
        if (!parent) {
            // Parent not found, return the original commentId as fallback
            return commentId;
        }
        // If parent has no parent_id, it's the root
        if (!parent.parent_id) {
            return parent.id;
        }
        currentComment = parent;
    }
    
    // Fallback: return original commentId
    return commentId;
}

/**
 * Submit reply
 */
async function submitReply(parentCommentId, photoId) {
    const replyInput = document.getElementById(`reply-input-${parentCommentId}`);
    if (!replyInput) return;
    
    const replyText = replyInput.value.trim();
    if (!replyText) {
        showNotification('Please enter a reply', 'warning');
        return;
    }
    
    try {
        // Get current user for instant display
        const currentUser = getUserData();
        const currentUserId = currentUser ? currentUser.id : null;
        
        // Get photo data
        const photos = window.galleryPhotos || [];
        const photo = photos.find(p => p.id === photoId);
        
        // Find root comment ID (if replying to a reply, use root's ID)
        const rootCommentId = photo && photo.comments 
            ? findRootCommentId(parentCommentId, photo.comments)
            : parentCommentId;
        
        // Create temporary reply object for instant display
        const tempReply = {
            id: 'temp-' + Date.now(),
            text: replyText,
            author: currentUser ? (currentUser.username || currentUser.email || 'You') : 'You',
            user_id: currentUserId,
            parent_id: rootCommentId, // Always use root comment ID
            reactions: {},
            is_edited: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };
        
        // Update local data immediately for instant feedback
        if (photo) {
            if (!photo.comments) {
                photo.comments = [];
            }
            // Add temporary reply to local data
            photo.comments.push(tempReply);
            
            // Re-render immediately
            const gallery = window.currentGalleryData || {};
            const isGalleryOwner = currentUserId === gallery.user_id;
            renderEnhancedComments(photo.comments || [], photoId, currentUserId, isGalleryOwner);
        }
        
        // Post to backend (always use root comment ID)
        const response = await apiRequest(`photos/${photoId}/comments`, {
            method: 'POST',
            body: JSON.stringify({
                text: replyText,
                parent_id: rootCommentId
            })
        });
        
        // Clear input and hide form AFTER backend success
        replyInput.value = '';
        cancelReply(parentCommentId);
        
        // Replace temporary reply with real one from backend
        if (photo && photo.comments) {
            const tempIndex = photo.comments.findIndex(c => c.id === tempReply.id);
            if (tempIndex >= 0) {
                photo.comments[tempIndex] = response;
            }
            
            // Re-render with the real comment from backend
            const gallery = window.currentGalleryData || {};
            const isGalleryOwner = currentUserId === gallery.user_id;
            renderEnhancedComments(photo.comments || [], photoId, currentUserId, isGalleryOwner);
        }
        
        // Reload comments to sync with backend AFTER successful post
        // Use silent=true to prevent restarting polling immediately
        await reloadComments(photoId, true);
        
        showNotification('Reply posted successfully!');
        
    } catch (error) {
        console.error('Error posting reply:', error);
        
        // Remove temporary reply on error
        const photos = window.galleryPhotos || [];
        const photo = photos.find(p => p.id === photoId);
        if (photo && photo.comments) {
            const tempIndex = photo.comments.findIndex(c => c.id && c.id.startsWith('temp-'));
            if (tempIndex >= 0) {
                photo.comments.splice(tempIndex, 1);
                // Re-render without the failed reply
                const currentUser = getUserData();
                const currentUserId = currentUser ? currentUser.id : null;
                const gallery = window.currentGalleryData || {};
                const isGalleryOwner = currentUserId === gallery.user_id;
                renderEnhancedComments(photo.comments || [], photoId, currentUserId, isGalleryOwner);
            }
        }
        
        showNotification('Failed to post reply. Please try again.', 'error');
    }
}

/**
 * Start editing a comment
 */
function startEditComment(commentId, photoId) {
    // Stop polling immediately and prevent any reloads while user is editing
    stopCommentsPolling();
    
    // Set this BEFORE any DOM manipulation to prevent any reloads
    currentEditingCommentId = commentId;
    
    // Hide any other edit forms
    document.querySelectorAll('.comment-edit-form').forEach(form => {
        form.style.display = 'none';
    });
    
    // Hide comment text
    const commentText = document.getElementById(`comment-text-${commentId}`);
    if (commentText) {
        commentText.style.display = 'none';
    }
    
    // Show edit form
    const editForm = document.getElementById(`edit-form-${commentId}`);
    if (editForm) {
        editForm.style.display = 'block';
        const editInput = document.getElementById(`edit-input-${commentId}`);
        if (editInput) {
            editInput.focus();
            editInput.select();
            // Store the current value to prevent it from being lost
            editInput.dataset.originalValue = editInput.value;
        }
    }
}

/**
 * Cancel edit
 */
function cancelEdit(commentId) {
    const editForm = document.getElementById(`edit-form-${commentId}`);
    if (editForm) {
        editForm.style.display = 'none';
    }
    
    const commentText = document.getElementById(`comment-text-${commentId}`);
    if (commentText) {
        commentText.style.display = 'block';
    }
    
    currentEditingCommentId = null;
}

/**
 * Submit edit
 */
async function submitEdit(commentId, photoId) {
    const editInput = document.getElementById(`edit-input-${commentId}`);
    if (!editInput) return;
    
    const newText = editInput.value.trim();
    if (!newText) {
        showNotification('Comment text cannot be empty', 'warning');
        return;
    }
    
    // Store original text for rollback on error
    const photos = window.galleryPhotos || [];
    const photo = photos.find(p => p.id === photoId);
    let originalComment = null;
    if (photo && photo.comments) {
        const commentIndex = photo.comments.findIndex(c => c.id === commentId);
        if (commentIndex >= 0) {
            originalComment = { ...photo.comments[commentIndex] };
            // Update local data immediately for instant feedback
            photo.comments[commentIndex] = {
                ...photo.comments[commentIndex],
                text: newText,
                is_edited: true,
                updated_at: new Date().toISOString()
            };
            
            // Re-render immediately
            const currentUser = getUserData();
            const currentUserId = currentUser ? currentUser.id : null;
            const gallery = window.currentGalleryData || {};
            const isGalleryOwner = currentUserId === gallery.user_id;
            renderEnhancedComments(photo.comments || [], photoId, currentUserId, isGalleryOwner);
        }
    }
    
    try {
        const response = await apiRequest(`photos/${photoId}/comments/${commentId}`, {
            method: 'PUT',
            body: JSON.stringify({
                text: newText
            })
        });
        
        // Replace with response from backend
        if (photo && photo.comments && originalComment) {
            const commentIndex = photo.comments.findIndex(c => c.id === commentId);
            if (commentIndex >= 0) {
                photo.comments[commentIndex] = response;
            }
        }
        
        // Reload comments to sync with backend (will also refresh for other users via polling)
        // Use silent=true to prevent restarting polling immediately
        await reloadComments(photoId, true);
        
        showNotification('Comment updated successfully!');
        
    } catch (error) {
        console.error('Error updating comment:', error);
        
        // Rollback to original comment on error
        if (photo && photo.comments && originalComment) {
            const commentIndex = photo.comments.findIndex(c => c.id === commentId);
            if (commentIndex >= 0) {
                photo.comments[commentIndex] = originalComment;
                // Re-render with original comment
                const currentUser = getUserData();
                const currentUserId = currentUser ? currentUser.id : null;
                const gallery = window.currentGalleryData || {};
                const isGalleryOwner = currentUserId === gallery.user_id;
                renderEnhancedComments(photo.comments || [], photoId, currentUserId, isGalleryOwner);
            }
        }
        
        showNotification('Failed to update comment. Please try again.', 'error');
    }
}

/**
 * Delete comment
 */
async function deleteComment(commentId, photoId) {
    if (!confirm('Are you sure you want to delete this comment? This action cannot be undone.')) {
        return;
    }
    
    // Store original comment for rollback on error
    const photos = window.galleryPhotos || [];
    const photo = photos.find(p => p.id === photoId);
    let deletedComment = null;
    let deletedIndex = -1;
    
    if (photo && photo.comments) {
        deletedIndex = photo.comments.findIndex(c => c.id === commentId);
        if (deletedIndex >= 0) {
            deletedComment = { ...photo.comments[deletedIndex] };
            // Remove from local data immediately for instant feedback
            photo.comments.splice(deletedIndex, 1);
            
            // Re-render immediately
            const currentUser = getUserData();
            const currentUserId = currentUser ? currentUser.id : null;
            const gallery = window.currentGalleryData || {};
            const isGalleryOwner = currentUserId === gallery.user_id;
            renderEnhancedComments(photo.comments || [], photoId, currentUserId, isGalleryOwner);
        }
    }
    
    try {
        await apiRequest(`photos/${photoId}/comments/${commentId}`, {
            method: 'DELETE'
        });
        
        // Reload comments to sync with backend (will also refresh for other users via polling)
        // Use silent=true to prevent restarting polling immediately
        await reloadComments(photoId, true);
        
        showNotification('Comment deleted successfully!');
        
    } catch (error) {
        console.error('Error deleting comment:', error);
        
        // Rollback: restore deleted comment on error
        if (photo && photo.comments && deletedComment !== null && deletedIndex >= 0) {
            photo.comments.splice(deletedIndex, 0, deletedComment);
            // Re-render with restored comment
            const currentUser = getUserData();
            const currentUserId = currentUser ? currentUser.id : null;
            const gallery = window.currentGalleryData || {};
            const isGalleryOwner = currentUserId === gallery.user_id;
            renderEnhancedComments(photo.comments || [], photoId, currentUserId, isGalleryOwner);
        }
        
        showNotification('Failed to delete comment. Please try again.', 'error');
    }
}

/**
 * Start polling for comment updates
 */
function startCommentsPolling(photoId) {
    // Stop any existing polling
    stopCommentsPolling();
    
    // Store current photo ID
    currentPhotoIdForPolling = photoId;
    
    // Poll every 3 seconds for updates
    commentsPollInterval = setInterval(async () => {
        if (currentPhotoIdForPolling) {
            try {
                await reloadComments(currentPhotoIdForPolling, true); // true = silent update
            } catch (error) {
                console.error('Error polling comments:', error);
            }
        }
    }, 3000); // Poll every 3 seconds
}

/**
 * Stop polling for comment updates
 */
function stopCommentsPolling() {
    if (commentsPollInterval) {
        clearInterval(commentsPollInterval);
        commentsPollInterval = null;
    }
    currentPhotoIdForPolling = null;
}

/**
 * Reload comments for current photo
 */
async function reloadComments(photoId, silent = false) {
    // CRITICAL: Never reload if user is currently typing a reply or editing
    // This prevents losing user input
    if (currentReplyingToCommentId || currentEditingCommentId) {
        return;
    }
    
    const photos = window.galleryPhotos || [];
    const photo = photos.find(p => p.id === photoId);
    
    if (!photo) {
        // Try to find photo by index if ID lookup fails
        const currentPhotoIndex = window.currentPhotoIndex !== undefined ? window.currentPhotoIndex : 0;
        const photoByIndex = photos[currentPhotoIndex];
        if (photoByIndex && photoByIndex.id === photoId) {
            photo = photoByIndex;
        }
    }
    
    if (!photo) {
        console.error('Photo not found for reload:', photoId);
        return;
    }
    
    // Reload photo data from backend to get updated comments
    // Skip backend reload only if user is currently typing a reply (to preserve temporary replies being written)
    if (!currentReplyingToCommentId) {
        try {
            // Preserve temporary comments (those starting with 'temp-') before reloading
            const tempComments = (photo.comments || []).filter(c => c.id && c.id.startsWith('temp-'));
            
            // Try to fetch updated photo data from backend
            // First try the gallery photos endpoint
            if (window.currentGalleryId) {
                const galleryResponse = await apiRequest(`galleries/${window.currentGalleryId}`);
                if (galleryResponse && galleryResponse.photos) {
                    const updatedPhoto = galleryResponse.photos.find(p => p.id === photoId);
                    if (updatedPhoto && updatedPhoto.comments) {
                        // Merge backend comments with temporary comments
                        // Remove any temporary comments that might have been saved (by ID matching)
                        const backendComments = updatedPhoto.comments.filter(c => !c.id || !c.id.startsWith('temp-'));
                        // Add back temporary comments that haven't been replaced yet
                        tempComments.forEach(tempComment => {
                            // Check if this temp comment has been replaced by a real one
                            const wasReplaced = backendComments.some(c => 
                                c.text === tempComment.text && 
                                c.parent_id === tempComment.parent_id &&
                                c.user_id === tempComment.user_id
                            );
                            if (!wasReplaced) {
                                backendComments.push(tempComment);
                            }
                        });
                        photo.comments = backendComments;
                        // Update the photo in the local array
                        const localIndex = photos.findIndex(p => p.id === photoId);
                        if (localIndex >= 0) {
                            photos[localIndex].comments = backendComments;
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Error reloading photo from backend:', error);
            // Continue with local data if backend fetch fails
        }
    }
    
    // Re-render comments
    const currentUser = getUserData();
    const currentUserId = currentUser ? currentUser.id : null;
    const gallery = window.currentGalleryData || {};
    const isGalleryOwner = currentUserId === gallery.user_id;
    
    // Store scroll position before re-rendering (to maintain scroll position during updates)
    const commentsList = document.getElementById('commentsList');
    const scrollPosition = commentsList ? commentsList.scrollTop : 0;
    
    renderEnhancedComments(photo.comments || [], photoId, currentUserId, isGalleryOwner);
    
    // Restore scroll position after re-rendering (only if it's a silent update)
    if (silent && commentsList && scrollPosition > 0) {
        commentsList.scrollTop = scrollPosition;
    }
    
    // Start polling if not already started AND not triggered by user action
    // Don't restart polling immediately after user actions (reaction, comment, reply)
    // Polling will restart naturally after a delay or when user opens photo modal
    if (!commentsPollInterval && !silent && !currentReplyingToCommentId && !currentEditingCommentId) {
        startCommentsPolling(photoId);
    }
}

/**
 * Enhanced add comment function (supports parent_id for replies)
 */
async function addEnhancedComment(photoId, text, parentId = null) {
    try {
        // Get current user for instant display
        const currentUser = getUserData();
        const currentUserId = currentUser ? currentUser.id : null;
        
        // Create temporary comment object for instant display
        const tempComment = {
            id: 'temp-' + Date.now(),
            text: text,
            author: currentUser ? (currentUser.username || currentUser.email || 'You') : 'You',
            user_id: currentUserId,
            parent_id: parentId,
            reactions: {},
            is_edited: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };
        
        // Update local photo data immediately for instant feedback
        const photos = window.galleryPhotos || [];
        const photo = photos.find(p => p.id === photoId);
        if (photo) {
            if (!photo.comments) {
                photo.comments = [];
            }
            // Add temporary comment to local data
            photo.comments.push(tempComment);
            
            // Re-render immediately
            const gallery = window.currentGalleryData || {};
            const isGalleryOwner = currentUserId === gallery.user_id;
            renderEnhancedComments(photo.comments || [], photoId, currentUserId, isGalleryOwner);
        }
        
        // Post to backend
        const response = await apiRequest(`photos/${photoId}/comments`, {
            method: 'POST',
            body: JSON.stringify({
                text: text,
                parent_id: parentId
            })
        });
        
        // Replace temporary comment with real one from backend
        if (photo && photo.comments) {
            const tempIndex = photo.comments.findIndex(c => c.id === tempComment.id);
            if (tempIndex >= 0) {
                photo.comments[tempIndex] = response;
            }
        }
        
        // Reload comments AFTER comment is posted and backend responds
        // Use silent=true to prevent restarting polling immediately
        await reloadComments(photoId, true);
        
        return response;
        
    } catch (error) {
        console.error('Error adding comment:', error);
        
        // Remove temporary comment on error
        const photos = window.galleryPhotos || [];
        const photo = photos.find(p => p.id === photoId);
        if (photo && photo.comments) {
            const tempIndex = photo.comments.findIndex(c => c.id && c.id.startsWith('temp-'));
            if (tempIndex >= 0) {
                photo.comments.splice(tempIndex, 1);
                // Re-render without the failed comment
                const currentUser = getUserData();
                const currentUserId = currentUser ? currentUser.id : null;
                const gallery = window.currentGalleryData || {};
                const isGalleryOwner = currentUserId === gallery.user_id;
                renderEnhancedComments(photo.comments || [], photoId, currentUserId, isGalleryOwner);
            }
        }
        
        throw error;
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#f44336' : type === 'warning' ? '#ff9800' : '#4CAF50'};
        color: white;
        padding: 14px 28px;
        border-radius: 999px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        white-space: nowrap;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format comment time
 */
function formatCommentTime(timestamp) {
    if (!timestamp) return 'Just now';
    
    try {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        
        if (diffMs < 0) return 'Just now';
        
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins === 1) return '1 minute ago';
        if (diffMins < 60) return `${diffMins} minutes ago`;
        if (diffHours === 1) return '1 hour ago';
        if (diffHours < 24) return `${diffHours} hours ago`;
        if (diffDays === 1) return '1 day ago';
        if (diffDays < 7) return `${diffDays} days ago`;
        
        return date.toLocaleDateString(undefined, { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    } catch (e) {
        console.error('Error formatting time:', e);
        return 'Just now';
    }
}

// Cleanup polling when page unloads
window.addEventListener('beforeunload', () => {
    stopCommentsPolling();
});

// Export functions to global scope
window.renderEnhancedComments = renderEnhancedComments;
window.toggleReaction = toggleReaction;
window.startReply = startReply;
window.cancelReply = cancelReply;
window.submitReply = submitReply;
window.startEditComment = startEditComment;
window.cancelEdit = cancelEdit;
window.submitEdit = submitEdit;
window.deleteComment = deleteComment;
window.addEnhancedComment = addEnhancedComment;
window.reloadComments = reloadComments;
window.startCommentsPolling = startCommentsPolling;
window.stopCommentsPolling = stopCommentsPolling;

