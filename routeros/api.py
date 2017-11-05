from socket import SHUT_RDWR, error as SOCKET_ERROR
from struct import pack, unpack

from routeros.exc import ConnectionError


class Socket:
    def __init__(self, sock):
        self.sock = sock

    def write(self, string):
        """
        Write given bytes string to socket. Loop as long as every byte in
        string is written unless exception is raised.
        :param string: string to write on socket.
        """
        try:
            self.sock.sendall(string)
        except OSError as exc:
            raise ConnectionError('Failed to write on socket. {0}'.format(exc))

    def read(self, length):
        """
        Read as many bytes from socket as specified in length.
        Loop as long as every byte is read unless exception is raised.
        :param length: length to read on socket.
        :return: data (string) received from socket.
        """
        try:
            data = self.sock.recv(length)
            if not data:
                raise ConnectionError('Connection was closed.')
            return data
        except OSError as exc:
            raise ConnectionError('Failed to read from socket. {0}'.format(exc))

    def close(self):
        """
        Close connection with the socket.
        """
        try:
            # inform other end that we will not read and write any more
            self.sock.shutdown(SHUT_RDWR)
        except SOCKET_ERROR:
            pass
        finally:
            self.sock.close()


class LengthUtils:
    @staticmethod
    def encode_length(length):
        if length < 0x80:
            new_length = length
            offset = -1
        elif length < 0x4000:
            new_length = length | 0x8000
            offset = -2
        elif length < 0x200000:
            new_length = length | 0xC00000
            offset = -3
        elif length < 0x10000000:
            new_length = length | 0xE0000000
            offset = -4
        else:
            raise ConnectionError('Unable to encode length of {}'.format(length))
        return pack('!I', new_length)[offset:]

    @staticmethod
    def decode_bytes(bytes):
        length = len(bytes)
        if length < 2:
            offset = b'\x00\x00\x00'
            xor = 0
        elif length < 3:
            offset = b'\x00\x00'
            xor = 0x8000
        elif length < 4:
            offset = b'\x00'
            xor = 0xC00000
        elif length < 5:
            offset = b''
            xor = 0xE0000000
        else:
            raise ConnectionError('Unable to decode length of {}'.format(length))

        decoded = unpack('!I', (offset + bytes))[0]
        decoded ^= xor
        return decoded
