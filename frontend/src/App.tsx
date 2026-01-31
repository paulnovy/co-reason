import { useEffect, useMemo, useState } from 'react';
import type { Variable, VariableList } from './types';
import { VariableGraph } from './components/VariableGraph';

function App() {
  const [variables, setVariables] = useState<Variable[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Runs history (persisted on backend)
  const [runs, setRuns] = useState<any[]>([]);
  const [runsError, setRunsError] = useState<string | null>(null);

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

  const refreshRuns = async () => {
    try {
      setRunsError(null);
      const data = await fetchJson('/runs');
      setRuns(data.items || []);
    } catch (e: any) {
      setRunsError(e?.message || String(e));
    }
  };

  const persistRun = async (run_type: 'doe' | 'optimize', title: string, request_json: any, response_json: any) => {
    try {
      await fetchJson('/runs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_type, title, request_json, response_json }),
      });
      // fire-and-forget refresh
      refreshRuns();
    } catch {
      // Ignore persistence errors in UI flow
    }
  };

  useEffect(() => {
    (async () => {
      try {
        const data = (await fetchJson('/variables')) as VariableList;
        setVariables(data.items || []);
        await refreshRuns();
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
  const [optMethod, setOptMethod] = useState<'random'>('random');
  const [optSeedRaw, setOptSeedRaw] = useState<string>('1');
  const [objectiveKind, setObjectiveKind] = useState<'maximize_variable' | 'minimize_variable'>('maximize_variable');
  const [objectiveVarId, setObjectiveVarId] = useState<number>(1);

  useEffect(() => {
    if (variables.length > 0) {
      setObjectiveVarId((prev) => {
        if (variables.some((v) => v.id === prev)) return prev;
        return variables[0].id;
      });
    }
  }, [variables]);
  const [optimizeResult, setOptimizeResult] = useState<any>(null);
  const [optimizeError, setOptimizeError] = useState<string | null>(null);
  const [useDoeAsInitial, setUseDoeAsInitial] = useState(true);
  const [maxInitialPoints, setMaxInitialPoints] = useState(50);

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
                      if (variable_ids.length === 0) {
                        setDoeError('Select at least one variable.');
                        return;
                      }
                      try {
                        const data = await fetchJson('/experiments/doe', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ variable_ids, n_points: nPoints, method }),
                        });
                        setDoeResult(data);
                        persistRun(
                          'doe',
                          `DOE (${method}, n=${nPoints})`,
                          { variable_ids, n_points: nPoints, method },
                          data
                        );
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
                  <label className="text-sm">Objective</label>
                  <select
                    className="border rounded px-2 py-1"
                    value={objectiveKind}
                    onChange={(e) => setObjectiveKind(e.target.value as any)}
                  >
                    <option value="maximize_variable">maximize</option>
                    <option value="minimize_variable">minimize</option>
                  </select>

                  <select
                    className="border rounded px-2 py-1"
                    value={objectiveVarId}
                    onChange={(e) => setObjectiveVarId(parseInt(e.target.value, 10))}
                  >
                    {variables.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.name} (id={v.id})
                      </option>
                    ))}
                  </select>

                  <label className="text-sm ml-4">Iterations</label>
                  <input
                    className="border rounded px-2 py-1 w-28"
                    type="number"
                    min={1}
                    max={5000}
                    value={nIter}
                    onChange={(e) => setNIter(parseInt(e.target.value || '1', 10))}
                  />

                  <label className="text-sm ml-4">Method</label>
                  <select
                    className="border rounded px-2 py-1"
                    value={optMethod}
                    onChange={(e) => setOptMethod(e.target.value as any)}
                  >
                    <option value="random">random</option>
                  </select>

                  <label className="text-sm ml-4">Seed</label>
                  <input
                    className="border rounded px-2 py-1 w-28"
                    type="text"
                    inputMode="numeric"
                    placeholder="(auto)"
                    value={optSeedRaw}
                    onChange={(e) => setOptSeedRaw(e.target.value)}
                  />

                  <span className="text-xs text-gray-500">(random within domain; placeholder objective)</span>
                </div>

                <div>
                  <div className="text-sm mb-2 flex items-center justify-between gap-2">
                    <span>Variables (reuse DOE selection)</span>
                    <button
                      className="px-3 py-1 border rounded text-xs"
                      onClick={() => {
                        if (!doeResult?.points || !doeResult?.variable_ids) {
                          setOptimizeError('No DOE points available. Run DOE first.');
                          return;
                        }
                        // Auto-select DOE variables
                        const next: Record<number, boolean> = {};
                        for (const vid of doeResult.variable_ids) next[vid] = true;
                        setSelectedIds(next);

                        // Ensure objective variable is included
                        setObjectiveVarId((prev) => {
                          if (doeResult.variable_ids.includes(prev)) return prev;
                          return doeResult.variable_ids[0] ?? prev;
                        });
                      }}
                    >
                      Use DOE vars
                    </button>
                  </div>

                  <div className="flex items-center gap-4 flex-wrap">
                    <label className="flex items-center gap-2 text-xs text-gray-700">
                      <input
                        type="checkbox"
                        checked={useDoeAsInitial}
                        onChange={(e) => setUseDoeAsInitial(e.target.checked)}
                      />
                      Seed with DOE points
                      <span className="text-gray-500">
                        ({doeResult?.points ? doeResult.points.length : 0})
                      </span>
                    </label>

                    <label className="flex items-center gap-2 text-xs text-gray-700">
                      Max initial points
                      <input
                        className="border rounded px-2 py-1 w-20 text-xs"
                        type="number"
                        min={0}
                        max={5000}
                        value={maxInitialPoints}
                        onChange={(e) => setMaxInitialPoints(parseInt(e.target.value || '0', 10))}
                      />
                    </label>
                  </div>
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
                      if (variable_ids.length === 0) {
                        setOptimizeError('Select at least one variable.');
                        return;
                      }
                      if (!variable_ids.includes(objectiveVarId)) {
                        setOptimizeError('Objective variable must be included in selected variables.');
                        return;
                      }
                      try {
                        const seed = optSeedRaw.trim() === '' ? null : parseInt(optSeedRaw, 10);
                        const doeInitial = (doeResult?.points && doeResult?.variable_ids)
                          ? doeResult.points.map((p: any) => {
                              const out: Record<string, number> = {};
                              for (const vid of doeResult.variable_ids) out[String(vid)] = Number(p[String(vid)]);
                              return out;
                            })
                          : [];

                        const initial_points = useDoeAsInitial
                          ? doeInitial.slice(0, Math.max(0, Number.isFinite(maxInitialPoints as any) ? maxInitialPoints : 0))
                          : [];

                        const data = await fetchJson('/experiments/optimize', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({
                            variable_ids,
                            n_iter: nIter,
                            method: optMethod,
                            seed: Number.isFinite(seed as any) ? seed : null,
                            objective: { kind: objectiveKind, variable_id: objectiveVarId },
                            initial_points,
                            max_initial_points: Math.max(0, maxInitialPoints),
                          }),
                        });
                        setOptimizeResult(data);
                        persistRun(
                          'optimize',
                          `Optimize (${objectiveKind} ${idToName[objectiveVarId] || `var ${objectiveVarId}`}, n=${nIter})`,
                          {
                            variable_ids,
                            n_iter: nIter,
                            method: optMethod,
                            seed: Number.isFinite(seed as any) ? seed : null,
                            objective: { kind: objectiveKind, variable_id: objectiveVarId },
                            initial_points,
                            max_initial_points: Math.max(0, maxInitialPoints),
                          },
                          data
                        );
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
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-medium">Optimize result</div>
                      <button
                        className="px-3 py-1 bg-emerald-600 text-white rounded text-xs"
                        onClick={async () => {
                          try {
                            const data = await fetchJson('/experiments/optimize/insight', {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({
                                variable_ids: optimizeResult.variable_ids,
                                best_point: optimizeResult.best_point,
                                meta: {
                                  ...(optimizeResult.meta || {}),
                                  variable_names: Object.fromEntries(
                                    (optimizeResult.variable_ids || []).map((vid: number) => [String(vid), idToName[vid] || String(vid)])
                                  ),
                                },
                              }),
                            });
                            setOptimizeResult((prev: any) => ({ ...prev, insight: data }));
                          } catch (err: any) {
                            setOptimizeError(err?.message || String(err));
                          }
                        }}
                      >
                        Generate insight
                      </button>
                    </div>
                    {optimizeResult.insight && (
                      <div className="p-3 bg-gray-50 border rounded">
                        <div className="text-sm font-medium">{optimizeResult.insight.summary}</div>
                        <ul className="list-disc pl-5 mt-2 text-xs text-gray-700 space-y-1">
                          {(optimizeResult.insight.bullets || []).map((b: string, i: number) => (
                            <li key={i}>{b}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="text-sm font-medium">Best point</div>
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <span>best_score: {Number(optimizeResult?.meta?.best_score ?? NaN).toFixed(4)}</span>
                        <span>
                          objective: {optimizeResult?.meta?.objective?.kind || '—'}
                          {' '}
                          ({idToName[Number(optimizeResult?.meta?.objective?.variable_id)] || `var ${optimizeResult?.meta?.objective?.variable_id ?? '—'}`})
                        </span>
                        <span>
                          seeded: {optimizeResult?.meta?.initial_points ?? 0}
                          {optimizeResult?.meta?.max_initial_points !== undefined ? ` / max ${optimizeResult.meta.max_initial_points}` : ''}
                        </span>
                      </div>
                    </div>
                    <div className="overflow-auto border rounded">
                      <table className="min-w-full text-xs">
                        <thead className="bg-gray-50">
                          <tr>
                            {(optimizeResult.variable_ids || []).map((vid: number) => (
                              <th key={vid} className="text-left p-2">
                                <div className="flex flex-col gap-1">
                                  <div className="flex items-center gap-2">
                                    <span>{idToName[vid] || String(vid)}</span>
                                    {sourceBadge(idToVar[vid]?.source)}
                                  </div>
                                  <div className="text-[10px] text-gray-500">
                                    [{optimizeResult?.meta?.domain?.[String(vid)]?.min ?? '—'}..{optimizeResult?.meta?.domain?.[String(vid)]?.max ?? '—'}] {optimizeResult?.meta?.domain?.[String(vid)]?.unit ?? ''}
                                  </div>
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

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <div className="text-sm font-medium mb-2">Variables</div>
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

              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium">Run history</div>
                  <button className="px-3 py-1 border rounded text-xs" onClick={refreshRuns}>Refresh</button>
                </div>
                {runsError && <pre className="text-xs text-red-600 whitespace-pre-wrap">{runsError}</pre>}
                <div className="space-y-2">
                  {runs.length === 0 ? (
                    <div className="text-xs text-gray-500">No runs saved yet.</div>
                  ) : (
                    runs.slice(0, 25).map((r: any) => (
                      <div key={r.id} className="p-3 bg-white rounded border border-gray-200 hover:bg-gray-50">
                        <div className="flex items-center justify-between gap-2">
                          <button
                            className="text-left flex-1"
                            onClick={async () => {
                              try {
                                const full = await fetchJson(`/runs/${r.id}`);
                                if (full.run_type === 'doe') {
                                  setDoeResult(full.response_json);
                                  setDoeError(null);
                                  setDoeOpen(true);
                                  const next: Record<number, boolean> = {};
                                  for (const vid of (full.response_json?.variable_ids || [])) next[Number(vid)] = true;
                                  setSelectedIds(next);
                                }
                                if (full.run_type === 'optimize') {
                                  setOptimizeResult(full.response_json);
                                  setOptimizeError(null);
                                  setOptimizeOpen(true);
                                  const next: Record<number, boolean> = {};
                                  for (const vid of (full.response_json?.variable_ids || [])) next[Number(vid)] = true;
                                  setSelectedIds(next);
                                  const ov = Number(full.response_json?.meta?.objective?.variable_id);
                                  if (Number.isFinite(ov)) setObjectiveVarId(ov);
                                  const ok = full.response_json?.meta?.objective?.kind;
                                  if (ok === 'maximize_variable' || ok === 'minimize_variable') setObjectiveKind(ok);
                                }
                              } catch (e: any) {
                                setRunsError(e?.message || String(e));
                              }
                            }}
                          >
                            <div className="font-medium text-sm">{r.title || `${r.run_type} #${r.id}`}</div>
                            <div className="text-[10px] text-gray-500 mt-1">{r.created_at}</div>
                          </button>

                          <div className="flex items-center gap-2">
                            <div className="text-[10px] text-gray-500">{r.run_type} • #{r.id}</div>

                            <button
                              className="px-2 py-1 border rounded text-[10px]"
                              onClick={async () => {
                                try {
                                  const full = await fetchJson(`/runs/${r.id}`);
                                  if (full.run_type === 'doe') {
                                    const req = full.request_json || {};
                                    const data = await fetchJson('/experiments/doe', {
                                      method: 'POST',
                                      headers: { 'Content-Type': 'application/json' },
                                      body: JSON.stringify(req),
                                    });
                                    setDoeResult(data);
                                    setDoeError(null);
                                    setDoeOpen(true);
                                    persistRun('doe', `${full.title || 'DOE'} (replay)`, req, data);
                                  }
                                  if (full.run_type === 'optimize') {
                                    const req = full.request_json || {};
                                    const data = await fetchJson('/experiments/optimize', {
                                      method: 'POST',
                                      headers: { 'Content-Type': 'application/json' },
                                      body: JSON.stringify(req),
                                    });
                                    setOptimizeResult(data);
                                    setOptimizeError(null);
                                    setOptimizeOpen(true);
                                    persistRun('optimize', `${full.title || 'Optimize'} (replay)`, req, data);
                                  }
                                } catch (e: any) {
                                  setRunsError(e?.message || String(e));
                                }
                              }}
                            >
                              Replay
                            </button>

                            <button
                              className="px-2 py-1 border rounded text-[10px]"
                              onClick={async () => {
                                try {
                                  await fetchJson(`/runs/${r.id}`, { method: 'DELETE' });
                                  refreshRuns();
                                } catch (e: any) {
                                  setRunsError(e?.message || String(e));
                                }
                              }}
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
