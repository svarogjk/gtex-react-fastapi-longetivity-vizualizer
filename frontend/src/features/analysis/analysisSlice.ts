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

interface AnalysisState {
  dropdownData: DropdownData | null;
  selectedGene: string;
  selectedDataset: string;
  loading: boolean;
  error: string | null;
}

const initialState: AnalysisState = {
  dropdownData: null,
  selectedGene: '',
  selectedDataset: '',
  loading: false,
  error: null
};

export const fetchDropdownOptions = createAsyncThunk(
  'analysis/fetchDropdownOptions',
  async () => {
    const response = await axios.get('http://localhost:8000/api/dropdown_routes/dropdown/options');
    return response.data;
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
    resetSelections: (state) => {
      state.selectedGene = '';
      state.selectedDataset = '';
    }
  },
  extraReducers: (builder) => {
    builder
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
      });
  }
});

export const { setSelectedGene, setSelectedDataset, resetSelections } = analysisSlice.actions;
export default analysisSlice.reducer;