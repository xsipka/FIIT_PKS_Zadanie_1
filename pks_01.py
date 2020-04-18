import socket
import struct
import math
import threading
import time
import binascii
import random
import os


#......Keep alive........................................
thread_status = True

def keep_alive(client_sock, server_addr, interval):

    while True:
        if thread_status == False:
            return
        client_sock.sendto(str.encode('3'), server_addr)
        print("Udrzujem spojenie")
        time.sleep(interval)


def start_thread(client_sock, server_addr, interval):
    thread = threading.Thread(target = keep_alive, args = (client_sock, server_addr, interval))
    thread.daemon = True
    thread.start()

    return thread


#......Client funkcie....................................
def client_login():
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = input("Zadaj IP adresu servera: ")
    port = input("Zadaj port: ")
    server_addr = (addr, int(port))
    client_sock.sendto(str.encode(''), server_addr)
    print("Pripojeny na adresu ", server_addr, "\n")
    user_client(client_sock, server_addr)


def add_error(num_of_packets):
    error = input("Pridat chybu? y - ano /iny znak - nie ")
    if error == 'y':
        if (num_of_packets >= 10):
            num = random.randint(1, 10)
        else:
            num = random.randint(1, num_of_packets)
        error = True
    else:
        num = 0
        error = False

    return error, num


def create_msg_header(packet_num, length, to_send, err, num):
    header = struct.pack("iii", packet_num, length, 0)
    crc_num = binascii.crc_hqx(header + to_send, 0)
    packet_num, length, crc = struct.unpack("iii", header)
    if err == True and num == packet_num:
        crc = crc_num + 1
        err = False
    else:
        crc = crc_num

    header = struct.pack("iii", packet_num, length, crc)
    return err, header


def create_file_header(packet_num, to_send, err, num):
    header = struct.pack("ii", packet_num, 0)
    crc_num = binascii.crc_hqx(header + to_send, 0)
    packet_num, crc = struct.unpack("ii", header)
    if err == True and num == packet_num:
        crc = crc_num + 1
        err = False
    else:
        crc = crc_num

    header = struct.pack("ii", packet_num, crc)
    return err, header


def check_reply(reply):
    reply = reply.decode()
    if reply == "OK":
        print("Pakety dorazili v poriadku.")
        return list()
    else:
        print("Nie vsetky pakety boli dorucene spravne...")
        return list(reply)


def repair_and_send(damaged_packets, packets_to_send, client_sock, server_addr):

    for i in damaged_packets:
        if len(packets_to_send) > int(i):
            to_send = packets_to_send[int(i)]
            client_sock.sendto(to_send, server_addr)
            status = client_sock.recv(1500)
            print(status.decode())
        else:
            break


def send_msg_info(client_sock, server_addr, all_packets):
    to_send = ("1" + str(all_packets))
    to_send = str.encode(to_send)
    client_sock.sendto(to_send, server_addr)
    client_sock.sendto(str.encode(''), server_addr)


def send_message(client_sock, server_addr):
    message = input("Zadaj svoju spravu: ")
    frag = int(input("Zadaj velkost fragmentu: "))
    while frag > 1488 or frag <= 0:
        frag = int(input("Znova zadaj velkost fragmentu: "))
    err, num = add_error(math.ceil(len(message) / frag))
    send_msg_info(client_sock, server_addr, math.ceil(len(message) / frag))

    while len(message) >= 0:
        packets_to_send = []
        packet_num = 0
        if (len(message) == 0):
            break
        while packet_num < 10:
            to_send = message[:frag]
            packet_num += 1
            to_send = str.encode(to_send)
            err, header = create_msg_header(packet_num, (len(to_send)), to_send, err, num)
            packets_to_send.append(header + to_send)
            message = message[frag:]
            client_sock.sendto(header + to_send, server_addr)
            if (len(message) == 0):
                client_sock.sendto(str.encode(''), server_addr)
                break
        status = client_sock.recv(1500)
        damaged_packets = check_reply(status)
        if len(damaged_packets) != 0:
            repair_and_send(damaged_packets, packets_to_send, client_sock, server_addr)

    print("Sprava uspesne odoslana.\n")


def send_file_info(client_sock, server_addr, file_name, all_packets):
    to_send = ("2" + str((all_packets)))
    to_send = str.encode(to_send)
    client_sock.sendto(to_send, server_addr)
    client_sock.sendto(str.encode(''), server_addr)
    client_sock.sendto(str.encode(file_name), server_addr)


