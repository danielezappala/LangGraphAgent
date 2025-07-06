import tiktoken
from langchain_openai import ChatOpenAI
from backend.config import MODEL_NAME, MIN_RESPONSE_TOKENS, CONTEXT_WINDOW, LOG_MONITOR, LOG_DEBUG
import time

class LLMClient:
    def __init__(self, model=MODEL_NAME, max_tokens=MIN_RESPONSE_TOKENS):
        self.llm = ChatOpenAI(model=model, max_tokens=max_tokens)
        self.model = model
        self.max_tokens = max_tokens

    def count_tokens(self, messages):
        enc = tiktoken.encoding_for_model(self.model)
        num_tokens = 0
        for msg in messages:
            num_tokens += 4
            for key, value in msg.items():
                num_tokens += len(enc.encode(str(value)))
        num_tokens += 2
        return num_tokens

    def invoke_with_continuation(self, messages, min_response_tokens=MIN_RESPONSE_TOKENS):
        full_response = ""
        continuation_count = 0
        while True:
            start_time = time.time()
            n_tokens = self.count_tokens(messages)
            response = self.llm.invoke(messages)
            elapsed = time.time() - start_time
            full_response += response.content
            response_tokens = self.count_tokens([{ "role": "assistant", "content": response.content }])
            truncated = False
            if hasattr(response, 'response_metadata') and response.response_metadata:
                usage = response.response_metadata.get('token_usage', {})
                if usage.get('completion_tokens', 0) >= min_response_tokens:
                    truncated = True
            elif len(response.content) >= min_response_tokens * 3 // 4:
                truncated = True
            if LOG_MONITOR:
                print(f"[MONITOR] Risposta effettiva: {response_tokens} token, {len(response.content)} caratteri")
                print(f"[MONITOR] Tempo di risposta: {elapsed:.2f} secondi")
                if truncated:
                    continuation_count += 1
                    print(f"[MONITOR] Continuazione necessaria: Sì (risposta troncata)")
                    print(f"[MONITOR] Numero chiamata continuativa: {continuation_count}")
                else:
                    print(f"[MONITOR] Continuazione necessaria: No")
            if not truncated:
                break
            if LOG_DEBUG:
                context_str = '\n'.join([f'{m["role"]}: {m["content"]}' for m in messages])
                if len(context_str) > 600:
                    print(f"[DEBUG] Estratto contesto inviato (inizio):\n{context_str[:300]}\n...\n[DEBUG] Estratto contesto inviato (fine):\n{context_str[-300:]}")
                else:
                    print(f"[DEBUG] Contesto inviato all'LLM:\n{context_str}")
                print(f"[DEBUG] Risposta ricevuta (troncata):\n{response.content}\n---")
            # Aggiungi la risposta e chiedi di continuare
            messages = messages + [{"role": "assistant", "content": response.content}, {"role": "user", "content": "continua"}]
        return full_response 