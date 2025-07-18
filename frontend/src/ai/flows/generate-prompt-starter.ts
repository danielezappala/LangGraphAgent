'use server';

/**
 * @fileOverview Flow to generate a prompt starter for new users.
 * AI functionality is disabled - no frontend LLM available.
 */

import { z } from 'zod';

const GeneratePromptStarterInputSchema = z.object({});
export type GeneratePromptStarterInput = z.infer<typeof GeneratePromptStarterInputSchema>;

const GeneratePromptStarterOutputSchema = z.object({
  prompt: z.string().describe('A starting prompt for the user.'),
});
export type GeneratePromptStarterOutput = z.infer<typeof GeneratePromptStarterOutputSchema>;

export async function generatePromptStarter(input: GeneratePromptStarterInput): Promise<GeneratePromptStarterOutput> {
  throw new Error('AI functionality disabled: no frontend LLM available.');
}
