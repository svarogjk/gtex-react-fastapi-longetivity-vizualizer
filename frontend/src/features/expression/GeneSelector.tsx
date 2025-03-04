import React from 'react';
import { useAppDispatch, useAppSelector } from '../../app/hooks';
import { setSelectedGene } from './expressionSlice';
import { useSearchGenesQuery } from '../../services/api';
import { Loading } from '../../components/common/Loading';
import { ErrorMessage } from '../../components/common/ErrorMessage';

export const GeneSelector: React.FC = () => {
  const dispatch = useAppDispatch();
  const selectedGene = useAppSelector(state => state.expression.selectedGene);
  
  // Using RTK Query hook instead of dispatching actions manually
  const { data, isLoading, error } = useSearchGenesQuery();
  
  // Debug logging
  console.log("Gene data received:", data);
  
  const handleGeneChange = (value: string) => {
    dispatch(setSelectedGene(value));
  };

  // Check the structure before rendering
  const geneOptions = React.useMemo(() => {
    if (!data?.genes) return [];
    
    console.log("Gene structure:", data.genes[0]); // Log the first item to see its structure
    
    // Handle both array of strings and array of objects
    return data.genes.map(gene => {
      if (typeof gene === 'string') {
        return { value: gene, label: gene };
      } else if (typeof gene === 'object' && gene !== null) {
        return { 
          value: gene.value || gene.id || gene.symbol || JSON.stringify(gene),
          label: gene.label || gene.name || gene.symbol || JSON.stringify(gene)
        };
      }
      return { value: 'unknown', label: 'Unknown Gene' };
    });
  }, [data]);

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Gene Selection</h2>
        
        {isLoading ? (
          <Loading message="Loading genes..." />
        ) : error ? (
          <ErrorMessage message={error.toString()} />
        ) : (
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Select Gene</label>
            <select
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              value={selectedGene}
              onChange={(e) => handleGeneChange(e.target.value)}
              disabled={isLoading}
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
            
            {/* Show the current selected value for debugging */}
            <div className="text-xs text-gray-500">
              Selected value: {JSON.stringify(selectedGene)}
            </div>
            
            {selectedGene && data?.gene_details && (
              <div className="mt-2 p-2 bg-gray-50 rounded-md">
                <p className="text-sm font-medium">Selected: {selectedGene}</p>
                {data.gene_details[selectedGene]?.description && (
                  <p className="text-xs text-gray-600 mt-1">
                    {data.gene_details[selectedGene].description}
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