import unittest
from unittest.mock import Mock
from collections import namedtuple
from socket import SHUT_RDWR, error as SOCKET_ERROR

from routeros.api import Socket, APIUtils
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


class TestLengthUtils(unittest.TestCase):
    def setUp(self):
        self.encoder = APIUtils.encode_length
        self.decoder = APIUtils.decode_bytes

        lengths = namedtuple('lengths', ('integer', 'encoded'))
        self.valid_lengths = [
            lengths(integer=0, encoded=b'\x00'),
            lengths(integer=127, encoded=b'\x7f'),
            lengths(integer=130, encoded=b'\x80\x82'),
            lengths(integer=2097140, encoded=b'\xdf\xff\xf4'),
            lengths(integer=268435440, encoded=b'\xef\xff\xff\xf0'),
        ]

    def test_encode_length(self):
        for valid_length in self.valid_lengths:
            result = self.encoder(valid_length.integer)
            self.assertEqual(result, valid_length.encoded)

    def test_encode_length_raises_if_lenghth_is_too_big(self):
        # length must be < 268435456
        invalid_length = 268435456

        with self.assertRaises(ConnectionError):
            self.encoder(invalid_length)

    def test_decodeLength(self):
        for valid_length in self.valid_lengths:
            result = self.decoder(valid_length.encoded)
            self.assertEqual(result, valid_length.integer)

    def test_decodeLength_raises(self):
        # len(length) must be < 5
        invalid_bytes =b'\xff\xff\xff\xff\xff'

        with self.assertRaises(ConnectionError):
            self.decoder(invalid_bytes)
