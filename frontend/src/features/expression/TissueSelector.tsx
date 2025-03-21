import React from 'react';
import { useAppDispatch, useAppSelector } from '../../app/hooks';
import { setSelectedTissue } from './expressionSlice';
import { useGetTissueSummaryQuery } from '../../services/api';
import { Loading } from '../../components/common/Loading';

export const TissueSelector: React.FC = () => {
  const dispatch = useAppDispatch();
  const selectedGene = useAppSelector(state => state.expression.selectedGene);
  const selectedTissue = useAppSelector(state => state.expression.selectedTissue);
  
  // Get tissue expression data using RTK Query
  const { data, isLoading } = useGetTissueSummaryQuery(selectedGene, {
    skip: !selectedGene
  });

  const handleTissueChange = (value: string) => {
    dispatch(setSelectedTissue(value));
  };

  // Don't render if no gene is selected or if there's no expression data
  if (!selectedGene || !data || !data.tissue_expression || data.tissue_expression.length === 0) {
    return null;
  }

  // Create a deduplicated list of tissues to prevent the duplicate key issue
  const tissueMap = new Map();
  data.tissue_expression.forEach(item => {
    // Only add the tissue if it hasn't been added yet
    if (!tissueMap.has(item.tissue)) {
      tissueMap.set(item.tissue, {
        id: item.tissue,
        displayName: item.display_name || item.tissue.replace(/_/g, ' '),
        sampleCount: item.sample_count
      });
    }
  });
  
  // Convert the Map to an array for rendering
  const uniqueTissues = Array.from(tissueMap.values());

  const getTissueDisplayName = (tissue: string): string => {
    return tissueMap.get(tissue)?.displayName || tissue.replace(/_/g, ' ');
  };

  return (
    <div className="bg-white shadow rounded-lg mt-6">
      <div className="p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Tissue Selection</h2>
        
        {isLoading ? (
          <Loading message="Loading tissues..." />
        ) : (
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Select Tissue</label>
            <select
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              value={selectedTissue}
              onChange={(e) => handleTissueChange(e.target.value)}
              disabled={uniqueTissues.length === 0}
            >
              <option value="">
                {uniqueTissues.length === 0 
                  ? "No tissues available" 
                  : "Choose a tissue..."}
              </option>
              {uniqueTissues.map((tissue) => (
                <option
                  key={`tissue-${tissue.id}`} // Add a prefix to ensure uniqueness
                  value={tissue.id}
                >
                  {tissue.displayName}
                </option>
              ))}
            </select>
            
            {uniqueTissues.length === 0 && (
              <p className="text-sm text-gray-500">No tissues available for this gene</p>
            )}
            
            {selectedTissue && (
              <div className="mt-2 p-2 bg-gray-50 rounded-md">
                <p className="text-sm font-medium">Selected: {getTissueDisplayName(selectedTissue)}</p>
                {tissueMap.get(selectedTissue)?.sampleCount > 0 && (
                  <p className="text-xs text-gray-600 mt-1">
                    Samples: {tissueMap.get(selectedTissue).sampleCount}
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