import { configureStore } from '@reduxjs/toolkit';
import expressionReducer from '../features/expression/expressionSlice';
import survivalReducer from '../features/survival/survivalSlice';

export const store = configureStore({
    reducer: {
        expression: expressionReducer,
        survival: survivalReducer
    }
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;