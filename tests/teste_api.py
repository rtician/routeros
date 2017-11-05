import unittest
from unittest.mock import Mock
from socket import SHUT_RDWR, error as SOCKET_ERROR

from routeros.api import Socket
from routeros.exc import ConnectionError


class TestSocket(unittest.TestCase):
    def setUp(self):
        self.transport = Socket(sock=Mock(sock='socket'))

    def test_calls_sendall(self):
        self.transport.write(b'foo bar')
        self.transport.sock.sendall.assert_called_once_with(b'foo bar')

    def test_calls_shutdown(self):
        self.transport.close()
        self.transport.sock.shutdown.assert_called_once_with(SHUT_RDWR)

    def test_close_shutdown_exception(self):
        self.transport.sock.shutdown.side_effect = SOCKET_ERROR
        self.transport.close()
        self.transport.sock.close.assert_called_once_with()

    def test_close(self):
        self.transport.close()
        self.transport.sock.close.assert_called_once_with()

    def test_write_raises_socket_errors(self):
        self.transport.sock.sendall.side_effect = SOCKET_ERROR
        with self.assertRaises(ConnectionError):
            self.transport.write(b'foo bar')

    def test_read_raises_when_recv_returns_empty_byte_string(self):
        self.transport.sock.recv.return_value = b''
        for length in (0, 3):
            with self.assertRaises(ConnectionError):
                self.transport.read(length)

    def test_read_returns_from_recv(self):
        self.transport.sock.recv.return_value = b'bar foo'
        assert self.transport.read(1024) == b'bar foo'

    def test_recv_raises_socket_errors(self):
        self.transport.sock.recv.side_effect = SOCKET_ERROR
        with self.assertRaises(ConnectionError):
            self.transport.read(2)
