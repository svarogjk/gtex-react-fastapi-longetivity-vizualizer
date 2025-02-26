import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';
const DROPDOWN_BASE_URL = `${API_BASE_URL}/dropdown_routes`;
const EXPRESSION_BASE_URL = `${API_BASE_URL}/expression`;

// Global request counter and timestamp to limit request frequency
const requestStats = {
  counter: 0,
  timestamp: Date.now(),
  requestsThisMinute: new Map(),
  requestHistory: {}
};

// Maximum requests allowed per endpoint per minute
const MAX_REQUESTS_PER_MINUTE = 5;

// Resets the request counter every minute
setInterval(() => {
  const now = Date.now();
  if (now - requestStats.timestamp > 60000) {
    console.log(`[API] Resetting request counters. Made ${requestStats.counter} requests in the last minute.`);
    const endpoints = [...requestStats.requestsThisMinute.keys()];
    for (const endpoint of endpoints) {
      const count = requestStats.requestsThisMinute.get(endpoint) || 0;
      requestStats.requestHistory[endpoint] = count;
      console.log(`[API] Endpoint ${endpoint}: ${count} requests`);
    }
    
    requestStats.counter = 0;
    requestStats.timestamp = now;
    requestStats.requestsThisMinute.clear();
  }
}, 10000); // Check every 10 seconds

// Retry configuration for API requests
const MAX_RETRIES = 2;
const RETRY_DELAY = 1000; // 1 second

// Helper function to add retry logic to API calls
const withRetry = async (apiCall) => {
  let lastError;
  
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      // Wait between retries
      if (attempt > 0) {
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
      }
      
      return await apiCall();
    } catch (error) {
      lastError = error;
      console.warn(`[API] Request failed (attempt ${attempt + 1}/${MAX_RETRIES + 1}):`, error.message);
      
      // Don't retry on 4xx client errors (except 429 too many requests)
      if (error.response && error.response.status >= 400 && error.response.status < 500 && error.response.status !== 429) {
        break;
      }
    }
  }
  
  throw lastError;
};

// Track in-flight requests to prevent duplicates
const pendingRequests = new Map();

// Function to deduplicate API requests
const dedupRequest = async (key, requestFn) => {
  // Track request count for this endpoint
  const endpointKey = key.split(':')[0];
  const currentCount = requestStats.requestsThisMinute.get(endpointKey) || 0;
  requestStats.requestsThisMinute.set(endpointKey, currentCount + 1);
  requestStats.counter++;
  
  // Check if we're making too many requests to this endpoint
  if (currentCount >= MAX_REQUESTS_PER_MINUTE) {
    console.warn(`[API] Too many requests to ${endpointKey}! Limiting to ${MAX_REQUESTS_PER_MINUTE} per minute.`);
    
    // For searchGenes specifically, return empty results instead of throwing
    if (endpointKey === 'searchGenes') {
      console.warn('[API] Returning empty results for searchGenes due to rate limiting');
      return { genes: [], gene_details: {}, total_count: 0 };
    }
    
    throw new Error(`Rate limited: Too many requests to ${endpointKey}`);
  }

  // If this exact request is already in progress, return its promise
  if (pendingRequests.has(key)) {
    console.log(`[API] Reusing in-flight request for: ${key}`);
    return pendingRequests.get(key);
  }

  // Create a new request promise
  console.log(`[API] Making request: ${key} (${currentCount + 1}/${MAX_REQUESTS_PER_MINUTE})`);
  const requestPromise = withRetry(requestFn).finally(() => {
    // Remove from pending requests when done (success or failure)
    pendingRequests.delete(key);
  });

  // Store this request
  pendingRequests.set(key, requestPromise);
  return requestPromise;
};

