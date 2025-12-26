import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// MOCK IMPLEMENTATION
// To use Firebase:
// 1. npm install firebase
// 2. Initialize firebaseApp
// 3. Replace these functions with signInWithEmailAndPassword, etc.

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check local storage for session
    const storedUser = localStorage.getItem('tahlil_user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.removeItem('tahlil_user');
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Simple mock validation
    if (password.length < 6) {
      setIsLoading(false);
      throw new Error("Password must be at least 6 characters");
    }

    const mockUser: User = {
      id: 'usr_' + Math.random().toString(36).substr(2, 9),
      email: email,
      username: email.split('@')[0], // Derive username from email for mock
      avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${email}`
    };

    setUser(mockUser);
    localStorage.setItem('tahlil_user', JSON.stringify(mockUser));
    setIsLoading(false);
  };

  const register = async (email: string, username: string, password: string) => {
    setIsLoading(true);
    await new Promise(resolve => setTimeout(resolve, 1000));

    const mockUser: User = {
      id: 'usr_' + Math.random().toString(36).substr(2, 9),
      email: email,
      username: username,
      avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${username}`
    };

    setUser(mockUser);
    localStorage.setItem('tahlil_user', JSON.stringify(mockUser));
    setIsLoading(false);
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('tahlil_user');
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
