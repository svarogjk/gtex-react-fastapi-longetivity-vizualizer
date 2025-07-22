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

interface Subject {
  subject_id: string;
  sex: string;
  dataset_id: string;
  age_bracket: string;
  hardy_scale: string;
}

type DatasetMetadataResponse = Subject[];

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

interface GeneSurvivalDataResponse {
  metadata: {
    gene: string;
    tissue: string;
    sample_count: number;
    high_expr_count: number;
    low_expr_count: number;
    median_expression: number;
    cutpoint: {
      value: number;
      type: string;
      high_expression_definition: string;
      low_expression_definition: string;
      percent_high: number;
      percent_low: number;
    };
  };
  high_expression: {
    survival_curve: Array<{
      time: number;
      survival_probability: number;
    }>;
    median_survival: number;
    min_time: number;
    max_time: number;
  };
  low_expression: {
    survival_curve: Array<{
      time: number;
      survival_probability: number;
    }>;
    median_survival: number;
    min_time: number;
    max_time: number;
  };
  statistical_analysis: {
    logrank_test: {
      p_value: number;
      test_statistic: number;
      is_significant: boolean;
    };
    cox_models: {
      continuous_expression: {
        gene_expression_coef: number;
        gene_expression_p_value: number;
        gene_expression_hazard_ratio: number;
        gene_expression_is_significant: boolean;
        covariates: {
          sex_male: Record<string, never>; // empty object
          hardy_numeric: {
            coef: number;
            p_value: number;
            hazard_ratio: number;
          };
        };
        model_quality: {
          concordance: number;
          log_likelihood: number;
          aic: number;
        };
      };
      binary_expression_group: {
        high_expression_group_coef: number;
        high_expression_group_p_value: number;
        high_expression_group_hazard_ratio: number;
        high_expression_group_is_significant: boolean;
        covariates: {
          sex_male: Record<string, never>; // empty object
          hardy_numeric: {
            coef: number;
            p_value: number;
            hazard_ratio: number;
          };
        };
        model_quality: {
          concordance: number;
          log_likelihood: number;
          aic: number;
        };
      };
    };
  };
  interpretation: string;
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

    // Gene Survival Analysis endpoint
    getGeneSurvivalData: builder.query<GeneSurvivalDataResponse, { gene: string; tissue: string }>({
      query: ({ gene, tissue }) => `survival/genes/${gene}/${tissue}`,
      providesTags: (result, error, arg) => [
        { type: 'Gene', id: arg.gene },
        { type: 'Tissue', id: arg.tissue },
        { type: 'Survival', id: `${arg.gene}-${arg.tissue}` }
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
  useGetGeneSurvivalDataQuery,
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

  getGeneSurvivalData: async (gene: string): Promise<TissueExpressionResponse> => {
    const response = await fetch(`/api/genes/${gene}/tissue-summary`);
    if (!response.ok) throw new Error(`Failed to fetch tissue summary for ${gene}`);
    return response.json();
  },
  
};