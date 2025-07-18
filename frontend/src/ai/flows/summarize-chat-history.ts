'use server';

/**
 * @fileOverview Summarizes the chat history for quick review.
 * AI functionality is disabled - no frontend LLM available.
 */

import { z } from 'zod';

const SummarizeChatHistoryInputSchema = z.object({
  chatHistory: z
    .string()
    .describe('The complete chat history to be summarized.'),
});
export type SummarizeChatHistoryInput = z.infer<typeof SummarizeChatHistoryInputSchema>;

const SummarizeChatHistoryOutputSchema = z.object({
  summary: z.string().describe('A concise summary of the chat history.'),
});
export type SummarizeChatHistoryOutput = z.infer<typeof SummarizeChatHistoryOutputSchema>;

export async function summarizeChatHistory(input: SummarizeChatHistoryInput): Promise<SummarizeChatHistoryOutput> {
  throw new Error('AI functionality disabled: no frontend LLM available.');
}
