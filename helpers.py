import queue, selectors, socket, io

def add_data_to_write_queue(key, new_data):
    sel, write_queues = key.data[1:3]
    if key.fileobj not in write_queues.keys():
        write_queues[key.fileobj] = queue.Queue()
    write_queues[key.fileobj].put(new_data)
    sel.modify(key.fileobj, selectors.EVENT_READ | selectors.EVENT_WRITE, key.data)

def auto_write_callback_w(key, event):
    sel, write_queues = key.data[1:3]
    data_to_be_sent = b""
    while not write_queues[key.fileobj].empty():
        object_to_be_sent = write_queues[key.fileobj].get()
        if isinstance(object_to_be_sent, io.IOBase): # this is probably a file descriptor - would like to use sendfile but that doesn't play with non blocking sockets
            # ideally would read from file in a separate thread and then come back here when we have the file ready to send
            data_to_be_sent += object_to_be_sent.read()
        else: # assume it is an encoded string vibing in memory somewhere
            data_to_be_sent += object_to_be_sent
    key.fileobj.send(data_to_be_sent)
    if write_queues[key.fileobj].empty():
        sel.modify(key.fileobj, selectors.EVENT_READ, key.data)

def write_callback_until_done_w(key, event): # used for HTTP/1.1 as ending the connection signals the end of the transaction
    auto_write_callback_w(key, event)
    sel, write_queues = key.data[1:3]
    if write_queues[key.fileobj].empty(): # if there is nothing more to write, kill the connection
        kill_connection(key)


def cleanup_dead_connection(key, data_received):
    sel = key.data[1]
    if not data_received:
        kill_connection(key)
        return True
    return False

def kill_connection(key):
    sel = key.data[1]
    sel.unregister(key.fileobj)
    key.fileobj.shutdown(socket.SHUT_RDWR)
    key.fileobj.close()