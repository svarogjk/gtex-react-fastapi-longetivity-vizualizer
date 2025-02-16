import React from 'react';
import { Card, CardContent } from '../../components/ui/card';

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