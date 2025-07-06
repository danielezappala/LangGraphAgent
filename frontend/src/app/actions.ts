'use server';

// import { ai } from '@/ai/genkit'; // Genkit disabilitato
import { z } from 'zod';
import type { Message as GenkitMessage } from '@genkit-ai/ai/model';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const getAiResponseSchema = z.object({
  messages: z.array(
    z.object({
      role: z.enum(['user', 'assistant']),
      content: z.string(),
    })
  ),
});

export async function getAiResponse(input: { messages: Message[] }): Promise<{ message: Message }> {
  const parsedInput = getAiResponseSchema.safeParse(input);

  if (!parsedInput.success) {
    console.error('Invalid input format:', parsedInput.error);
    return { message: { role: 'assistant', content: 'Invalid input format.' } };
  }
  
  const { messages } = parsedInput.data;

  const history: GenkitMessage[] = messages.slice(0, -1).map((msg) => ({
    role: msg.role === 'assistant' ? 'model' : 'user',
    content: [{ text: msg.content }],
  }));

  const lastMessage = messages[messages.length - 1];

  try {
    // AI frontend disabilitata
    return { message: { role: 'assistant', content: 'Funzionalità AI lato frontend disabilitata: nessun modello disponibile.' } };
  }
}
