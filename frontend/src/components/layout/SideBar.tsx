import React from 'react';
import { Card } from '../../components/ui/card';

export const Sidebar: React.FC = () => {
    return (
        <Card className="h-full p-4">
            <h2 className="text-lg font-semibold mb-4">Analysis Options</h2>
            <nav className="space-y-2">
                <a href="#expression" className="block p-2 hover:bg-gray-100 rounded">
                    Gene Expression
                </a>
                <a href="#survival" className="block p-2 hover:bg-gray-100 rounded">
                    Survival Analysis
                </a>
                <a href="#prediction" className="block p-2 hover:bg-gray-100 rounded">
                    Predictions
                </a>
            </nav>
        </Card>
    );
};