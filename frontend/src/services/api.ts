import axios from 'axios';

const DROPDOWN_BASE_URL = 'http://localhost:8000/api/dropdown_routes';
const API_BASE_URL = 'http://localhost:8000/api';

export const api = {
    getDropdownOptions: async () => {
        const response = await axios.get(`${DROPDOWN_BASE_URL}/dropdown/options`);
        return response.data;
    },

    searchGenes: async (query?: string) => {
        const response = await axios.get(`${DROPDOWN_BASE_URL}/dropdown/genes`, {
            params: { query }
        });
        return response.data;
    },

    searchDatasets: async (genes?: string[]) => {
        const response = await axios.get(`${DROPDOWN_BASE_URL}/dropdown/datasets`, {
            params: { genes }
        });
        return response.data;
    },

    getTissues: async (gene: string) => {
        const response = await axios.get(`${API_BASE_URL}/genes/${gene}/tissue-summary`);
        // Transform the response to match the expected format
        const tissueData = response.data?.data?.tissue_expression || [];
        return {
            tissues: tissueData.map((t: any) => t.tissue),
            categories: {}  // If you need categories, you can group tissues here
        };
    },
    
    getDatasetMetadata: async (datasetId: string) => {
        const response = await axios.get(`${API_BASE_URL}/datasets/${datasetId}/metadata`);
        return response.data;
    }
};