import React from "react";
import { useAppSelector } from "@/app/hooks";
import { useGetGeneSurvivalDataQuery } from "@/services/api";
import { Loading } from "@/components/common/Loading";
import { ErrorMessage } from "@/components/common/ErrorMessage";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer} from "recharts";

export const GeneSurvivalAnalysisTable = () => {
    const selectedGene = useAppSelector(state => state.expression.selectedGene);
    const selectedTissue = useAppSelector(state => state.expression.selectedTissue);

    const { data, isLoading, error } = useGetGeneSurvivalDataQuery(
    { gene: selectedGene, tissue: selectedTissue },
    {
      skip: !selectedGene || !selectedTissue
    }
  );

  // Don't render if no gene or tissue is selected
  if (!selectedGene || !selectedTissue) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg mt-4">
        <div className="p-6">
          <Loading message="Loading survival analysis data..." />
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
              <p>Gene: {selectedGene}</p>
              <p>Tissue: {selectedTissue}</p>
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
          <h2 className="text-lg font-semibold text-gray-900">Gene Survival Analysis</h2>
          <p className="text-gray-600 mt-2">No survival data available for the selected gene and tissue.</p>
        </div>
      </div>
    );
  }
  const formatSurvivalData = () => {
    const highExprData = data.high_expression.survival_curve.map(point => ({
      time: point.time,
      high_expression: point.survival_probability,
      low_expression: null
    }));

    const lowExprData = data.low_expression.survival_curve.map(point => ({
      time: point.time,
      high_expression: null,
      low_expression: point.survival_probability
    }));

    // Combine and sort by time
    const combined = [...highExprData, ...lowExprData].sort((a, b) => a.time - b.time);
    
    // Fill in missing values by carrying forward the last known value
    let lastHighValue = null;
    let lastLowValue = null;
    
    return combined.map(point => {
      if (point.high_expression !== null) lastHighValue = point.high_expression;
      if (point.low_expression !== null) lastLowValue = point.low_expression;
      
      return {
        time: point.time,
        high_expression: point.high_expression || lastHighValue,
        low_expression: point.low_expression || lastLowValue
      };
    });
  };

  const chartData = formatSurvivalData();

  const formatPValue = (pValue: number) => {
    if (pValue < 0.001) return '< 0.001';
    if (pValue < 0.01) return '< 0.01';
    if (pValue < 0.05) return '< 0.05';
    return pValue.toFixed(3);
  };

  const formatNumber = (num: number) => {
    if (num === null || num === undefined) return 'N/A';
    return num.toFixed(3);
  };

  return (
    <div className="bg-white shadow rounded-lg mt-4">
      <div className="p-6 space-y-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Gene Survival Analysis</h2>
          <p className="text-sm text-gray-600 mt-1">
            Survival analysis for gene {selectedGene} in {selectedTissue} tissue
          </p>
        </div>

        {/* Metadata Summary */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-md font-medium text-gray-900 mb-3">Analysis Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Total Samples:</span>
              <span className="ml-2 text-gray-900">{data.metadata.sample_count}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">High Expression:</span>
              <span className="ml-2 text-gray-900">{data.metadata.high_expr_count} ({data.metadata.cutpoint.percent_high.toFixed(1)}%)</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Low Expression:</span>
              <span className="ml-2 text-gray-900">{data.metadata.low_expr_count} ({data.metadata.cutpoint.percent_low.toFixed(1)}%)</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Median Expression:</span>
              <span className="ml-2 text-gray-900">{formatNumber(data.metadata.median_expression)}</span>
            </div>
          </div>
        </div>

        {/* Kaplan-Meier Plot */}
        <div>
          <h3 className="text-md font-medium text-gray-900 mb-3">Kaplan-Meier Survival Curves</h3>
          <div className="h-96 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="time" 
                  label={{ value: 'Time (years)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis 
                  label={{ value: 'Survival Probability', angle: -90, position: 'insideLeft' }}
                  domain={[0, 1]}
                />
                <Tooltip 
                  formatter={(value, name) => [
                    value ? value.toFixed(3) : 'N/A',
                    name === 'high_expression' ? 'High Expression' : 'Low Expression'
                  ]}
                  labelFormatter={(label) => `Time: ${label} years`}
                />
                <Legend />
                <Line 
                  type="stepAfter" 
                  dataKey="high_expression" 
                  stroke="#ef4444" 
                  name="High Expression"
                  strokeWidth={2}
                  dot={false}
                  connectNulls={false}
                />
                <Line 
                  type="stepAfter" 
                  dataKey="low_expression" 
                  stroke="#3b82f6" 
                  name="Low Expression"
                  strokeWidth={2}
                  dot={false}
                  connectNulls={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Statistical Analysis */}
        <div className="space-y-4">
          <h3 className="text-md font-medium text-gray-900">Statistical Analysis</h3>
          
          {/* Log-rank Test */}
          <div className="bg-blue-50 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2">Log-rank Test</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="font-medium text-blue-700">P-value:</span>
                <span className={`ml-2 ${data.statistical_analysis.logrank_test.is_significant ? 'text-red-600 font-semibold' : 'text-blue-900'}`}>
                  {formatPValue(data.statistical_analysis.logrank_test.p_value)}
                </span>
              </div>
              <div>
                <span className="font-medium text-blue-700">Test Statistic:</span>
                <span className="ml-2 text-blue-900">{formatNumber(data.statistical_analysis.logrank_test.test_statistic)}</span>
              </div>
              <div>
                <span className="font-medium text-blue-700">Significant:</span>
                <span className={`ml-2 ${data.statistical_analysis.logrank_test.is_significant ? 'text-red-600' : 'text-green-600'}`}>
                  {data.statistical_analysis.logrank_test.is_significant ? 'Yes' : 'No'}
                </span>
              </div>
            </div>
          </div>

          {/* Cox Models */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Continuous Expression Model */}
            <div className="bg-green-50 rounded-lg p-4">
              <h4 className="font-medium text-green-900 mb-2">Continuous Expression Model</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="font-medium text-green-700">Hazard Ratio:</span>
                  <span className="text-green-900">{formatNumber(data.statistical_analysis.cox_models.continuous_expression.gene_expression_hazard_ratio)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium text-green-700">P-value:</span>
                  <span className={`${data.statistical_analysis.cox_models.continuous_expression.gene_expression_is_significant ? 'text-red-600 font-semibold' : 'text-green-900'}`}>
                    {formatPValue(data.statistical_analysis.cox_models.continuous_expression.gene_expression_p_value)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium text-green-700">Concordance:</span>
                  <span className="text-green-900">{formatNumber(data.statistical_analysis.cox_models.continuous_expression.model_quality.concordance)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium text-green-700">AIC:</span>
                  <span className="text-green-900">{formatNumber(data.statistical_analysis.cox_models.continuous_expression.model_quality.aic)}</span>
                </div>
              </div>
            </div>

            {/* Binary Expression Model */}
            <div className="bg-purple-50 rounded-lg p-4">
              <h4 className="font-medium text-purple-900 mb-2">Binary Expression Model</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="font-medium text-purple-700">Hazard Ratio:</span>
                  <span className="text-purple-900">{formatNumber(data.statistical_analysis.cox_models.binary_expression_group.high_expression_group_hazard_ratio)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium text-purple-700">P-value:</span>
                  <span className={`${data.statistical_analysis.cox_models.binary_expression_group.high_expression_group_is_significant ? 'text-red-600 font-semibold' : 'text-purple-900'}`}>
                    {formatPValue(data.statistical_analysis.cox_models.binary_expression_group.high_expression_group_p_value)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium text-purple-700">Concordance:</span>
                  <span className="text-purple-900">{formatNumber(data.statistical_analysis.cox_models.binary_expression_group.model_quality.concordance)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium text-purple-700">AIC:</span>
                  <span className="text-purple-900">{formatNumber(data.statistical_analysis.cox_models.binary_expression_group.model_quality.aic)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Median Survival Times */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-md font-medium text-gray-900 mb-3">Median Survival Times</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">High Expression Group:</span>
              <span className="ml-2 text-gray-900">
                {data.high_expression.median_survival ? `${data.high_expression.median_survival} years` : 'Not reached'}
              </span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Low Expression Group:</span>
              <span className="ml-2 text-gray-900">
                {data.low_expression.median_survival ? `${data.low_expression.median_survival} years` : 'Not reached'}
              </span>
            </div>
          </div>
        </div>

        {/* Interpretation */}
        {data.interpretation && (
          <div className="bg-yellow-50 rounded-lg p-4">
            <h3 className="text-md font-medium text-yellow-900 mb-2">Interpretation</h3>
            <p className="text-sm text-yellow-800">{data.interpretation}</p>
          </div>
        )}

        {/* Cutpoint Information */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-md font-medium text-gray-900 mb-3">Expression Cutpoint</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Cutpoint Value:</span>
              <span className="ml-2 text-gray-900">{formatNumber(data.metadata.cutpoint.value)}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Cutpoint Type:</span>
              <span className="ml-2 text-gray-900">{data.metadata.cutpoint.type}</span>
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-600">
            <p>High: {data.metadata.cutpoint.high_expression_definition}</p>
            <p>Low: {data.metadata.cutpoint.low_expression_definition}</p>
          </div>
        </div>
      </div>
    </div>
  );
}