import { AlertTriangle, Clock } from 'lucide-react';

interface ExpirationBannerProps {
  expiryDate?: string | null;
  expiryDays?: number | null;
  archived?: boolean;
}

export default function ExpirationBanner({ expiryDate, archived }: ExpirationBannerProps) {
  if (archived) {
    return (
      <div className="bg-red-50 border-b border-red-100 p-4 sticky top-[73px] z-30">
        <div className="max-w-7xl mx-auto flex items-center justify-center gap-3 text-red-700">
          <AlertTriangle className="w-5 h-5" />
          <p className="font-medium">This gallery has been archived and is no longer accessible to clients.</p>
        </div>
      </div>
    );
  }

  if (!expiryDate) return null;

  const expiration = new Date(expiryDate);
  const now = new Date();
  const diffTime = expiration.getTime() - now.getTime();

  // If already expired
  if (diffTime < 0) {
    return (
      <div className="bg-red-600 text-white p-4 sticky top-[73px] z-30 shadow-md">
        <div className="max-w-7xl mx-auto flex items-center justify-center gap-3 animate-in slide-in-from-top-2">
          <AlertTriangle className="w-5 h-5 text-white" />
          <div>
            <span className="font-bold">This gallery has expired.</span>
            <span className="ml-2 opacity-90">Access is restricted. Contact the photographer to extend access.</span>
          </div>
        </div>
      </div>
    );
  }

  // Calculate detailed remaining time
  const days = Math.floor(diffTime / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diffTime % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((diffTime % (1000 * 60 * 60)) / (1000 * 60));

  // Only show if expiring soon (<= 7 days)
  if (days > 7) return null;

  let timeString = '';
  if (days > 0) {
    timeString = `${days} day${days === 1 ? '' : 's'} remaining`;
  } else if (hours > 0) {
    timeString = `${hours} hour${hours === 1 ? '' : 's'} remaining`;
  } else {
    timeString = `${minutes} minute${minutes === 1 ? '' : 's'} remaining`;
    if (minutes === 0) timeString = 'Expiring shortly';
  }

    return (
      <div className="bg-amber-500 text-white p-4 sticky top-[73px] z-30 shadow-md">
        <div className="max-w-7xl mx-auto flex items-center justify-center gap-3 animate-in slide-in-from-top-2">
          <Clock className="w-5 h-5 text-white" />
          <div>
            <span className="font-bold">Expiring soon!</span>
            <span className="ml-2 opacity-90">
            {timeString}
            </span>
          </div>
        </div>
      </div>
    );
}

