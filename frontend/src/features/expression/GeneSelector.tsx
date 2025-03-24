import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../app/hooks';
import { setSelectedGene } from './expressionSlice';
import { useSearchGenesQuery } from '../../services/api';
import { Loading } from '../../components/common/Loading';
import { ErrorMessage } from '../../components/common/ErrorMessage';

export const GeneSelector = () => {
  const dispatch = useAppDispatch();
  const selectedGene = useAppSelector(state => state.expression.selectedGene);
  
  // Using RTK Query hook
  const { data, isLoading, error, refetch } = useSearchGenesQuery();
  
  useEffect(() => {
    // Log detailed information about the current state
    console.log("Gene selector state:", {
      isLoading,
      hasData: !!data,
      dataStructure: data ? Object.keys(data) : 'undefined',
      error: error ? (error as any).message || String(error) : null
    });
  }, [data, isLoading, error]);
  
  const handleGeneChange = (value: string) => {
    dispatch(setSelectedGene(value));
  };

  const handleRetry = () => {
    refetch();
  };

  // Process the data for use in the dropdown
  const geneOptions = React.useMemo(() => {
    if (!data) return [];
    
    // Check if data.genes is an array
    if (Array.isArray(data.genes)) {
      return data.genes.map(gene => {
        if (typeof gene === 'string') {
          return { value: gene, label: gene };
        } else if (typeof gene === 'object' && gene !== null) {
          // For object structure (if the API returns gene objects)
          return { 
            value: gene.value || gene.id || gene.symbol || JSON.stringify(gene),
            label: gene.label || gene.name || gene.symbol || JSON.stringify(gene)
          };
        }
        return { value: 'unknown', label: 'Unknown Gene' };
      });
    }
    
    // If data.genes is not an array, check other potential structures
    if (data.options && Array.isArray(data.options)) {
      return data.options;
    }
    
    // Last resort - try to convert the whole data object to options
    try {
      if (typeof data === 'object') {
        return Object.entries(data).map(([key, value]) => ({
          value: key,
          label: typeof value === 'string' ? value : key
        }));
      }
    } catch (e) {
      console.error("Failed to process gene data:", e);
    }
    
    return [];
  }, [data]);

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Gene Selection</h2>
        
        {isLoading ? (
          <Loading message="Loading genes..." />
        ) : error ? (
          <div>
            <ErrorMessage message={
              typeof error === 'string' 
                ? error 
                : (error as any)?.message || 'An error occurred fetching genes'
            } />
            <button 
              onClick={handleRetry}
              className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Retry
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Select Gene</label>
            <select
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              value={selectedGene}
              onChange={(e) => handleGeneChange(e.target.value)}
              disabled={isLoading || geneOptions.length === 0}
            >
              <option value="">Choose a gene...</option>
              {geneOptions.map((option) => (
                <option
                  key={option.value}
                  value={option.value}
                >
                  {option.label}
                </option>
              ))}
            </select>
            
            {/* Debug information */}
            <details className="mt-2 text-xs text-gray-500">
              <summary>Debug Info</summary>
              <div className="p-2 bg-gray-50 mt-1 rounded">
                <p>Selected: {JSON.stringify(selectedGene)}</p>
                <p>Options count: {geneOptions.length}</p>
                <p>Data available: {data ? 'Yes' : 'No'}</p>
                {data && <p>Data keys: {Object.keys(data).join(', ')}</p>}
              </div>
            </details>
            
            {selectedGene && data?.gene_details && data.gene_details[selectedGene] && (
              <div className="mt-2 p-2 bg-gray-50 rounded-md">
                <p className="text-sm font-medium">Selected: {selectedGene}</p>
                <p className="text-xs text-gray-600 mt-1">
                  {data.gene_details[selectedGene].description}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};