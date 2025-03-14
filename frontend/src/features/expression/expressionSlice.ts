import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface ExpressionState {
  selectedGene: string;
  selectedTissue: string;
  selectedDataset: string
}

const initialState: ExpressionState = {
  selectedGene: '',
  selectedTissue: '',
  selectedDataset: ''
};

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
      state.selectedDataset = ''; // Reset dataset when tissue changes
    },
    setSelectedDataset: (state, action: PayloadAction<string>) => {
      state.selectedDataset = action.payload;
    },
  },
});

export const { setSelectedGene, setSelectedTissue, setSelectedDataset } = expressionSlice.actions;
export default expressionSlice.reducer;