def send_file(client_sock, server_addr):
    file_name = input("Zadaj meno suboru: ")
    frag = int(input("Zadaj velkost fragmentu: "))
    while frag > 1492 or frag <= 0:
        frag = int(input("Znova zadaj velkost fragmentu: "))
    data = ''
    file = open(file_name, "rb")
    err, num = add_error(10)
    size = os.path.getsize(file_name)
    send_file_info(client_sock, server_addr, file_name, math.ceil(size/frag) + 1)

    while True:
        packets_to_send = []
        packet_num = 0
        while packet_num < 10:
            packet_num += 1
            data = file.read(frag)
            err, header = create_file_header(packet_num, data, err, num)
            packets_to_send.append(header + data)
            client_sock.sendto(header + data, server_addr)
            if (len(data) == 0):
                client_sock.sendto(str.encode(''), server_addr)
                file.close()
                break
        status = client_sock.recv(1500)
        damaged_packets = check_reply(status)
        if len(damaged_packets) != 0:
            repair_and_send(damaged_packets, packets_to_send, client_sock, server_addr)
        if (len(data) == 0):
            break

    print("Subor uspesne odoslany.\n")
    file.close()


def user_client(client_sock, server_addr):
    global thread_status
    interval = 5
    t = None

    while True:
        choice = input("\nt - poslat textovu spravu\ns - poslat subor\nl - odhlasit sa\non/off - zapnut/vypnut keep alive\n")
        if (choice == 'l'):
            if t != None:
                thread_status = False
                t.join()
            switch_users(client_sock, server_addr)
        elif (choice == 't'):
            if t != None:
                thread_status = False
                t.join()
            send_message(client_sock, server_addr)
        elif (choice == 's'):
            if t != None:
                thread_status = False
                t.join()
            send_file(client_sock, server_addr)
        elif (choice == 'on'):
            thread_status = True
            t = start_thread(client_sock, server_addr, interval)
            print("Keep alive zapnute\n")
        elif (choice == 'off'):
            if t != None:
                thread_status = False
                t.join()
        else:
            print("BRUH MOMENT\n")



#......Server funkcie....................................
def server_login():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    port = input("Zadaj port: ")
    server_sock.bind(("", int(port)))
    data, addr = server_sock.recvfrom(1500)
    print("Nadviazane spojenie z adresy ", addr,"\n")
    user_server(server_sock, addr)


def wait_for_msg_repair(server_sock):
    data, addr = server_sock.recvfrom(1500)
    message = data[12:]
    status, packet_num = check_msg_packet(data[:12], message, 1)
    if status == True:
        print("Chybajuci paket doruceny.")
        server_sock.sendto(str.encode("Chybajuci paket prijaty bez chyby"), addr)
        return message.decode(), packet_num
    else:
        server_sock.sendto(str.encode("Stale je niekde chyba :("), addr)
        return message.decode(), packet_num


def wait_for_file_repair(server_sock):
    data, addr = server_sock.recvfrom(1500)
    file_frag = data[8:]
    status, packet_num = check_file_packet(data[:8], file_frag, 1)
    if status == True:
        print("Chybajuci paket doruceny.")
        server_sock.sendto(str.encode("Chybajuci paket prijaty bez chyby"), addr)
    else:
        server_sock.sendto(str.encode("Stale je niekde chyba :("), addr)
    return file_frag, packet_num


def check_msg_packet(head, message, repair):
    packet_num, length, crc = struct.unpack("iii", head)
    header = struct.pack("iii", packet_num, length, 0)
    crc_num = binascii.crc_hqx(header + message, 0)
    if repair == 0:
        if crc_num != crc:
            return False, packet_num
        else:
            return True, packet_num
    elif repair == 1:
        if crc_num + 1 == crc:
            return True, packet_num
        else:
            return False, packet_num


def check_file_packet(head, file_frag, repair):
    packet_num, crc = struct.unpack("ii", head)
    header = struct.pack("ii", packet_num, 0)
    crc_num = binascii.crc_hqx(header + file_frag, 0)
    if repair == 0:
        if crc_num != crc:
            return False, packet_num
        else:
            return True, packet_num
    elif repair == 1:
        if crc_num + 1 == crc:
            return True, packet_num
        else:
            return False, packet_num


def check_missing(packet_bundle, damaged_packets, num_of_packets, all_packets):

    if len(packet_bundle) == 10 or len(damaged_packets) + len(packet_bundle) == int(all_packets):
        return damaged_packets
    else:
        for i in range(1, 11):
            if num_of_packets == int(all_packets) or len(damaged_packets) + len(packet_bundle) == int(all_packets):
                break
            if i in packet_bundle or str(i - 1) in damaged_packets:
                lol = ''
            else:
                if num_of_packets < int(all_packets):
                    num_of_packets += 1
                    damaged_packets += str(i - 1)

        return damaged_packets


