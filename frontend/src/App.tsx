import { useEffect, useState } from 'react';
import type { Variable, VariableList } from './types';
import { VariableGraph } from './components/VariableGraph';

function App() {
  const [variables, setVariables] = useState<Variable[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/variables')
      .then((r) => r.json())
      .then((data: VariableList) => {
        setVariables(data.items || []);
        setLoading(false);
      })
      .catch((e) => {
        setError(e?.message || 'Failed to load');
        setLoading(false);
      });
  }, []);

  const useGraph = import.meta.env.VITE_USE_GRAPH === 'true';

  return (
    <div className="w-screen h-screen bg-gray-50 text-gray-900">
      <header className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Product Optimizer</h1>
          <p className="text-sm text-gray-500">
            {useGraph ? 'ReactFlow grid (diagnostic)' : 'Variables list (stable)'}
          </p>
        </div>
        <div className="text-xs text-gray-400">API: /variables → 8000 (proxy)</div>
      </header>
      <main className={useGraph ? 'w-full h-[calc(100vh-64px)]' : 'p-6'}>
        {error ? (
          <div className="text-red-600">{error}</div>
        ) : loading ? (
          <div>Loading…</div>
        ) : useGraph ? (
          <VariableGraph variables={variables} isLoading={loading} />
        ) : (
          <ul className="space-y-2">
            {variables.map((v) => (
              <li key={v.id} className="p-3 bg-white rounded border border-gray-200">
                <div className="font-medium">{v.name}</div>
                <div className="text-xs text-gray-500">{String(v.variable_type)} • {String(v.source)}</div>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
}

export default App;
