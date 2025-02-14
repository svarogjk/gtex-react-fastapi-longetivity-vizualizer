// src/features/dashboard/Dashboard.tsx
import React from 'react';
import { Header } from '../../components/layout/Header';
import { Sidebar } from '../../components/layout/Sidebar';
import { AnalysisDropdowns } from '../../components/analysis/AnalysisDropdowns';

export const Dashboard: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-100">
      <Header />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Left Panel with Dropdowns */}
          <div className="w-64 flex-shrink-0">
            <AnalysisDropdowns />
          </div>
          
          {/* Main Content Area */}
          <div className="flex-1 bg-white rounded-lg shadow">
            {/* Main content will go here */}
            <div className="p-6">
              <h2 className="text-xl font-semibold text-gray-900">Analysis Results</h2>
              {/* Add your analysis components here */}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};