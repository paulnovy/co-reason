import { useEffect, useMemo, useState } from 'react';
import type { Variable, VariableList } from './types';
import { VariableGraph } from './components/VariableGraph';

function App() {
  const [variables, setVariables] = useState<Variable[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchJson = async (url: string, options?: RequestInit) => {
    const resp = await fetch(url, options);
    const ct = resp.headers.get('content-type') || '';
    if (!ct.includes('application/json')) {
      const text = await resp.text().catch(() => '');
      throw new Error(
        `Expected JSON from ${url} (status ${resp.status}), got content-type=${ct}. ` +
          `Body starts with: ${JSON.stringify(text.slice(0, 120))}`
      );
    }
    const data = await resp.json();
    if (!resp.ok) throw new Error(JSON.stringify(data));
    return data;
  };

  useEffect(() => {
    (async () => {
      try {
        const data = (await fetchJson('/variables')) as VariableList;
        setVariables(data.items || []);
      } catch (e: any) {
        setError(e?.message || 'Failed to load');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const useGraph = import.meta.env.VITE_USE_GRAPH === 'true';

  // DOE UI (baseline view)
  const [doeOpen, setDoeOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Record<number, boolean>>({});
  const [method, setMethod] = useState<'sobol' | 'lhs'>('sobol');
  const [nPoints, setNPoints] = useState(20);
  const [doeResult, setDoeResult] = useState<any>(null);
  const [doeError, setDoeError] = useState<string | null>(null);

  // Optimize UI (stub)
  const [optimizeOpen, setOptimizeOpen] = useState(false);
  const [nIter, setNIter] = useState(30);
  const [optSeed, setOptSeed] = useState(1);
  const [optimizeResult, setOptimizeResult] = useState<any>(null);
  const [optimizeError, setOptimizeError] = useState<string | null>(null);

  const idToName = useMemo(() => Object.fromEntries(variables.map(v => [v.id, v.name])), [variables]);
  const idToVar = useMemo(() => Object.fromEntries(variables.map(v => [v.id, v])), [variables]);

  const sourceBadge = (source?: string) => {
    const s = String(source || '').toUpperCase();
    const cfg: Record<string, { label: string; dot: string; text: string }> = {
      HARD_DATA: { label: 'HARD_DATA', dot: 'bg-emerald-500', text: 'text-emerald-700' },
      USER_INPUT: { label: 'USER_INPUT', dot: 'bg-blue-500', text: 'text-blue-700' },
      AI_SUGGESTION: { label: 'AI_SUGGESTION', dot: 'bg-amber-500', text: 'text-amber-700' },
      MIXED: { label: 'MIXED', dot: 'bg-violet-500', text: 'text-violet-700' },
    };
    const c = cfg[s] || { label: s || 'UNKNOWN', dot: 'bg-gray-400', text: 'text-gray-600' };
    return (
      <span className={"inline-flex items-center gap-1 text-[10px] font-medium " + c.text}>
        <span className={"inline-block w-2 h-2 rounded-full " + c.dot} />
        {c.label}
      </span>
    );
  };

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
          <div className="space-y-6">
            <div className="flex items-center gap-3 flex-wrap">
              <button
                className="px-4 py-2 bg-gray-900 text-white rounded"
                onClick={() => setDoeOpen((v) => !v)}
              >
                Run DOE
              </button>
              <div className="text-xs text-gray-500">Endpoint: POST /experiments/doe</div>

              <button
                className="px-4 py-2 bg-purple-700 text-white rounded"
                onClick={() => setOptimizeOpen((v) => !v)}
              >
                Run Optimize
              </button>
              <div className="text-xs text-gray-500">Endpoint: POST /experiments/optimize</div>
            </div>

            {doeOpen && (
              <div className="p-4 bg-white rounded border border-gray-200 space-y-3">
                <div className="text-sm font-medium">DOE settings</div>

                <div className="flex gap-3 items-center">
                  <label className="text-sm">Method</label>
                  <select
                    className="border rounded px-2 py-1"
                    value={method}
                    onChange={(e) => setMethod(e.target.value as any)}
                  >
                    <option value="sobol">sobol</option>
                    <option value="lhs">lhs</option>
                  </select>

                  <label className="text-sm ml-4">Points</label>
                  <input
                    className="border rounded px-2 py-1 w-24"
                    type="number"
                    min={1}
                    max={5000}
                    value={nPoints}
                    onChange={(e) => setNPoints(parseInt(e.target.value || '1', 10))}
                  />
                </div>

                <div>
                  <div className="text-sm mb-2">Variables</div>
                  <div className="grid grid-cols-2 gap-2">
                    {variables.map((v) => (
                      <label key={v.id} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={!!selectedIds[v.id]}
                          onChange={(e) => setSelectedIds((prev) => ({ ...prev, [v.id]: e.target.checked }))}
                        />
                        <span className="flex items-center gap-2">
                          <span>{v.name}</span>
                          {sourceBadge(v.source)}
                        </span>
                        <span className="text-xs text-gray-400">[{v.min_value ?? '—'}..{v.max_value ?? '—'}]</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    className="px-4 py-2 bg-blue-600 text-white rounded"
                    onClick={async () => {
                      setDoeError(null);
                      setDoeResult(null);
                      const variable_ids = Object.entries(selectedIds)
                        .filter(([, v]) => v)
                        .map(([k]) => parseInt(k, 10));
                      try {
                        const data = await fetchJson('/experiments/doe', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ variable_ids, n_points: nPoints, method }),
                        });
                        setDoeResult(data);
                      } catch (err: any) {
                        setDoeError(err?.message || String(err));
                      }
                    }}
                  >
                    Generate
                  </button>

                  <button className="px-4 py-2 border rounded" onClick={() => { setDoeOpen(false); setDoeError(null); setDoeResult(null); }}>
                    Close
                  </button>
                </div>

                {doeError && <pre className="text-xs text-red-600 whitespace-pre-wrap">{doeError}</pre>}

                {doeResult && (
                  <div className="pt-2 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-medium">DOE result</div>
                      <button
                        className="px-3 py-1 bg-emerald-600 text-white rounded text-xs"
                        onClick={async () => {
                          try {
                            const data = await fetchJson('/experiments/doe/insight', {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({
                                variable_ids: doeResult.variable_ids,
                                points: doeResult.points,
                              }),
                            });
                            setDoeResult((prev: any) => ({ ...prev, insight: data }));
                          } catch (err: any) {
                            setDoeError(err?.message || String(err));
                          }
                        }}
                      >
                        Generate insight
                      </button>
                    </div>

                    <div className="overflow-auto border rounded">
                      <table className="min-w-full text-xs">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="text-left p-2">#</th>
                            {(doeResult.variable_ids || []).map((vid: number) => (
                              <th key={vid} className="text-left p-2">
                                <div className="flex items-center gap-2">
                                  <span>{idToName[vid] || String(vid)}</span>
                                  {sourceBadge(idToVar[vid]?.source)}
                                </div>
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {(doeResult.points || []).map((p: any, idx: number) => (
                            <tr key={idx} className="border-t">
                              <td className="p-2">{idx + 1}</td>
                              {(doeResult.variable_ids || []).map((vid: number) => (
                                <td key={vid} className="p-2">{Number(p[String(vid)]).toFixed(4)}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {doeResult.insight && (
                      <div className="p-3 bg-gray-50 border rounded">
                        <div className="flex items-center justify-between gap-2">
                          <div className="text-sm font-medium">{doeResult.insight.summary}</div>
                          <div className="flex flex-wrap gap-2">
                            {(doeResult.variable_ids || []).map((vid: number) => (
                              <span key={vid} className="text-[10px] text-gray-500">
                                {idToName[vid] || String(vid)} {sourceBadge(idToVar[vid]?.source)}
                              </span>
                            ))}
                          </div>
                        </div>
                        <ul className="list-disc pl-5 mt-2 text-xs text-gray-700 space-y-1">
                          {(doeResult.insight.bullets || []).map((b: string, i: number) => (
                            <li key={i}>{b}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {optimizeOpen && (
              <div className="p-4 bg-white rounded border border-gray-200 space-y-3">
                <div className="text-sm font-medium">Optimize (stub)</div>

                <div className="flex gap-3 items-center flex-wrap">
                  <label className="text-sm">Iterations</label>
                  <input
                    className="border rounded px-2 py-1 w-28"
                    type="number"
                    min={1}
                    max={5000}
                    value={nIter}
                    onChange={(e) => setNIter(parseInt(e.target.value || '1', 10))}
                  />

                  <label className="text-sm ml-4">Seed</label>
                  <input
                    className="border rounded px-2 py-1 w-28"
                    type="number"
                    value={optSeed}
                    onChange={(e) => setOptSeed(parseInt(e.target.value || '0', 10))}
                  />

                  <span className="text-xs text-gray-500">(random within domain; placeholder objective)</span>
                </div>

                <div>
                  <div className="text-sm mb-2">Variables (reuse DOE selection)</div>
                  <div className="flex items-center gap-3 flex-wrap">
                    <div className="text-xs text-gray-500">
                      Wybrane: {Object.entries(selectedIds).filter(([, v]) => v).length}
                    </div>
                    <button
                      className="px-3 py-1 border rounded text-xs"
                      onClick={() => setSelectedIds({})}
                    >
                      Clear selection
                    </button>
                    <button
                      className="px-3 py-1 border rounded text-xs"
                      onClick={() => {
                        const next: Record<number, boolean> = {};
                        for (const v of variables) next[v.id] = true;
                        setSelectedIds(next);
                      }}
                    >
                      Select all
                    </button>
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    className="px-4 py-2 bg-purple-700 text-white rounded"
                    onClick={async () => {
                      setOptimizeError(null);
                      setOptimizeResult(null);
                      const variable_ids = Object.entries(selectedIds)
                        .filter(([, v]) => v)
                        .map(([k]) => parseInt(k, 10));
                      try {
                        const data = await fetchJson('/experiments/optimize', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ variable_ids, n_iter: nIter, method: 'random', seed: optSeed }),
                        });
                        setOptimizeResult(data);
                      } catch (err: any) {
                        setOptimizeError(err?.message || String(err));
                      }
                    }}
                  >
                    Run
                  </button>

                  <button className="px-4 py-2 border rounded" onClick={() => { setOptimizeOpen(false); setOptimizeError(null); setOptimizeResult(null); }}>
                    Close
                  </button>
                </div>

                {optimizeError && <pre className="text-xs text-red-600 whitespace-pre-wrap">{optimizeError}</pre>}

                {optimizeResult && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <div className="text-sm font-medium">Best point</div>
                      <div className="text-xs text-gray-500">
                        best_score: {Number(optimizeResult?.meta?.best_score ?? NaN).toFixed(4)}
                      </div>
                    </div>
                    <div className="overflow-auto border rounded">
                      <table className="min-w-full text-xs">
                        <thead className="bg-gray-50">
                          <tr>
                            {(optimizeResult.variable_ids || []).map((vid: number) => (
                              <th key={vid} className="text-left p-2">
                                <div className="flex items-center gap-2">
                                  <span>{idToName[vid] || String(vid)}</span>
                                  {sourceBadge(idToVar[vid]?.source)}
                                </div>
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          <tr className="border-t">
                            {(optimizeResult.variable_ids || []).map((vid: number) => (
                              <td key={vid} className="p-2">{Number(optimizeResult.best_point?.[String(vid)]).toFixed(4)}</td>
                            ))}
                          </tr>
                        </tbody>
                      </table>
                    </div>

                    <div className="text-sm font-medium">History (first 10)</div>
                    <div className="overflow-auto border rounded">
                      <table className="min-w-full text-xs">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="text-left p-2">#</th>
                            {(optimizeResult.variable_ids || []).map((vid: number) => (
                              <th key={vid} className="text-left p-2">{idToName[vid] || String(vid)}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {(optimizeResult.history || []).slice(0, 10).map((p: any, idx: number) => (
                            <tr key={idx} className="border-t">
                              <td className="p-2">{idx + 1}</td>
                              {(optimizeResult.variable_ids || []).map((vid: number) => (
                                <td key={vid} className="p-2">{Number(p[String(vid)]).toFixed(4)}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}

            <ul className="space-y-2">
              {variables.map((v) => (
                <li key={v.id} className="p-3 bg-white rounded border border-gray-200">
                  <div className="font-medium flex items-center justify-between gap-2">
                    <span>{v.name}</span>
                    {sourceBadge(v.source)}
                  </div>
                  <div className="text-xs text-gray-500">{String(v.variable_type)}</div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
