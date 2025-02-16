import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';

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

interface AnalysisState {
  dropdownData: DropdownData | null;
  selectedGene: string;
  selectedDataset: string;
  selectedTarget: string;
  metadataColumns: MetadataColumn[];
  loading: boolean;
  error: string | null;
  metadataLoading: boolean;
  metadataError: string | null;
}

const initialState: AnalysisState = {
  dropdownData: null,
  selectedGene: '',
  selectedDataset: '',
  selectedTarget: '',
  metadataColumns: [],
  loading: false,
  error: null,
  metadataLoading: false,
  metadataError: null
};

export const fetchDropdownOptions = createAsyncThunk(
  'analysis/fetchDropdownOptions',
  async () => {
    const response = await axios.get('http://localhost:8000/api/dropdown_routes/dropdown/options');
    return response.data;
  }
);

export const fetchDatasetMetadata = createAsyncThunk(
  'analysis/fetchDatasetMetadata',
  async (datasetId: string) => {
    const response = await axios.get(`http://localhost:8000/api/datasets/${datasetId}/metadata`);
    return response.data.columns;
  }
);

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
    resetSelections: (state) => {
      state.selectedGene = '';
      state.selectedDataset = '';
      state.selectedTarget = '';
      state.metadataColumns = [];
    }
  },
  extraReducers: (builder) => {
    builder
      // Dropdown options fetch cases
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
        state.error = action.error.message || 'Failed to fetch options';
      })
      // Dataset metadata fetch cases
      .addCase(fetchDatasetMetadata.pending, (state) => {
        state.metadataLoading = true;
        state.metadataError = null;
      })
      .addCase(fetchDatasetMetadata.fulfilled, (state, action) => {
        state.metadataLoading = false;
        state.metadataColumns = action.payload;
      })
      .addCase(fetchDatasetMetadata.rejected, (state, action) => {
        state.metadataLoading = false;
        state.metadataError = action.error.message || 'Failed to fetch metadata';
      });
  }
});

export const { 
  setSelectedGene, 
  setSelectedDataset, 
  setSelectedTarget, 
  resetSelections 
} = analysisSlice.actions;

export default analysisSlice.reducer;