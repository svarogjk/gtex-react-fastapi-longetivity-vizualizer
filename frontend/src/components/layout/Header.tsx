// src/components/layout/Header.tsx
import React from 'react';

export const Header: React.FC = () => {
    return (
        <header className="bg-white shadow-sm">
            <div className="max-w-7xl mx-auto px-4 py-4">
                <h1 className="text-2xl font-bold text-gray-900">Longevity Analysis</h1>
            </div>
        </header>
    );
};

// src/components/layout/Sidebar.tsx
import React from 'react';
import { Card } from '@/components/ui/card';

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

// src/components/analysis/GeneSelector.tsx
import React from 'react';
import { Card, CardContent } from '@/components/ui/card';

interface GeneSelectorProps {
    selectedGenes: string[];
    onSelectGene: (gene: string) => void;
}

export const GeneSelector: React.FC<GeneSelectorProps> = ({
    selectedGenes,
    onSelectGene
}) => {
    const commonGenes = ['SIRT1', 'FOXO3', 'CDKN2A', 'TERC', 'TERT'];

    return (
        <Card>
            <CardContent className="p-4">
                <h3 className="text-lg font-semibold mb-4">Select Genes</h3>
                <div className="space-y-2">
                    {commonGenes.map(gene => (
                        <label key={gene} className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                checked={selectedGenes.includes(gene)}
                                onChange={() => onSelectGene(gene)}
                                className="form-checkbox"
                            />
                            <span>{gene}</span>
                        </label>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
};

// src/components/analysis/TissueSelector.tsx
import React from 'react';
import { Card, CardContent } from '@/components/ui/card';

interface TissueSelectorProps {
    selectedTissue: string;
    onSelectTissue: (tissue: string) => void;
}

export const TissueSelector: React.FC<TissueSelectorProps> = ({
    selectedTissue,
    onSelectTissue
}) => {
    const tissues = [
        'WHOLE_BLOOD',
        'BRAIN',
        'HEART',
        'LIVER',
        'MUSCLE_SKELETAL'
    ];

    return (
        <Card>
            <CardContent className="p-4">
                <h3 className="text-lg font-semibold mb-4">Select Tissue</h3>
                <select
                    value={selectedTissue}
                    onChange={(e) => onSelectTissue(e.target.value)}
                    className="w-full p-2 border rounded"
                >
                    {tissues.map(tissue => (
                        <option key={tissue} value={tissue}>
                            {tissue.replace('_', ' ')}
                        </option>
                    ))}
                </select>
            </CardContent>
        </Card>
    );
};

// src/components/analysis/ExpressionChart.tsx
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardHeader, CardContent } from '@/components/ui/card';

interface ExpressionChartProps {
    data: any;
    title: string;
}

export const ExpressionChart: React.FC<ExpressionChartProps> = ({ data, title }) => {
    if (!data) return null;

    return (
        <Card>
            <CardHeader>
                <h3 className="text-lg font-semibold">{title}</h3>
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="value" stroke="#8884d8" />
                    </LineChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
};

// src/components/analysis/SurvivalChart.tsx
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardHeader, CardContent } from '@/components/ui/card';

interface SurvivalChartProps {
    survivalData: {
        high_expression: any[];
        low_expression: any[];
    };
}

export const SurvivalChart: React.FC<SurvivalChartProps> = ({ survivalData }) => {
    if (!survivalData) return null;

    return (
        <Card>
            <CardHeader>
                <h3 className="text-lg font-semibold">Survival Analysis</h3>
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="time" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line
                            type="monotone"
                            data={survivalData.high_expression}
                            dataKey="survival_function"
                            stroke="#82ca9d"
                            name="High Expression"
                        />
                        <Line
                            type="monotone"
                            data={survivalData.low_expression}
                            dataKey="survival_function"
                            stroke="#8884d8"
                            name="Low Expression"
                        />
                    </LineChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
};

// src/components/common/Loading.tsx
import React from 'react';

export const Loading: React.FC = () => (
    <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
    </div>
);

// src/components/common/ErrorMessage.tsx
import React from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ErrorMessageProps {
    message: string;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message }) => (
    <Alert variant="destructive">
        <AlertDescription>{message}</AlertDescription>
    </Alert>
);