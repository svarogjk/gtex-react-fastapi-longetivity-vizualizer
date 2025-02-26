export interface GeneExpressionData {
    gene: string;
    expression: number;
    tissue: string;
}


export interface ApiResponse<T> {
    data: T;
    status: string;
    error?: string;
}