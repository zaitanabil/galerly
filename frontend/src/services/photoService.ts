/* eslint-disable @typescript-eslint/no-explicit-any */
// Photo service - handles all photo-related API calls
import { api } from '../utils/api';

export interface Photo {
  id: string;
  gallery_id: string;
  user_id: string;
  filename: string;
  url: string;
  original_download_url?: string;
  thumbnail_url?: string;
  small_url?: string;
  medium_url?: string;
  large_url?: string;
  file_size: number;
  width?: number;
  height?: number;
  uploaded_at: string;
  metadata?: Record<string, any>;
  comments?: Comment[];
  is_favorite?: boolean;
  favorites_count?: number;
  comments_count?: number;
  status?: string;
  type?: 'image' | 'video';
  hls_url?: string;
}

export interface Comment {
  id: string;
  photo_id: string;
  user_id: string;
  user_name: string;
  user_email?: string;
  text: string;
  created_at: string;
  updated_at?: string;
  parent_id?: string | null;
  reactions?: {
    like?: string[];
    heart?: string[];
    dislike?: string[];
  };
  is_edited?: boolean;
  annotation?: string;
}

export interface UploadUrlResponse {
  upload_url: string;
  photo_id: string;
  fields?: Record<string, string>;
}

// Get upload URL for presigned upload
export async function getUploadUrl(galleryId: string, filename: string, fileSize: number, fileType: string) {
  return api.post<UploadUrlResponse>(`/galleries/${galleryId}/photos/upload-url`, {
    filename,
    file_size: fileSize,
    file_type: fileType,
  });
}

// Confirm photo upload after successful upload  
export async function confirmUpload(photoId: string, galleryId: string, s3Key: string, filename: string, fileSize: number, fileHash?: string) {
  return api.post<Photo>(`/galleries/${galleryId}/photos/confirm-upload`, {
    photo_id: photoId,
    s3_key: s3Key,
    filename: filename,
    file_size: fileSize,
    file_hash: fileHash,
  });
}

// Check for duplicate photo
export async function checkDuplicates(galleryId: string, filename: string, fileSize: number) {
  return api.post<{ has_duplicates: boolean; duplicates: Photo[] }>(`/galleries/${galleryId}/photos/check-duplicates`, {
    filename,
    file_size: fileSize,
  });
}

// Update photo metadata
export async function updatePhoto(photoId: string, data: { filename?: string; status?: string; metadata?: Record<string, any> }) {
  return api.put<Photo>(`/photos/${photoId}`, data);
}

// Delete photos
export async function deletePhotos(galleryId: string, photoIds: string[]) {
  return api.delete(`/galleries/${galleryId}/photos/delete`, { photo_ids: photoIds });
}

// Add comment to photo
export async function addComment(
  photoId: string, 
  text: string, 
  parentId?: string,
  authorName?: string,
  authorEmail?: string,
  annotation?: string // JSON string of points or SVG path
) {
  return api.post<Comment>(`/photos/${photoId}/comments`, { 
    text,
    parent_id: parentId,
    author_name: authorName,
    author_email: authorEmail,
    annotation
  });
}

// Update comment (text or reactions)
export async function updateComment(
  photoId: string, 
  commentId: string, 
  data: { text?: string; reaction?: string; action?: 'toggle' }
) {
  return api.put<Comment>(`/photos/${photoId}/comments/${commentId}`, data);
}

// Delete comment
export async function deleteComment(photoId: string, commentId: string) {
  return api.delete(`/photos/${photoId}/comments/${commentId}`);
}

// Search photos
export async function searchPhotos(params: {
  gallery_id?: string;
  query?: string;
  page?: number;
  limit?: number;
}) {
  const queryParams = new URLSearchParams();
  if (params.gallery_id) queryParams.append('gallery_id', params.gallery_id);
  if (params.query) queryParams.append('q', params.query);
  if (params.page) queryParams.append('page', params.page.toString());
  if (params.limit) queryParams.append('limit', params.limit.toString());
  
  return api.get<{ photos: Photo[]; total: number }>(`/photos/search?${queryParams.toString()}`);
}

// Send batch notification to clients
export async function sendBatchNotification(galleryId: string, photoIds: string[], message: string) {
  return api.post(`/galleries/${galleryId}/notify-clients`, {
    photo_ids: photoIds,
    message,
  });
}

// Initialize multipart upload (for large files)
export async function initializeMultipartUpload(galleryId: string, filename: string, fileSize: number, fileType: string) {
  return api.post(`/galleries/${galleryId}/photos/multipart-upload/init`, {
    filename,
    file_size: fileSize,
    file_type: fileType,
  });
}

// Complete multipart upload
export async function completeMultipartUpload(galleryId: string, uploadId: string, photoId: string, parts: { PartNumber: number; ETag: string }[], fileHash?: string, s3Key?: string) {
  return api.post(`/galleries/${galleryId}/photos/multipart-upload/complete`, {
    upload_id: uploadId,
    photo_id: photoId,
    parts,
    file_hash: fileHash,
    s3_key: s3Key,
  });
}

// Abort multipart upload
export async function abortMultipartUpload(galleryId: string, uploadId: string, photoId: string) {
  return api.post(`/galleries/${galleryId}/photos/multipart-upload/abort`, {
    upload_id: uploadId,
    photo_id: photoId,
  });
}

// Get single photo details
export async function getPhoto(photoId: string) {
  return api.get<Photo>(`/photos/${photoId}`);
}

export default {
  getPhoto,
  getUploadUrl,
  confirmUpload,
  checkDuplicates,
  updatePhoto,
  deletePhotos,
  addComment,
  updateComment,
  deleteComment,
  searchPhotos,
  sendBatchNotification,
  initializeMultipartUpload,
  completeMultipartUpload,
  abortMultipartUpload,
};

