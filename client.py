import socket
import sys


def convert_to_server_syntax(msg, command):             # Function to check if correct number of argument is passed to the command
    nr_args = {'NICK': 2, 'JOIN': 2, 'PART': 2, 'SEND': 3, 'LIST': 2, 'KICK': 4, 'QUIT': 2}
    try:
        msg_split_list = msg.split()
        str_for_server = command
        for args in range(1, nr_args[command]):
            if args != nr_args[command] - 1:
                str_for_server += " " + msg_split_list[args]
            else:
                str_for_server += ":" + msg_split_list[args]
                msg_split_list = msg_split_list[args + 1:]
                for word in range(len(msg_split_list)):
                    str_for_server += " " + msg_split_list[word]
        return str_for_server
    except:
        print("Too few arguments, try again.")
        return


def send_buffer():                          # Function to send command to server
    while True:
        try:
            msg = input("Enter cmd:")
            if not msg:
                s.send(bytes("NOOP:NOOP", "utf8"))
                break

            else:
                command = msg.upper()[:4]
                command_list = ["QUIT", "NICK", "JOIN", "PART", "SEND", "LIST", "KICK"]

                if command in command_list and msg[4] == " ":
                    server_syntax = convert_to_server_syntax(msg, command)
                    if server_syntax:
                        s.send(bytes(server_syntax, "utf8"))
                    break
                else:
                    print("No such command! Try again.")

        except IndexError:
            print("No such command or you've entered to few arguments! Try again.")


def rcv_buffer():                           # Function to receive data from server
    data = ''
    while True:
        try:
            data += s.recv(1024).decode("utf8")
            while '\n' in data:
                i = data.index('\n')
                msg, data = data[:i], data[i + 1:]
                if msg == "QUIT":
                    print("Disconnected from server...")
                    s.close()
                    sys.exit()
                else:
                    print(msg)

        except socket.timeout:
            break


HOST = ''
PORT = 12373
ADDRESS = (HOST, PORT)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(ADDRESS)
s.settimeout(0.5)

while True:
    rcv_buffer()
    send_buffer()


