import { useAppSelector } from '../../app/hooks';
import { useGetDatasetMetadataQuery } from '../../services/api';
import { Loading } from '../../components/common/Loading';
import { ErrorMessage } from '../../components/common/ErrorMessage';

export const DatasetMetadataTable = () => {
  const selectedDataset = useAppSelector(state => state.expression.selectedDataset);
  
  // Using RTK Query hook with skip option to prevent fetching when no dataset is selected
  const { data, isLoading, error } = useGetDatasetMetadataQuery(selectedDataset, {
    skip: !selectedDataset
  });

  // Don't render if no dataset is selected
  if (!selectedDataset) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg mt-4">
        <div className="p-6">
          <Loading message="Loading dataset metadata..." />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg mt-4">
        <div className="p-6">
          <ErrorMessage message={error.toString()} />
          
          {/* Debug information */}
          <details className="mt-2 text-xs text-gray-500">
            <summary>Debug Info</summary>
            <div className="p-2 bg-gray-50 mt-1 rounded">
              <p>Error: {JSON.stringify(error)}</p>
              <p>Dataset: {selectedDataset}</p>
            </div>
          </details>
        </div>
      </div>
    );
  }

  // Handle case where there's no data
  if (!data) {
    return (
      <div className="bg-white shadow rounded-lg mt-4">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900">Dataset Metadata</h2>
          <p className="text-gray-600 mt-2">No metadata available for the selected dataset.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg mt-4">
      <div className="p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Dataset Metadata</h2>
        <p className="text-sm text-gray-600">
          {`Displaying metadata for dataset: ${selectedDataset}`}
        </p>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Column Name
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Unique Values
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.columns.map((column, index) => (
                <tr key={`column-${index}`} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {column.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {column.type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {column.unique_values}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Debug information */}
        <details className="mt-2 text-xs text-gray-500">
          <summary>Debug Info</summary>
          <div className="p-2 bg-gray-50 mt-1 rounded">
            <p>Dataset: {selectedDataset}</p>
            <p>Status: {data.status}</p>
            <p>Column count: {data.columns.length}</p>
          </div>
        </details>
      </div>
    </div>
  );
};