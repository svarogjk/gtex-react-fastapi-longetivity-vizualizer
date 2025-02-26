// src/middleware/requestMiddleware.ts
import { Middleware } from 'redux';

interface RequestTracker {
  actionCounts: Record<string, number>;
  lastReset: number;
}

// Track API request actions to prevent excessive calls
const requestTracker: RequestTracker = {
  actionCounts: {},
  lastReset: Date.now()
};

// Reset counters every minute
setInterval(() => {
  console.log('[REDUX MIDDLEWARE] Resetting action counters');
  console.log('Previous counts:', requestTracker.actionCounts);
  requestTracker.actionCounts = {};
  requestTracker.lastReset = Date.now();
}, 60000);

// List of action types to throttle
const API_REQUEST_ACTIONS = [
  'expression/fetchGenes/pending',
  'expression/fetchTissueExpression/pending',
  'analysis/fetchDropdownOptions/pending',
  'analysis/fetchTissues/pending',
  'analysis/fetchDatasetMetadata/pending'
];

// Maximum number of times an action can be dispatched per minute
const MAX_ACTION_DISPATCHES = 2;

/**
 * Middleware to prevent excessive API requests
 */
export const requestMiddleware: Middleware = store => next => action => {
  // Only monitor API request actions
  if (API_REQUEST_ACTIONS.includes(action.type)) {
    // Count this action
    requestTracker.actionCounts[action.type] = (requestTracker.actionCounts[action.type] || 0) + 1;
    
    // Log the counts
    console.log(`[REDUX MIDDLEWARE] Action ${action.type} count: ${requestTracker.actionCounts[action.type]}`);
    
    // If we've exceeded the limit, block the action
    if (requestTracker.actionCounts[action.type] > MAX_ACTION_DISPATCHES) {
      console.warn(`[REDUX MIDDLEWARE] Blocking excessive action: ${action.type}`);
      // Don't forward the action, effectively blocking it
      return;
    }
  }
  
  // Allow the action through
  return next(action);
};