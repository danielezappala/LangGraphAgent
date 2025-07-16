#!/bin/bash

# Crea i file .env se non esistono
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Creato file .env dalla configurazione di esempio"
else
    echo "Il file .env esiste già"
fi

if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "Creato file backend/.env dalla configurazione di esempio"
else
    echo "Il file backend/.env esiste già"
fi

if [ ! -f frontend/.env ]; then
    cp frontend/.env.example frontend/.env
    echo "Creato file frontend/.env dalla configurazione di esempio"
else
    echo "Il file frontend/.env esiste già"
fi

# Imposta i permessi corretti
chmod 600 .env backend/.env frontend/.env 2>/dev/null

echo "\nSetup completato. Per favore, modifica i file .env con le tue configurazioni."
