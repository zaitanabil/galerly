// Usage Warning Components - Alert users when approaching limits
import { AlertTriangle, X, TrendingUp, HardDrive, Video, FileImage } from 'lucide-react';
import { Link } from 'react-router-dom';

interface UsageWarningProps {
  type: 'storage' | 'video' | 'photos' | 'galleries';
  current: number;
  limit: number;
  unit: string;
  onDismiss?: () => void;
  onUpgrade?: () => void;
}

export function UsageWarning({ type, current, limit, unit, onDismiss, onUpgrade }: UsageWarningProps) {
  const percentage = (current / limit) * 100;
  
  // Only show warning if over 80%
  if (percentage < 80) return null;

  const isOverLimit = percentage >= 100;
  const isCritical = percentage >= 90;

  const getIcon = () => {
    switch (type) {
      case 'storage': return HardDrive;
      case 'video': return Video;
      case 'photos': return FileImage;
      case 'galleries': return TrendingUp;
      default: return AlertTriangle;
    }
  };

  const getTitle = () => {
    if (isOverLimit) return `${type.charAt(0).toUpperCase() + type.slice(1)} Limit Reached`;
    if (isCritical) return `${type.charAt(0).toUpperCase() + type.slice(1)} Almost Full`;
    return `Approaching ${type.charAt(0).toUpperCase() + type.slice(1)} Limit`;
  };

  const getMessage = () => {
    if (isOverLimit) {
      return `You've reached your ${type} limit. Upgrade your plan to continue.`;
    }
    if (isCritical) {
      return `You're using ${Math.round(percentage)}% of your ${type} quota. Consider upgrading soon.`;
    }
    return `You're at ${Math.round(percentage)}% of your ${type} limit.`;
  };

  const Icon = getIcon();
  const bgColor = isOverLimit ? 'bg-red-50' : isCritical ? 'bg-orange-50' : 'bg-yellow-50';
  const borderColor = isOverLimit ? 'border-red-200' : isCritical ? 'border-orange-200' : 'border-yellow-200';
  const textColor = isOverLimit ? 'text-red-800' : isCritical ? 'text-orange-800' : 'text-yellow-800';
  const iconColor = isOverLimit ? 'text-red-600' : isCritical ? 'text-orange-600' : 'text-yellow-600';
  const barColor = isOverLimit ? 'bg-red-500' : isCritical ? 'bg-orange-500' : 'bg-yellow-500';

  return (
    <div className={`${bgColor} border ${borderColor} rounded-xl p-4 mb-4`}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0">
          <Icon className={`w-5 h-5 ${iconColor}`} />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3 mb-2">
            <div>
              <h3 className={`font-medium ${textColor} mb-1`}>{getTitle()}</h3>
              <p className={`text-sm ${textColor}/80`}>{getMessage()}</p>
            </div>
            {onDismiss && (
              <button
                onClick={onDismiss}
                className={`p-1 ${textColor}/40 hover:${textColor} transition-colors flex-shrink-0`}
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Usage Bar */}
          <div className="mb-3">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className={`${textColor}/70`}>
                {current.toFixed(1)} {unit} of {limit} {unit}
              </span>
              <span className={`font-medium ${textColor}`}>
                {Math.min(percentage, 100).toFixed(0)}%
              </span>
            </div>
            <div className="w-full h-2 bg-white/50 rounded-full overflow-hidden">
              <div
                className={`h-full ${barColor} transition-all duration-300`}
                style={{ width: `${Math.min(percentage, 100)}%` }}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            {onUpgrade && (
              <button
                onClick={onUpgrade}
                className={`px-4 py-2 ${isOverLimit ? 'bg-red-600 hover:bg-red-700' : isCritical ? 'bg-orange-600 hover:bg-orange-700' : 'bg-yellow-600 hover:bg-yellow-700'} text-white text-sm font-medium rounded-lg transition-colors`}
              >
                Upgrade Plan
              </button>
            )}
            <Link
              to="/billing"
              className={`px-4 py-2 bg-white border ${borderColor} ${textColor} text-sm font-medium rounded-lg hover:bg-white/50 transition-colors`}
            >
              View Usage
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

// Usage Warnings Container - Shows all relevant warnings
interface UsageWarningsContainerProps {
  storageUsed: number;
  storageLimit: number;
  videoUsed: number;
  videoLimit: number;
  photosCount?: number;
  photosLimit?: number;
  onUpgrade?: () => void;
}

export function UsageWarningsContainer({
  storageUsed,
  storageLimit,
  videoUsed,
  videoLimit,
  photosCount,
  photosLimit,
  onUpgrade
}: UsageWarningsContainerProps) {
  const warnings = [];

  // Storage warning
  if ((storageUsed / storageLimit) * 100 >= 80) {
    warnings.push(
      <UsageWarning
        key="storage"
        type="storage"
        current={storageUsed}
        limit={storageLimit}
        unit="GB"
        onUpgrade={onUpgrade}
      />
    );
  }

  // Video warning
  if ((videoUsed / videoLimit) * 100 >= 80) {
    warnings.push(
      <UsageWarning
        key="video"
        type="video"
        current={videoUsed}
        limit={videoLimit}
        unit="min"
        onUpgrade={onUpgrade}
      />
    );
  }

  // Photos warning (if limits apply)
  if (photosCount && photosLimit && (photosCount / photosLimit) * 100 >= 80) {
    warnings.push(
      <UsageWarning
        key="photos"
        type="photos"
        current={photosCount}
        limit={photosLimit}
        unit="photos"
        onUpgrade={onUpgrade}
      />
    );
  }

  if (warnings.length === 0) return null;

  return <div className="space-y-3">{warnings}</div>;
}

// Mini Usage Badge - For dashboard/header
export function UsageBadge({ percentage, type }: { percentage: number; type: string }) {
  if (percentage < 80) return null;

  const isOverLimit = percentage >= 100;
  const isCritical = percentage >= 90;

  const bgColor = isOverLimit ? 'bg-red-100' : isCritical ? 'bg-orange-100' : 'bg-yellow-100';
  const textColor = isOverLimit ? 'text-red-700' : isCritical ? 'text-orange-700' : 'text-yellow-700';

  return (
    <Link
      to="/billing"
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 ${bgColor} ${textColor} rounded-full text-xs font-medium hover:opacity-80 transition-opacity`}
    >
      <AlertTriangle className="w-3 h-3" />
      <span>{Math.round(percentage)}% {type}</span>
    </Link>
  );
}
