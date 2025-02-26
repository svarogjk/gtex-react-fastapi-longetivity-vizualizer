import { createSlice, createAsyncThunk, PayloadAction, createSelector } from '@reduxjs/toolkit';
import api from '../../services/api';
import { RootState } from '../../app/store';

// Types
export interface MetadataColumn {
  name: string;
  unique_values: number;
  type: string;
}

interface AnalysisState {
  dropdownData: {
    genes: {
      options: Array<{ value: string; label: string; details?: any }>;
      total_count: number;
    };
    datasets: {
      options: Array<{ value: string; label: string; details?: any }>;
      total_count: number;
    };
  } | null;
  selectedGene: string;
  selectedDataset: string;
  selectedTarget: string;
  selectedTissue: string;
  tissues: string[];
  metadataColumns: MetadataColumn[];
  loading: boolean;
  error: string | null;
}

// Initial state
const initialState: AnalysisState = {
  dropdownData: null,
  selectedGene: '',
  selectedDataset: '',
  selectedTarget: '',
  selectedTissue: '',
  tissues: [],
  metadataColumns: [],
  loading: false,
  error: null
};

// Thunks
export const fetchDropdownOptions = createAsyncThunk(
  'analysis/fetchDropdownOptions',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.searchGenes();
      return {
        genes: {
          options: response.genes.map((gene: string) => ({
            value: gene,
            label: gene,
            details: response.gene_details?.[gene] || {}
          })),
          total_count: response.total_count
        },
        datasets: {
          options: [],
          total_count: 0
        }
      };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch dropdown options');
    }
  },
  {
    // This condition prevents the action from firing if it's already in progress
    condition: (_, { getState }) => {
      const state = getState() as { analysis?: AnalysisState };
      const analysisState = state.analysis;
      
      // Only proceed if we have a valid state and it's not already loading
      return !analysisState?.loading;
    }
  }
);

export const fetchTissues = createAsyncThunk(
  'analysis/fetchTissues',
  async (gene: string, { rejectWithValue }) => {
    try {
      const response = await api.getTissueSummary(gene);
      const tissues = response.data.tissue_expression.map((item: any) => item.tissue);
      return [...new Set(tissues)]; // Remove duplicates
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch tissues');
    }
  }
);

export const fetchDatasetMetadata = createAsyncThunk(
  'analysis/fetchDatasetMetadata',
  async (datasetId: string, { rejectWithValue }) => {
    try {
      const response = await api.getDatasetMetadata(datasetId);
      return response.columns || [];
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch dataset metadata');
    }
  }
);

// Slice
const analysisSlice = createSlice({
  name: 'analysis',
  initialState,
  reducers: {
    setSelectedGene: (state, action: PayloadAction<string>) => {
      state.selectedGene = action.payload;
    },
    setSelectedDataset: (state, action: PayloadAction<string>) => {
      state.selectedDataset = action.payload;
    },
    setSelectedTarget: (state, action: PayloadAction<string>) => {
      state.selectedTarget = action.payload;
    },
    setSelectedTissue: (state, action: PayloadAction<string>) => {
      state.selectedTissue = action.payload;
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch dropdown options
      .addCase(fetchDropdownOptions.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDropdownOptions.fulfilled, (state, action) => {
        state.loading = false;
        
        // Skip updating if response is null
        if (action.payload === null) {
          console.log('[REDUX] Skipping dropdown options update since payload is null');
          return;
        }
        
        state.dropdownData = action.payload;
      })
      .addCase(fetchDropdownOptions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      // Fetch tissues
      .addCase(fetchTissues.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchTissues.fulfilled, (state, action) => {
        state.loading = false;
        
        // Skip updating if response is null
        if (action.payload === null) {
          console.log('[REDUX] Skipping tissues update since payload is null');
          return;
        }
        
        state.tissues = action.payload;
      })
      .addCase(fetchTissues.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        state.tissues = [];
      })
      
      // Fetch dataset metadata
      .addCase(fetchDatasetMetadata.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDatasetMetadata.fulfilled, (state, action) => {
        state.loading = false;
        
        // Skip updating if response is null
        if (action.payload === null) {
          console.log('[REDUX] Skipping metadata update since payload is null');
          return;
        }
        
        state.metadataColumns = action.payload;
      })
      .addCase(fetchDatasetMetadata.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        state.metadataColumns = [];
      });
  }
});

// Export actions before defining selectors
export const { setSelectedGene, setSelectedDataset, setSelectedTarget, setSelectedTissue } = analysisSlice.actions;

// Memoized selectors
// Base selector for the analysis slice
const selectAnalysisState = (state: RootState) => state.analysis;

// Selector for the AnalysisDropdowns component
export const selectAnalysisDropdownState = createSelector(
  [selectAnalysisState],
  (analysisState) => ({
    dropdownData: analysisState.dropdownData,
    loading: analysisState.loading,
    error: analysisState.error,
    selectedGene: analysisState.selectedGene,
    selectedDataset: analysisState.selectedDataset,
    selectedTarget: analysisState.selectedTarget,
    selectedTissue: analysisState.selectedTissue,
    tissues: analysisState.tissues,
    metadataColumns: analysisState.metadataColumns
  })
);

export default analysisSlice.reducer;