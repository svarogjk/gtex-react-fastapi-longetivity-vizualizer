import { Activity, Database, Thermometer } from 'lucide-react';

export const Header = () => {
  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Thermometer className="h-7 w-7 text-purple-600" />
            <h1 className="text-2xl font-bold text-gray-900">Longevity Gene Explorer</h1>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center text-sm font-medium text-gray-700">
              <Activity className="h-5 w-5 mr-1 text-green-600" />
              <span>Expression</span>
            </div>
            
            <div className="flex items-center text-sm font-medium text-gray-500">
              <Database className="h-5 w-5 mr-1 text-gray-400" />
              <span>Datasets</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};