// Batch Operations Bar - Multi-select actions for galleries
import { useState } from 'react';
import { Check, Trash2, Lock, Unlock, Mail, Download, X } from 'lucide-react';

interface BatchOperationsBarProps {
  selectedCount: number;
  onDeselectAll: () => void;
  onDelete: () => void;
  onChangePrivacy: (isPublic: boolean) => void;
  onSendEmails: () => void;
  onExport: () => void;
}

export default function BatchOperationsBar({
  selectedCount,
  onDeselectAll,
  onDelete,
  onChangePrivacy,
  onSendEmails,
  onExport
}: BatchOperationsBarProps) {
  const [showConfirm, setShowConfirm] = useState(false);

  if (selectedCount === 0) return null;

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 animate-slide-up">
      <div className="bg-[#1D1D1F] text-white rounded-2xl shadow-2xl px-6 py-4 flex items-center gap-4">
        {/* Selection Count */}
        <div className="flex items-center gap-2 pr-4 border-r border-white/20">
          <div className="w-8 h-8 bg-[#0066CC] rounded-full flex items-center justify-center">
            <Check className="w-5 h-5" />
          </div>
          <span className="font-medium">
            {selectedCount} {selectedCount === 1 ? 'item' : 'items'} selected
          </span>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => onChangePrivacy(true)}
            className="p-2.5 hover:bg-white/10 rounded-lg transition-colors"
            title="Make Public"
          >
            <Unlock className="w-5 h-5" />
          </button>
          <button
            onClick={() => onChangePrivacy(false)}
            className="p-2.5 hover:bg-white/10 rounded-lg transition-colors"
            title="Make Private"
          >
            <Lock className="w-5 h-5" />
          </button>
          <button
            onClick={onSendEmails}
            className="p-2.5 hover:bg-white/10 rounded-lg transition-colors"
            title="Send Emails"
          >
            <Mail className="w-5 h-5" />
          </button>
          <button
            onClick={onExport}
            className="p-2.5 hover:bg-white/10 rounded-lg transition-colors"
            title="Export"
          >
            <Download className="w-5 h-5" />
          </button>
          
          <div className="w-px h-6 bg-white/20 mx-2" />
          
          <button
            onClick={() => setShowConfirm(true)}
            className="p-2.5 hover:bg-red-500/20 rounded-lg transition-colors text-red-400 hover:text-red-300"
            title="Delete Selected"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>

        {/* Close Button */}
        <button
          onClick={onDeselectAll}
          className="ml-2 p-2 hover:bg-white/10 rounded-lg transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Delete Confirmation */}
      {showConfirm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md">
            <h3 className="text-lg font-medium text-[#1D1D1F] mb-2">
              Delete {selectedCount} {selectedCount === 1 ? 'Gallery' : 'Galleries'}?
            </h3>
            <p className="text-[#1D1D1F]/60 mb-6">
              This action cannot be undone. All photos and client access will be permanently removed.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowConfirm(false)}
                className="flex-1 py-2.5 border border-gray-200 text-[#1D1D1F] rounded-xl hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  onDelete();
                  setShowConfirm(false);
                }}
                className="flex-1 py-2.5 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Selection Checkbox Component
export function SelectionCheckbox({ checked, onChange }: { checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <div
      className={`w-6 h-6 rounded-lg border-2 flex items-center justify-center cursor-pointer transition-all ${
        checked
          ? 'bg-[#0066CC] border-[#0066CC]'
          : 'border-gray-300 hover:border-[#0066CC]'
      }`}
      onClick={(e) => {
        e.stopPropagation();
        onChange(!checked);
      }}
    >
      {checked && <Check className="w-4 h-4 text-white" />}
    </div>
  );
}
