// src/components/analysis/AnalysisDropdowns.tsx
import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../app/hooks';
import { 
  fetchDropdownOptions, 
  setSelectedGene, 
  setSelectedDataset,
  setSelectedTarget,
  fetchDatasetMetadata 
} from '../../features/analysis/analysisSlice';
import { Card, CardContent } from '../../components/ui/card';
import { Label } from '../../components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface DropdownOption {
  value: string;
  label: string;
  details?: Record<string, any>;
}

interface DropdownData {
  genes: {
    options: DropdownOption[];
    total_count: number;
  };
  datasets: {
    options: DropdownOption[];
    total_count: number;
  };
}

interface MetadataColumn {
  name: string;
  unique_values: number;
  type: string;
}

export const AnalysisDropdowns = () => {
  const dispatch = useAppDispatch();
  const { 
    dropdownData, 
    loading, 
    error, 
    selectedGene, 
    selectedDataset,
    selectedTarget,
    metadataColumns 
  } = useAppSelector((state) => state.analysis);

  // Initial load of gene options
  useEffect(() => {
    dispatch(fetchDropdownOptions());
  }, [dispatch]);

  // Fetch dataset metadata when dataset is selected
  useEffect(() => {
    if (selectedDataset) {
      dispatch(fetchDatasetMetadata(selectedDataset));
    }
  }, [selectedDataset, dispatch]);

  // Reset dependent selections when parent selection changes
  const handleGeneChange = (value: string) => {
    dispatch(setSelectedGene(value));
    dispatch(setSelectedDataset(''));
    dispatch(setSelectedTarget(''));
  };

  const handleDatasetChange = (value: string) => {
    dispatch(setSelectedDataset(value));
    dispatch(setSelectedTarget(''));
  };

  if (loading) {
    return (
      <Card className="w-64 p-4">
        <CardContent className="space-y-4">
          <div className="h-20 animate-pulse bg-gray-200 rounded" />
          <div className="h-20 animate-pulse bg-gray-200 rounded" />
          <div className="h-20 animate-pulse bg-gray-200 rounded" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-64 p-4">
        <CardContent>
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  // Filter metadata columns for valid target variables (2-10 unique values)
  const validTargetColumns = metadataColumns?.filter(
    column => column.unique_values >= 2 && column.unique_values <= 10
  ) || [];

  return (
    <Card className="w-64">
      <CardContent className="p-4 space-y-6">
        <div className="space-y-2">
          <Label className="text-sm font-medium">Step 1. Select Gene</Label>
          <Select
            value={selectedGene}
            onValueChange={handleGeneChange}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Search genes..." />
            </SelectTrigger>
            <SelectContent>
              {dropdownData?.genes.options.map((option) => (
                <SelectItem
                  key={option.value}
                  value={option.value}
                  className="cursor-pointer"
                >
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label className="text-sm font-medium">Step 2. Select Dataset</Label>
          <Select
            value={selectedDataset}
            onValueChange={handleDatasetChange}
            disabled={!selectedGene}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select dataset..." />
            </SelectTrigger>
            <SelectContent>
              {dropdownData?.datasets.options.map((option) => (
                <SelectItem
                  key={option.value}
                  value={option.value}
                  className="cursor-pointer"
                >
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label className="text-sm font-medium">Step 3. Select Target Variable</Label>
          <Select
            value={selectedTarget}
            onValueChange={(value) => dispatch(setSelectedTarget(value))}
            disabled={!selectedDataset}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select target..." />
            </SelectTrigger>
            <SelectContent>
              {validTargetColumns.map((column) => (
                <SelectItem
                  key={column.name}
                  value={column.name}
                  className="cursor-pointer"
                >
                  {`${column.name} (${column.unique_values} values)`}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  );
};