// The API service object
const api = {
    // Gene related endpoints
    searchGenes: async (query?: string) => {
        try {
            // Create a unique key for this request
            const requestKey = `searchGenes:${query || ''}`;
            
            // Use the deduplication function
            return await dedupRequest(requestKey, async () => {
                console.log(`[API] Making request: ${requestKey}`);
                const response = await axios.get(`${DROPDOWN_BASE_URL}/dropdown/genes`, {
                    params: { query },
                    timeout: 10000 // 10 second timeout
                });
                return response.data;
            });
        } catch (error) {
            console.error('[API] Error in searchGenes:', error);
            throw error;
        }
    },

    // Get tissue expression summary for a gene
    getTissueSummary: async (gene: string) => {
        try {
            // Create a unique key for this request
            const requestKey = `getTissueSummary:${gene}`;
            
            // Use the deduplication function
            return await dedupRequest(requestKey, async () => {
                console.log(`[API] Making request: ${requestKey}`);
                const response = await axios.get(`${EXPRESSION_BASE_URL}/genes/${gene}/tissue-summary`, {
                    timeout: 10000 // 10 second timeout
                });
                return response.data;
            });
        } catch (error) {
            console.error('[API] Error in getTissueSummary:', error);
            throw error;
        }
    },

    // Expression data for specific gene and tissue
    getGeneExpression: async (gene: string, tissue: string) => {
        try {
            // Create a unique key for this request
            const requestKey = `getGeneExpression:${gene}:${tissue}`;
            
            // Use the deduplication function
            return await dedupRequest(requestKey, async () => {
                console.log(`[API] Making request: ${requestKey}`);
                const response = await axios.get(
                    `${EXPRESSION_BASE_URL}/genes/${gene}/expression/${tissue}`,
                    { timeout: 10000 }
                );
                return response.data;
            });
        } catch (error) {
            console.error('[API] Error in getGeneExpression:', error);
            throw error;
        }
    },

    // Get all available tissues
    getTissues: async () => {
        try {
            // Create a unique key for this request
            const requestKey = `getTissues`;
            
            // Use the deduplication function
            return await dedupRequest(requestKey, async () => {
                console.log(`[API] Making request: ${requestKey}`);
                const response = await axios.get(`${EXPRESSION_BASE_URL}/tissues`, {
                    timeout: 10000
                });
                return response.data;
            });
        } catch (error) {
            console.error('[API] Error in getTissues:', error);
            throw error;
        }
    },

    // Longevity analysis
    analyzeLongevity: async (genes: string[], tissue: string) => {
        try {
            // Create a unique key for this request
            const requestKey = `analyzeLongevity:${genes.join(',')}:${tissue}`;
            
            // Use the deduplication function
            return await dedupRequest(requestKey, async () => {
                console.log(`[API] Making request: ${requestKey}`);
                const response = await axios.get(`${EXPRESSION_BASE_URL}/genes/longevity-analysis`, {
                    params: { genes, tissue },
                    timeout: 10000
                });
                return response.data;
            });
        } catch (error) {
            console.error('[API] Error in analyzeLongevity:', error);
            throw error;
        }
    },
    
    // Methods for AnalysisDropdowns
    getDropdownOptions: async () => {
        try {
            // Create a unique key for this request
            const requestKey = `getDropdownOptions`;
            
            // Use the deduplication function
            return await dedupRequest(requestKey, async () => {
                console.log(`[API] Making request: ${requestKey}`);
                const response = await axios.get(`${DROPDOWN_BASE_URL}/dropdown/options`, {
                    timeout: 10000
                });
                return response.data;
            });
        } catch (error) {
            console.error('[API] Error in getDropdownOptions:', error);
            throw error;
        }
    },
    
    getDatasetMetadata: async (datasetId: string) => {
        try {
            // Create a unique key for this request
            const requestKey = `getDatasetMetadata:${datasetId}`;
            
            // Use the deduplication function
            return await dedupRequest(requestKey, async () => {
                console.log(`[API] Making request: ${requestKey}`);
                const response = await axios.get(`${EXPRESSION_BASE_URL}/datasets/${datasetId}/metadata`, {
                    timeout: 10000
                });
                return response.data;
            });
        } catch (error) {
            console.error('[API] Error in getDatasetMetadata:', error);
            throw error;
        }
    }
};

// Export both as named export and default export to ensure compatibility
export { api };
export default api;