import socket

def test_socket():
    try:
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Bind the socket to a specific address and port
        server_address = ('localhost', 30003)
        print(f'Starting up on {server_address}')
        sock.bind(server_address)
        
        # Listen for incoming connections
        sock.listen(1)
        print('Socket is listening')
        
        while True:
            # Wait for a connection
            print('Waiting for a connection')
            connection, client_address = sock.accept()
            
            try:
                print(f'Connection from {client_address}')
                
                # Send a response
                message = 'Hello from socket server!\n'
                connection.sendall(message.encode())
                
            finally:
                # Clean up the connection
                connection.close()
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()

if __name__ == '__main__':
    test_socket()
