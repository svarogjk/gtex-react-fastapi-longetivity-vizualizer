import { configureStore } from '@reduxjs/toolkit';
import analysisSlice from '../features/analysis/analysisSlice';

// We'll add reducers as we create them
const store = configureStore({
  reducer: {
    analysis: analysisSlice,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export { store };