import unittest
from unittest.mock import patch
from socket import error as SOCKET_ERROR, timeout as SOCKET_TIMEOUT

from routeros import encode_password, create_transport, ConnectionError


class TestLogin(unittest.TestCase):
    def test_password_encoding(self):
        expected_value = '00c7fd865183a43a772dde231f6d0bff13'
        self.assertEqual(encode_password('259e0bc05acd6f46926dc2f809ed1bba', 'test'),
                         expected_value)

    def test_non_ascii_password_encoding(self):
        # Only ascii characters are allowed in password.
        with self.assertRaises(UnicodeEncodeError):
            encode_password(
                token='259e0bc05acd6f46926dc2f809ed1bba',
                password=b'\xc5\x82\xc4\x85'.decode('utf-8')
            )

    def test_create_transport_calls_create_connection(self):
        with patch('routeros.create_connection') as connection:
            create_transport(host='127.0.0.1', port=9099)
            connection.assert_called_once_with(address=('127.0.0.1', 9099), timeout=10)

    def test_create_transport_raises_connection_error(self):
        for error in (SOCKET_ERROR, SOCKET_TIMEOUT):
            with patch('routeros.create_connection') as connection:
                connection.side_effect = error
                with self.assertRaises(ConnectionError):
                    create_transport(host='127.0.0.1', port=9099)

    def test_create_transport_calls_socket(self):
        with patch('routeros.Socket') as socket:
            with patch('routeros.create_connection') as connection:
                a = create_transport(host='127.0.0.1', port=9099)
                socket.assert_called_once_with(sock=connection.return_value)
