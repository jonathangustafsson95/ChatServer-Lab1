import socket
import re, sys
from threading import *


class User:                                             # Class for creating a server client
    def __init__(self, name, sock):
        self.name = name
        self.socket = sock
        self.message_queue = []
        self.in_channels = []


class Channel:                                          # Class for creating a server channel
    def __init__(self, channel_name):
        self.channel_name = channel_name
        self.channel_op = None
        self.channel_users = []


def client_func(client_sock, addr):                     # Function for handling a client
    client_sock.send(bytes(
        "Welcome, enter 'nick' followed by your nickname and press enter. To leave the chat, type QUIT." + '\n',
        "utf8"))
    while True:
        try:
            message = client_sock.recv(1024).decode("utf8")             # Receiving message from client
            comd = message[:4]                                          # comd = command to check with server protocol
            name = message[5:]                                          # name is either the nickname or reason to quit

            if comd == "QUIT":
                if not name:
                    client_sock.send(bytes("Please enter a reason for quitting." + '\n', "utf8"))
                else:
                    print("%s: %s has left the server" % addr)
                    client_sock.send(bytes("QUIT" + '\n', "utf8"))
                    client_sock.close()
                    sys.exit()

            elif comd == "NICK":
                name_ok = nick(name, client_sock, new_client=None)      # Check if nickname is approved
                if name_ok == "NAME EXISTS":
                    client_sock.send(bytes("Name is already taken.\n", "utf8"))
                elif name_ok == "UNALLOWED CHARS":
                    client_sock.send(bytes("Names can only contain 'a-z', 'A-Z', '0-9', '-', '_'\n", "utf8"))
                elif name_ok:
                    client_sock.send(bytes("""
                         QUIT <Reason>: To exit the chat. 
                         NICK <New nickname>: To change your nickname.
                         JOIN #<Channel_name>: To join a existing channel or create a new one.
                         PART #<Channel_name>: To leave a channel.
                         SEND <Username> <Message> or #<Channel_name> <Message>: To msg a user or channel.
                         LIST #<Channel_name>: To list all users in channel.
                         KICK #<Channel_name> <Username> <Reason>: To kick a user in a channel.
                         """ + '\n', "utf8"))
                    break

            else:
                client_sock.send(
                    bytes("You can only choose (NICK <Nickname>) or quit the server (QUIT <Reason>)" + '\n',
                          "utf8"))

        except ConnectionResetError:                                # Error handling for noticing disconnected clients
            print("%s: %s has left the server. Reason: Disconnected (ConnectionReset)" % addr)
            client_sock.close()
            return

        except BrokenPipeError:                                     # Error handling for noticing disconnected clients
            print("%s: %s has left the server. Reason: Disconnected (BrokenPipe)" % addr)
            client_sock.close()
            return

        except OSError:                                             # Error handling for noticing disconnected clients
            print("%s: %s has left the server. Reason: Disconnected (OSError)" % addr)
            client_sock.close()
            return

    new_client = User(name, client_sock)                            # Creating a new user with chose nickname
    server_users.append(new_client)
    print("%s has joined the server." % name)

    while True:
        try:
            msg = client_sock.recv(1024).decode()                   # Receiving from client
            command, args = msg.split(":")                          # Splitting msg to extract command and msg
            cmd = command[:4]

            if cmd == "QUIT":
                if not args:
                    new_client.message_queue.append("Please enter a reason for quitting.")
                    send_msg_queue(new_client)
                else:
                    print("%s: %s has left the server. Reason:" % addr, args)
                    server_users.remove(new_client)
                    quit_server(new_client, args)
                    sys.exit()

            while True:
                if command == "NOOP":
                    send_msg_queue(new_client)
                    break

                elif cmd == "NICK":
                    nick(args, client_sock, new_client)
                    send_msg_queue(new_client)
                    break

                elif cmd == "JOIN":
                    if args[0] != "#":
                        new_client.message_queue.append("You have to type # in front of channel name.")
                        send_msg_queue(new_client)
                        break
                    else:
                        join(new_client, args)
                        send_msg_queue(new_client)
                        break

                elif cmd == "PART":
                    if args[0] != "#":
                        new_client.message_queue.append("You have to type # in front of channel name.")
                        send_msg_queue(new_client)
                        break
                    else:
                        part(new_client, args)
                        send_msg_queue(new_client)
                        break

                elif cmd == "SEND":
                    receiver = command[5:]
                    send(new_client, receiver, args)
                    send_msg_queue(new_client)
                    break

                elif cmd == "LIST":
                    if args[0] != "#":
                        new_client.message_queue.append("You have to type # in front of channel name.")
                        send_msg_queue(new_client)
                        break
                    else:
                        list_all(new_client, args)
                        send_msg_queue(new_client)
                        break

                elif cmd == "KICK":
                    receiver = command[5:]
                    if receiver[0] != "#":
                        new_client.message_queue.append("You have to type # in front of channel name.")
                        send_msg_queue(new_client)
                        break
                    else:
                        kick(new_client, receiver[1:], args)
                        send_msg_queue(new_client)
                        break

                else:
                    new_client.message_queue.append("No such command. (server)")
                    break

        except ConnectionResetError:                               # Error handling for noticing disconnected clients
            print("%s: %s has left the server. Reason: Disconnected (ConnectionResetError)" % addr)
            quit_server(new_client, "Disconnected (ConnectionResetError)", error=True)
            server_users.remove(new_client)
            return

        except ValueError:                                         # Error handling for noticing disconnected clients
            print("%s: %s has left the server. Reason: Disconnected (ValueError)" % addr)
            quit_server(new_client, "Disconnected (ValueError)", error=True)
            server_users.remove(new_client)
            return

        except BrokenPipeError:                                    # Error handling for noticing disconnected clients
            print("%s: %s has left the server. Reason: Disconnected (BrokenPipe)" % addr)
            quit_server(new_client, "Disconnected (BrokenPipe)", error=True)
            server_users.remove(new_client)
            return


