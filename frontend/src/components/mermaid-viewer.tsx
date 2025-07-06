"use client";
import { useState } from "react";
import Mermaid from "react-mermaid2";

export function MermaidViewer({ chart }: { chart: string }) {
  // Fallback demo se il grafo reale è vuoto o non contiene edge
  const fallback = 'graph TD\nA[Start] --> B[End]';
  const isChartValid = typeof chart === 'string' && chart.includes('-->');
  const chartToRender = isChartValid ? chart : fallback; // Mostra sempre qualcosa


  const [open, setOpen] = useState(false);
  const [zoom, setZoom] = useState(1);

  return (
    <div>
      <button
        className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition"
        onClick={() => setOpen((open) => !open)}
      >{open ? 'Nascondi grafo' : 'Visualizza grafo'}</button>
      {open && (
        <div style={{ marginTop: 18, marginBottom: 12 }}>
          {/* Controlli Zoom */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
            <button onClick={() => setZoom(z => Math.min(z + 0.2, 3))} style={{ padding: '4px 12px', fontWeight: 'bold', fontSize: 18 }}>＋</button>
            <button onClick={() => setZoom(z => Math.max(z - 0.2, 0.4))} style={{ padding: '4px 12px', fontWeight: 'bold', fontSize: 18 }}>－</button>
            <button onClick={() => setZoom(1)} style={{ padding: '4px 12px', fontWeight: 'bold', fontSize: 16 }}>Reset</button>
            <span style={{ marginLeft: 10, color: '#888', fontSize: 14 }}>Zoom: {Math.round(zoom * 100)}%</span>
          </div>
          <div style={{ minHeight: 400, minWidth: 400, background: '#fff', color: '#000', border: '1px solid #eee', borderRadius: 8, padding: 8, overflow: 'auto', display: 'block', maxWidth: '100%', boxSizing: 'border-box', transition: 'transform 0.2s', transform: `scale(${zoom})`, transformOrigin: 'top left' }}>
            <Mermaid chart={chartToRender} />
          </div>
          <pre className="text-xs text-gray-400 mt-2">{chartToRender}</pre>
        </div>
      )}
    </div>
  );
}
