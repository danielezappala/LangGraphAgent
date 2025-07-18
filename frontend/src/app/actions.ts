'use server';

import { z } from 'zod';

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

  // History processing removed since AI is disabled

  // AI frontend disabilitata
  return { message: { role: 'assistant', content: 'Funzionalità AI lato frontend disabilitata: nessun modello disponibile.' } };
}
