# Redi – Agenti AI sempre pronti

> **Redi** è la piattaforma per la configurazione e l'utilizzo di agenti AI. Il nome richiama "ready" (pronto), trasmettendo l'idea di assistente sempre disponibile e reattivo. È breve, facile da ricordare, con richiami culturali a Francesco Redi, scienziato innovatore. Redi si distingue per originalità, versatilità e neutralità culturale, facilitando il posizionamento del brand nel mercato AI.

---

# Agente Conversazionale con LangGraph e LangChain

## Requisiti OOP e struttura degli agenti

- Ogni agente AI deve essere un'istanza di una sottoclasse di `BaseAgent` (vedi `agent.py`).
- Un agente deve avere almeno: `name`, `memory`, `llm_client`, `system_prompt`, `graph`.
- **Requisito fondamentale:** il grafo di ogni agente deve includere sempre almeno un nodo di start e uno di end, con edge iniziale e finale. Questo garantisce la corretta visualizzazione e coerenza tra backend e frontend.
- La costruzione del grafo avviene tramite il metodo `_build_graph()` della classe agente.
- L'esportazione del grafo in formato Mermaid avviene tramite utility che usano solo API pubbliche (`nodes`, `get_graph`), senza accedere a proprietà private.
- Sono presenti test automatici che validano l'istanziazione degli agenti e la struttura del grafo.

## Struttura del progetto

```
LGA1/
├── agent.py                # Classi BaseAgent, ConversationalAgent: OOP, orchestrazione, grafo
├── config.py               # Parametri di configurazione e flag di logging
├── llm_utils.py            # Classe LLMClient: invocazione LLM, conteggio token, continuazione automatica
├── main.py                 # Entry point: avvio dell'agente
├── persistent_memory.py    # Classe PersistentMemory: gestione cronologia persistente
├── graph_mermaid.py        # Utility per esportazione Mermaid del grafo
├── test_agent.py           # Test automatici OOP e grafo
├── system_prompt.json      # Prompt di sistema
├── history.json            # Cronologia conversazione persistente
```

## Avvio rapido

1. Assicurati di avere un file `.env` con la tua chiave OpenAI:
   ```
   OPENAI_API_KEY=sk-...
   ```
2. Installa le dipendenze:
   ```bash
   pip install langgraph langchain-openai openai tiktoken python-dotenv
   ```
3. Avvia l'agente:
   ```bash
   python main.py
   ```

## Configurazione dei log

Nel file `config.py` puoi attivare o disattivare i vari livelli di log:
- `LOG_MONITOR`: log dettagliati su token, tempi, continuazioni
- `LOG_DEBUG`: log di debug su contesto e risposte troncate
- `LOG_INFO`: log informativi su cronologia, riassunti, ecc.

## Descrizione dei moduli principali

- **main.py**: punto di ingresso, carica la configurazione, la memoria, il prompt di sistema e avvia la conversazione.
- **agent.py**: contiene la classe `ConversationalAgent` che gestisce il ciclo di conversazione e la logica del grafo.
- **persistent_memory.py**: classe `PersistentMemory` per la gestione della cronologia persistente su file JSON.
- **llm_utils.py**: classe `LLMClient` per la gestione delle chiamate all'LLM, conteggio token e continuazione automatica delle risposte.
- **config.py**: parametri di configurazione, modello, limiti token, file, flag di logging.
- **system_prompt.json**: prompt di sistema personalizzabile.
- **history.json**: cronologia della conversazione, aggiornata e salvata automaticamente.

## Note
- Tutta la logica è ora modulare, OOP e facilmente estendibile.
- Puoi cambiare modello, prompt, limiti di token e log senza modificare il codice principale.
- Per aggiungere nuove strategie di memoria o prompt, crea nuovi moduli e aggiorna la configurazione. 