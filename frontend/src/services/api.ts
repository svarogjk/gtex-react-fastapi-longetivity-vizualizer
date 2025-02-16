import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/dropdown_routes';

export const api = {
    getDropdownOptions: async () => {
        const response = await axios.get(`${API_BASE_URL}/dropdown/options`);
        return response.data;
    },

    searchGenes: async (query?: string) => {
        const response = await axios.get(`${API_BASE_URL}/dropdown/genes`, {
            params: { query }
        });
        return response.data;
    },

    searchDatasets: async (genes?: string[]) => {
        const response = await axios.get(`${API_BASE_URL}/dropdown/datasets`, {
            params: { genes }
        });
        return response.data;
    }
};