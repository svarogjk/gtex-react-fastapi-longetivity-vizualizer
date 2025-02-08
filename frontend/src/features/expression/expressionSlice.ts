import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../../services/api';

export const fetchExpressionData = createAsyncThunk(
    'expression/fetchData',
    async ({ genes, tissue }: { genes: string[], tissue: string }) => {
        const response = await api.getExpressionData(genes, tissue);
        return response;
    }
);

const expressionSlice = createSlice({
    name: 'expression',
    initialState: {
        data: null,
        status: 'idle',
        error: null as string | null
    },
    reducers: {},
    extraReducers: (builder) => {
        builder
            .addCase(fetchExpressionData.pending, (state) => {
                state.status = 'loading';
            })
            .addCase(fetchExpressionData.fulfilled, (state, action) => {
                state.status = 'succeeded';
                state.data = action.payload;
            })
            .addCase(fetchExpressionData.rejected, (state, action) => {
                state.status = 'failed';
                state.error = action.error.message || 'Failed to fetch data';
            });
    }
});

export default expressionSlice.reducer;