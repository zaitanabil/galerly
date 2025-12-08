// Services Pricing Section Component - For public portfolio display
import { useState, useEffect } from 'react';
import { Check, Clock, Image, DollarSign } from 'lucide-react';
import { api } from '../utils/api';

interface Service {
  id: string;
  name: string;
  category: string;
  description: string;
  price: number;
  currency: string;
  duration_hours: number;
  included_photos: number;
  included_items: string[];
  addons_available: string[];
  booking_deposit: number;
  display_order: number;
}

interface ServicesProps {
  photographerId: string;
}

export default function ServicesSection({ photographerId }: ServicesProps) {
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadServices();
  }, [photographerId]);

  const loadServices = async () => {
    try {
      const response = await api.get(`/public/photographers/${photographerId}/services`);
      if (response.success && response.data) {
        setServices(response.data.services || []);
      }
    } catch (error) {
      console.error('Error loading services:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  if (loading) {
    return (
      <div className="py-8 text-center">
        <div className="w-8 h-8 border-4 border-[#0066CC] border-t-transparent rounded-full animate-spin mx-auto" />
      </div>
    );
  }

  if (services.length === 0) {
    return null; // Don't show empty section
  }

  return (
    <div className="py-16">
      {/* Header */}
      <div className="text-center mb-12">
        <h2 className="text-3xl md:text-4xl font-serif font-medium text-[#1D1D1F] mb-4">
          Services & Pricing
        </h2>
        <p className="text-[#1D1D1F]/60 max-w-2xl mx-auto">
          Professional photography services tailored to your needs
        </p>
      </div>

      {/* Services Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {services.map((service) => (
          <div
            key={service.id}
            className="glass-panel p-8 hover:shadow-xl transition-all duration-300 flex flex-col"
          >
            {/* Category Badge */}
            <div className="mb-4">
              <span className="inline-block px-3 py-1 bg-[#0066CC]/10 text-[#0066CC] rounded-full text-xs font-medium uppercase tracking-wide">
                {service.category}
              </span>
            </div>

            {/* Service Name */}
            <h3 className="text-2xl font-serif font-medium text-[#1D1D1F] mb-3">
              {service.name}
            </h3>

            {/* Price */}
            <div className="mb-6">
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-bold text-[#1D1D1F]">
                  {formatPrice(service.price, service.currency)}
                </span>
              </div>
              {service.booking_deposit > 0 && (
                <p className="text-sm text-[#1D1D1F]/60 mt-1">
                  {formatPrice(service.booking_deposit, service.currency)} deposit required
                </p>
              )}
            </div>

            {/* Description */}
            {service.description && (
              <p className="text-[#1D1D1F]/70 mb-6 leading-relaxed">
                {service.description}
              </p>
            )}

            {/* Quick Stats */}
            <div className="flex flex-wrap gap-4 mb-6 text-sm text-[#1D1D1F]/60">
              {service.duration_hours > 0 && (
                <div className="flex items-center gap-1.5">
                  <Clock className="w-4 h-4" />
                  <span>{service.duration_hours}h coverage</span>
                </div>
              )}
              {service.included_photos > 0 && (
                <div className="flex items-center gap-1.5">
                  <Image className="w-4 h-4" />
                  <span>{service.included_photos} photos</span>
                </div>
              )}
            </div>

            {/* Included Items */}
            {service.included_items && service.included_items.length > 0 && (
              <div className="mb-6 flex-1">
                <h4 className="text-sm font-semibold text-[#1D1D1F] mb-3 uppercase tracking-wide">
                  What's Included
                </h4>
                <ul className="space-y-2">
                  {service.included_items.map((item, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm text-[#1D1D1F]/70">
                      <Check className="w-4 h-4 text-[#0066CC] flex-shrink-0 mt-0.5" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Add-ons */}
            {service.addons_available && service.addons_available.length > 0 && (
              <div className="mb-6 pt-6 border-t border-gray-100">
                <h4 className="text-sm font-semibold text-[#1D1D1F] mb-3 uppercase tracking-wide">
                  Available Add-ons
                </h4>
                <ul className="space-y-2">
                  {service.addons_available.map((addon, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm text-[#1D1D1F]/60">
                      <DollarSign className="w-4 h-4 flex-shrink-0 mt-0.5" />
                      <span>{addon}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* CTA Button */}
            <button
              onClick={() => {
                // Scroll to contact form or open booking modal
                const contactSection = document.getElementById('contact');
                if (contactSection) {
                  contactSection.scrollIntoView({ behavior: 'smooth' });
                }
              }}
              className="w-full py-3 bg-[#1D1D1F] text-white rounded-xl font-medium hover:bg-black transition-all hover:scale-[1.02] mt-auto"
            >
              Book Now
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