def nick(args, client_sock=None, new_client=None):                  # Function for clients choosing nick
    new_nick = name_ok(args)
    if new_nick is False:
        if new_client is None:
            return "UNALLOWED CHARS"
        new_client.message_queue.append("Names can only contain 'a-z', 'A-Z', '0-9', '-', '_'")
        return False
    else:
        for user in server_users:
            if args == user.name:
                if new_client is None:
                    return "NAME EXISTS"
                new_client.message_queue.append("Name is already taken.")
                return False

        if new_client is None:
            return True

        else:
            old_name = new_client.name
            new_client.message_queue.append("New nick: " + args)
            for channel in new_client.in_channels:
                for user in channel.channel_users:
                    if user.name == old_name:
                        continue
                    user.message_queue.append(("#" + channel.channel_name + ": " + old_name + " has changed their name to: " + args))
            new_client.name = args


def join(new_client, args):                                         # Function for joining/creating new channels
    channel_name = args[1:]
    for channels in new_client.in_channels:
        if channels.channel_name == channel_name:
            new_client.message_queue.append("You are already a member of that channel")
            return

    new_channel_name = name_ok(channel_name)
    if new_channel_name is False:
        new_client.message_queue.append("Names can only contain 'a-z', 'A-Z', '0-9', '-', '_'")
        return

    else:
        for channel in server_channels:
            if channel.channel_name == channel_name:
                channel.channel_users.append(new_client)
                new_client.in_channels.append(channel)
                for user in channel.channel_users:
                    user.message_queue.append(new_client.name + " has joined #" + channel_name)
                return

    new_channel = Channel(channel_name)
    server_channels.append(new_channel)
    new_channel.channel_users.append(new_client)
    new_channel.channel_op = new_client
    new_client.in_channels.append(new_channel)
    new_client.message_queue.append("No channel with that name, #%s created" % new_channel.channel_name)
    return


def part(new_client, args):                                         # Function for parting from channel
    channel_name = args[1:]
    for channel in new_client.in_channels:
        if channel.channel_name == channel_name:
            if len(channel.channel_users) > 1:
                if new_client.name == channel.channel_op.name:
                    channel.channel_op = channel.channel_users[1]
                for user in channel.channel_users:
                    user.message_queue.append(new_client.name + " left " + "#" + channel_name)
                channel.channel_users.remove(new_client)
                new_client.in_channels.remove(channel)
                return
            else:
                channel.channel_users.remove(new_client)
                new_client.in_channels.remove(channel)
                for server_channel in server_channels:
                    if server_channel.channel_name == channel_name:
                        server_channels.remove(server_channel)
                        print("No more members of #%s, channel removed" % channel_name)
                        new_client.message_queue.append("You've left channel: #%s" % channel_name)
                        return

    new_client.message_queue.append("You are not in a channel with that name.")
    return


