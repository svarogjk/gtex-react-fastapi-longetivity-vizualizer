import { configureStore } from '@reduxjs/toolkit';
import expressionReducer from '../features/expression/expressionSlice';
import analysisReducer from '../features/analysis/analysisSlice';
import { requestMiddleware } from '../middleware/requestMiddleware';

// Debug middleware to log actions
const loggerMiddleware = store => next => action => {
  if (!action.type.includes('@@redux')) {
    console.log('[REDUX] dispatching:', action.type);
  }
  return next(action);
};

export const store = configureStore({
    reducer: {
        expression: expressionReducer,
        analysis: analysisReducer
    },
    middleware: (getDefaultMiddleware) => 
        getDefaultMiddleware().concat(requestMiddleware, loggerMiddleware)
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;