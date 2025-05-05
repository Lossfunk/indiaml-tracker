import React from 'react';
import { dashboardData } from '@/components/dashboard-data';
import Dashboard from './components/dashboard/Dashboard';

// --- Example Usage ---
const App = () => {
  return <Dashboard dashboardData={dashboardData} />;
};

export default App;