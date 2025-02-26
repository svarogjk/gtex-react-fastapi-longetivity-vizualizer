import { createSlice, createAsyncThunk, PayloadAction, createSelector } from '@reduxjs/toolkit';
import api from '../../services/api';
import { RootState } from '../../app/store';

// Types
interface TissueExpression {
  tissue: string;
  display_name: string;
  median_expression: number;
  tissue_name: string;
  sample_count: number;
}

interface GeneOption {
  value: string;
  label: string;
  details?: any;
}

interface GenesState {
  options: GeneOption[];
  loading: boolean;
  error: string | null;
}

interface ExpressionState {
  loading: boolean;
  error: string | null;
  genes: GenesState;
  selectedGene: string;
  selectedTissue: string;
  tissueExpression: TissueExpression[];
  tissues: string[];
  loadingTissues: boolean;
}

// Initial state
const initialState: ExpressionState = {
  loading: false,
  error: null,
  genes: {
    options: [],
    loading: false,
    error: null,
  },
  selectedGene: '',
  selectedTissue: '',
  tissueExpression: [],
  tissues: [],
  loadingTissues: false,
};

// Thunks
export const fetchGenes = createAsyncThunk(
  'expression/fetchGenes',
  async (_, { rejectWithValue, getState }) => {
    try {
      console.log('[REDUX] fetchGenes thunk called');
      
      // Get current state to check if we should make this request
      const state = getState() as { expression?: ExpressionState };
      const expressionState = state.expression;
      
      // Skip if we already have data or are loading
      if (expressionState?.genes?.options?.length > 0) {
        console.log('[REDUX] Already have genes data, skipping fetch');
        return null;
      }
      
      if (expressionState?.genes?.loading) {
        console.log('[REDUX] Already loading genes, skipping fetch');
        return null;
      }
      
      // Make the request
      console.log('[REDUX] Making searchGenes API call');
      const response = await api.searchGenes();
      return response;
    } catch (error: any) {
      console.error('[REDUX] Error fetching genes:', error);
      return rejectWithValue(error.message || 'Failed to fetch genes');
    }
  }
);

export const fetchTissueExpression = createAsyncThunk(
  'expression/fetchTissueExpression',
  async (gene: string, { rejectWithValue, getState }) => {
    try {
      console.log(`[REDUX] fetchTissueExpression thunk called for gene: ${gene}`);
      
      // Get current state to check if we should make this request
      const state = getState() as { expression?: ExpressionState };
      const expressionState = state.expression;
      
      // Skip if we're already loading tissues
      if (expressionState?.loadingTissues) {
        console.log('[REDUX] Already loading tissues, skipping fetch');
        return null;
      }
      
      // Skip if we already have tissue expression data for this gene
      if (expressionState?.tissueExpression?.length > 0 && 
          expressionState?.selectedGene === gene) {
        console.log(`[REDUX] Already have tissue data for gene ${gene}, skipping fetch`);
        return null;
      }
      
      // Make the request
      console.log('[REDUX] Making getTissueSummary API call');
      const response = await api.getTissueSummary(gene);
      return response.data.tissue_expression;
    } catch (error: any) {
      console.error('[REDUX] Error fetching tissue expression:', error);
      return rejectWithValue(error.message || 'Failed to fetch tissue expression');
    }
  }
);

// Slice
const expressionSlice = createSlice({
  name: 'expression',
  initialState,
  reducers: {
    setSelectedGene: (state, action: PayloadAction<string>) => {
      state.selectedGene = action.payload;
      state.selectedTissue = ''; // Reset tissue when gene changes
    },
    setSelectedTissue: (state, action: PayloadAction<string>) => {
      state.selectedTissue = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch genes
      .addCase(fetchGenes.pending, (state) => {
        state.genes.loading = true;
        state.genes.error = null;
      })
      .addCase(fetchGenes.fulfilled, (state, action) => {
        state.genes.loading = false;
        
        // Skip updating if response is null (we returned null when already loading)
        if (action.payload === null) {
          console.log('[REDUX] Skipping genes update since payload is null');
          return;
        }
        
        state.genes.options = action.payload.genes.map((gene: string) => ({
          value: gene,
          label: gene,
          details: action.payload.gene_details?.[gene] || {}
        }));
      })
      .addCase(fetchGenes.rejected, (state, action) => {
        state.genes.loading = false;
        state.genes.error = action.payload as string;
      })
      
      // Fetch tissue expression
      .addCase(fetchTissueExpression.pending, (state) => {
        state.loadingTissues = true;
        state.error = null;
      })
      .addCase(fetchTissueExpression.fulfilled, (state, action) => {
        state.loadingTissues = false;
        
        // Skip updating if response is null
        if (action.payload === null) {
          console.log('[REDUX] Skipping tissue expression update since payload is null');
          return;
        }
        
        state.tissueExpression = action.payload || [];
        // Extract unique tissues from the expression data
        state.tissues = [...new Set(state.tissueExpression.map(item => item.tissue))];
      })
      .addCase(fetchTissueExpression.rejected, (state, action) => {
        state.loadingTissues = false;
        state.error = action.payload as string;
        state.tissueExpression = [];
        state.tissues = [];
      });
  },
});

// Export actions before defining selectors
export const { setSelectedGene, setSelectedTissue } = expressionSlice.actions;

// Memoized selectors
// Base selector for the expression slice
const selectExpressionState = (state: RootState) => state.expression;

// Selector for GeneSelector component
export const selectGeneState = createSelector(
  [selectExpressionState],
  (expressionState) => ({
    genes: expressionState.genes || { loading: false, error: null, options: [] },
    selectedGene: expressionState.selectedGene || ''
  })
);

// Selector for TissueSelector component
export const selectTissueState = createSelector(
  [selectExpressionState],
  (expressionState) => ({
    selectedGene: expressionState.selectedGene || '',
    tissues: expressionState.tissues || [],
    selectedTissue: expressionState.selectedTissue || '',
    loadingTissues: expressionState.loadingTissues || false,
    tissueExpression: expressionState.tissueExpression || []
  })
);

// Selector for TissueExpressionChart component
export const selectExpressionChartState = createSelector(
  [selectExpressionState],
  (expressionState) => ({
    selectedGene: expressionState.selectedGene || '',
    tissueExpression: expressionState.tissueExpression || [],
    loadingTissues: expressionState.loadingTissues || false,
    error: expressionState.error || null
  })
);

// Selector for ExpressionAnalysis component
export const selectExpressionAnalysisState = createSelector(
  [selectExpressionState],
  (expressionState) => ({
    selectedGene: expressionState.selectedGene || '',
    genes: expressionState.genes || { loading: false, error: null, options: [] }
  })
);

export default expressionSlice.reducer;