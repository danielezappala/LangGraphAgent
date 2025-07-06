// Genkit disabilitato: nessuna AI disponibile lato frontend
export const ai = {
  generate: () => { throw new Error('Genkit is disabled: no frontend LLM available.'); },
  // puoi aggiungere altri stub se necessario
};
