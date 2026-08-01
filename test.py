import socket, sys
try:
    s = socket.create_connection(("smtp-relay.brevo.com", 587), timeout=10)
    print("OK: connected")
    s.close()
except Exception as e:
    print("ERR:", e)
sys.exit(1)