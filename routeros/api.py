from socket import SHUT_RDWR, error as SOCKET_ERROR
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
