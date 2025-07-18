import { Message } from "./types";

export function convertBackendMessage(backendMsg: any): Message | null {
  if (!backendMsg.content || backendMsg.content.trim() === '') {
    return null;
  }

  const baseMessage: Message = {
    role: backendMsg.type === 'human' ? 'user' as const : 'assistant' as const,
    content: backendMsg.content,
    id: backendMsg.id || crypto.randomUUID()
  };

  if (backendMsg.type === 'tool') {
    return {
      ...baseMessage,
      tool: true,
      content: `Tool output: ${typeof backendMsg.content === 'string' 
        ? backendMsg.content 
        : JSON.stringify(backendMsg.content, null, 2)}`
    };
  }

  return baseMessage;
}

export function convertBackendMessages(messages: any[]): Message[] {
  return messages
    .map(convertBackendMessage)
    .filter(msg => msg !== null);
}
