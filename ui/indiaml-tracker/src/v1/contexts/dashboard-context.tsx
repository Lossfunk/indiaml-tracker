// src/contexts/DashboardContext.tsx

import React, { createContext, useContext, ReactNode } from 'react';
import { DashboardContextState } from '../types/dashboard';

// Create the context with default values
const DashboardContext = createContext<DashboardContextState | undefined>(undefined);

// Provider component
interface DashboardProviderProps {
  children: ReactNode;
  value: DashboardContextState;
}

export const DashboardProvider: React.FC<DashboardProviderProps> = ({ 
  children, 
  value 
}) => {
  return (
    <DashboardContext.Provider value={value}>
      {children}
    </DashboardContext.Provider>
  );
};

// Custom hook to use the dashboard context
export const useDashboardContext = () => {
  const context = useContext(DashboardContext);
  
  if (context === undefined) {
    throw new Error('useDashboardContext must be used within a DashboardProvider');
  }
  
  return context;
};
