// About Section Component - For public portfolio display
import { Award, Camera, MapPin, Calendar } from 'lucide-react';

interface AboutProps {
  photographer: {
    name: string;
    business_name?: string;
    bio?: string;
    city?: string;
    country?: string;
    specializations?: string[];
    years_experience?: number;
    awards?: string[];
    equipment?: string[];
    philosophy?: string;
  };
}

export default function AboutSection({ photographer }: AboutProps) {
  if (!photographer.bio && !photographer.philosophy) {
    return null; // Don't show empty section
  }

  return (
    <div className="py-16">
      {/* Header */}
      <div className="text-center mb-12">
        <h2 className="text-3xl md:text-4xl font-serif font-medium text-[#1D1D1F] mb-4">
          About {photographer.name}
        </h2>
        {photographer.business_name && (
          <p className="text-xl text-[#1D1D1F]/60">{photographer.business_name}</p>
        )}
      </div>

      <div className="max-w-4xl mx-auto">
        {/* Main Bio */}
        {photographer.bio && (
          <div className="glass-panel p-8 mb-8">
            <p className="text-lg text-[#1D1D1F]/80 leading-relaxed whitespace-pre-line">
              {photographer.bio}
            </p>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Location */}
          {(photographer.city || photographer.country) && (
            <div className="glass-panel p-6 text-center">
              <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center mx-auto mb-3">
                <MapPin className="w-6 h-6 text-[#0066CC]" />
              </div>
              <h3 className="font-medium text-[#1D1D1F] mb-1">Location</h3>
              <p className="text-sm text-[#1D1D1F]/60">
                {[photographer.city, photographer.country].filter(Boolean).join(', ')}
              </p>
            </div>
          )}

          {/* Experience */}
          {photographer.years_experience && (
            <div className="glass-panel p-6 text-center">
              <div className="w-12 h-12 bg-purple-50 rounded-xl flex items-center justify-center mx-auto mb-3">
                <Calendar className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="font-medium text-[#1D1D1F] mb-1">Experience</h3>
              <p className="text-sm text-[#1D1D1F]/60">
                {photographer.years_experience} {photographer.years_experience === 1 ? 'year' : 'years'}
              </p>
            </div>
          )}

          {/* Specializations */}
          {photographer.specializations && photographer.specializations.length > 0 && (
            <div className="glass-panel p-6 text-center">
              <div className="w-12 h-12 bg-green-50 rounded-xl flex items-center justify-center mx-auto mb-3">
                <Camera className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="font-medium text-[#1D1D1F] mb-1">Specializations</h3>
              <p className="text-sm text-[#1D1D1F]/60">
                {photographer.specializations.slice(0, 3).join(', ')}
              </p>
            </div>
          )}
        </div>

        {/* Philosophy */}
        {photographer.philosophy && (
          <div className="glass-panel p-8 mb-8 bg-gradient-to-br from-blue-50/50 to-purple-50/50">
            <h3 className="text-xl font-medium text-[#1D1D1F] mb-4 flex items-center gap-2">
              <Camera className="w-5 h-5 text-[#0066CC]" />
              Photography Philosophy
            </h3>
            <p className="text-[#1D1D1F]/80 leading-relaxed italic">
              "{photographer.philosophy}"
            </p>
          </div>
        )}

        {/* Awards & Recognition */}
        {photographer.awards && photographer.awards.length > 0 && (
          <div className="glass-panel p-8 mb-8">
            <h3 className="text-xl font-medium text-[#1D1D1F] mb-6 flex items-center gap-2">
              <Award className="w-5 h-5 text-[#0066CC]" />
              Awards & Recognition
            </h3>
            <ul className="space-y-3">
              {photographer.awards.map((award, index) => (
                <li key={index} className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-[#0066CC] rounded-full mt-2 flex-shrink-0" />
                  <span className="text-[#1D1D1F]/70">{award}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Equipment */}
        {photographer.equipment && photographer.equipment.length > 0 && (
          <div className="glass-panel p-8">
            <h3 className="text-xl font-medium text-[#1D1D1F] mb-6 flex items-center gap-2">
              <Camera className="w-5 h-5 text-[#0066CC]" />
              Equipment
            </h3>
            <div className="flex flex-wrap gap-2">
              {photographer.equipment.map((item, index) => (
                <span
                  key={index}
                  className="px-4 py-2 bg-white/50 border border-gray-200 rounded-full text-sm text-[#1D1D1F]/70"
                >
                  {item}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