def send(new_client, receiver, args):                           # Function for clients to send msg to clients/channels
    name = new_client.name
    if receiver[0] == "#":
        rcv_channel = receiver[1:]
        for channel in new_client.in_channels:
            if channel.channel_name == rcv_channel:
                for user in channel.channel_users:
                    user.message_queue.append("#" + rcv_channel + " " + name + ":" + args)
                return
        new_client.message_queue.append("You cannot send to a channel you're not a member of")
        return
    else:
        for user in server_users:
            if receiver == name:
                new_client.message_queue.append("You can't message yourself.")
                return
            elif user.name == receiver:
                user.message_queue.append(name + ":" + args)
                new_client.message_queue.append(name + ":" + args)
                return
        new_client.message_queue.append("No user with that name")
        return


def list_all(new_client, args):                              # Function to list all channel members of specified channel
    all_users = ''
    rcv_channel = args[1:]

    for channel in new_client.in_channels:
        if channel.channel_name == rcv_channel:
            all_users += ("#" + rcv_channel + ": \n" + "+" + channel.channel_op.name)
            for user in channel.channel_users:
                if user.name == channel.channel_op.name:
                    pass
                else:
                    all_users += '\n' + user.name
            new_client.message_queue.append(all_users)
            return
    new_client.message_queue.append("You are not member of any channel named: '%s'." % rcv_channel)
    return


def kick(new_client, cmd, args):                            # Function for operators to kick channel users
    chan, user_to_kick = cmd.split(' ')                     # Split command to know which channel and which user
    for channel in new_client.in_channels:
        if channel.channel_name == chan:
            if channel.channel_op.name == new_client.name and new_client.name != user_to_kick:
                for user in channel.channel_users:
                    if user.name == user_to_kick:
                        for chan_users in channel.channel_users:
                            chan_users.message_queue.append("#" + chan + ": " + user_to_kick + " was kicked by "
                                                            + new_client.name + ". Reason: " + args)
                        channel.channel_users.remove(user)
                        user.in_channels.remove(channel)
                        return

                new_client.message_queue.append("No user in channel with that name.")
                return
            elif new_client.name == user_to_kick and new_client.name == channel.channel_op.name:
                new_client.message_queue.append("You cant kick yourself from a chat, use 'Part' instead.")
                return
            else:
                new_client.message_queue.append("Only an operator can kick users.")
                return
    new_client.message_queue.append("You are not a member of a channel with that name.")
    return


def quit_server(new_client, args, error=False):                 # Function for quitting server and removing client
    for channel in reversed(new_client.in_channels):                                # Looking through clients channels and broadcasting client leaving
        channel_arg = "#" + channel.channel_name
        part(new_client, channel_arg)

    for user in server_users:                                   # Broadcasting to all server clients that client left
        if user.name == new_client.name:
            continue
        user.message_queue.append(new_client.name + " left the server. Reason: " + args)

    if not error:                                               # If client disconnected with error, these lines wont be executed
        new_client.socket.send(bytes("QUIT" + '\n', "utf8"))
        new_client.socket.close()


def send_msg_queue(new_client):                                 # Function for sending all msgs i clients msg queue.
    msg_len = len(new_client.message_queue)

    if msg_len == 0:
        new_client.socket.send(bytes("You have no messages. \n", "utf8"))

    for msg in range(msg_len):
        item = new_client.message_queue.pop(0)
        new_client.socket.send(bytes(item + '\n', "utf8"))


def name_ok(name):                                              # Regex function to check if names/channels contains approved characters
    name = name.rstrip()
    if re.match(r'[a-zA-Z0-9][A-Za-z0-9_-]*$', name):
        return True
    return False


server_users = []
server_channels = []

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

HOST = ''
PORT = 12373
ADDRESS = (HOST, PORT)
QUEUE_SIZE = 5

s.bind(ADDRESS)
s.listen(QUEUE_SIZE)
print("Server running..")

while True:
    client_sock, addr = s.accept()
    print("%s: %s has connected" % addr)
    t_client = Thread(target=client_func, args=(client_sock, addr))
    t_client.start()

s.close()

