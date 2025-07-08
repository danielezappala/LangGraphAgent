import subprocess
import time
import pytest
import os

@pytest.mark.e2e
def test_full_conversation_flow():
    """
    Tests a full conversation flow:
    1. Simple chat
    2. Search tool usage
    3. Human assistance request
    4. Back to simple chat (ensuring human assistance is not sticky)
    """
    # Assicurati che il percorso del chatbot sia corretto
    chatbot_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'basic_chatbot.py')
    
    print("\n--- AVVIO TEST E2E ---")
    
    process = subprocess.Popen(
        ['python', '-u', chatbot_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1, # Line-buffered
        encoding='utf-8'
    )

    def read_output(proc, timeout=30): # Timeout aumentato
        output = ""
        start_time = time.time()
        print("[TEST] In attesa dell'output del chatbot...")
        while time.time() - start_time < timeout:
            if proc.stdout.readable():
                line = proc.stdout.readline()
                if line:
                    print(f"[STDOUT] {line.strip()}")
                    output += line
                    # Condizioni di uscita comuni
                    if "Tu:" in line or "/fine' per terminare." in line:
                        print("[TEST] Rilevata condizione di uscita. Continuo.")
                        break
                else:
                    time.sleep(0.1)
            else:
                time.sleep(0.1)
        if not output:
            raise TimeoutError("Non è stato ricevuto nessun output dal chatbot.")
        return output

    def write_input(proc, text):
        print(f"\n[TEST] Invio input: '{text}'")
        proc.stdin.write(text + '\n')
        proc.stdin.flush()

    try:
        # Wait for the initial prompt
        print("\n--- STEP 0: Avvio Chatbot ---")
        output = read_output(process)
        assert "Chatbot LangGraph" in output
        assert "Tu:" in output
        print("--- STEP 0: COMPLETATO ---")

        # 1. Simple chat
        print("\n--- STEP 1: Chat Semplice ---")
        write_input(process, "Ciao")
        output = read_output(process)
        assert "Ciao! Come posso aiutarti oggi?" in output
        print("--- STEP 1: COMPLETATO ---")

        # 2. Search tool
        print("\n--- STEP 2: Utilizzo Tool di Ricerca ---")
        write_input(process, "Cosa dice il meteo a Roma?")
        output = read_output(process)
        assert "meteo" in output.lower() or "gradi" in output.lower() or "sole" in output.lower() or "pioggia" in output.lower()
        print("--- STEP 2: COMPLETATO ---")

        # 3. Human assistance
        print("\n--- STEP 3: Richiesta Assistenza Umana ---")
        write_input(process, "Ho bisogno di aiuto da un umano")
        supervision_output = read_output(process)
        assert "Avvio della sessione di supervisione" in supervision_output
        
        print("[TEST] Simulo interazione supervisore...")
        write_input(process, "rispondi che non posso aiutarlo")
        time.sleep(2) # Aumentato il tempo di attesa
        write_input(process, "/fine")
        
        final_response_output = read_output(process)
        assert "non posso aiutarlo" in final_response_output
        print("--- STEP 3: COMPLETATO ---")

        # 4. Back to simple chat
        print("\n--- STEP 4: Ritorno a Chat Semplice ---")
        write_input(process, "Quanto fa 5+5?")
        final_calc_output = read_output(process)
        assert "10" in final_calc_output
        assert "sessione di supervisione" not in final_calc_output
        print("--- STEP 4: COMPLETATO ---")
        
        print("\n--- TEST E2E COMPLETATO CON SUCCESSO ---")

    finally:
        # Clean up
        write_input(process, "exit")
        process.wait(timeout=10)
        
        # Stampa eventuali errori per il debug
        stderr_output = process.stderr.read()
        if stderr_output:
            print(f"[STDERR]\n{stderr_output}")
        
        assert "Errore" not in stderr_output and "Error" not in stderr_output, f"Trovato errore in stderr: {stderr_output}"
