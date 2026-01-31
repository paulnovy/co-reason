import './index.css';
import App from './App.tsx';
import * as React from 'react';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { error?: string }> {
  constructor(props: any) {
    super(props);
    this.state = { error: undefined };
  }
  static getDerivedStateFromError(error: any) {
    return { error: error?.message || String(error) };
  }
  componentDidCatch(error: any) {
    console.error('App error', error);
  }
  render() {
    if (this.state.error) {
      return (
        <pre style={{ padding: 20, fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
          JS Error: {this.state.error}
        </pre>
      );
    }
    return this.props.children as any;
  }
}

try {
  document.body.insertAdjacentHTML('beforeend', '<div id="main-ok" style="font-family:sans-serif;padding:8px;">MAIN_OK</div>');
  const rootEl = document.getElementById('root');
  if (rootEl) {
    createRoot(rootEl).render(
      <StrictMode>
        <ErrorBoundary>
          <App />
        </ErrorBoundary>
      </StrictMode>
    );
  } else {
    document.body.innerHTML = '<div style="padding:20px;font-family:sans-serif">Root element not found</div>';
  }
} catch (err: any) {
  const msg = err?.message || String(err);
  document.body.innerHTML = `<pre style="padding:20px;font-family:monospace;white-space:pre-wrap">JS Error: ${msg}</pre>`;
}
