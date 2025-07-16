# Redi – Agenti AI sempre pronti

**Redi** è una piattaforma moderna per la configurazione e l'utilizzo di agenti AI modulari e personalizzabili.

## Perché "Redi"?
- Il nome richiama "ready" (pronto): semplicità, reattività, disponibilità.
- È breve, internazionale, facile da ricordare e pronunciare.
- Richiama anche Francesco Redi, scienziato innovatore, conferendo autorevolezza e spirito di ricerca.
- È versatile (es. RediBot, RediSuite) e privo di connotazioni negative.

**Redi** vuole essere sinonimo di affidabilità, innovazione e rapidità nell'adozione di agenti AI.

---

## Configurazione Ambiente

### Variabili d'Ambiento Richieste

Crea un file `.env` nella root del progetto basandoti su `.env.example` con le seguenti variabili:

#### Configurazione Base
- `NEXT_PUBLIC_API_BASE_URL`: URL base per le chiamate API (es. `http://localhost:8000`)
- `NEXT_PUBLIC_APP_NAME`: Nome dell'applicazione (default: "LangGraph Agent")
- `NEXT_PUBLIC_APP_ENV`: Ambiente di esecuzione (`development`, `staging`, `production`)

#### Autenticazione
- `NEXTAUTH_URL`: URL base dell'applicazione (es. `http://localhost:3000`)
- `NEXTAUTH_SECRET`: Chiave segreta per le sessioni di autenticazione

#### Provider LLM
- `NEXT_PUBLIC_DEFAULT_MODEL`: Modello LLM predefinito
- `NEXT_PUBLIC_DEFAULT_API_VERSION`: Versione API predefinita per i provider

#### Analitica e Monitoraggio (Opzionali)
- `NEXT_PUBLIC_GOOGLE_ANALYTICS_ID`: ID per Google Analytics
- `NEXT_PUBLIC_SENTRY_DSN`: DSN per l'integrazione con Sentry

#### Debug e Sviluppo
- `NEXT_PUBLIC_ENABLE_ANALYTICS`: Abilita/disabilita le analitiche (true/false)
- `NEXT_PUBLIC_ENABLE_DEBUG`: Abilita/disabilita il debug (true/false)

### Avvio in Sviluppo

1. Copia il file di esempio:
   ```bash
   cp .env.example .env.local
   ```
2. Modifica le variabili nel file `.env.local` secondo le tue esigenze
3. Installa le dipendenze:
   ```bash
   npm install
   # oppure
   yarn install
   ```
4. Avvia il server di sviluppo:
   ```bash
   npm run dev
   # oppure
   yarn dev
   ```

## Struttura del Progetto

- `/src/app`: File di routing e pagine di Next.js
- `/src/components`: Componenti React riutilizzabili
- `/src/lib`: Utilità e logica di business
- `/public`: File statici

---

_Questa piattaforma si basa su Next.js e offre un'interfaccia utente avanzata per la gestione e visualizzazione di agenti AI._
