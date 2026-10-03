'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

export interface User {
  id: string;
  email: string;
  name: string;
  plan: 'FREE' | 'CREATOR' | 'PRO' | 'ENTERPRISE';
  role: 'USER' | 'ADMIN';
  videosLimit: number;
  videosUsed: number;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, name: string) => void;
  logout: () => void;
  upgradeToCreator: () => void;
}

const DEFAULT_USER: User = {
  id: 'usr_local_creator_123',
  email: 'creator@qoneqt.ai',
  name: 'Prachi Zala',
  plan: 'CREATOR',
  role: 'USER',
  videosLimit: 15,
  videosUsed: 3
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem('qoneqt_user');
    if (saved) {
      try {
        setUser(JSON.parse(saved));
      } catch {
        setUser(DEFAULT_USER);
      }
    } else {
      setUser(DEFAULT_USER);
      localStorage.setItem('qoneqt_user', JSON.stringify(DEFAULT_USER));
    }
  }, []);

  const login = (email: string, name: string) => {
    const newUser: User = {
      ...DEFAULT_USER,
      email,
      name,
    };
    setUser(newUser);
    localStorage.setItem('qoneqt_user', JSON.stringify(newUser));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('qoneqt_user');
  };

  const upgradeToCreator = () => {
    if (!user) return;
    const updatedUser: User = {
      ...user,
      plan: 'CREATOR',
      videosLimit: 15,
    };
    setUser(updatedUser);
    localStorage.setItem('qoneqt_user', JSON.stringify(updatedUser));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: Boolean(user),
        login,
        logout,
        upgradeToCreator,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
