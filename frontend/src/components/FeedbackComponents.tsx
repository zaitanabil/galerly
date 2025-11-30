// Error alert component for displaying API errors
import { AlertCircle, X } from 'lucide-react';

interface ErrorAlertProps {
  error: string | null;
  onDismiss?: () => void;
  className?: string;
}

export function ErrorAlert({ error, onDismiss, className = '' }: ErrorAlertProps) {
  if (!error) return null;

  return (
    <div className={`p-4 bg-red-50 border border-red-100 rounded-2xl flex items-start gap-3 ${className}`}>
      <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <p className="text-sm text-red-800">{error}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="p-1 text-red-600 hover:bg-red-100 rounded-lg transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

// Success alert component
interface SuccessAlertProps {
  message: string | null;
  onDismiss?: () => void;
  className?: string;
}

export function SuccessAlert({ message, onDismiss, className = '' }: SuccessAlertProps) {
  if (!message) return null;

  return (
    <div className={`p-4 bg-green-50 border border-green-100 rounded-2xl flex items-start gap-3 ${className}`}>
      <div className="w-5 h-5 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
        <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <div className="flex-1">
        <p className="text-sm text-green-800">{message}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="p-1 text-green-600 hover:bg-green-100 rounded-lg transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

// Loading spinner component
interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  text?: string;
}

export function LoadingSpinner({ size = 'md', className = '', text }: LoadingSpinnerProps) {
  const sizes = {
    sm: 'w-8 h-8 border-2',
    md: 'w-12 h-12 border-3',
    lg: 'w-16 h-16 border-4',
  };

  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <div
        className={`${sizes[size]} border-[#0066CC] border-t-transparent rounded-full animate-spin`}
      />
      {text && <p className="mt-4 text-sm text-[#1D1D1F]/60">{text}</p>}
    </div>
  );
}

// Empty state component
interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function EmptyState({ icon, title, description, action, className = '' }: EmptyStateProps) {
  return (
    <div className={`glass-panel p-12 text-center ${className}`}>
      {icon && (
        <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
          {icon}
        </div>
      )}
      <h3 className="text-xl font-medium text-[#1D1D1F] mb-2">{title}</h3>
      {description && (
        <p className="text-[#1D1D1F]/60 mb-6">{description}</p>
      )}
      {action && (
        <button
          onClick={action.onClick}
          className="inline-flex items-center gap-2 px-8 py-4 bg-[#0066CC] text-white rounded-full font-medium hover:bg-[#0052A3] transition-all hover:scale-105 shadow-lg shadow-blue-500/20"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}

export default {
  ErrorAlert,
  SuccessAlert,
  LoadingSpinner,
  EmptyState,
};