def recieve_message(all_packets, server_sock):
    addr = ''
    full_message = []
    num_of_packets = 0

    while True:
        damaged_packets = ''
        packet_bundle = []
        packet_num = 0
        if num_of_packets == int(all_packets):
            break
        while packet_num < 10:
            data, addr = server_sock.recvfrom(1500)
            if len(data) <= 0 or num_of_packets == int(all_packets):
                break
            message = data[12:]
            status, packet_num = check_msg_packet(data[:12], message, 0)
            if status == False:
                damaged_packets += str(packet_num - 1)
            else:
                num_of_packets += 1
                packet_bundle.append(packet_num)
                full_message.append(message.decode())
        if num_of_packets < int(all_packets):
            damaged_packets = check_missing(packet_bundle, damaged_packets, num_of_packets, all_packets)

        if len(damaged_packets) == 0:
            server_sock.sendto(str.encode("OK"), addr)
            print("Pocet spravne dorucenych paketov: ", len(packet_bundle))
        else:
            server_sock.sendto(str.encode(damaged_packets), addr)
            print("Pocet spravne dorucenych paketov: ", len(packet_bundle))
            print("Pocet nespravne dorucenych paketov: ", len(damaged_packets))
            missing, num = wait_for_msg_repair(server_sock)
            full_message.insert(int(num - 1), str(missing))
            packet_bundle.append(packet_num)
            num_of_packets += 1

    print("\nPocet prijatych packetov: " + str(num_of_packets))
    print("Sprava: ", ''.join(full_message))
    user_server(server_sock, addr)


def recieve_file(file_name, server_sock, all_packets):
    data = ''
    addr = ''
    num_of_packets = 0
    file_frags = []

    file = open(file_name, "wb")
    while True:
        damaged_packets = ''
        packet_bundle = []
        packet_num = 0
        while packet_num < 10:
            data, addr = server_sock.recvfrom(1500)
            if len(data) <= 0:
                break
            file_frag = data[8:]
            status, packet_num = check_file_packet(data[:8], file_frag, 0)
            if status == False:
                damaged_packets += str(packet_num - 1)
            else:
                num_of_packets += 1
                packet_bundle.append(packet_num)
                file_frags.append(file_frag)
            if len(packet_bundle) == 10:
                break
        if num_of_packets < int(all_packets):
            damaged_packets = check_missing(packet_bundle, damaged_packets, num_of_packets, all_packets)
        if len(damaged_packets) == 0:
            server_sock.sendto(str.encode("OK"), addr)
            print("Pocet spravne dorucenych paketov: ", len(packet_bundle))
        else:
            server_sock.sendto(str.encode(damaged_packets), addr)
            print("Pocet spravne dorucenych paketov: ", len(packet_bundle))
            print("Pocet nespravne dorucenych paketov: ", len(damaged_packets))
            for i in damaged_packets:
                missing, num = wait_for_file_repair(server_sock)
                file_frags.insert(int(num - 1), missing)
                packet_bundle.append(packet_num)
                num_of_packets += 1

        if len(data) <= 0:
            break

    for frag in file_frags:
        file.write(frag)

    file.close()
    print("\nPocet prijatych packetov: " + str(num_of_packets))
    size = os.path.getsize(file_name)
    print(file_name, "doruceny:", size, "B")
    print("Subor bol ulozeny do:", os.path.abspath(file_name))
    user_server(server_sock, addr)


def user_server(server_sock, addr):
    choice = input("l - odhlasit sa a vypnut server\niny znak - pokracovat\n")
    if (choice == 'l'):
        switch_users(server_sock, addr)
    else:
        print("Server bezi.")
    info = ''

    try:
        server_sock.settimeout(40)
        while True:
            while True:
                data = server_sock.recv(1500)
                if len(data) <= 0:
                    break
                info = str(data.decode())
                if info == '3':
                    print("Spojenie sa udrzuje...")
                    info = ''
                    break
            typ = info[:1]
            if typ == '1':
                all_packets = info[1:]
                print("Pride sprava zlozena z " + all_packets + " paketov\n")
                recieve_message(all_packets, server_sock)
            elif typ == '2':
                all_packets = info[1:]
                file_info = server_sock.recv(1500)
                path = str(file_info.decode())
                if '\\' in str(path):
                    path = path.rsplit('\\', 1)
                    file_name = ''.join(path[1])
                else:
                    file_name = path
                print("Pride subor " + file_name + " zlozeny z ", all_packets, " paketov\n")
                recieve_file(file_name, server_sock, all_packets)

    except socket.timeout:
        print("Klient neaktivny, server sa vypina...\n")
        server_sock.close()
        main()



#......Ostatne...........................................
def switch_users(sock, addr):
    while True:
        choice = input("o - odosielatel\np - prijemca\nk - koniec programu\n")
        if (choice == 'o'):
            user_client(sock, addr)
        elif (choice == 'p'):
            user_server(sock, addr)
        elif (choice == 'k'):
            exit()
        else:
            print("....")


def main():
    while True:
        choice = input("o - odosielatel\np - prijemca\nk - koniec programu\n")
        if (choice == 'o'):
            client_login()
        elif (choice == 'p'):
            server_login()
        elif (choice == 'k'):
            exit()
        else:
            print("....")


main()