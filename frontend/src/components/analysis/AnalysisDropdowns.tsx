import React, { useEffect } from 'react';
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
import { Card, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';

export const AnalysisDropdowns = () => {
  const dispatch = useAppDispatch();
  const { 
    dropdownData, 
    loading, 
    error, 
    selectedGene, 
    selectedDataset,
    selectedTarget,
    selectedTissue,
    tissues,
    metadataColumns 
  } = useAppSelector((state) => state.analysis);

  // Initial load of dropdown options
  useEffect(() => {
    dispatch(fetchDropdownOptions());
  }, [dispatch]);

  // Fetch tissues when gene is selected
  useEffect(() => {
    if (selectedGene) {
      dispatch(fetchTissues(selectedGene));
    }
  }, [selectedGene, dispatch]);

  // Fetch dataset metadata when dataset is selected
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
  };

  // Filter metadata columns for valid target variables (2-10 unique values)
  const validTargetColumns = metadataColumns?.filter(
    column => column.unique_values >= 2 && column.unique_values <= 10
  ) || [];

  if (loading) {
    return (
      <Card className="w-64">
        <CardContent className="p-6 space-y-4">
          <div className="h-20 animate-pulse bg-gray-200 rounded" />
          <div className="h-20 animate-pulse bg-gray-200 rounded" />
          <div className="h-20 animate-pulse bg-gray-200 rounded" />
          <div className="h-20 animate-pulse bg-gray-200 rounded" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-64 bg-white">
      <CardContent className="p-6 space-y-6">
        <h2 className="text-lg font-semibold text-gray-900">Analysis Steps</h2>

        <div className="space-y-6">
          {/* Gene Selection */}
          <div className="space-y-2">
            <Label className="text-sm font-medium text-gray-700">1. Select Gene</Label>
            <Select
              value={selectedGene}
              onValueChange={handleGeneChange}
            >
              <SelectTrigger className="w-full bg-white">
                <SelectValue placeholder="Choose a gene..." />
              </SelectTrigger>
              <SelectContent>
                {dropdownData?.genes?.options?.map((option) => (
                  <SelectItem
                    key={option.value}
                    value={option.value}
                    className="cursor-pointer hover:bg-gray-100"
                  >
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Tissue Selection */}
          <div className="space-y-2">
            <Label className="text-sm font-medium text-gray-700">2. Select Tissue</Label>
            <Select
              value={selectedTissue}
              onValueChange={handleTissueChange}
              disabled={!selectedGene || tissues.length === 0}
            >
              <SelectTrigger className="w-full bg-white">
                <SelectValue placeholder={
                  !selectedGene 
                    ? "Select a gene first" 
                    : tissues.length === 0 
                      ? "No tissues available" 
                      : "Choose a tissue..."
                } />
              </SelectTrigger>
              <SelectContent>
                {tissues?.map((tissue: string) => (
                  <SelectItem
                    key={tissue}
                    value={tissue}
                    className="cursor-pointer hover:bg-gray-100"
                  >
                    {tissue.replace(/_/g, ' ')}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {selectedGene && tissues.length === 0 && (
              <p className="text-sm text-gray-500">No tissues available for this gene</p>
            )}
          </div>

          {/* Rest of the component remains the same */}
        </div>

        {error && (
          <Alert variant="destructive" className="mt-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default AnalysisDropdowns;