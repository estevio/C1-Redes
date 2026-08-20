import socket
import json
import sys

IP_VM = "10.0.2.15"

# recibe un mensaje en formato HTTP
# retorna una 3-tupla que contiene:
# - start line: str
# - headers: dict
# - body: bin
def parse_HTTP_message(message):
    head, body = message.split(b"\r\n\r\n")
    decoded_head = head.decode()
    print("mensaje decodificado: " + decoded_head)
    
    headers_list = decoded_head.split("\r\n")
    start_line = headers_list.pop(0)
    headers = {}
    for h in headers_list:
        name, details = h.split(":", maxsplit=1)
        headers[name] = details

    return (start_line, headers, body)

# recibe los datos para el mensaje HTTP en una 3-tupla
# - start line: str
# - headers: dict
# - body: bin
# retorna un mensaje en HTTP codificado
def create_HTTP_message(data):
    start_line = data[0]
    headers = data[1]
    body = data[2]
    if start_line.startswith("HTTP"):
        headers["Content-Length"] = " " + str(len(body))
    head = ""
    for k, v in headers.items():
        head += (k + ":" + v + "\r\n")
    message = (start_line + "\r\n" + head + "\r\n").encode() + body
    return message

if __name__ == "__main__":

    buff_size = 10240
    response_headers = {}
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        path = sys.argv[1]

        with open(path) as file:
            json_data = json.load(file)
            response_headers["X-ElQuePregunta"] = json_data["user"]

    con_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    con_socket.bind((IP_VM, 8000))
    con_socket.listen(1)
    print("esperando clientes")

    
    client_socket, client_address = con_socket.accept()
    print("cliente aceptado")
    recv_message = client_socket.recv(buff_size)
    print("\nMensaje Codificado:\n")
    print(recv_message)
    print("\n")

    start_line, headers, body = parse_HTTP_message(recv_message)
    print(start_line)
    print(headers.keys, body)

    if start_line.startswith("GET"):
        pag = start_line.split(" ")[1] # http://example.com/
        host = pag.replace("http://", "")
        host = host.rstrip("/")
        print(f"host: {host}")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((host, 80))

    server_socket.send(recv_message)
    recv_message = server_socket.recv(buff_size)
    client_socket.send(recv_message)

    client_socket.close()
    server_socket.close()
    
    # message = create_HTTP_message((response_start_line, response_headers, response_body))
    # client_socket.send(message)
    con_socket.close()