import socket
import json
import sys

IP_VM = "192.168.1.18"

# recibe un mensaje en formato HTTP
# retorna una 3-tupla que contiene:
# - start line: str
# - headers: dict
# - body: bin
def parse_HTTP_message(message):
    try:
        head, body = message.split(b"\r\n\r\n")
    except ValueError:
        head = message
        body = b""
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

def receive_full_message(connection_socket, buff_size):
 
    # recibimos la primera parte del mensaje
    recv_message = connection_socket.recv(buff_size)
    while b"\r\n\r\n" not in recv_message:
        recv_message += connection_socket.recv(buff_size)
    data = parse_HTTP_message(recv_message)
    start_line = data[0]
    headers = data[1]
    body = data[2]

    if not start_line.startswith("HTTP"):
        return recv_message

    print(headers)
    # entramos a un while para recibir el resto y seguimos esperando información
    # mientras el buffer no contenga secuencia de fin de mensaje
    body_size = int(headers["Content-Length"][1:])
    while len(body) != body_size:
        
        # recibimos un nuevo trozo del mensaje
        body += connection_socket.recv(buff_size)

        # lo añadimos al mensaje "completo"
        

    # finalmente retornamos el mensaje
    return create_HTTP_message((start_line,headers,body))

# recibe los
def error403():
    start_line = "HTTP/1.1 403 Forbidden"
    headers = {"Content-type":"text/html"}
    with open("Forbidden.html") as fb:
        body = fb.read().encode()
    data = (start_line,headers,body)
    return create_HTTP_message(data)

def imagenResponse():
    start_line = "HTTP/1.1 200 Ok"
    headers = {"Content-type":"image/png"}
    with open("Gatito.png", "rb") as miau:
        body = miau.read()
    data = (start_line,headers,body)
    return create_HTTP_message(data)

def addUserHeader(message, user):
    data = parse_HTTP_message(message)
    start_line = data[0]
    headers = data[1]
    body = data[2]
    headers["X-ElQuePregunta"] = user
    data = (start_line,headers,body)
    return create_HTTP_message(data)

def sanitize(message, badWords):
    data = parse_HTTP_message(message)
    start_line = data[0]
    headers = data[1]
    body = data[2]

    for key,value in badWords.items():
        #bkey = ''.join(format(ord(char), '08b') for char in key)
        #bvalue = ''.join(format(ord(char), '08b') for char in value)
        body = body.decode()
        body = body.replace(key,value)
        body = body.encode()

    data = (start_line,headers,body)
    return create_HTTP_message(data)


if __name__ == "__main__":

    buff_size = 50
    response_headers = {}
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        path = sys.argv[1]

        with open(path) as file:
            json_data = json.load(file)
            response_headers["X-ElQuePregunta"] = json_data["user"]
            dictProhibido = {}
            listaDePalabrotas = json_data["forbidden_words"]
            
            for miniDict in listaDePalabrotas:
                for key, value in miniDict.items():
                    dictProhibido[key] = value

    con_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    con_socket.bind((IP_VM, 8000))
    i = 2
    j = 0
    con_socket.listen(i)

    close = True
    while close:

        print("esperando cliente")

        client_socket, client_address = con_socket.accept()
        print("cliente aceptado")
        # Se conecta el usuario del proxy
        
        recv_message = receive_full_message(client_socket, buff_size)
        print("\nMensaje Codificado:\n")
        print(recv_message)
        print("\n")

        start_line, headers, body = parse_HTTP_message(recv_message)
        print(start_line)
        print("\n")
        print(headers.keys, body)

        if start_line.startswith("GET") or start_line.startswith("CONNECT"):
            pag = start_line.split(" ")[1] # http://example.com/
            pag = pag.replace("http://", "")
            host = pag.split("/")[0]
            pag = pag.rstrip("/")
            print(f"host: {host}")

            if pag in json_data["blocked"]:
                recv_message = error403()
                client_socket.send(recv_message)
                recv_message = receive_full_message(client_socket, buff_size)
                recv_message = imagenResponse()
                client_socket.send(recv_message)
            else:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.connect((host, 80))
                
                
                recv_message = addUserHeader(recv_message, json_data["user"])
                server_socket.send(recv_message)
                recv_message = receive_full_message(server_socket, buff_size)
                # aqui hay que hacer la censura
                recv_message = sanitize(recv_message, dictProhibido)
                server_socket.close()
                
                client_socket.send(recv_message)
        client_socket.close()
    
    # message = create_HTTP_message((response_start_line, response_headers, response_body))
    # client_socket.send(message)
    con_socket.close()