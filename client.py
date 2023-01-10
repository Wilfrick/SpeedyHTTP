import queue, selectors, helpers, pathlib

basepath = pathlib.Path("D:\Program_Files\PyCharm\Projects\SpeedyHTTP\server_root").resolve()

def client_callback_rw(key, event):
    if event == selectors.EVENT_READ:
        return client_callback_r(key, event)
    if event == selectors.EVENT_WRITE:
        return client_callback_w(key, event)

def client_callback_r(key, event):
    data_received = key.fileobj.recv(4096)
    if helpers.cleanup_dead_connection(key, data_received): # connection was terminated from the far side
        return
    request = data_received.decode()
    lines = request.splitlines()
    request_line = lines[0]
    request_method, url, proto_version = request_line.split(" ")
    url = "./" + url
    print(f"{key.data[3]}:{request_method} {url}")
    if request_method == "GET" or request_method == "HEAD": # need to construct headers, possibly need to provide content
        status_line = "HTTP/1.1"
        print(basepath, url)
        potential_path = (basepath / url).resolve()
        file_path = None
        if not potential_path.is_relative_to(basepath): # path is badly formed, reject it
            status_code = 400
            reason = "Bad Request"
        else: # path is well formed, but who knows if it points somewhere meaningful?
            if potential_path == basepath:
                potential_path = (potential_path / "index.html").resolve()
            print(potential_path)
            if not potential_path.exists():
                status_code = 404
                reason = "Not Found"
            else: # the requested file exists, so serve it?
                status_code = 200
                reason = "OK"
                file_path = potential_path


        status_line = " ".join((status_line, str(status_code), reason))
        response_headers = ("","")
        header = "\r\n".join((status_line, *response_headers))

        helpers.add_data_to_write_queue(key, header.encode())

        if request_method == "GET" and file_path:
            f = open(file_path, "rb")
            helpers.add_data_to_write_queue(key, f)


        print(f"->{key.data[3]}:{repr(header)}")
    if request_method == "POST":
        print("Bruh I dunno what to do")


client_callback_w = helpers.write_callback_until_done_w
