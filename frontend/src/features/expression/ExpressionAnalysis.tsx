import React, { useEffect, useMemo } from 'react';
import { GeneSelector } from './GeneSelector';
import { TissueSelector } from './TissueSelector';
import { TissueExpressionChart } from './TissueExpressionChart';
import { useAppSelector, useAppDispatch } from '../../app/hooks';
import { fetchGenes } from './expressionSlice';
import { Loading } from '../../components/common/Loading';
import { ErrorMessage } from '../../components/common/ErrorMessage';

export const ExpressionAnalysis: React.FC = () => {
  const dispatch = useAppDispatch();
  
  // Get raw state values from Redux
  const rawSelectedGene = useAppSelector(state => state.expression.selectedGene);
  const rawGenes = useAppSelector(state => state.expression.genes);
  
  // Memoize the derived state
  const selectedGene = useMemo(() => 
    rawSelectedGene || ''
  , [rawSelectedGene]);
  
  const genes = useMemo(() => 
    rawGenes || { loading: false, error: null, options: [] }
  , [rawGenes]);

  // Skip fetching genes here as GeneSelector will handle it
  // This prevents duplicate API calls
  // useEffect(() => {
  //   dispatch(fetchGenes());
  // }, [dispatch]);

  // Show loading state
  if (genes.loading) {
    return <Loading message="Loading gene data..." />;
  }

  // Show error state
  if (genes.error) {
    return <ErrorMessage message={genes.error} />;
  }

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