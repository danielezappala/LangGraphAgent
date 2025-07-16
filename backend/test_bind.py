import socket

def test_bind(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('0.0.0.0', port))
        print(f"Successo nel binding sulla porta {port}")
        s.close()
        return True
    except Exception as e:
        print(f"Errore nel binding sulla porta {port}: {e}")
        return False

# Prova su una porta casuale alta
test_bind(8000)
