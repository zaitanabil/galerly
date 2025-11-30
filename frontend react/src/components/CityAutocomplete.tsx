import { useState, useEffect, useRef } from 'react';
import { api } from '../utils/api';
import { MapPin, Loader } from 'lucide-react';

interface City {
  city: string;
  country: string;
}

interface CityAutocompleteProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export default function CityAutocomplete({
  value,
  onChange,
  placeholder = 'Enter your city',
  className = '',
}: CityAutocompleteProps) {
  const [query, setQuery] = useState(value);
  const [suggestions, setSuggestions] = useState<City[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setQuery(value);
  }, [value]);

  useEffect(() => {
    // Close suggestions on click outside
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const searchCities = async (searchTerm: string) => {
    if (!searchTerm || searchTerm.length < 2) {
      setSuggestions([]);
      return;
    }

    setLoading(true);
    try {
      const response = await api.get<{ cities: City[] }>(`/cities/search?q=${encodeURIComponent(searchTerm)}`);
      if (response.success && response.data) {
        setSuggestions(response.data.cities);
      }
    } catch (error) {
      console.error('Error searching cities:', error);
    } finally {
      setLoading(false);
    }
  };

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (query && query !== value) {
        searchCities(query);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query, value]);

  const handleSelect = (city: City) => {
    const cityString = `${city.city}, ${city.country}`;
    setQuery(cityString);
    onChange(cityString);
    setShowSuggestions(false);
  };

  return (
    <div className={`relative ${className}`} ref={wrapperRef}>
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setShowSuggestions(true);
            onChange(e.target.value);
          }}
          onFocus={() => setShowSuggestions(true)}
          placeholder={placeholder}
          className="w-full pl-14 pr-6 py-5 bg-white/80 backdrop-blur-md border border-[#1D1D1F]/10 rounded-full text-[#1D1D1F] placeholder-[#1D1D1F]/40 focus:outline-none focus:ring-2 focus:ring-[#0066CC]/20 focus:border-[#0066CC] transition-all shadow-lg text-lg"
        />
        {/* Loader positioned absolutely in parent usually, but here we can keep it */}
        {loading && (
          <div className="absolute right-6 top-1/2 -translate-y-1/2">
            <Loader className="w-5 h-5 animate-spin text-[#0066CC]" />
          </div>
        )}
      </div>

      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-100 rounded-2xl shadow-xl max-h-60 overflow-y-auto overflow-hidden">
          {suggestions.map((city, index) => (
            <button
              key={`${city.city}-${city.country}-${index}`}
              onClick={() => handleSelect(city)}
              className="w-full text-left px-6 py-4 hover:bg-gray-50 flex items-center gap-3 transition-colors border-b border-gray-50 last:border-0"
            >
              <MapPin className="w-4 h-4 text-[#1D1D1F]/40 flex-shrink-0" />
              <span className="text-base text-[#1D1D1F]">
                <span className="font-medium">{city.city}</span>, {city.country}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

