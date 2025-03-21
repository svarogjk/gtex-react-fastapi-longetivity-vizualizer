import React from 'react';
import { useAppSelector } from '../../app/hooks';
import { useGetTissueSummaryQuery } from '../../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Loading } from '../../components/common/Loading';
import { ErrorMessage } from '../../components/common/ErrorMessage';

export const TissueExpressionChart: React.FC = () => {
  const selectedGene = useAppSelector(state => state.expression.selectedGene);
  
  // Using RTK Query hook with skip option to prevent fetching when no gene is selected
  const { data, isLoading, error } = useGetTissueSummaryQuery(selectedGene, {
    skip: !selectedGene
  });

  // Don't render anything if no gene is selected
  if (!selectedGene) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="p-6">
          <Loading message="Loading tissue expression data..." />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="p-6">
          <ErrorMessage message={error.toString()} />
        </div>
      </div>
    );
  }

  if (!data || !data.tissue_expression || data.tissue_expression.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="p-6">
          <p className="text-gray-600">No expression data available for {selectedGene}.</p>
        </div>
      </div>
    );
  }

  // Prepare data for the chart
  const sortedData = [...data.tissue_expression]
    .sort((a, b) => b.median_expression - a.median_expression)
    .slice(0, 15) // Show top 15 tissues
    .map(item => ({
      ...item,
      name: item.display_name || item.tissue.replace(/_/g, ' ')
    }));

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {selectedGene} Expression Across Tissues
        </h2>
        
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={sortedData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" label={{ value: 'Median Expression', position: 'insideBottom', offset: -5 }} />
              <YAxis type="category" dataKey="name" width={100} />
              <Tooltip
                formatter={(value: any, name: any) => [`${value.toFixed(2)}`, 'Expression']}
                labelFormatter={(label) => `Tissue: ${label}`}
              />
              <Bar dataKey="median_expression" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};