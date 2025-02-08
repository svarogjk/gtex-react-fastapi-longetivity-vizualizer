// src/features/expression/ExpressionAnalysis.tsx
import React, { useState, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../app/hooks';
import { fetchExpressionData } from './expressionSlice';
import { GeneSelector } from '../../components/analysis/GeneSelector';
import { TissueSelector } from '../../components/analysis/TissueSelector';
import { ExpressionChart } from '../../components/analysis/ExpressionChart';
import { Loading } from '../../components/common/Loading';
import { ErrorMessage } from '../../components/common/ErrorMessage';

export const ExpressionAnalysis: React.FC = () => {
    const dispatch = useAppDispatch();
    const { data, status, error } = useAppSelector((state) => state.expression);
    const [selectedGenes, setSelectedGenes] = useState<string[]>(['SIRT1']);
    const [selectedTissue, setSelectedTissue] = useState('WHOLE_BLOOD');

    useEffect(() => {
        if (selectedGenes.length > 0) {
            dispatch(fetchExpressionData({
                genes: selectedGenes,
                tissue_type: selectedTissue
            }));
        }
    }, [dispatch, selectedGenes, selectedTissue]);

    const handleGeneSelect = (gene: string) => {
        setSelectedGenes(prev =>
            prev.includes(gene)
                ? prev.filter(g => g !== gene)
                : [...prev, gene]
        );
    };

    if (status === 'loading') return <Loading />;
    if (status === 'failed') return <ErrorMessage message={error || 'Failed to fetch data'} />;

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <GeneSelector
                    selectedGenes={selectedGenes}
                    onSelectGene={handleGeneSelect}
                />
                <TissueSelector
                    selectedTissue={selectedTissue}
                    onSelectTissue={setSelectedTissue}
                />
            </div>
            <ExpressionChart
                data={data}
                title="Gene Expression Analysis"
            />
        </div>
    );
};

// src/features/survival/SurvivalAnalysis.tsx
import React, { useState, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../app/hooks';
import { fetchSurvivalData } from './survivalSlice';
import { SurvivalChart } from '../../components/analysis/SurvivalChart';
import { Loading } from '../../components/common/Loading';
import { ErrorMessage } from '../../components/common/ErrorMessage';
import { Card, CardContent } from '@/components/ui/card';

export const SurvivalAnalysis: React.FC = () => {
    const dispatch = useAppDispatch();
    const { data, status, error } = useAppSelector((state) => state.survival);
    const [selectedGene, setSelectedGene] = useState<string>('SIRT1');

    useEffect(() => {
        if (selectedGene) {
            dispatch(fetchSurvivalData({ gene: selectedGene }));
        }
    }, [dispatch, selectedGene]);

    if (status === 'loading') return <Loading />;
    if (status === 'failed') return <ErrorMessage message={error || 'Failed to fetch data'} />;

    return (
        <div className="space-y-4">
            <Card>
                <CardContent className="p-4">
                    <select
                        value={selectedGene}
                        onChange={(e) => setSelectedGene(e.target.value)}
                        className="w-full p-2 border rounded"
                    >
                        <option value="SIRT1">SIRT1</option>
                        <option value="FOXO3">FOXO3</option>
                        <option value="CDKN2A">CDKN2A</option>
                    </select>
                </CardContent>
            </Card>
            {data && <SurvivalChart survivalData={data} />}
        </div>
    );
};

// src/features/dashboard/Dashboard.tsx
import React from 'react';
import { ExpressionAnalysis } from '../expression/ExpressionAnalysis';
import { SurvivalAnalysis } from '../survival/SurvivalAnalysis';
import { Header } from '../../components/layout/Header';
import { Sidebar } from '../../components/layout/Sidebar';

export const Dashboard: React.FC = () => {
    return (
        <div className="min-h-screen bg-gray-100">
            <Header />
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="grid grid-cols-12 gap-6">
                    <div className="col-span-3">
                        <Sidebar />
                    </div>
                    <div className="col-span-9">
                        <div className="space-y-6">
                            <section id="expression">
                                <h2 className="text-xl font-bold mb-4">Gene Expression Analysis</h2>
                                <ExpressionAnalysis />
                            </section>
                            <section id="survival">
                                <h2 className="text-xl font-bold mb-4">Survival Analysis</h2>
                                <SurvivalAnalysis />
                            </section>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};