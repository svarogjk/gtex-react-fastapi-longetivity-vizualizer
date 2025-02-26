import React, { useEffect, useMemo } from 'react';
import { useAppDispatch, useAppSelector } from '../../app/hooks';
import { fetchGenes, setSelectedGene, fetchTissueExpression } from './expressionSlice';
import { Loading } from '../../components/common/Loading';
import { ErrorMessage } from '../../components/common/ErrorMessage';

export const GeneSelector: React.FC = () => {
  const dispatch = useAppDispatch();
  
  // Get raw state values from Redux
  const rawGenes = useAppSelector(state => state.expression.genes);
  const rawSelectedGene = useAppSelector(state => state.expression.selectedGene);
  
  // Memoize the derived state to prevent unnecessary re-renders
  const genes = useMemo(() => 
    rawGenes || { loading: false, error: null, options: [] }
  , [rawGenes]);
  
  const selectedGene = useMemo(() => 
    rawSelectedGene || ''
  , [rawSelectedGene]);

  // Fetch genes exactly once on mount, using a ref to track it
  const hasFetchedRef = React.useRef(false);
  
  useEffect(() => {
    // Only fetch if we don't have data, aren't already loading, and haven't fetched before
    if (!hasFetchedRef.current && !genes.loading && genes.options.length === 0 && !genes.error) {
      console.log('[COMPONENT] GeneSelector - fetching genes data');
      hasFetchedRef.current = true;
      dispatch(fetchGenes());
    }
  }, []); // Empty dependency array - only run on mount

  const handleGeneChange = (value: string) => {
    dispatch(setSelectedGene(value));
    dispatch(fetchTissueExpression(value));
  };

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Gene Selection</h2>
        
        {genes.loading ? (
          <Loading message="Loading genes..." />
        ) : (
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Select Gene</label>
            <select
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              value={selectedGene}
              onChange={(e) => handleGeneChange(e.target.value)}
            >
              <option value="">Choose a gene...</option>
              {genes.options.map((option) => (
                <option
                  key={option.value}
                  value={option.value}
                >
                  {option.label}
                </option>
              ))}
            </select>
            
            {genes.error && <ErrorMessage message={genes.error} />}
            
            {selectedGene && (
              <div className="mt-2 p-2 bg-gray-50 rounded-md">
                <p className="text-sm font-medium">Selected: {selectedGene}</p>
                {genes.options.find(g => g.value === selectedGene)?.details?.description && (
                  <p className="text-xs text-gray-600 mt-1">
                    {genes.options.find(g => g.value === selectedGene)?.details?.description}
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};