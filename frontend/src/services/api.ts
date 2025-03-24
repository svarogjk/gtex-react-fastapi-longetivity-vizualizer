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
  gene: string;
  gencode_id: string;
  tissue_expression: TissueExpression[];
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

interface DatasetSummary {
  dataset_id: string;
  dataset_name: string;
  dataset_type: string;
  median_expression: number;
  mean_expression: number;
  unit: string;
  sample_count: number;
  source: string;
  tissue: string;
}

interface ExpressionDataResponse {
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
  baseQuery: fetchBaseQuery({ 
    baseUrl: 'http://localhost:8000/api',
    // Add headers for content type and request identification
    prepareHeaders: (headers) => {
      headers.set('Content-Type', 'application/json');
      return headers;
    }
  }),
  endpoints: (builder) => ({
    // Gene-related endpoints
    searchGenes: builder.query<GenesResponse, void>({
      query: () => 'dropdown_routes/dropdown/genes',
      // Transform the response if needed
      transformResponse: (response: GenesResponse) => {
        console.log('Raw search genes response:', response);
        return response;
      },
      // Provide some tags for caching
      providesTags: ['Genes']
    }),
    
    getTissueSummary: builder.query<TissueExpressionResponse, string>({
      query: (gene) => `expression/genes/${gene}/tissue-summary`,
      providesTags: (result, error, gene) => [{ type: 'Gene', id: gene }]
    }),
    
    getGeneTissueExpression: builder.query<ExpressionDataResponse, { gene: string; tissue: string }>({
      query: ({ gene, tissue }) => `genes/${gene}/expression/${tissue}`,
      providesTags: (result, error, arg) => [
        { type: 'Gene', id: arg.gene },
        { type: 'Tissue', id: arg.tissue }
      ]
    }),
    
    // Tissue-related endpoints
    getTissues: builder.query<TissuesResponse, void>({
      query: () => 'tissues',
      providesTags: ['Tissues']
    }),
    
    // Dataset-related endpoints
    getDatasetsSummary: builder.query<Record<string, any>, { gene: string; tissue: string }>({
      query: ({ gene, tissue }) => ({
        url: `/expression/datasets-summary/genes/${gene}/tissues/${tissue}`,
        params: { limit: 50 }
      }),
      providesTags: ['Datasets']
    }),
    
    getDatasetMetadata: builder.query<DatasetMetadataResponse, string>({
      query: (datasetId) => `/expression/datasets/${datasetId}/metadata`,
      providesTags: (result, error, datasetId) => [{ type: 'Dataset', id: datasetId }]
    }),
    
    getDatasetDetails: builder.query<DatasetDetailsResponse, string>({
      query: (datasetId) => `/expression/ddatasets/${datasetId}/details`,
      providesTags: (result, error, datasetId) => [{ type: 'Dataset', id: datasetId }]
    }),
    
    // Dropdown options
    getDropdownOptions: builder.query<Record<string, any>, void>({
      query: () => 'dropdown/options',
      providesTags: ['Dropdowns']
    }),
    
    // Analysis endpoints
    getExpressionData: builder.query<ExpressionDataResponse, { genes: string[]; tissue: string }>({
      query: ({ genes, tissue }) => ({
        url: 'genes/expression',
        params: { genes, tissue },
      }),
      providesTags: (result, error, arg) => [
        ...arg.genes.map(gene => ({ type: 'Gene' as const, id: gene })),
        { type: 'Tissue' as const, id: arg.tissue }
      ]
    }),
    
    analyzeLongevity: builder.query<LongevityAnalysisResponse, { genes: string[]; tissue: string }>({
      query: ({ genes, tissue }) => ({
        url: 'genes/longevity-analysis',
        params: { genes, tissue },
      }),
      providesTags: (result, error, arg) => [
        ...arg.genes.map(gene => ({ type: 'Gene' as const, id: gene })),
        { type: 'Tissue' as const, id: arg.tissue }
      ]
    }),
  }),
});


// Export hooks for each endpoint
export const {
  useSearchGenesQuery,
  useGetTissueSummaryQuery,
  useGetGeneTissueExpressionQuery,
  useGetTissuesQuery,
  useGetDatasetsSummaryQuery,
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
  
  getDatasetSummary: async (gene: string, tissue: string): Promise<DatasetSummary> => {
    const response = await fetch(`/api/expression/datasets-summary/genes/${gene}/tissues/${tissue}`);
    if (!response.ok) throw new Error(`Failed to fetch dataset summary for ${gene} in ${tissue}`);
    return response.json();
  },

  getDatasetMetadata: async (datasetId: string): Promise<DatasetMetadataResponse> => {
    const response = await fetch(`/api/expression/datasets/${datasetId}/metadata`);
    if (!response.ok) throw new Error(`Failed to fetch metadata for dataset ${datasetId}`);
    return response.json();
  },
  
};