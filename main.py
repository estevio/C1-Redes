import socket
import json
import sys

IP_VM = "10.0.2.15"

# recibe un mensaje en formato HTTP
# retorna una 3-tupla que contiene:
# - start line: str
# - headers: dict
# - body: str
def parse_HTTP_message(message):
    decoded_message = message.decode()
    print("mensaje decodificado: " + decoded_message)
    head, body = decoded_message.split("\r\n\r\n")
    headers_list = head.split("\r\n")
    start_line = headers_list.pop(0)
    headers = {}
    for h in headers_list:
        name, details = h.split(":", maxsplit=1)
        headers[name] = details

    return (start_line, headers, body)

# recibe los datos para el mensaje HTTP en una 3-tupla
# - start line: str
# - headers: dict
# - body: str
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
    message = start_line + "\r\n" + head + "\r\n" + body
    return message.encode()

if __name__ == "__main__":

    buff_size = 1024
    response_headers = {}
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        path = sys.argv[1]

        with open(path) as file:
            json_data = json.load(file)
            response_headers["X-ElQuePregunta"] = json_data["user"]

    con_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    con_socket.bind((IP_VM, 8000))
    con_socket.listen(2)
    print("esperando clientes")

    while True:
        new_socket, nwe_address = con_socket.accept()
        print("cliente aceptado")
        recv_message = new_socket.recv(buff_size)
        print("\nMensaje Codeificado:\n")
        print(recv_message)
        print("\n")

        start_line, headers, body = parse_HTTP_message(recv_message)
        print(start_line)
        print(headers.keys, body)

        response_start_line = "HTTP/1.1 200 OK"
        response_headers |= {"Content-Type": " text/html; charset=utf-8",
                "Content-Length": " 237"}
        response_body = "Hola!"
        message = create_HTTP_message((response_start_line, response_headers, response_body))
        new_socket.send(message)