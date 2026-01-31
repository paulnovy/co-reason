// @ts-nocheck
import { motion, AnimatePresence } from 'framer-motion';
import type React from 'react';
import { X, Database, User, Bot, Layers, Calendar, Shield } from 'lucide-react';
import { useVariable } from '../hooks/useVariables';
import { useUIStore } from '../stores/uiStore';
import { cn } from '../lib/utils';
import type { VariableSource, VariableCategory, Variable } from '../types';

const sourceConfig: Record<VariableSource, { color: string; bgColor: string; icon: React.ReactNode; label: string }> = {
  HARD_DATA: {
    color: 'text-emerald-600',
    bgColor: 'bg-emerald-50',
    icon: <Database className="w-4 h-4" />,
    label: 'Hard Data',
  },
  USER_INPUT: {
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    icon: <User className="w-4 h-4" />,
    label: 'User Input',
  },
  AI_SUGGESTION: {
    color: 'text-amber-600',
    bgColor: 'bg-amber-50',
    icon: <Bot className="w-4 h-4" />,
    label: 'AI Suggestion',
  },
  MIXED: {
    color: 'text-violet-600',
    bgColor: 'bg-violet-50',
    icon: <Layers className="w-4 h-4" />,
    label: 'Mixed',
  },
};

const categoryLabel: Record<VariableCategory, string> = {
  PHYSICAL_CONSTANT: 'Physical Constant',
  ENGINEERING_PROCESS_METRIC: 'Process Metric',
  BUSINESS_KPI: 'Business KPI',
  SUBJECTIVE_FACTOR: 'Subjective Factor',
};

function RangeRow({ variable }: { variable: Variable }) {
  if (variable.min_value == null && variable.max_value == null) return null;
  return (
    <div>
      <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
        Valid Range
      </label>
      <div className="mt-1 flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">
          {variable.min_value ?? '—'}
        </span>
        <span>to</span>
        <span className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">
          {variable.max_value ?? '—'}
        </span>
        {variable.unit && <span>{variable.unit}</span>}
      </div>
    </div>
  );
}

export function VariableDetailPanel() {
  const { isDetailPanelOpen, setDetailPanelOpen, selectedVariableId } = useUIStore();
  const { data: variable, isLoading } = useVariable(selectedVariableId || '');

  if (!isDetailPanelOpen || !selectedVariableId) return null;

  const sourceKey = variable ? String(variable.source || '').toUpperCase() as VariableSource : null;
  const config = variable ? (sourceConfig[sourceKey as VariableSource] || sourceConfig.HARD_DATA) : null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ x: 400, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: 400, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="fixed right-0 top-0 h-full w-96 bg-white dark:bg-gray-900 shadow-2xl z-50 overflow-hidden flex flex-col"
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Variable Details
          </h2>
          <button
            onClick={() => setDetailPanelOpen(false)}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
            </div>
          ) : variable ? (
            <div className="space-y-6">
              {config && (
                <div className={cn('inline-flex items-center gap-2 px-3 py-1.5 rounded-lg', config.bgColor)}>
                  <span className={config.color}>{config.icon}</span>
                  <span className={cn('text-sm font-medium', config.color)}>{config.label}</span>
                </div>
              )}

              <div>
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Name</label>
                <h3 className="mt-1 text-xl font-bold text-gray-900 dark:text-gray-100">{variable.name}</h3>
              </div>

              {variable.description && (
                <div>
                  <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Description</label>
                  <p className="mt-1 text-sm text-gray-700 dark:text-gray-300">{variable.description}</p>
                </div>
              )}

              <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4">
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">Category</label>
                <div className="mt-2 text-sm text-gray-700 dark:text-gray-300">
                  {categoryLabel[String(variable.variable_type || '').toUpperCase() as VariableCategory] || String(variable.variable_type)}
                </div>
              </div>

              <RangeRow variable={variable} />

              <div className="border-t border-gray-200 dark:border-gray-800 pt-4">
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center gap-2">
                  <Shield className="w-3 h-3" />
                  Provenance
                </label>
                <div className="mt-2 text-sm text-gray-700 dark:text-gray-300">
                  Source: <span className="font-medium">{variable.source}</span> • Confidence: {Math.round(variable.confidence * 100)}%
                </div>
                {variable.source_description && (
                  <div className="mt-1 text-xs text-gray-500">{variable.source_description}</div>
                )}
              </div>

              <div className="border-t border-gray-200 dark:border-gray-800 pt-4 text-xs text-gray-400">
                <div className="flex items-center gap-2">
                  <Calendar className="w-3 h-3" />
                  <span>Created: {new Date(variable.created_at).toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <Calendar className="w-3 h-3" />
                  <span>Updated: {new Date(variable.updated_at).toLocaleString()}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">Variable not found</div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
