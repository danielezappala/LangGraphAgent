export interface Message {
  role: 'user' | 'assistant';
  content: string;
  tool?: boolean;
  id?: string;
}

export interface Conversation {
  thread_id: string;
  last_message_ts: string;
  preview: string;
}
