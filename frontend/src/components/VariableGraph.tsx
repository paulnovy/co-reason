import { useEffect, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  Panel,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { motion } from 'framer-motion';
import { Plus, Search, Bot } from 'lucide-react';
import { VariableNode, type VariableNodeData } from './VariableNode';
import type { Variable, VariableSource } from '../types';
import { useUIStore } from '../stores/uiStore';
import { cn } from '../lib/utils';

const nodeTypes = {
  variable: VariableNode,
};

interface VariableGraphProps {
  variables: Variable[];
  relationships?: { source_variable_id: number; target_variable_id: number }[];
  isLoading?: boolean;
}

const typeFilters: { type: VariableSource | 'ALL'; label: string; color: string }[] = [
  { type: 'ALL', label: 'All', color: 'bg-gray-500' },
  { type: 'HARD_DATA', label: 'Hard Data', color: 'bg-emerald-500' },
  { type: 'USER_INPUT', label: 'User Input', color: 'bg-blue-500' },
  { type: 'AI_SUGGESTION', label: 'AI', color: 'bg-amber-500' },
  { type: 'MIXED', label: 'Mixed', color: 'bg-violet-500' },
];

export function VariableGraph({ variables, relationships = [], isLoading }: VariableGraphProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<VariableNodeData>>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const {
    filterType,
    setFilterType,
    searchQuery,
    setSearchQuery,
    setCreateModalOpen,
    setAIAssistantOpen,
  } = useUIStore();

  const filteredVariables = useMemo(() => {
    return variables.filter((v) => {
      const sourceKey = String(v.source || '').toUpperCase();
      if (filterType !== 'ALL' && sourceKey !== filterType) return false;
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          v.name.toLowerCase().includes(query) ||
          v.description?.toLowerCase().includes(query)
        );
      }
      return true;
    });
  }, [variables, filterType, searchQuery]);

  // Build a simple grid layout from variables + edges from relationships
  useEffect(() => {
    const columns = 4;
    const xGap = 260;
    const yGap = 180;

    const nextNodes: Node<VariableNodeData>[] = filteredVariables.map((variable, index) => {
      const col = index % columns;
      const row = Math.floor(index / columns);
      return {
        id: String(variable.id),
        type: 'variable',
        position: { x: col * xGap + 40, y: row * yGap + 40 },
        data: {
          variable,
          hasChildren: false,
        },
      };
    });

    const nextEdges = relationships.map((rel, idx) => ({
      id: `e-${rel.source_variable_id}-${rel.target_variable_id}-${idx}`,
      source: String(rel.source_variable_id),
      target: String(rel.target_variable_id),
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#94a3b8', strokeWidth: 2 },
    }));

    setNodes(nextNodes);
    setEdges(nextEdges);
  }, [filteredVariables, relationships, setNodes, setEdges]);

  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  return (
    <div className="w-full h-full relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
        minZoom={0.1}
        maxZoom={2}
      >
        <Background color="#94a3b8" gap={20} size={1} />
        <Controls className="!bg-white dark:!bg-gray-800 !shadow-lg" />
        <MiniMap
          className="!bg-white dark:!bg-gray-800 !rounded-lg !shadow-lg"
          nodeColor={(node) => {
            const sourceRaw = (node.data?.variable as Variable)?.source;
            const source = String(sourceRaw || '').toUpperCase();
            switch (source) {
              case 'HARD_DATA': return '#10b981';
              case 'USER_INPUT': return '#3b82f6';
              case 'AI_SUGGESTION': return '#f59e0b';
              case 'MIXED': return '#8b5cf6';
              default: return '#6b7280';
            }
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
        />

        {/* Toolbar */}
        <Panel position="top-left" className="m-4">
          <motion.div
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-3 flex flex-col gap-3"
          >
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search variables..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-48 pl-9 pr-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Filter buttons */}
            <div className="flex flex-wrap gap-1">
              {typeFilters.map(({ type, label, color }) => (
                <button
                  key={type}
                  onClick={() => setFilterType(type)}
                  className={cn(
                    'px-2 py-1 text-xs rounded-md transition-all flex items-center gap-1',
                    filterType === type
                      ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                  )}
                >
                  <span className={cn('w-2 h-2 rounded-full', color)} />
                  {label}
                </button>
              ))}
            </div>
          </motion.div>
        </Panel>

        {/* Action buttons */}
        <Panel position="top-right" className="m-4">
          <motion.div
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="flex flex-col gap-2"
          >
            <button
              onClick={() => setAIAssistantOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-violet-500 to-purple-600 text-white rounded-xl shadow-lg hover:shadow-xl transition-all hover:scale-105"
            >
              <Bot className="w-4 h-4" />
              <span className="text-sm font-medium">AI Assistant</span>
            </button>
            
            <button
              onClick={() => setCreateModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-xl shadow-lg hover:shadow-xl transition-all hover:scale-105"
            >
              <Plus className="w-4 h-4" />
              <span className="text-sm font-medium">New Variable</span>
            </button>
          </motion.div>
        </Panel>
      </ReactFlow>
    </div>
  );
}
