import { useState, useEffect } from 'react';
import { Calendar as CalendarIcon, Clock, ChevronLeft, ChevronRight, Loader } from 'lucide-react';
import { api } from '../utils/api';
import { toast } from 'react-hot-toast';

interface AvailableSlot {
  start: string;
  end: string;
  available: boolean;
}

interface AvailabilityCalendarProps {
  photographerId: string;
  onSlotSelect: (slot: { start: string; end: string }) => void;
  selectedSlot?: { start: string; end: string } | null;
}

export default function AvailabilityCalendar({ 
  photographerId, 
  onSlotSelect, 
  selectedSlot 
}: AvailabilityCalendarProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [availableSlots, setAvailableSlots] = useState<AvailableSlot[]>([]);
  const [busyDates, setBusyDates] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [loadingSlots, setLoadingSlots] = useState(false);

  // Load busy times for the current month
  useEffect(() => {
    loadBusyTimes();
  }, [currentDate, photographerId]);

  // Load available slots when a date is selected
  useEffect(() => {
    if (selectedDate) {
      loadAvailableSlots(selectedDate);
    }
  }, [selectedDate, photographerId]);

  const loadBusyTimes = async () => {
    setLoading(true);
    try {
      const startOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
      const endOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);

      const response = await api.get(
        `/public/photographers/${photographerId}/availability/busy-times`,
        {
          params: {
            start_date: startOfMonth.toISOString(),
            end_date: endOfMonth.toISOString()
          }
        }
      );

      if (response.success && response.data) {
        const busySet = new Set<string>();
        response.data.busy_times?.forEach((time: any) => {
          const date = new Date(time.start).toISOString().split('T')[0];
          busySet.add(date);
        });
        setBusyDates(busySet);
      }
    } catch (error) {
      console.error('Error loading busy times:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableSlots = async (date: Date) => {
    setLoadingSlots(true);
    try {
      const dateStr = date.toISOString().split('T')[0]; // YYYY-MM-DD
      const response = await api.get(
        `/public/photographers/${photographerId}/availability/available-slots`,
        {
          params: { date: dateStr }
        }
      );

      if (response.success && response.data) {
        setAvailableSlots(response.data.available_slots || []);
      } else {
        toast.error('No available slots for this date');
        setAvailableSlots([]);
      }
    } catch (error: any) {
      console.error('Error loading slots:', error);
      toast.error(error.response?.data?.error || 'Failed to load available times');
      setAvailableSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  };

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    return { daysInMonth, startingDayOfWeek, year, month };
  };

  const isDateDisabled = (date: Date) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // Disable past dates
    if (date < today) return true;
    
    // Disable dates more than 60 days in advance
    const maxDate = new Date();
    maxDate.setDate(maxDate.getDate() + 60);
    if (date > maxDate) return true;

    return false;
  };

  const isDayBusy = (date: Date) => {
    const dateStr = date.toISOString().split('T')[0];
    return busyDates.has(dateStr);
  };

  const handlePrevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1));
    setSelectedDate(null);
    setAvailableSlots([]);
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1));
    setSelectedDate(null);
    setAvailableSlots([]);
  };

  const handleDateClick = (date: Date) => {
    if (isDateDisabled(date)) return;
    setSelectedDate(date);
  };

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  };

  const { daysInMonth, startingDayOfWeek, year, month } = getDaysInMonth(currentDate);
  const monthName = currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

  // Generate calendar grid
  const calendarDays = [];
  for (let i = 0; i < startingDayOfWeek; i++) {
    calendarDays.push(<div key={`empty-${i}`} className="p-2" />);
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const date = new Date(year, month, day);
    const isDisabled = isDateDisabled(date);
    const isBusy = isDayBusy(date);
    const isSelected = selectedDate && 
      selectedDate.getDate() === day && 
      selectedDate.getMonth() === month && 
      selectedDate.getFullYear() === year;

    calendarDays.push(
      <button
        key={day}
        onClick={() => handleDateClick(date)}
        disabled={isDisabled}
        className={`
          relative p-2 rounded-lg text-sm font-medium transition-all
          ${isSelected 
            ? 'bg-[#0066CC] text-white ring-2 ring-[#0066CC] ring-offset-2' 
            : isDisabled 
              ? 'text-gray-300 cursor-not-allowed' 
              : isBusy
                ? 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                : 'bg-white text-[#1D1D1F] hover:bg-gray-50 border border-gray-200'
          }
        `}
      >
        {day}
        {isBusy && !isDisabled && (
          <div className="absolute bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-orange-400" />
        )}
      </button>
    );
  }

  return (
    <div className="space-y-6">
      {/* Calendar */}
      <div className="bg-white rounded-2xl p-6 border border-gray-200">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-[#1D1D1F] flex items-center gap-2">
            <CalendarIcon className="w-5 h-5 text-[#0066CC]" />
            Select a Date
          </h3>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrevMonth}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Previous month"
            >
              <ChevronLeft className="w-5 h-5 text-[#1D1D1F]" />
            </button>
            <span className="text-sm font-medium text-[#1D1D1F] min-w-[150px] text-center">
              {monthName}
            </span>
            <button
              onClick={handleNextMonth}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Next month"
            >
              <ChevronRight className="w-5 h-5 text-[#1D1D1F]" />
            </button>
          </div>
        </div>

        {/* Weekday headers */}
        <div className="grid grid-cols-7 gap-2 mb-2">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
            <div key={day} className="text-center text-xs font-semibold text-gray-500 uppercase p-2">
              {day}
            </div>
          ))}
        </div>

        {/* Calendar grid */}
        {loading ? (
          <div className="py-12 text-center">
            <Loader className="w-8 h-8 text-[#0066CC] animate-spin mx-auto" />
          </div>
        ) : (
          <div className="grid grid-cols-7 gap-2">
            {calendarDays}
          </div>
        )}

        {/* Legend */}
        <div className="flex items-center gap-4 mt-6 pt-6 border-t border-gray-100">
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <div className="w-3 h-3 rounded-full bg-[#0066CC]" />
            <span>Selected</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <div className="w-3 h-3 rounded-full bg-gray-100 border border-gray-200 relative">
              <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-orange-400" />
            </div>
            <span>Limited</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <div className="w-3 h-3 rounded-full bg-gray-200" />
            <span>Unavailable</span>
          </div>
        </div>
      </div>

      {/* Time Slots */}
      {selectedDate && (
        <div className="bg-white rounded-2xl p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-[#1D1D1F] mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-[#0066CC]" />
            Available Times
            <span className="text-sm font-normal text-gray-500">
              {selectedDate.toLocaleDateString('en-US', { 
                weekday: 'long', 
                month: 'long', 
                day: 'numeric' 
              })}
            </span>
          </h3>

          {loadingSlots ? (
            <div className="py-12 text-center">
              <Loader className="w-8 h-8 text-[#0066CC] animate-spin mx-auto" />
              <p className="text-sm text-gray-500 mt-4">Loading available times...</p>
            </div>
          ) : availableSlots.length === 0 ? (
            <div className="py-12 text-center">
              <Clock className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-sm text-gray-600">No available times for this date</p>
              <p className="text-xs text-gray-500 mt-2">Please select another date</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {availableSlots.map((slot, index) => {
                const isSlotSelected = selectedSlot && 
                  selectedSlot.start === slot.start && 
                  selectedSlot.end === slot.end;

                return (
                  <button
                    key={index}
                    onClick={() => onSlotSelect({ start: slot.start, end: slot.end })}
                    className={`
                      p-3 rounded-xl text-sm font-medium transition-all
                      ${isSlotSelected
                        ? 'bg-[#0066CC] text-white ring-2 ring-[#0066CC] ring-offset-2'
                        : 'bg-gray-50 text-[#1D1D1F] hover:bg-gray-100 border border-gray-200'
                      }
                    `}
                  >
                    {formatTime(slot.start)}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
