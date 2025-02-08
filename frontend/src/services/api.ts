import axios from 'axios';
import { GeneExpressionData, SurvivalData } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

export const api = {
    getExpressionData: async (genes: string[], tissue: string) => {
        const response = await axios.get(`${API_BASE_URL}/expression/genes/${tissue}`, {
            params: { genes }
        });
        return response.data;
    },

    getSurvivalData: async (gene: string) => {
        const response = await axios.get(`${API_BASE_URL}/survival/${gene}`);
        return response.data;
    }
};