import React from 'react';
import { useAppDispatch, useAppSelector } from '../../app/hooks';
import { setSelectedDataset } from './expressionSlice';
import { useGetDatasetsSummaryQuery } from '../../services/api';
import { Loading } from '../../components/common/Loading';
import { ErrorMessage } from '../../components/common/ErrorMessage';

export const DatasetSelector = () => {
  const dispatch = useAppDispatch();
  const selectedGene = useAppSelector(state => state.expression.selectedGene);
  const selectedTissue = useAppSelector(state => state.expression.selectedTissue);
  const selectedDataset = useAppSelector(state => state.expression.selectedDataset);
  
  // Using RTK Query hook with skip option to prevent fetching when no gene or tissue is selected
  const { data, isLoading, error } = useGetDatasetsSummaryQuery(
    { gene: selectedGene, tissue: selectedTissue },
    { skip: !selectedGene || !selectedTissue }
  );

  const handleDatasetChange = (value: string) => {
    dispatch(setSelectedDataset(value));
  };

  // Don't render if no gene or tissue is selected
  if (!selectedGene || !selectedTissue) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="p-6">
          <Loading message="Loading available datasets..." />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="p-6">
          <ErrorMessage message={error.toString()} />
          
          {/* Debug information */}
          <details className="mt-2 text-xs text-gray-500">
            <summary>Debug Info</summary>
            <div className="p-2 bg-gray-50 mt-1 rounded">
              <p>Error: {JSON.stringify(error)}</p>
              <p>Gene: {selectedGene}</p>
              <p>Tissue: {selectedTissue}</p>
            </div>
          </details>
        </div>
      </div>
    );
  }

  // Handle case where there's no dataset data or empty datasets array
  if (!data || !data || !data.datasets || data.datasets.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900">Dataset Selection</h2>
          <p className="text-gray-600 mt-2">No datasets available for {selectedGene} in {selectedTissue.replace(/_/g, ' ')}.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Dataset Selection</h2>
        
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">Select Dataset</label>
          <select
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            value={selectedDataset}
            onChange={(e) => handleDatasetChange(e.target.value)}
          >
            <option value="">Choose a dataset...</option>
            {data.datasets.map((dataset) => (
              <option
                key={dataset.dataset_id}
                value={dataset.dataset_id}
              >
                {dataset.dataset_name || dataset.dataset_id}
              </option>
            ))}
          </select>
          
          {selectedDataset && (
            <div className="mt-2 p-2 bg-gray-50 rounded-md">
              <p className="text-sm font-medium">
                Selected: {
                  data.datasets.find(ds => ds.dataset_id === selectedDataset)?.dataset_name || 
                  selectedDataset
                }
              </p>
              {data.datasets.find(ds => ds.dataset_id === selectedDataset)?.sample_count > 0 && (
                <p className="text-xs text-gray-600 mt-1">
                  Samples: {data.datasets.find(ds => ds.dataset_id === selectedDataset).sample_count}
                </p>
              )}
              {data.datasets.find(ds => ds.dataset_id === selectedDataset)?.source && (
                <p className="text-xs text-gray-600">
                  Source: {data.datasets.find(ds => ds.dataset_id === selectedDataset).source}
                </p>
              )}
            </div>
          )}
          
          {/* Debug information */}
          <details className="mt-2 text-xs text-gray-500">
            <summary>Debug Info</summary>
            <div className="p-2 bg-gray-50 mt-1 rounded">
              <p>Selected: {selectedDataset || 'None'}</p>
              <p>Datasets count: {data.datasets.length}</p>
              <p>Gene: {selectedGene}</p>
              <p>Tissue: {selectedTissue}</p>
            </div>
          </details>
        </div>
      </div>
    </div>
  );
};