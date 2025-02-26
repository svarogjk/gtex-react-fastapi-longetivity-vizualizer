import React from 'react';

interface LoadingProps {
  message?: string;
}

export const Loading: React.FC<LoadingProps> = ({ message = 'Loading...' }) => {
  return (
    <div className="flex items-center justify-center p-6 space-x-2">
      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-800"></div>
      <span className="text-gray-700">{message}</span>
    </div>
  );
};