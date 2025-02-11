import React, { useState } from 'react';
import { Header } from '../../components/layout/Header';
import { Sidebar } from '../../components/layout/Sidebar';
import DatasetAnalysis from '../analysis/DatasetAnalysis';
import { ExpressionAnalysis } from '../expression/ExpressionAnalysis';
import { SurvivalAnalysis } from '../survival/SurvivalAnalysis';

// Mock data for demonstration - replace with actual data from your API
const SAMPLE_DATASETS = [
  {
    id: 'dataset1',
    name: 'GTEx v8',
    description: 'Gene expression data from GTEx version 8'
  },
  {
    id: 'dataset2',
    name: 'TCGA',
    description: 'The Cancer Genome Atlas Program data'
  }
];

export const Dashboard: React.FC = () => {
  const [selectedDataset, setSelectedDataset] = useState<string>('');
  const [selectedTarget, setSelectedTarget] = useState<string>('');

  const handleDatasetSelect = (datasetId: string) => {
    setSelectedDataset(datasetId);
  };

  const handleTargetVariableSelect = (variable: string) => {
    setSelectedTarget(variable);
  };

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
              <section id="dataset-selection">
                <h2 className="text-xl font-bold mb-4">Dataset Analysis</h2>
                <DatasetAnalysis
                  datasets={SAMPLE_DATASETS}
                  onDatasetSelect={handleDatasetSelect}
                  onTargetVariableSelect={handleTargetVariableSelect}
                />
              </section>
              
              {selectedDataset && selectedTarget && (
                <>
                  <section id="expression">
                    <h2 className="text-xl font-bold mb-4">Gene Expression Analysis</h2>
                    <ExpressionAnalysis />
                  </section>
                  <section id="survival">
                    <h2 className="text-xl font-bold mb-4">Survival Analysis</h2>
                    <SurvivalAnalysis />
                  </section>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};