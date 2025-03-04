import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface AnalysisState {
  selectedGene: string;
  selectedDataset: string;
  selectedTarget: string;
  selectedTissue: string;
}

const initialState: AnalysisState = {
  selectedGene: '',
  selectedDataset: '',
  selectedTarget: '',
  selectedTissue: '',
};

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
  }
});

export const { 
  setSelectedGene, 
  setSelectedDataset, 
  setSelectedTarget, 
  setSelectedTissue 
} = analysisSlice.actions;

export default analysisSlice.reducer;