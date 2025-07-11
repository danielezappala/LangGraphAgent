import { Message } from "./types";

export function convertBackendMessage(backendMsg: any): Message {
  if (!backendMsg.content || backendMsg.content.trim() === '') {
    return null;
  }

  const baseMessage = {
    role: backendMsg.type === 'human' ? 'user' : 'assistant',
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
