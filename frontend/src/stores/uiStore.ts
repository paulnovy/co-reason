import { create } from 'zustand';
import { AIAssistantMessage, VariableSource } from '../types';

interface UIState {
  // Selected variable
  selectedVariableId: string | null;
  setSelectedVariableId: (id: string | null) => void;

  // Detail panel
  isDetailPanelOpen: boolean;
  setDetailPanelOpen: (open: boolean) => void;

  // Create modal
  isCreateModalOpen: boolean;
  setCreateModalOpen: (open: boolean) => void;
  createModalParentId: string | null;
  setCreateModalParentId: (id: string | null) => void;

  // AI Assistant
  isAIAssistantOpen: boolean;
  setAIAssistantOpen: (open: boolean) => void;
  aiMessages: AIAssistantMessage[];
  addAIMessage: (message: AIAssistantMessage) => void;
  clearAIMessages: () => void;

  // Graph view
  expandedNodes: Set<string>;
  toggleNodeExpanded: (nodeId: string) => void;
  setNodeExpanded: (nodeId: string, expanded: boolean) => void;

  // Filter
  filterType: VariableSource | 'ALL';
  setFilterType: (type: VariableSource | 'ALL') => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
}

export const useUIStore = create<UIState>((set, get) => ({
  // Selected variable
  selectedVariableId: null,
  setSelectedVariableId: (id) => set({ selectedVariableId: id }),

  // Detail panel
  isDetailPanelOpen: false,
  setDetailPanelOpen: (open) => set({ isDetailPanelOpen: open }),

  // Create modal
  isCreateModalOpen: false,
  setCreateModalOpen: (open) => set({ isCreateModalOpen: open }),
  createModalParentId: null,
  setCreateModalParentId: (id) => set({ createModalParentId: id }),

  // AI Assistant
  isAIAssistantOpen: false,
  setAIAssistantOpen: (open) => set({ isAIAssistantOpen: open }),
  aiMessages: [],
  addAIMessage: (message) =>
    set((state) => ({
      aiMessages: [...state.aiMessages, message],
    })),
  clearAIMessages: () => set({ aiMessages: [] }),

  // Graph view
  expandedNodes: new Set(),
  toggleNodeExpanded: (nodeId) =>
    set((state) => {
      const newExpanded = new Set(state.expandedNodes);
      if (newExpanded.has(nodeId)) {
        newExpanded.delete(nodeId);
      } else {
        newExpanded.add(nodeId);
      }
      return { expandedNodes: newExpanded };
    }),
  setNodeExpanded: (nodeId, expanded) =>
    set((state) => {
      const newExpanded = new Set(state.expandedNodes);
      if (expanded) {
        newExpanded.add(nodeId);
      } else {
        newExpanded.delete(nodeId);
      }
      return { expandedNodes: newExpanded };
    }),

  // Filter
  filterType: 'ALL',
  setFilterType: (type) => set({ filterType: type }),
  searchQuery: '',
  setSearchQuery: (query) => set({ searchQuery: query }),
}));
