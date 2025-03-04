import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface ExpressionState {
  selectedGene: string;
  selectedTissue: string;
}

const initialState: ExpressionState = {
  selectedGene: '',
  selectedTissue: '',
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
    },
  },
});

export const { setSelectedGene, setSelectedTissue } = expressionSlice.actions;
export default expressionSlice.reducer;