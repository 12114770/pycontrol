import socket

ip = "192.168.178.59"
port = 7090
message = "i"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2)

# Send the UDP packet
sock.sendto(message.encode(), (ip, port))

# Wait for response
try:
    data, addr = sock.recvfrom(1024)
    print("✅ Received from KEBA:", data.decode())
except socket.timeout:
    print("❌ No response received.")
