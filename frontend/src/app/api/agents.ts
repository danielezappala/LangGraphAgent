// API client for agents endpoints
import { config } from "@/lib/config";

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
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const res = await fetch(`${baseUrl}/api/agents`);
  if (!res.ok) throw new Error("Failed to fetch agents");
  return res.json();
}

export async function fetchAgentDetails(agentId: string): Promise<AgentDetails> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const res = await fetch(`${baseUrl}/api/agents/${agentId}`);
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
  
  const requestBody = {
    message: message,
    thread_id: threadId || "",
  };
  
  console.log("Sending streaming chat request to /api/chat/stream");
  
  try {
    const apiUrl = `${config.apiBaseUrl}/api/chat/stream`;
    console.log("Using API URL:", apiUrl);
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      console.error("Chat API error:", response.status, errorBody);
      throw new Error(`Chat failed with status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('No response body');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullResponse = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n\n').filter(line => line.trim() !== '');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6)); // Remove 'data: ' prefix
            if (onChunk) {
              // Handle both direct and nested message formats
              const messageData = data.message || data;
              const chunkToSend = {
                id: messageData.id || crypto.randomUUID(),
                type: messageData.type || 'text',
                content: messageData.content || '',
                tool_name: messageData.tool_name,
                is_final: data.metadata?.is_final || false
              };
              onChunk(JSON.stringify(chunkToSend));
            }
            
            // Update full response with content from either format
            if (data.message?.content) {
              fullResponse += data.message.content;
            } else if (data.content) {
              fullResponse += data.content;
            }
          } catch (e) {
            console.error('Error parsing chunk:', e, 'Chunk:', line);
          }
        }
      }
    }

    return fullResponse || "No response from the agent.";

  } catch (error) {
    console.error('Error in chatWithAgent:', error);
    throw error;
  }
}