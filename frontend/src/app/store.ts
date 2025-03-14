import { configureStore } from '@reduxjs/toolkit';
import expressionReducer from '../features/expression/expressionSlice';
import { api } from '../services/api';

export const store = configureStore({
    reducer: {
        expression: expressionReducer,
        [api.reducerPath]: api.reducer,
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware().concat(api.middleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;