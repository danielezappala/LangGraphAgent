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
  const res = await fetch("http://localhost:8000/agents");
  if (!res.ok) throw new Error("Failed to fetch agents");
  return res.json();
}

export async function fetchAgentDetails(agentId: string): Promise<AgentDetails> {
  const res = await fetch(`http://localhost:8000/agents/${agentId}`);
  if (!res.ok) throw new Error("Failed to fetch agent details");
  return res.json();
}

export async function chatWithAgent(agentId: string, message: string): Promise<string> {
  const res = await fetch(`http://localhost:8000/agents/${agentId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error("Chat failed");
  const data = await res.json();
  return data.response;
}
