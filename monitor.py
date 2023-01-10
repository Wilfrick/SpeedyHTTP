import socket, selectors, queue, helpers

def monitor_callback_rw(key, event):
    if event == selectors.EVENT_READ: # have a command to process
        return monitor_callback_r(key, event)
    elif event == selectors.EVENT_WRITE: # can write data to the monitor
        return monitor_callback_w(key, event)

def monitor_callback_r(key, event):
    sel, write_queues, (server, server_callback_r) = key.data[1:]
    # we have a command to process
    data_received = key.fileobj.recv(4096)
    if helpers.cleanup_dead_connection(key, data_received): # if the connection was terminated
        return "QUIT"

    command_string = data_received.decode()
    print(f"[]:{command_string}")
    if command_string[0] == "!":
        command = command_string[1:].lower()
        if command == "quit": # we should kill the server
            return "QUIT"
        elif command == "pause": # stop accepting new connections for now
            # still listening for connections and will get through the backlog once resumed
            # some connections may be lost if the number of pending connections gets too high
            sel.unregister(server)
        elif command == "unpause": # undo PAUSE
            sel.register(server, selectors.EVENT_READ, server_callback_r)
        elif command == "len" or command == "length":
            helpers.add_data_to_write_queue(key, str(len(sel.select(0))).encode())
        elif command == "echo": # interpret as ping
            helpers.add_data_to_write_queue(key, "ping!".encode())
        elif command[:5] == "echo ":
            data_to_echo = command_string[6:]
            if len(data_to_echo) == 0:
                data_to_echo = "ping!"
            helpers.add_data_to_write_queue(key, data_to_echo.encode())
        elif command == "h" or command == "help": # explain what can be done
            helpers.add_data_to_write_queue(key, """Currently supported commands:
!quit\tKills the server
!pause\tTemporarily stops the server from dealing with new connections. Some new connections are storred and may be acted on later
!unpause\tResumes dealing with new connections, some of which may have carried over from when the server was !paused
!length\t[To be changed] Gives the number of sockets currently with actions to be taken (should be small and should reset to 0 unless active communication is happening)
!echo <arg>\tEchos back the given argument. Defaults to returning the string 'ping!'
!help\tGives this help text""".encode())
        else:
            helpers.add_data_to_write_queue(key, "Unreconginsed command; try !h for help".encode())
            print("Unrecognised command; try !h for help")

monitor_callback_w = helpers.auto_write_callback_w

if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 8080))
    print("Connected")
    while True:
        data = input()
        if len(data) == 0:
            continue
        s.send(data.encode())
        if data[0] == "!": # this is a command
            command = data[1:].lower()
            if command == "quit":
                break
            print(s.recv(4096).decode()) # most commands should give some output

    s.shutdown(socket.SHUT_RDWR)
    s.close()