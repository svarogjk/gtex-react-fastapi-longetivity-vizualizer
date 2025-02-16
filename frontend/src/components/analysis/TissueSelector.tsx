import React from 'react';
import { Card, CardContent } from '../../components/ui/card';

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