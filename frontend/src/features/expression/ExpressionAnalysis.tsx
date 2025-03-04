import React from 'react';
import { GeneSelector } from './GeneSelector';
import { TissueSelector } from './TissueSelector';
import { TissueExpressionChart } from './TissueExpressionChart';
import { useAppSelector } from '../../app/hooks';

export const ExpressionAnalysis: React.FC = () => {
  // Get selected gene from Redux store
  const selectedGene = useAppSelector(state => state.expression.selectedGene);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Gene Expression Analysis</h1>
      
      <div className="space-y-6">
        <GeneSelector />
        
        {selectedGene && (
          <>
            <TissueExpressionChart />
            <TissueSelector />
          </>
        )}
      </div>
    </div>
  );
};