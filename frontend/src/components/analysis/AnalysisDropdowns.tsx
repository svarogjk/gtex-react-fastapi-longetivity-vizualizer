import React from 'react';
import { useAppDispatch, useAppSelector } from '../../app/hooks';
import { 
  setSelectedGene, 
  setSelectedDataset,
  setSelectedTarget,
  setSelectedTissue,
} from '../../features/analysis/analysisSlice';
import { 
  useGetDropdownOptionsQuery,
  useGetTissuesQuery,
  useGetDatasetsSummaryQuery,
  useGetDatasetMetadataQuery
} from '../../services/api';
import { ErrorMessage } from '../common/ErrorMessage';

export const AnalysisDropdowns: React.FC = () => {
  const dispatch = useAppDispatch();

  // Get selected values from Redux store
  const selectedGene = useAppSelector(state => state.analysis.selectedGene);
  const selectedDataset = useAppSelector(state => state.analysis.selectedDataset);
  const selectedTissue = useAppSelector(state => state.analysis.selectedTissue);

  // Fetch dropdown options using RTK Query
  const { data: dropdownData, isLoading: isLoadingDropdowns, error: dropdownError } = useGetDropdownOptionsQuery();
  
  // Fetch tissues when gene is selected
  const { data: tissuesData, isLoading: isLoadingTissues } = useGetTissuesQuery(undefined, {
    skip: !selectedGene
  });

   // Fetch datasets when tissue is selected
   const { data: datasetsData, isLoading: isLoadingDatasets } = useGetDatasetsSummaryQuery(undefined, {
    skip: !selectedTissue
  });
  
  // Fetch dataset metadata when dataset is selected
  const { data: metadataData, isLoading: isLoadingMetadata } = useGetDatasetMetadataQuery(selectedDataset, {
    skip: !selectedDataset
  });

  // Filter metadata columns for valid target variables (2-10 unique values)
  const validTargetColumns = metadataData?.columns?.filter(
    column => column.unique_values >= 2 && column.unique_values <= 10
  ) || [];

  // Handler functions
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
  };

  if (isLoadingDropdowns) {
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
              {dropdownData?.genes?.options?.map((option: { value: React.Key | readonly string[] | null | undefined; label: string | number | boolean | React.ReactElement<any, string | React.JSXElementConstructor<any>> | Iterable<React.ReactNode> | React.ReactPortal | null | undefined; }) => (
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
              disabled={!selectedGene || isLoadingTissues || !tissuesData?.tissues.length}
            >
              <option value="">
                {!selectedGene 
                  ? "Select a gene first" 
                  : isLoadingTissues
                    ? "Loading tissues..."
                    : !tissuesData?.tissues.length
                      ? "No tissues available" 
                      : "Choose a tissue..."}
              </option>
              {tissuesData?.tissues?.map((tissue: string) => (
                <option
                  key={tissue}
                  value={tissue}
                >
                  {tissue.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
            {selectedGene && !isLoadingTissues && (!tissuesData?.tissues || tissuesData.tissues.length === 0) && (
              <p className="text-sm text-gray-500">No tissues available for this gene</p>
            )}
          </div>

          {/* Dataset Selection */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">3. Select Dataset</label>
            <select
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              value={selectedDataset}
              onChange={(e) => handleDatasetChange(e.target.value)}
              disabled={!selectedTissue || isLoadingDatasets || !datasetsData?.datasets.length}
            >
              <option value="">
                {!selectedTissue 
                  ? "Select a tissue first" 
                  : isLoadingDatasets
                    ? "Loading datasets..."
                    : !datasetsData?.datasets.length
                      ? "No tissues available" 
                      : "Choose a tissue..."}
              </option>
              {datasetsData?.datasets?.map((dataset: string) => (
                <option
                  key={dataset}
                  value={dataset}
                >
                  {dataset.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
            {selectedDataset && !isLoadingDatasets && (!datasetsData?.datasets || datasetsData.datasets.length === 0) && (
              <p className="text-sm text-gray-500">No datasets available for this tissue</p>
            )}
          </div>
        </div>

        {dropdownError && <ErrorMessage message={dropdownError.toString()} />}
      </div>
    </div>
  );
};