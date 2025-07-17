#!/usr/bin/env python3
"""
Script di debug per analizzare lo stato delle conversazioni nel database.
Questo script aiuta a diagnosticare perché le chat scompaiono dalla Chat History.
"""

import sqlite3
import os
import json
from datetime import datetime
import pathlib

# Percorso del database
DB_PATH = str(pathlib.Path(__file__).parent / "backend" / "data" / "chatbot_memory.sqlite")

def analyze_database():
    """Analizza il database per identificare problemi con le conversazioni."""
    
    print(f"=== ANALISI DATABASE CONVERSAZIONI ===")
    print(f"Database path: {DB_PATH}")
    print(f"Database exists: {os.path.exists(DB_PATH)}")
    
    if not os.path.exists(DB_PATH):
        print("❌ Database non trovato!")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Verifica struttura tabelle
        print("\n1. STRUTTURA TABELLE:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tabelle trovate: {[t[0] for t in tables]}")
        
        # 2. Conta totale checkpoints
        print("\n2. STATISTICHE CHECKPOINTS:")
        cursor.execute("SELECT COUNT(*) FROM checkpoints")
        total_checkpoints = cursor.fetchone()[0]
        print(f"Totale checkpoints: {total_checkpoints}")
        
        # 3. Conta thread unici
        cursor.execute("SELECT COUNT(DISTINCT thread_id) FROM checkpoints")
        unique_threads = cursor.fetchone()[0]
        print(f"Thread unici: {unique_threads}")
        
        # 4. Analizza thread con i loro checkpoint
        print("\n3. ANALISI THREAD:")
        cursor.execute("""
            SELECT 
                thread_id, 
                COUNT(*) as checkpoint_count,
                MIN(checkpoint_ns) as first_checkpoint,
                MAX(checkpoint_ns) as last_checkpoint
            FROM checkpoints 
            GROUP BY thread_id 
            ORDER BY last_checkpoint DESC
        """)
        
        threads = cursor.fetchall()
        print(f"Thread trovati: {len(threads)}")
        
        for i, (thread_id, count, first_ns, last_ns) in enumerate(threads[:10]):  # Mostra primi 10
            print(f"  {i+1}. Thread: {thread_id[:20]}...")
            print(f"     Checkpoints: {count}")
            print(f"     Primo: {first_ns} ({datetime.fromtimestamp(first_ns/1000000000) if first_ns else 'N/A'})")
            print(f"     Ultimo: {last_ns} ({datetime.fromtimestamp(last_ns/1000000000) if last_ns else 'N/A'})")
        
        # 5. Verifica checkpoint con contenuto
        print("\n4. VERIFICA CONTENUTO CHECKPOINT:")
        cursor.execute("""
            SELECT thread_id, checkpoint_ns, LENGTH(checkpoint) as size
            FROM checkpoints 
            WHERE checkpoint IS NOT NULL 
            ORDER BY checkpoint_ns DESC 
            LIMIT 5
        """)
        
        recent_checkpoints = cursor.fetchall()
        print(f"Checkpoint recenti con contenuto:")
        for thread_id, ns, size in recent_checkpoints:
            print(f"  Thread: {thread_id[:20]}... | NS: {ns} | Size: {size} bytes")
        
        # 6. Verifica checkpoint vuoti o corrotti
        print("\n5. VERIFICA PROBLEMI:")
        cursor.execute("SELECT COUNT(*) FROM checkpoints WHERE checkpoint IS NULL")
        null_checkpoints = cursor.fetchone()[0]
        print(f"Checkpoint NULL: {null_checkpoints}")
        
        cursor.execute("SELECT COUNT(*) FROM checkpoints WHERE LENGTH(checkpoint) < 100")
        small_checkpoints = cursor.fetchone()[0]
        print(f"Checkpoint molto piccoli (<100 bytes): {small_checkpoints}")
        
        # 7. Verifica writes associati
        print("\n6. VERIFICA WRITES:")
        cursor.execute("SELECT COUNT(*) FROM writes")
        total_writes = cursor.fetchone()[0]
        print(f"Totale writes: {total_writes}")
        
        cursor.execute("SELECT COUNT(DISTINCT thread_id) FROM writes")
        threads_with_writes = cursor.fetchone()[0]
        print(f"Thread con writes: {threads_with_writes}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Errore durante l'analisi: {e}")

def test_api_response():
    """Testa la risposta dell'API history."""
    print(f"\n=== TEST API RESPONSE ===")
    
    try:
        import requests
        import time
        
        # Test dell'endpoint history
        base_url = "http://localhost:30010"  # Porta backend di default
        
        print(f"Testando: {base_url}/api/history/")
        
        start_time = time.time()
        response = requests.get(f"{base_url}/api/history/", timeout=10)
        response_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            conversations = data.get('conversations', [])
            print(f"Conversazioni trovate: {len(conversations)}")
            
            for i, conv in enumerate(conversations[:5]):  # Mostra prime 5
                print(f"  {i+1}. ID: {conv.get('thread_id', 'N/A')[:20]}...")
                print(f"     Preview: {conv.get('preview', 'N/A')[:50]}...")
                print(f"     Timestamp: {conv.get('last_message_ts', 'N/A')}")
        else:
            print(f"❌ Errore API: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossibile connettersi al backend. È in esecuzione?")
    except Exception as e:
        print(f"❌ Errore durante il test API: {e}")

if __name__ == "__main__":
    analyze_database()
    test_api_response()
    
    print(f"\n=== RACCOMANDAZIONI ===")
    print("1. Verifica che il backend sia in esecuzione")
    print("2. Controlla i log del backend per errori")
    print("3. Se ci sono checkpoint NULL o corrotti, potrebbero causare problemi")
    print("4. Verifica che le conversazioni vengano salvate correttamente durante la chat")