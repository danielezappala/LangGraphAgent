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
  const res = await fetch("/agents");
  if (!res.ok) throw new Error("Failed to fetch agents");
  return res.json();
}

export async function fetchAgentDetails(agentId: string): Promise<AgentDetails> {
  const res = await fetch(`/agents/${agentId}`);
  if (!res.ok) throw new Error("Failed to fetch agent details");
  return res.json();
}

export async function chatWithAgent(
  agentId: string, 
  message: string, 
  onChunk?: (chunk: string) => void,
  threadId?: string
): Promise<string> {
  console.log(`Sending message to agent ${agentId} in thread ${threadId || 'new'}: ${message}`);
  
  // Use the non-streaming endpoint for now as we debug streaming issues
  const requestBody = {
    message: message,
    thread_id: threadId || "", // Always include thread_id, even if empty
  };
  
  console.log("Sending chat request:", JSON.stringify(requestBody, null, 2));
  
  const res = await fetch(`/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(requestBody),
  });

  if (!res.ok) {
    const errorBody = await res.text();
    console.error("Chat API error:", res.status, errorBody);
    throw new Error(`Chat failed with status: ${res.status}`);
  }

  const data = await res.json();
  
  // If a chunk callback is provided, call it once with the entire content
  if (onChunk && data.content) {
    onChunk(data.content);
  }
  
  return data.content || "No response from the agent.";
}
