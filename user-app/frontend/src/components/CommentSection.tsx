import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import * as photoService from '../services/photoService';
import { Comment } from '../services/photoService';
import { Send, Heart, ThumbsUp, ThumbsDown, MessageCircle, Edit2, Trash2, PenTool } from 'lucide-react';
import { useBrandedModal } from './BrandedModal';

interface CommentSectionProps {
  photoId: string;
  comments: Comment[];
  onCommentsChange: (comments: Comment[]) => void;
  allowComments: boolean;
  isGalleryOwner: boolean;
}

export default function CommentSection({
  photoId,
  comments,
  onCommentsChange,
  allowComments,
  isGalleryOwner,
}: CommentSectionProps) {
  const { user } = useAuth();
  const { showConfirm, showPrompt, ModalComponent } = useBrandedModal();
  const [newComment, setNewComment] = useState('');
  const [replyTo, setReplyTo] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState('');
  const [loading, setLoading] = useState(false);

  // Poll for comments
  useEffect(() => {
    // Initial fetch to ensure we have latest data
    const fetchLatestComments = async () => {
        try {
            const response = await photoService.getPhoto(photoId);
            if (response.success && response.data && response.data.comments) {
                // Check if comments are different before updating to avoid loops/redraws
                const newComments = response.data.comments;
                if (JSON.stringify(newComments) !== JSON.stringify(comments)) {
                    onCommentsChange(newComments);
                }
            }
        } catch (e) {
            console.error("Error polling comments:", e);
        }
    };

    // Poll every 5 seconds
    const pollInterval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        fetchLatestComments();
      }
    }, 5000);
    
    return () => clearInterval(pollInterval);
  }, [photoId, comments, onCommentsChange]);

  const handleAddComment = async (parentId?: string) => {
    const text = parentId ? (document.getElementById(`reply-input-${parentId}`) as HTMLInputElement)?.value : newComment;
    
    if (!text?.trim()) return;
    if (!allowComments && !isGalleryOwner) return;

    // Handle guest user
    let authorName = user?.name || user?.username;
    let authorEmail = user?.email;

    if (!user) {
      // Check local storage first
      let storedEmail = localStorage.getItem('guest_email');
      let storedName = localStorage.getItem('guest_name');

      if (!storedName) {
        storedName = await showPrompt(
          'Enter Your Name',
          'Please enter your name to comment:',
          'Your Name'
        );
        if (!storedName) return;
        localStorage.setItem('guest_name', storedName);
      }

      if (!storedEmail) {
        // Optional email
        storedEmail = await showPrompt(
          'Enter Your Email (Optional)',
          'Please enter your email (optional, for notifications):',
          'your@email.com'
        );
        if (storedEmail) localStorage.setItem('guest_email', storedEmail);
      }

      authorName = storedName;
      authorEmail = storedEmail || undefined;
    }

    setLoading(true);
    try {
      const response = await photoService.addComment(photoId, text.trim(), parentId, authorName, authorEmail);
      if (response.success && response.data) {
        onCommentsChange([...comments, response.data]);
        if (parentId) {
          setReplyTo(null);
        } else {
          setNewComment('');
        }
      }
    } catch (error) {
      console.error('Error adding comment:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateComment = async (commentId: string, text: string) => {
    try {
      const response = await photoService.updateComment(photoId, commentId, { text });
      if (response.success && response.data) {
        onCommentsChange(comments.map(c => c.id === commentId ? response.data! : c));
        setEditingId(null);
        setEditText('');
      }
    } catch (error) {
      console.error('Error updating comment:', error);
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    const confirmed = await showConfirm(
      'Delete Comment',
      'Are you sure you want to delete this comment?',
      'Delete',
      'Cancel',
      'danger'
    );
    
    if (!confirmed) return;
    
    try {
      await photoService.deleteComment(photoId, commentId);
      // Remove comment and any replies locally
      onCommentsChange(comments.filter(c => c.id !== commentId && c.parent_id !== commentId));
    } catch (error) {
      console.error('Error deleting comment:', error);
    }
  };

  const handleReaction = async (commentId: string, type: 'like' | 'heart' | 'dislike') => {
    // Optimistic update
    // Note: In client view without auth, backend tracks by session/cookie, so user_id might not match what we see here.
    // We'll rely on backend response for consistency.
    
    try {
      const response = await photoService.updateComment(photoId, commentId, { 
        reaction: type, 
        action: 'toggle' 
      });
      if (response.success && response.data) {
        onCommentsChange(comments.map(c => c.id === commentId ? response.data! : c));
      }
    } catch (error) {
      console.error('Error toggling reaction:', error);
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = (now.getTime() - date.getTime()) / 1000;

    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return date.toLocaleDateString();
  };

  // Organize comments into threads
  const rootComments = comments.filter(c => !c.parent_id).sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  const getReplies = (parentId: string) => comments.filter(c => c.parent_id === parentId).sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());

  const renderComment = (comment: Comment, isReply = false) => {
    // Determine if current user is the author
    const isAuthor = user?.id 
      ? user.id === comment.user_id 
      : (localStorage.getItem('guest_email') && comment.user_email === localStorage.getItem('guest_email')) || 
        (localStorage.getItem('guest_name') && comment.user_name === localStorage.getItem('guest_name') && comment.user_id?.startsWith('guest-'));

    // Permission: Only author can delete/edit their own comment
    // Photographer cannot delete client comments, Client cannot delete photographer comments
    const canEdit = isAuthor;
    
    const replies = getReplies(comment.id);
    
    // Reaction counts
    const likes = comment.reactions?.like?.length || 0;
    const hearts = comment.reactions?.heart?.length || 0;
    const dislikes = comment.reactions?.dislike?.length || 0;
    
    // Has current user reacted? (Requires consistent user ID tracking)
    const hasLiked = user?.id && comment.reactions?.like?.includes(user.id);
    const hasHearted = user?.id && comment.reactions?.heart?.includes(user.id);
    const hasDisliked = user?.id && comment.reactions?.dislike?.includes(user.id);
    
    const hasAnnotation = !!comment.annotation;

    return (
      <div key={comment.id} className={`group ${isReply ? 'ml-8 mt-2' : 'mt-4'}`}>
        <div className={`p-4 rounded-2xl ${isReply ? 'bg-gray-50/50 border border-gray-100' : 'bg-gray-50'}`}>
          <div className="flex justify-between items-start mb-2">
            <div className="flex items-center gap-2">
              <span className="font-medium text-[#1D1D1F] text-sm">{comment.user_name || 'Anonymous'}</span>
              <span className="text-xs text-[#1D1D1F]/40">{formatTime(comment.created_at)}</span>
              {hasAnnotation && (
                  <span className="flex items-center gap-1 text-[10px] font-medium bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded border border-yellow-200">
                      <PenTool className="w-3 h-3" /> Edit Request
                  </span>
              )}
              {comment.is_edited && <span className="text-xs text-[#1D1D1F]/40">(edited)</span>}
            </div>
            
            {canEdit && (
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button 
                  onClick={() => { setEditingId(comment.id); setEditText(comment.text); }}
                  className="p-1 hover:bg-gray-200 rounded text-[#1D1D1F]/60"
                >
                  <Edit2 className="w-3 h-3" />
                </button>
                <button 
                  onClick={() => handleDeleteComment(comment.id)}
                  className="p-1 hover:bg-red-100 rounded text-red-500"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            )}
          </div>

          {editingId === comment.id ? (
            <div className="mb-2">
              <textarea
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                className="w-full p-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
                rows={2}
                autoFocus
              />
              <div className="flex gap-2 mt-2">
                <button 
                  onClick={() => handleUpdateComment(comment.id, editText)}
                  className="px-3 py-1 bg-[#0066CC] text-white text-xs rounded-md"
                >
                  Save
                </button>
                <button 
                  onClick={() => setEditingId(null)}
                  className="px-3 py-1 bg-gray-200 text-gray-700 text-xs rounded-md"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-[#1D1D1F]/80 whitespace-pre-wrap">{comment.text}</p>
          )}

          <div className="flex items-center gap-4 mt-3">
            <div className="flex items-center gap-2">
              <button 
                onClick={() => handleReaction(comment.id, 'like')}
                className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full transition-colors ${
                  hasLiked ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-200 text-[#1D1D1F]/60'
                }`}
              >
                <ThumbsUp className="w-3 h-3" />
                {likes > 0 && <span>{likes}</span>}
              </button>
              <button 
                onClick={() => handleReaction(comment.id, 'heart')}
                className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full transition-colors ${
                  hasHearted ? 'bg-red-100 text-red-600' : 'hover:bg-gray-200 text-[#1D1D1F]/60'
                }`}
              >
                <Heart className="w-3 h-3" />
                {hearts > 0 && <span>{hearts}</span>}
              </button>
              {/* Only show dislike if > 0 or if user disliked, to reduce negativity? Or keep consistent. */}
              <button 
                onClick={() => handleReaction(comment.id, 'dislike')}
                className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full transition-colors ${
                  hasDisliked ? 'bg-gray-200 text-gray-800' : 'hover:bg-gray-200 text-[#1D1D1F]/60'
                }`}
              >
                <ThumbsDown className="w-3 h-3" />
                {dislikes > 0 && <span>{dislikes}</span>}
              </button>
            </div>

            {!isReply && allowComments && (
              <button 
                onClick={() => setReplyTo(replyTo === comment.id ? null : comment.id)}
                className="text-xs font-medium text-[#1D1D1F]/60 hover:text-[#0066CC] transition-colors"
              >
                Reply
              </button>
            )}
          </div>
        </div>

        {/* Reply Input */}
        {replyTo === comment.id && (
          <div className="ml-8 mt-2 flex gap-2 animate-in fade-in slide-in-from-top-1">
            <input
              id={`reply-input-${comment.id}`}
              type="text"
              placeholder="Write a reply..."
              className="flex-1 px-3 py-2 text-sm bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20"
              onKeyDown={(e) => e.key === 'Enter' && handleAddComment(comment.id)}
              autoFocus
            />
            <button
              onClick={() => handleAddComment(comment.id)}
              className="p-2 bg-[#0066CC] text-white rounded-lg hover:bg-[#0052A3]"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Nested Replies */}
        {replies.map(reply => renderComment(reply, true))}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      <h3 className="text-lg font-medium text-[#1D1D1F] mb-4 flex items-center gap-2">
        Comments <span className="text-[#1D1D1F]/40 text-sm font-normal">({comments.length})</span>
      </h3>

      <div className="flex-1 overflow-y-auto pr-2 -mr-2 space-y-2">
        {comments.length === 0 ? (
          <div className="text-center py-8 text-[#1D1D1F]/40">
            <MessageCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No comments yet. Be the first to share your thoughts!</p>
          </div>
        ) : (
          rootComments.map(comment => renderComment(comment))
        )}
      </div>

      {allowComments && (
        <div className="mt-4 pt-4 border-t border-gray-100 bg-white">
          <div className="flex gap-2">
            <textarea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Add a comment..."
              className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-2xl text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all resize-none text-sm"
              rows={1}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleAddComment();
                }
              }}
            />
            <button
              onClick={() => handleAddComment()}
              disabled={!newComment.trim() || loading}
              className="p-3 bg-[#0066CC] text-white rounded-xl hover:bg-[#0052A3] transition-all disabled:opacity-50 disabled:cursor-not-allowed self-end"
            >
              {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Send className="w-5 h-5" />}
            </button>
          </div>
        </div>
      )}

      {/* Branded Modal */}
      <ModalComponent />
    </div>
  );
}

