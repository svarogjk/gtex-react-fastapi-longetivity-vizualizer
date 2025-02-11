import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loading } from '../../components/common/Loading';

interface Dataset {
  id: string;
  name: string;
  description: string;
}

interface MetadataColumn {
  name: string;
  type: string;
  description: string;
}

interface DatasetAnalysisProps {
  datasets: Dataset[];
  onDatasetSelect: (datasetId: string) => void;
  onTargetVariableSelect: (variable: string) => void;
}

const DatasetAnalysis: React.FC<DatasetAnalysisProps> = ({
  datasets,
  onDatasetSelect,
  onTargetVariableSelect,
}) => {
  const [selectedDataset, setSelectedDataset] = useState<string>('');
  const [selectedTarget, setSelectedTarget] = useState<string>('');
  const [metadata, setMetadata] = useState<Record<string, any>[]>([]);
  const [metadataColumns, setMetadataColumns] = useState<MetadataColumn[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetadata = async () => {
      if (!selectedDataset) return;
      
      setLoading(true);
      try {
        // Replace with your actual API call
        const response = await fetch(`/api/datasets/${selectedDataset}/metadata`);
        const data = await response.json();
        setMetadata(data.rows);
        setMetadataColumns(data.columns);
        setError(null);
      } catch (err) {
        setError('Failed to fetch metadata');
        setMetadata([]);
        setMetadataColumns([]);
      } finally {
        setLoading(false);
      }
    };

    fetchMetadata();
  }, [selectedDataset]);

  const handleDatasetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const datasetId = event.target.value;
    setSelectedDataset(datasetId);
    setSelectedTarget('');
    onDatasetSelect(datasetId);
  };

  const handleTargetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const target = event.target.value;
    setSelectedTarget(target);
    onTargetVariableSelect(target);
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Step 1. Dataset</h3>
          </CardHeader>
          <CardContent>
            <select
              value={selectedDataset}
              onChange={handleDatasetChange}
              className="w-full p-2 border rounded"
            >
              <option value="">Select dataset...</option>
              {datasets.map((dataset) => (
                <option key={dataset.id} value={dataset.id}>
                  {dataset.name}
                </option>
              ))}
            </select>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Step 2. Target Variable</h3>
          </CardHeader>
          <CardContent>
            <select
              value={selectedTarget}
              onChange={handleTargetChange}
              className="w-full p-2 border rounded"
              disabled={!selectedDataset || loading}
            >
              <option value="">Select target variable...</option>
              {metadataColumns.map((column) => (
                <option key={column.name} value={column.name}>
                  {column.name}
                </option>
              ))}
            </select>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">Dataset Metadata</h3>
        </CardHeader>
        <CardContent>
          {loading && <Loading />}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          {!loading && !error && metadata.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    {metadataColumns.map((column) => (
                      <th key={column.name} className="p-2 text-left border bg-gray-50">
                        {column.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {metadata.map((row, index) => (
                    <tr key={index}>
                      {metadataColumns.map((column) => (
                        <td key={column.name} className="p-2 border">
                          {row[column.name]}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DatasetAnalysis;