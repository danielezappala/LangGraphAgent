#!/bin/bash

# Funzione per terminare i processi figli
cleanup() {
    echo "Stopping child processes..."
    # Invia il segnale SIGTERM a tutti i processi nello stesso gruppo di processi
    kill -TERM 0
    wait
    echo "All processes stopped."
}

# Imposta la trap per catturare l'uscita (Ctrl+C, chiusura del terminale, ecc.)
trap cleanup INT TERM EXIT

# Imposta l'opzione per uscire immediatamente se un comando fallisce
set -e

# Avvia il backend in background
echo "Starting backend..."
(cd backend && source ../venv/bin/activate && python server.py) &

# Avvia il frontend in primo piano
echo "Starting frontend..."
(cd frontend && npm run dev)

# Attendi che tutti i processi in background terminino (non verrà mai raggiunto in questo script)
wait
