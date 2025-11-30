/* eslint-disable react-refresh/only-export-components */
// Authentication context and hooks - cookie-based auth (matches backend)
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api, setUserData, removeUserData } from '../utils/api';

export interface User {
  id: string;
  email: string;
  name?: string;
  username?: string;
  role?: string;
  plan?: string;
  subscription_tier?: string; // Kept for compatibility if used elsewhere
  city?: string;
  country?: string;
  bio?: string;
  // Watermark settings
  watermark_enabled?: boolean;
  watermark_text?: string;
  watermark_position?: string;
  watermark_opacity?: number;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (email: string, password: string, name: string, role: string, city?: string, country?: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Check auth status on mount by calling /auth/me
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Try to get current user from backend (cookie-based)
        const response = await api.get<User>('/auth/me');
        
        if (response.success && response.data) {
          const userData = response.data;
          setUserData(userData);
          setUser(userData);
        } else {
          // No valid session - clear local data
          removeUserData();
          setUser(null);
        }
    } catch {
      removeUserData();
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await api.post<{ user: User } | User>('/auth/login', { email, password });
      
      if (response.success && response.data) {
        // Backend returns user data and sets HttpOnly cookie
        const userData = (response.data as { user: User }).user || response.data as User;
        
        setUserData(userData);
        setUser(userData);
        
        return { success: true };
      }
      
      return { success: false, error: response.error || 'Login failed' };
    } catch {
      return { success: false, error: 'Login failed. Please try again.' };
    }
  };

  const register = async (
    email: string, 
    password: string, 
    name: string, 
    role: string,
    city?: string,
    country?: string
  ) => {
    try {
      const response = await api.post<{ user: User } | User>('/auth/register', { 
        email, 
        password, 
        name, 
        role,
        ...(city && { city }),
        ...(country && { country }),
      });
      
      if (response.success && response.data) {
        // Backend returns user data and sets HttpOnly cookie
        const userData = (response.data as { user: User }).user || response.data as User;
        
        setUserData(userData);
        setUser(userData);
        
        return { success: true };
      }
      
      return { success: false, error: response.error || 'Registration failed' };
    } catch {
      return { success: false, error: 'Registration failed. Please try again.' };
    }
  };

  const logout = async () => {
    try {
      // Call logout endpoint to clear cookie
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Always clear local data
      removeUserData();
    setUser(null);
    }
  };

  const refreshUser = async () => {
    try {
      const response = await api.get<User>('/auth/me');
      
      if (response.success && response.data) {
        setUserData(response.data);
        setUser(response.data);
      } else {
        await logout();
      }
    } catch {
      await logout();
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

