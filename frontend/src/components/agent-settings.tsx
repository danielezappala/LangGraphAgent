"use client";
import { useEffect, useState } from "react";
import { AgentDetails, fetchAgentDetails } from "@/app/api/agents";
import { MermaidViewer } from "@/components/mermaid-viewer";

export function AgentSettings({ agentId }: { agentId: string }) {
  const [details, setDetails] = useState<AgentDetails | null>(null);
  const [mermaidDef, setMermaidDef] = useState<string>("");

  useEffect(() => {
    if (agentId) {
      fetchAgentDetails(agentId).then((data) => {
        setDetails(data);
        console.log('[AgentSettings] Grafo ricevuto dal backend:', data.grafo);
        // Demo: genera un grafo mermaid semplice se non presente
        if (typeof data.grafo === "string" && data.grafo.startsWith("graph")) {
          let grafo = data.grafo;
          if (!grafo.includes("-->") && !grafo.includes("---") && !grafo.includes("-.->")) {
            // Aggiungi edge fittizio se manca
            grafo += "\nA --> B";
          }
          setMermaidDef(grafo);
        } else {
          setMermaidDef(`graph TD\nA[Start] --> B[LLM: ${data.llm}]`);
        }
      });
    }
  }, [agentId]);

  if (!details) return <div className="p-4">Loading agent details...</div>;

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-bold">Agent Settings</h2>
      <div><b>Name:</b> {details.name}</div>
      <div><b>LLM:</b> {details.llm}</div>
      <div><b>Prompt:</b> <pre className="whitespace-pre-wrap break-words max-h-40 overflow-auto bg-muted p-2 rounded">{JSON.stringify(details.prompt, null, 2)}</pre></div>
      <div>
        <b>Grafo:</b>
        <div className="bg-white p-2 rounded border mt-2 overflow-auto">
          {details.grafo && (
            <>
              <pre className="text-xs text-gray-400 mb-2">{details.grafo}</pre>
              {mermaidDef && <MermaidViewer chart={mermaidDef} />}
            </>
          )}
          {!details.grafo && (
            <span className="text-red-500 text-xs">Nessun grafo disponibile per questo agente.</span>
          )}
        </div>
      </div>
    </div>
  );
}
