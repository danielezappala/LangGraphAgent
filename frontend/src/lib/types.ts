export interface Message {
  role: 'user' | 'assistant' ;
  content: string;
  tool?: boolean; // Indica se il messaggio è un output di un tool
  tool_name?: string; // Nome del tool, se applicabile
  id?: string;
}


export interface Conversation {
  thread_id: string;
  last_message_ts: string | null;
  preview: string;
}
