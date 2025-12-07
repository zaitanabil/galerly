import React from 'react';
import { X, AlertCircle, CheckCircle, Info } from 'lucide-react';

interface BrandedModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  message: string;
  type?: 'alert' | 'confirm' | 'prompt' | 'success' | 'error' | 'info';
  confirmText?: string;
  cancelText?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
  promptValue?: string;
  onPromptChange?: (value: string) => void;
  promptPlaceholder?: string;
  showCloseButton?: boolean;
  confirmButtonVariant?: 'primary' | 'danger' | 'success';
}

export const BrandedModal: React.FC<BrandedModalProps> = ({
  isOpen,
  onClose,
  title,
  message,
  type = 'alert',
  confirmText = 'OK',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  promptValue = '',
  onPromptChange,
  promptPlaceholder = '',
  showCloseButton = true,
  confirmButtonVariant = 'primary',
}) => {
  if (!isOpen) return null;

  const handleConfirm = () => {
    if (onConfirm) onConfirm();
    onClose();
  };

  const handleCancel = () => {
    if (onCancel) onCancel();
    onClose();
  };

  const getIcon = () => {
    switch (type) {
      case 'error':
        return <AlertCircle className="w-12 h-12 text-red-500" />;
      case 'success':
        return <CheckCircle className="w-12 h-12 text-green-500" />;
      case 'confirm':
        return <AlertCircle className="w-12 h-12 text-amber-500" />;
      case 'info':
      default:
        return <Info className="w-12 h-12 text-blue-500" />;
    }
  };

  const getConfirmButtonClass = () => {
    switch (confirmButtonVariant) {
      case 'danger':
        return 'bg-red-600 hover:bg-red-700 text-white';
      case 'success':
        return 'bg-green-600 hover:bg-green-700 text-white';
      case 'primary':
      default:
        return 'bg-[#0066CC] hover:bg-[#0052A3] text-white';
    }
  };

  return (
    <div className="fixed inset-0 z-[99999] flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200"
        onClick={type === 'alert' || type === 'info' ? onClose : undefined}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 animate-in zoom-in-95 fade-in duration-200">
        {/* Close Button */}
        {showCloseButton && type !== 'confirm' && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}

        {/* Content */}
        <div className="p-8">
          {/* Icon */}
          <div className="flex justify-center mb-4">
            {getIcon()}
          </div>

          {/* Title */}
          <h2 className="text-2xl font-semibold text-[#1D1D1F] text-center mb-3">
            {title}
          </h2>

          {/* Message */}
          <p className="text-base text-[#1D1D1F]/70 text-center mb-6 whitespace-pre-line">
            {message}
          </p>

          {/* Prompt Input */}
          {type === 'prompt' && (
            <input
              type="text"
              value={promptValue}
              onChange={(e) => onPromptChange?.(e.target.value)}
              placeholder={promptPlaceholder}
              className="w-full px-4 py-3 bg-white/50 border border-gray-200 rounded-xl text-sm mb-6 focus:outline-none focus:ring-2 focus:ring-[#0066CC]"
              autoFocus
            />
          )}

          {/* Buttons */}
          <div className="flex gap-3">
            {(type === 'confirm' || type === 'prompt') && (
              <button
                onClick={handleCancel}
                className="flex-1 px-6 py-3 bg-gray-100 hover:bg-gray-200 text-[#1D1D1F] rounded-xl font-medium transition-colors"
              >
                {cancelText}
              </button>
            )}
            <button
              onClick={handleConfirm}
              className={`flex-1 px-6 py-3 rounded-xl font-medium transition-colors ${getConfirmButtonClass()}`}
            >
              {confirmText}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Hook for easier usage
export const useBrandedModal = () => {
  const [modalState, setModalState] = React.useState<{
    isOpen: boolean;
    title: string;
    message: string;
    type: 'alert' | 'confirm' | 'prompt' | 'success' | 'error' | 'info';
    confirmText?: string;
    cancelText?: string;
    onConfirm?: () => void;
    onCancel?: () => void;
    promptValue?: string;
    promptPlaceholder?: string;
    confirmButtonVariant?: 'primary' | 'danger' | 'success';
    resolve?: ((value: boolean) => void) | ((value: string | null) => void) | ((value: void) => void);
  }>({
    isOpen: false,
    title: '',
    message: '',
    type: 'alert',
    promptValue: '',
  });

  const showAlert = (title: string, message: string, type: 'success' | 'error' | 'info' = 'info') => {
    return new Promise<void>((resolve) => {
      setModalState({
        isOpen: true,
        title,
        message,
        type,
        confirmText: 'OK',
        onConfirm: () => resolve(),
      });
    });
  };

  const showConfirm = (
    title: string,
    message: string,
    confirmText: string = 'Confirm',
    cancelText: string = 'Cancel',
    variant: 'primary' | 'danger' | 'success' = 'primary'
  ) => {
    return new Promise<boolean>((resolve) => {
      setModalState({
        isOpen: true,
        title,
        message,
        type: 'confirm',
        confirmText,
        cancelText,
        confirmButtonVariant: variant,
        onConfirm: () => resolve(true),
        onCancel: () => resolve(false),
        resolve,
      });
    });
  };

  const showPrompt = (
    title: string,
    message: string,
    placeholder: string = '',
    defaultValue: string = ''
  ) => {
    return new Promise<string | null>((resolve) => {
      setModalState({
        isOpen: true,
        title,
        message,
        type: 'prompt',
        promptValue: defaultValue,
        promptPlaceholder: placeholder,
        confirmText: 'Submit',
        cancelText: 'Cancel',
        onConfirm: () => resolve(modalState.promptValue || null),
        onCancel: () => resolve(null),
        resolve,
      });
    });
  };

  const closeModal = () => {
    if (modalState.resolve && modalState.type === 'confirm') {
      (modalState.resolve as (value: boolean) => void)(false);
    } else if (modalState.resolve && modalState.type === 'prompt') {
      (modalState.resolve as (value: string | null) => void)(null);
    }
    setModalState((prev) => ({ ...prev, isOpen: false }));
  };

  const handlePromptChange = (value: string) => {
    setModalState((prev) => ({ ...prev, promptValue: value }));
  };

  const ModalComponent = () => (
    <BrandedModal
      {...modalState}
      onClose={closeModal}
      onPromptChange={handlePromptChange}
    />
  );

  return {
    showAlert,
    showConfirm,
    showPrompt,
    ModalComponent,
  };
};

