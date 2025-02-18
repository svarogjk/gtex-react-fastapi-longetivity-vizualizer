import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../../services/api';

interface AnalysisState {
  dropdownData: any;
  loading: boolean;
  error: string | null;
  selectedGene: string;
  selectedTissue: string;
  selectedDataset: string;
  selectedTarget: string;
  tissues: string[];
  metadataColumns: Array<{
    name: string;
    unique_values: number;
    type: string;
  }>;
}

const initialState: AnalysisState = {
  dropdownData: null,
  loading: false,
  error: null,
  selectedGene: '',
  selectedTissue: '',
  selectedDataset: '',
  selectedTarget: '',
  tissues: [],
  metadataColumns: [],
};

export const fetchDropdownOptions = createAsyncThunk(
  'analysis/fetchDropdownOptions',
  async () => {
    const response = await api.getDropdownOptions();
    return response;
  }
);

export const fetchTissues = createAsyncThunk(
  'analysis/fetchTissues',
  async (gene: string) => {
    const response = await api.getTissues(gene);
    return response.tissues;
  }
);

export const fetchDatasetMetadata = createAsyncThunk(
  'analysis/fetchDatasetMetadata',
  async (datasetId: string) => {
    const response = await api.getDatasetMetadata(datasetId);
    return response.columns;
  }
);

const analysisSlice = createSlice({
  name: 'analysis',
  initialState,
  reducers: {
    setSelectedGene: (state, action) => {
      state.selectedGene = action.payload;
    },
    setSelectedTissue: (state, action) => {
      state.selectedTissue = action.payload;
    },
    setSelectedDataset: (state, action) => {
      state.selectedDataset = action.payload;
    },
    setSelectedTarget: (state, action) => {
      state.selectedTarget = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // Dropdown Options
      .addCase(fetchDropdownOptions.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDropdownOptions.fulfilled, (state, action) => {
        state.loading = false;
        state.dropdownData = action.payload;
      })
      .addCase(fetchDropdownOptions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch dropdown options';
      })
      // Tissues
      .addCase(fetchTissues.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchTissues.fulfilled, (state, action) => {
        state.loading = false;
        state.tissues = action.payload;
      })
      .addCase(fetchTissues.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch tissues';
      })
      // Dataset Metadata
      .addCase(fetchDatasetMetadata.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDatasetMetadata.fulfilled, (state, action) => {
        state.loading = false;
        state.metadataColumns = action.payload;
      })
      .addCase(fetchDatasetMetadata.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch dataset metadata';
      });
  },
});

export const { 
  setSelectedGene, 
  setSelectedTissue,
  setSelectedDataset, 
  setSelectedTarget 
} = analysisSlice.actions;

export default analysisSlice.reducer;