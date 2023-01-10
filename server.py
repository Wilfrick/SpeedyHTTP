import socket, selectors, queue
from importlib import reload
import monitor, client



def server_callback_r(key, event):
    conn, addr = server.accept()
    conn.setblocking(False)
    sel = key.data[1]
    sel.register(conn, selectors.EVENT_READ, (client_callback, *key.data[1:3], addr))
    print(f"New connection recieved from {addr}")

def monitor_callback(key, event):
    reload(monitor) # remove this in the final thing, but very fun for testing
    return monitor.monitor_callback_rw(key, event)

def client_callback(key, event):
    reload(client)
    return client.client_callback_rw(key, event)


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("", 8080))

server.listen()

print("Please connect monitor")
monitor_soc, addr = server.accept()
print("Monitor connected")

server.setblocking(False)
monitor_soc.setblocking(False)

write_queues = {}

sel = selectors.DefaultSelector()
sel.register(server, selectors.EVENT_READ, (server_callback_r, sel, write_queues))
sel.register(monitor_soc, selectors.EVENT_READ, (monitor_callback, sel, write_queues, (server, server_callback_r)))



running = True
while running:
    for key, event in sel.select(None): # None means block until something to do
        callback = key.data[0]
        if callback(key, event) == "QUIT":
            running = False


sel.close()
server.close()
