import unittest
from unittest.mock import Mock, patch
from collections import namedtuple
from struct import pack
from socket import SHUT_RDWR, error as SOCKET_ERROR

from routeros.utils import Socket, API, APIUtils
from routeros.exc import ConnectionError, FatalError


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
        self.determine_length = APIUtils.determine_length

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

    def test_decode_length(self):
        for valid_length in self.valid_lengths:
            result = self.decoder(valid_length.encoded)
            self.assertEqual(result, valid_length.integer)

    def test_decode_length_raises(self):
        # len(length) must be < 5
        invalid_bytes = b'\xff\xff\xff\xff\xff'

        with self.assertRaises(ConnectionError):
            self.decoder(invalid_bytes)

    def test_determine_length(self):
        bytes = [
            (b'x', 0),  # 120
            (b'\xbf', 1),  # 191
            (b'\xdf', 2),  # 223
            (b'\xef', 3),  # 239
        ]
        for length, expected in bytes:
            self.assertEqual(self.determine_length(length), expected)

    def test_determine_length_raises(self):
        # First byte of length must be < 240.
        invalid_lengths = (pack('>B', i) for i in range(240, 256))
        for invalid_length in invalid_lengths:
            with self.assertRaises(ConnectionError):
                self.determine_length(invalid_length)


class TestWordUtils(unittest.TestCase):
    def setUp(self):
        self.encoder = APIUtils().encode_word

    def test_encode_word(self):
        with patch('routeros.utils.APIUtils.encode_length', return_value=b'len_') as encoder:
            self.assertEqual(self.encoder('ASCII', 'word'), b'len_word')
            self.assertEqual(encoder.call_count, 1)

    def test_non_ASCII_word_encoding(self):
        # Word may only contain ASCII characters.
        word = b'\xc5\x82\xc4\x85'.decode('utf-8')
        with self.assertRaises(UnicodeEncodeError):
            self.encoder('ASCII', word)

    def test_utf_8_word_encoding(self):
        # Assert that utf-8 encoding works.
        expected_bytes = b'\x02\xc5\x82\xc4\x85'
        self.assertEqual(self.encoder('utf-8', 'łą'), expected_bytes)


class TestSentenceUtils(unittest.TestCase):
    def setUp(self):
        self.encoder = APIUtils().encode_sentence
        self.decoder = APIUtils().decode_sentence

    def test_encode_sentence(self):
        with patch('routeros.utils.APIUtils.encode_word', return_value=b'') as encoder:
            encoded = self.encoder('ASCII', 'first', 'second')
            self.assertEqual(encoder.call_count, 2)
            self.assertEqual(encoded[-1:], b'\x00')

    def test_decode_sentence(self):
        sentence = b'\x11/ip/address/print\x05first\x06second'
        expected = ('/ip/address/print', 'first', 'second')
        self.assertEqual(self.decoder('ASCII', sentence), expected)

    def test_decode_sentence_non_ASCII(self):
        # Word may only contain ASCII characters.
        sentence = b'\x12/ip/addres\xc5\x82/print\x05first\x06second'
        with self.assertRaises(UnicodeDecodeError):
            self.decoder('ASCII', sentence)

    def test_decode_sentence_utf_8(self):
        # Assert that utf-8 encoding works.
        sentence = b'\x12/ip/addres\xc5\x82/print\x05first\x06second'
        self.assertEqual(self.decoder('utf-8', sentence),
                         ('/ip/addresł/print', 'first', 'second'))


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.api = API(transport=Mock(spec=Socket), encoding='ASCII')

    def test_write_sentence_calls_encode_sentence(self):
        with patch('routeros.utils.APIUtils.encode_sentence') as encoder:
            self.api.write_sentence('/ip/address/print', '=key=value')
            encoder.assert_called_once_with('ASCII', '/ip/address/print', '=key=value')

    def test_write_sentence_calls_transport_write(self):
        # Assert that write is called with encoded sentence.
        with patch('routeros.utils.APIUtils.encode_sentence') as encoder:
            self.api.write_sentence('/ip/address/print', '=key=value')
            self.api.transport.write.assert_called_once_with(encoder.return_value)

    def test_readSentence_raises_FatalError(self):
        # Assert that FatalError is raised with its reason.
        with patch('routeros.utils.iter', return_value=('!fatal', 'reason')):
            with self.assertRaises(FatalError):
                self.api.read_sentence()
            self.assertEqual(self.api.transport.close.call_count, 1)

    def test_close(self):
        self.api.close()
        self.api.transport.close.assert_called_once_with()
