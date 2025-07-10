// API client for agents endpoints
export type AgentSummary = {
  id: string;
  name: string;
  llm: string;
  grafo: string;
};

export type AgentDetails = AgentSummary & {
  prompt: any;
};

export async function fetchAgents(): Promise<AgentSummary[]> {
  const res = await fetch("http://localhost:9003/agents");
  if (!res.ok) throw new Error("Failed to fetch agents");
  return res.json();
}

export async function fetchAgentDetails(agentId: string): Promise<AgentDetails> {
  const res = await fetch(`http://localhost:9003/agents/${agentId}`);
  if (!res.ok) throw new Error("Failed to fetch agent details");
  return res.json();
}

export async function chatWithAgent(agentId: string, message: string): Promise<string> {
  console.log(`Sending message to agent ${agentId}: ${message}`);
  const res = await fetch(`http://localhost:8000/chat`, { // Puntiamo al nuovo endpoint generico
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      message: message, 
      thread_id: "1" // Usiamo un thread_id fisso per coerenza con il backend
    }),
  });
  if (!res.ok) {
    const errorBody = await res.text();
    console.error("Chat API error:", res.status, errorBody);
    throw new Error(`Chat failed with status: ${res.status}`);
  }
  const data = await res.json();
  return data.response;
}
