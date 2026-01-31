import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { Variable, VariableList, CreateVariableRequest, UpdateVariableRequest } from '../types';

const VARIABLES_KEY = 'variables';

export function useVariables() {
  return useQuery<VariableList>({
    queryKey: [VARIABLES_KEY],
    queryFn: () => apiClient.getVariables(),
  });
}

export function useVariable(id: number | string) {
  return useQuery({
    queryKey: [VARIABLES_KEY, id],
    queryFn: () => apiClient.getVariable(id),
    enabled: !!id,
  });
}

export function useVariableTree(rootId?: string) {
  return useQuery({
    queryKey: [VARIABLES_KEY, 'tree', rootId],
    queryFn: () => apiClient.getVariableTree(rootId),
    enabled: rootId !== undefined,
  });
}

export function useCreateVariable() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateVariableRequest) => apiClient.createVariable(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [VARIABLES_KEY] });
    },
  });
}

export function useUpdateVariable() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number | string; data: UpdateVariableRequest }) =>
      apiClient.updateVariable(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [VARIABLES_KEY] });
      // variables is the response, but keep it safe
      if ((variables as unknown as { id?: number | string })?.id) {
        queryClient.invalidateQueries({ queryKey: [VARIABLES_KEY, (variables as { id: number | string }).id] });
      }
    },
  });
}

export function useDeleteVariable() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiClient.deleteVariable(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [VARIABLES_KEY] });
    },
  });
}

// AI Assistant hooks
export function useAIChat() {
  return useMutation({
    mutationFn: ({ message, context }: { message: string; context?: { variableIds?: string[] } }) =>
      apiClient.sendAIMessage(message, context),
  });
}

export function useAISuggestions(variableId: string) {
  return useQuery({
    queryKey: ['ai', 'suggestions', variableId],
    queryFn: () => apiClient.getAISuggestions(variableId),
    enabled: !!variableId,
  });
}
