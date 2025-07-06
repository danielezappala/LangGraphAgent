'use server';

/**
 * @fileOverview Flow to generate a prompt starter for new users.
 *
 * - generatePromptStarter - A function that generates a prompt starter.
 * - GeneratePromptStarterInput - The input type for the generatePromptStarter function (empty object).
 * - GeneratePromptStarterOutput - The return type for the generatePromptStarter function.
 */

// import {ai} from '@/ai/genkit'; // Genkit disabilitato
import {z} from 'genkit';

const GeneratePromptStarterInputSchema = z.object({});
export type GeneratePromptStarterInput = z.infer<typeof GeneratePromptStarterInputSchema>;

const GeneratePromptStarterOutputSchema = z.object({
  prompt: z.string().describe('A starting prompt for the user.'),
});
export type GeneratePromptStarterOutput = z.infer<typeof GeneratePromptStarterOutputSchema>;

export async function generatePromptStarter(input: GeneratePromptStarterInput): Promise<GeneratePromptStarterOutput> {
  throw new Error('Funzionalità AI lato frontend disabilitata: nessun modello disponibile.');
}

// Tutta la logica Genkit/flow è stata rimossa: questo modulo ora solo stubba la funzione richiesta.
