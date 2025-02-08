export interface GeneExpressionData {
    gene: string;
    expression: number;
    tissue: string;
}

export interface SurvivalData {
    time: number[];
    event: number[];
    expression: number[];
}

export interface ApiResponse<T> {
    data: T;
    status: string;
    error?: string;
}