// Only fetch dropdown options once on initial mount
useEffect(() => {
  // We can rely on the API deduplication now
  if (!loading && !dropdownData) {
    dispatch(fetchDropdownOptions());
  }
}, [dispatch, loading, dropdownData]);

// Fetch tissues when gene is selected - but prevent duplicate requests
const prevSelectedGene = React.useRef('');
const isLoadingTissues = React.useRef(false);

useEffect(() => {
  if (selectedGene && selectedGene !== prevSelectedGene.current && !isLoadingTissues.current) {
    prevSelectedGene.current = selectedGene;
    isLoadingTissues.current = true;
    
    dispatch(fetchTissues(selectedGene))
      .finally(() => {
        isLoadingTissues.current = false;
      });
  }
}, [selectedGene, dispatch]);

// Fetch dataset metadata when dataset is selected - API will deduplicate requests
useEffect(() => {
  if (selectedDataset) {
    dispatch(fetchDatasetMetadata(selectedDataset));
  }
}, [selectedDataset, dispatch]);

// Reset dependent selections when parent selection changes
const handleGeneChange = (value: string) => {
  dispatch(setSelectedGene(value));
  dispatch(setSelectedTissue(''));
  dispatch(setSelectedDataset(''));
  dispatch(setSelectedTarget(''));
};

const handleTissueChange = (value: string) => {
  dispatch(setSelectedTissue(value));
  dispatch(setSelectedDataset(''));
  dispatch(setSelectedTarget(''));
};

const handleDatasetChange = (value: string) => {
  dispatch(setSelectedDataset(value));
  dispatch(setSelectedTarget(''));
};import React, { useEffect, useMemo } from 'react';
import { useAppDispatch, useAppSelector } from '../../app/hooks';
import { 
fetchDropdownOptions, 
setSelectedGene, 
setSelectedDataset,
setSelectedTarget,
fetchDatasetMetadata,
setSelectedTissue,
fetchTissues
} from '../../features/analysis/analysisSlice';
import { Loading } from '../common/Loading';
import { ErrorMessage } from '../common/ErrorMessage';

export const AnalysisDropdowns = () => {
const dispatch = useAppDispatch();

// Get individual state pieces to avoid unnecessary re-renders
const dropdownData = useAppSelector(state => state.analysis.dropdownData);
const loading = useAppSelector(state => state.analysis.loading);
const error = useAppSelector(state => state.analysis.error);
const selectedGene = useAppSelector(state => state.analysis.selectedGene);
const selectedDataset = useAppSelector(state => state.analysis.selectedDataset);
const selectedTarget = useAppSelector(state => state.analysis.selectedTarget);
const selectedTissue = useAppSelector(state => state.analysis.selectedTissue);
const tissues = useAppSelector(state => state.analysis.tissues);
const rawMetadataColumns = useAppSelector(state => state.analysis.metadataColumns);

// Memoize any computed values
const metadataColumns = useMemo(() => rawMetadataColumns || [], [rawMetadataColumns]);

// Filter metadata columns for valid target variables (2-10 unique values)
const validTargetColumns = useMemo(() => 
  metadataColumns.filter(column => column.unique_values >= 2 && column.unique_values <= 10) || []
, [metadataColumns]);

if (loading) {
  return (
    <div className="w-full bg-white shadow rounded-lg">
      <div className="p-6 space-y-4">
        <div className="h-20 animate-pulse bg-gray-200 rounded" />
        <div className="h-20 animate-pulse bg-gray-200 rounded" />
        <div className="h-20 animate-pulse bg-gray-200 rounded" />
        <div className="h-20 animate-pulse bg-gray-200 rounded" />
      </div>
    </div>
  );
}

return (
  <div className="w-full bg-white shadow rounded-lg">
    <div className="p-6 space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">Analysis Steps</h2>

      <div className="space-y-6">
        {/* Gene Selection */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">1. Select Gene</label>
          <select
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            value={selectedGene}
            onChange={(e) => handleGeneChange(e.target.value)}
          >
            <option value="">Choose a gene...</option>
            {dropdownData?.genes?.options?.map((option) => (
              <option
                key={option.value}
                value={option.value}
              >
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Tissue Selection */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">2. Select Tissue</label>
          <select
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            value={selectedTissue}
            onChange={(e) => handleTissueChange(e.target.value)}
            disabled={!selectedGene || tissues.length === 0}
          >
            <option value="">
              {!selectedGene 
                ? "Select a gene first" 
                : tissues.length === 0 
                  ? "No tissues available" 
                  : "Choose a tissue..."}
            </option>
            {tissues?.map((tissue: string) => (
              <option
                key={tissue}
                value={tissue}
              >
                {tissue.replace(/_/g, ' ')}
              </option>
            ))}
          </select>
          {selectedGene && tissues.length === 0 && (
            <p className="text-sm text-gray-500">No tissues available for this gene</p>
          )}
        </div>
      </div>

      {error && <ErrorMessage message={error} />}
    </div>
  </div>
);
};