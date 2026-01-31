export type VariableCategory =
  | 'PHYSICAL_CONSTANT'
  | 'ENGINEERING_PROCESS_METRIC'
  | 'BUSINESS_KPI'
  | 'SUBJECTIVE_FACTOR';

export type VariableSource = 'HARD_DATA' | 'USER_INPUT' | 'AI_SUGGESTION' | 'MIXED';

export interface Variable {
  id: number;
  name: string;
  description?: string | null;
  symbol?: string | null;
  variable_type: VariableCategory;
  min_value?: number | null;
  max_value?: number | null;
  unit?: string | null;
  source: VariableSource;
  confidence: number;
  source_description?: string | null;
  layer_level: number;
  parent_variable_id?: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface VariableList {
  items: Variable[];
  total: number;
  skip: number;
  limit: number;
}

export interface CreateVariableRequest {
  name: string;
  description?: string | null;
  symbol?: string | null;
  variable_type: VariableCategory;
  min_value?: number | null;
  max_value?: number | null;
  unit?: string | null;
  source: VariableSource;
  confidence?: number;
  source_description?: string | null;
  layer_level?: number;
  parent_variable_id?: number | null;
}

export interface UpdateVariableRequest {
  name?: string;
  description?: string | null;
  symbol?: string | null;
  variable_type?: VariableCategory;
  min_value?: number | null;
  max_value?: number | null;
  unit?: string | null;
  source?: VariableSource;
  confidence?: number;
  source_description?: string | null;
  layer_level?: number;
  parent_variable_id?: number | null;
  is_active?: boolean;
}

export interface Relationship {
  id: number;
  source_variable_id: number;
  target_variable_id: number;
  relationship_type: 'DRIVES' | 'INFLUENCES' | 'CORRELATES_WITH';
  direction: 'POSITIVE' | 'NEGATIVE' | 'UNKNOWN';
  shape: 'LINEAR' | 'NONLINEAR' | 'THRESHOLD' | 'UNKNOWN';
  confidence: number;
  provenance_source?: string | null;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RelationshipList {
  items: Relationship[];
  total: number;
  skip: number;
  limit: number;
}

export interface AIAssistantMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  suggestions?: VariableSuggestion[];
}

export interface VariableSuggestion {
  variableName: string;
  suggestedValue: unknown;
  reasoning: string;
  confidence: number;
}
