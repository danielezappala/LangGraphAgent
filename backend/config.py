CONTEXT_WINDOW = 4096
MIN_RESPONSE_TOKENS = 128
MODEL_NAME = "gpt-3.5-turbo"
HISTORY_FILE = "backend/history.json"
SYSTEM_PROMPT_FILE = "backend/system_prompt.json"

# Logging switches
LOG_MONITOR = True   # Log dettagli monitor (token, tempi, ecc.)
LOG_DEBUG = True     # Log debug (estratti contesto, risposte troncate)
LOG_INFO = True      # Log info (riassunti, caricamento cronologia, ecc.) 