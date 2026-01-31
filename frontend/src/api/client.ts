import type { Variable, VariableList, CreateVariableRequest, UpdateVariableRequest } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

class APIError extends Error {
  status: number;
  data?: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

async function fetchWithError<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new APIError(
      errorData?.message || `HTTP error! status: ${response.status}`,
      response.status,
      errorData
    );
  }

  return response.json();
}

export const apiClient = {
  // Variables
  getVariables: (params?: { skip?: number; limit?: number; include_inactive?: boolean }): Promise<VariableList> => {
    const qs = new URLSearchParams();
    if (params?.skip !== undefined) qs.set('skip', String(params.skip));
    if (params?.limit !== undefined) qs.set('limit', String(params.limit));
    if (params?.include_inactive !== undefined) qs.set('include_inactive', String(params.include_inactive));
    const query = qs.toString();
    return fetchWithError(`/variables${query ? `?${query}` : ''}`);
  },

  getVariable: (id: number | string): Promise<Variable> =>
    fetchWithError(`/variables/${id}`),

  createVariable: (data: CreateVariableRequest): Promise<Variable> =>
    fetchWithError('/variables', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateVariable: (id: number | string, data: UpdateVariableRequest): Promise<Variable> =>
    fetchWithError(`/variables/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  deleteVariable: (id: number | string): Promise<void> =>
    fetchWithError(`/variables/${id}`, {
      method: 'DELETE',
    }),
};

export { APIError };
