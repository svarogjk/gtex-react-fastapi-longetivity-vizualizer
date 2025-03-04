// src/services/api.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

// Types
interface TissueExpression {
  tissue: string;
  display_name: string;
  median_expression: number;
  tissue_name: string;
  sample_count: number;
}

interface GeneDetails {
  description: string;
  type: string;
  summary: string;
  aliases: string[];
  chromosome: string;
  location: string;
}

interface GenesResponse {
  genes: string[];
  gene_details: Record<string, GeneDetails>;
  total_count: number;
}

interface TissueExpressionResponse {
  status: string;
  data: {
    gene: string;
    gencode_id: string;
    tissue_expression: TissueExpression[];
  };
}

interface MetadataColumn {
  name: string;
  unique_values: number;
  type: string;
}

interface DatasetMetadataResponse {
  status: string;
  columns: MetadataColumn[];
}

interface DatasetDetailsResponse {
  success: boolean;
  metadata: Record<string, string[]>;
  title: string;
  summary: string;
  samples: number;
}

interface TissuesResponse {
  tissues: string[];
  categories: Record<string, Array<{ id: string; name: string }>>;
}

interface ExpressionDataResponse {
  status: string;
  message: string;
  data: {
    expression: any[];
    metadata: any[];
    summary: {
      n_samples: number;
      n_genes: number;
      tissue: string;
      unit: string;
      gene_stats: Record<string, any>;
      correlations: Record<string, any>;
    };
  };
}

interface LongevityAnalysisResponse {
  status: string;
  data: {
    longevity_analysis: {
      longevity_genes_found: string[];
      pathway_analysis: Record<string, any>;
      gene_stats: Record<string, any>;
      correlations: Record<string, any>;
    };
    metadata: {
      tissue: string;
      total_genes: number;
      longevity_genes_count: number;
    };
  };
}

// Define the API service
export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({ baseUrl: '/api' }),
  endpoints: (builder) => ({
    // Gene-related endpoints
    searchGenes: builder.query<GenesResponse, void>({
      query: () => 'dropdown/genes',
    }),
    
    getTissueSummary: builder.query<TissueExpressionResponse, string>({
      query: (gene) => `genes/${gene}/tissue-summary`,
    }),
    
    getGeneTissueExpression: builder.query<ExpressionDataResponse, { gene: string; tissue: string }>({
      query: ({ gene, tissue }) => `genes/${gene}/expression/${tissue}`,
    }),
    
    // Tissue-related endpoints
    getTissues: builder.query<TissuesResponse, void>({
      query: () => 'tissues',
    }),
    
    // Dataset-related endpoints
    searchDatasets: builder.query<Record<string, any>, string[] | void>({
      query: (genes) => ({
        url: 'dropdown/datasets',
        params: genes ? { genes } : undefined,
      }),
    }),
    
    getDatasetMetadata: builder.query<DatasetMetadataResponse, string>({
      query: (datasetId) => `datasets/${datasetId}/metadata`,
    }),
    
    getDatasetDetails: builder.query<DatasetDetailsResponse, string>({
      query: (datasetId) => `datasets/${datasetId}/details`,
    }),
    
    // Dropdown options
    getDropdownOptions: builder.query<Record<string, any>, void>({
      query: () => 'dropdown/options',
    }),
    
    // Analysis endpoints
    getExpressionData: builder.query<ExpressionDataResponse, { genes: string[]; tissue: string }>({
      query: ({ genes, tissue }) => ({
        url: 'genes/expression',
        params: { genes, tissue },
      }),
    }),
    
    analyzeLongevity: builder.query<LongevityAnalysisResponse, { genes: string[]; tissue: string }>({
      query: ({ genes, tissue }) => ({
        url: 'genes/longevity-analysis',
        params: { genes, tissue },
      }),
    }),
  }),
});

// Export hooks for each endpoint
export const {
  useSearchGenesQuery,
  useGetTissueSummaryQuery,
  useGetGeneTissueExpressionQuery,
  useGetTissuesQuery,
  useSearchDatasetsQuery,
  useGetDatasetMetadataQuery,
  useGetDatasetDetailsQuery,
  useGetDropdownOptionsQuery,
  useGetExpressionDataQuery,
  useAnalyzeLongevityQuery,
} = api;

// For non-hook usage (in thunks or other places)
export default {
  searchGenes: async (): Promise<GenesResponse> => {
    const response = await fetch('/api/dropdown/genes');
    if (!response.ok) throw new Error('Failed to fetch genes');
    return response.json();
  },
  
  getTissueSummary: async (gene: string): Promise<TissueExpressionResponse> => {
    const response = await fetch(`/api/genes/${gene}/tissue-summary`);
    if (!response.ok) throw new Error(`Failed to fetch tissue summary for ${gene}`);
    return response.json();
  },
  
  getDatasetMetadata: async (datasetId: string): Promise<DatasetMetadataResponse> => {
    const response = await fetch(`/api/datasets/${datasetId}/metadata`);
    if (!response.ok) throw new Error(`Failed to fetch metadata for dataset ${datasetId}`);
    return response.json();
  },
  
  // Add additional methods as needed for imperative calls
};