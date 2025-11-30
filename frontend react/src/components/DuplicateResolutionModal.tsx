import { Photo } from '../services/photoService';
import { X, AlertTriangle, FileImage } from 'lucide-react';
import { cdnBaseUrl } from '../config/env';

interface DuplicateResolutionModalProps {
  isOpen: boolean;
  onClose: () => void;
  newFile: File;
  duplicates: Photo[];
  onResolve: (action: 'skip' | 'upload') => void;
}

export default function DuplicateResolutionModal({
  isOpen,
  onClose,
  newFile,
  duplicates,
  onResolve,
}: DuplicateResolutionModalProps) {
  if (!isOpen) return null;

  const handleSkip = () => {
    onResolve('skip');
    onClose();
  };

  const handleUpload = () => {
    onResolve('upload');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[20000] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-white rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-300">
        {/* Header */}
        <div className="p-6 border-b border-gray-100 flex items-start justify-between bg-gradient-to-b from-white to-gray-50/50">
          <div className="flex gap-4">
            <div className="p-3 bg-amber-50 rounded-full h-fit">
              <AlertTriangle className="w-6 h-6 text-amber-500" />
            </div>
            <div>
              <h2 className="text-2xl font-serif font-medium text-[#1D1D1F] mb-1">
                Duplicate File Detected
              </h2>
              <p className="text-[#1D1D1F]/60">
                This file already exists in your gallery. How would you like to proceed?
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-[#1D1D1F]/60" />
          </button>
        </div>

        {/* Content */}
        <div className="p-8 overflow-y-auto bg-gray-50/30 flex-1">
          {/* New File Card */}
          <div className="bg-blue-50/50 border border-blue-100 rounded-2xl p-6 mb-8 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 bg-blue-100/50 text-blue-700 text-xs font-bold uppercase tracking-wider rounded-bl-2xl">
              New Upload
            </div>
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
                <FileImage className="w-8 h-8 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-medium text-[#1D1D1F] mb-1">{newFile.name}</h3>
                <p className="text-sm text-[#1D1D1F]/60">
                  {(newFile.size / (1024 * 1024)).toFixed(2)} MB • Ready to upload
                </p>
              </div>
            </div>
          </div>

          {/* Existing Duplicates */}
          <h3 className="text-sm font-bold text-[#1D1D1F]/40 uppercase tracking-wider mb-4">
            Existing Duplicate{duplicates.length > 1 ? 's' : ''} Found
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {duplicates.map((dup) => (
              <div key={dup.id} className="bg-white border border-gray-200 rounded-2xl overflow-hidden hover:shadow-lg transition-all duration-300 group">
                <div className="aspect-video bg-gray-100 relative overflow-hidden">
                  <img
                    src={`${cdnBaseUrl}/${dup.medium_url || dup.url}`}
                    alt={dup.filename}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute top-3 right-3 bg-white/90 backdrop-blur px-3 py-1 rounded-full text-xs font-medium text-amber-600 shadow-sm">
                    Existing Match
                  </div>
                </div>
                <div className="p-4">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-medium text-[#1D1D1F] truncate pr-2">{dup.filename}</h4>
                  </div>
                  <div className="flex gap-3 text-xs text-[#1D1D1F]/60">
                    <span className="flex items-center gap-1 bg-gray-100 px-2 py-1 rounded-md">
                      {(dup.file_size / (1024 * 1024)).toFixed(2)} MB
                    </span>
                    <span className="flex items-center gap-1 bg-gray-100 px-2 py-1 rounded-md">
                      {new Date(dup.uploaded_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="p-6 border-t border-gray-100 bg-white flex justify-end gap-3">
          <button
            onClick={handleSkip}
            className="px-6 py-3 bg-white border border-gray-200 text-[#1D1D1F] rounded-xl font-medium hover:bg-gray-50 transition-all focus:ring-2 focus:ring-gray-200"
          >
            Skip Upload
          </button>
          <button
            onClick={handleUpload}
            className="px-6 py-3 bg-[#0066CC] text-white rounded-xl font-medium hover:bg-[#0052A3] transition-all shadow-lg shadow-blue-500/20 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Upload Anyway
          </button>
        </div>
      </div>
    </div>
  );
}

