// src/components/analysis/AnalysisDropdowns.tsx
import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../app/hooks';
import { fetchDropdownOptions, setSelectedGene, setSelectedDataset } from '../../features/analysis/analysisSlice';
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

export const AnalysisDropdowns = () => {
  const dispatch = useAppDispatch();
  const { dropdownData, loading, error, selectedGene, selectedDataset } = useAppSelector(
    (state) => state.analysis
  );

  useEffect(() => {
    dispatch(fetchDropdownOptions());
  }, [dispatch]);

  if (loading) {
    return (
      <Card className="w-64 p-4">
        <CardContent className="space-y-4">
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

  return (
    <Card className="w-64">
      <CardContent className="p-4 space-y-6">
        <div className="space-y-2">
          <Label className="text-sm font-medium">Step 1. Dataset</Label>
          <Select
            value={selectedDataset}
            onValueChange={(value) => dispatch(setSelectedDataset(value))}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select..." />
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
          <Label className="text-sm font-medium">Step 2. Color by</Label>
          <Select
            value={selectedGene}
            onValueChange={(value) => dispatch(setSelectedGene(value))}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select..." />
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
      </CardContent>
    </Card>
  );
};