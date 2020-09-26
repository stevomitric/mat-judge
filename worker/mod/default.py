'''
General utill file for unclasified functions/classes
'''

import json, copy

# Default settings for sockets
SERVER = {
    'ip': '192.168.0.114',
    'port': 29595,
}

NOT_FOUND = -99998

SOCKET_RECV_FAILED = -99995
SOCKET_RECV_EMPTY = -99994
SOCKET_RECV_TIMEOUT = -99993

# Logging out messages to STDOUT (or file)
class Logging:
    def __init__(self):
        # TODO: implement these
        self.VERBOSE = True
        self.WRITE_TO_FILE = False

    def write(self, msg, state = 'info'):
        print(state.upper() +": "+ str(msg) )

def __socket_calc_bytes_needed(number):
    bytes_needed, can_store = 1, 256
    while (number >= can_store):
        can_store *= 256
        bytes_needed += 1
    return bytes_needed


def socket_protocol_create_request(data_arguments_):
    ''' Convert all arguments to byte objects and return it'''

    data_arguments = copy.deepcopy(data_arguments_)

    # Map their size, and size of their size (?)
    arguments_data = []
    for inx, arg in enumerate(data_arguments[:] ):
        data_arguments[inx] = bytes(str(arg).encode())
        arguments_data.append( ( __socket_calc_bytes_needed(len(data_arguments[inx])) , len(data_arguments[inx]) ))

    encoded_message = b''
    for i in range(len(data_arguments)):
        first_byte = (arguments_data[i][0]).to_bytes(1, byteorder="big")
        byte_block_1 = (arguments_data[i][1]).to_bytes(arguments_data[i][0], byteorder="big")
        byte_block_2 = data_arguments[i]

        encoded_message += first_byte + byte_block_1 + byte_block_2

    encoded_message += (255).to_bytes(1, byteorder="big")
    return encoded_message

def __socket_raw_recieve(socket, buff, close_on_timeout = True):
    data = b''
    while (len(data) < buff):
        try:
            single_byte = socket.recv(1)
        except Exception as e:
            if 'timed out' in str(e):
                if close_on_timeout:
                    socket.close()
                    log.write("Socket closed due to timeout")
                return SOCKET_RECV_TIMEOUT

            socket.close()
            log.write("Socket closed due to failing to read byte")
            return SOCKET_RECV_FAILED

        if not single_byte:
            socket.close()
            log.write("Socket closed due to recieving terminate signal")
            return SOCKET_RECV_EMPTY

        data += single_byte

    return data

def __socket_flush(socket):
    ''' Removes all socket data untill terminate character 255'''
    while 1:
        byte = __socket_raw_recieve(socket, 1)
        if byte == SOCKET_RECV_EMPTY or byte == SOCKET_RECV_FAILED:
            return byte
        byte_int = int.from_bytes(byte, 'big')
        if byte_int == 255:
            break
    return 0

def socket_protocol_recieve(socket, close_on_timeout = True):
    ''' recieve request from socket recv and transform to arguments object '''
    data_arguments = []    
    
    while 1:
        byte1 = __socket_raw_recieve(socket, 1, close_on_timeout=close_on_timeout)
        if byte1 == SOCKET_RECV_EMPTY or byte1 == SOCKET_RECV_FAILED or byte1 == SOCKET_RECV_TIMEOUT:
            return byte1

        first_byte = int.from_bytes(byte1, 'big')
        # End of message
        if first_byte == 255:
            break

        byte2 = __socket_raw_recieve(socket, first_byte)
        if byte2 == SOCKET_RECV_EMPTY or byte2 == SOCKET_RECV_FAILED or byte2 == SOCKET_RECV_TIMEOUT:
            return byte2
        byte_block1 = int.from_bytes(byte2, 'big')

        byte3 = __socket_raw_recieve(socket, byte_block1)
        if byte3 == SOCKET_RECV_EMPTY or byte3 == SOCKET_RECV_FAILED or byte3 == SOCKET_RECV_TIMEOUT:
            return byte3
        byte_block2 = byte3

        data_arguments.append(byte_block2.decode())

    # Fill up to 10
    while len(data_arguments) < 10:
        data_arguments.append('')

    return data_arguments

log = Logging()