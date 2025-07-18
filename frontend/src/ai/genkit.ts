// AI functionality disabled: no frontend LLM available
export const ai = {
  generate: () => { throw new Error('AI is disabled: no frontend LLM available.'); },
  // Additional stubs can be added if needed
};
