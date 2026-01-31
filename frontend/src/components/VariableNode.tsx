import { memo } from 'react';
import type React from 'react';
import { Handle, Position, type Node, type NodeProps } from '@xyflow/react';
import { motion } from 'framer-motion';
import { ChevronRight, ChevronDown, Database, User, Bot, Layers } from 'lucide-react';
import type { Variable, VariableSource, VariableCategory } from '../types';
import { cn } from '../lib/utils';
import { useUIStore } from '../stores/uiStore';

export interface VariableNodeData extends Record<string, unknown> {
  variable: Variable;
  hasChildren: boolean;
}

export type VariableNodeType = Node<VariableNodeData>;

const sourceConfig: Record<VariableSource, { color: string; icon: React.ReactNode; label: string }> = {
  HARD_DATA: {
    color: 'bg-emerald-500',
    icon: <Database className="w-3 h-3" />,
    label: 'Hard Data',
  },
  USER_INPUT: {
    color: 'bg-blue-500',
    icon: <User className="w-3 h-3" />,
    label: 'User Input',
  },
  AI_SUGGESTION: {
    color: 'bg-amber-500',
    icon: <Bot className="w-3 h-3" />,
    label: 'AI Suggestion',
  },
  MIXED: {
    color: 'bg-violet-500',
    icon: <Layers className="w-3 h-3" />,
    label: 'Mixed',
  },
};

const categoryLabel: Record<VariableCategory, string> = {
  PHYSICAL_CONSTANT: 'Physical Constant',
  ENGINEERING_PROCESS_METRIC: 'Process Metric',
  BUSINESS_KPI: 'Business KPI',
  SUBJECTIVE_FACTOR: 'Subjective Factor',
};

function VariableNodeComponent({ data, id }: NodeProps<VariableNodeType>) {
  const { variable, hasChildren } = data;
  const { expandedNodes, toggleNodeExpanded, setSelectedVariableId, setDetailPanelOpen } = useUIStore();
  
  const isExpanded = expandedNodes.has(id);
  const sourceKey = String(variable.source || '').toUpperCase() as VariableSource;
  const config = sourceConfig[sourceKey] || sourceConfig.HARD_DATA;

  const handleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    toggleNodeExpanded(id);
  };

  const handleClick = () => {
    setSelectedVariableId(String(variable.id));
    setDetailPanelOpen(true);
  };

  const formatRange = () => {
    if (variable.min_value !== undefined && variable.max_value !== undefined && variable.min_value !== null && variable.max_value !== null) {
      return `[${variable.min_value}${variable.unit || ''} - ${variable.max_value}${variable.unit || ''}]`;
    }
    if (variable.min_value !== undefined && variable.min_value !== null) {
      return `≥ ${variable.min_value}${variable.unit || ''}`;
    }
    if (variable.max_value !== undefined && variable.max_value !== null) {
      return `≤ ${variable.max_value}${variable.unit || ''}`;
    }
    return null;
  };

  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      whileHover={{ scale: 1.02 }}
      className={cn(
        'relative min-w-[180px] max-w-[240px] rounded-xl overflow-hidden',
        'bg-white dark:bg-gray-800 shadow-lg border-2 transition-all cursor-pointer',
        'hover:shadow-xl'
      )}
      style={{
        borderColor: config.color.replace('bg-', '').replace('500', '') === 'emerald' ? '#10b981' :
                     config.color.replace('bg-', '').replace('500', '') === 'blue' ? '#3b82f6' :
                     config.color.replace('bg-', '').replace('500', '') === 'amber' ? '#f59e0b' : '#8b5cf6'
      }}
      onClick={handleClick}
    >
      {/* Type indicator bar */}
      <div className={cn('h-1.5 w-full', config.color)} />
      
      <div className="p-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-1.5 min-w-0">
            <span className={cn('p-1 rounded text-white', config.color)}>
              {config.icon}
            </span>
            <span className="text-[10px] uppercase tracking-wider text-gray-500 dark:text-gray-400 font-medium">
              {config.label}
            </span>
          </div>
          
          {hasChildren && (
            <button
              onClick={handleExpand}
              className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-gray-500" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-500" />
              )}
            </button>
          )}
        </div>

        {/* Variable name */}
        <h3 className="mt-2 font-semibold text-sm text-gray-900 dark:text-gray-100 truncate">
          {variable.name}
        </h3>

        {/* Description */}
        {variable.description && (
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
            {variable.description}
          </p>
        )}

        {/* Category */}
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          {categoryLabel[String(variable.variable_type || '').toUpperCase() as VariableCategory] || String(variable.variable_type)}
        </div>

        {/* Range */}
        {formatRange() && (
          <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {formatRange()}
          </div>
        )}

        {/* Confidence */}
        <div className="mt-2 text-xs text-gray-400 dark:text-gray-500">
          Confidence: {Math.round(variable.confidence * 100)}%
        </div>
      </div>

      {/* Connection handles */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-gray-400 !border-2 !border-white dark:!border-gray-800"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 !bg-gray-400 !border-2 !border-white dark:!border-gray-800"
      />
    </motion.div>
  );
}

export const VariableNode = memo(VariableNodeComponent);
