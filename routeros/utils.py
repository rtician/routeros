from socket import SHUT_RDWR, error as SOCKET_ERROR, timeout as SOCKET_TIMEOUT
from struct import pack, unpack

from routeros.exc import ConnectionError, FatalError


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
        except SOCKET_TIMEOUT as exc:
            raise ConnectionError('Socket timed out. ' + str(exc))
        except SOCKET_ERROR as exc:
            raise ConnectionError('Failed to write to socket. ' + str(exc))

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
        except SOCKET_TIMEOUT as exc:
            raise ConnectionError('Socket timed out. ' + str(exc))
        except SOCKET_ERROR as exc:
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


class APIUtils:
    @staticmethod
    def encode_length(length):
        """
        Decode length based on given bytes.

        :param length: bytes string to decode.
        :return: decoded length.
        """
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

    def encode_word(self, encoding, word):
        """
        Encode word in API format.

        :param word: Word to encode.
        :param encoding: encoding type.
        :return: encoded word.
        """
        encoded_word = word.encode(encoding=encoding, errors='strict')
        return self.encode_length(len(word)) + encoded_word

    def encode_sentence(self, encoding, *words):
        """
        Encode given sentence in API format.

        :param words: Words to encode.
        :param encoding: encoding type.
        :returns: Encoded sentence.
        """
        encoded = [self.encode_word(encoding, word) for word in words]
        encoded = b''.join(encoded)
        # append EOS (end of sentence) byte
        encoded += b'\x00'
        return encoded

    @staticmethod
    def decode_bytes(bytes):
        """
        Decode length based on given bytes.

        :param bytes: bytes string to decode.
        :return: decoded length.
        """
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

    @staticmethod
    def determine_length(length):
        """
        Given first read byte, determine how many more bytes
        needs to be known in order to get fully encoded length.

        :param length: first read byte.
        :return: how many bytes to read.
        """
        integer = ord(length)

        if integer < 128:
            return 0
        elif integer < 192:
            return 1
        elif integer < 224:
            return 2
        elif integer < 240:
            return 3
        else:
            raise ConnectionError('Unknown controll byte {}'.format(length))

    def decode_sentence(self, encoding, sentence):
        """
        Decode given sentence.


        :param encoding: encoding type.
        :param sentence: bytes string with sentence (without ending \x00 EOS byte).
        :return: tuple with decoded words.
        """
        words = []
        start, end = 0, 1
        while end < len(sentence):
            end += self.determine_length(sentence[start:end])
            word_length = self.decode_bytes(sentence[start:end])
            words.append(sentence[end:word_length+end])
            start, end = end + word_length, end + word_length + 1
        return tuple(word.decode(encoding=encoding, errors='strict') for word in words)


class API(APIUtils):
    def __init__(self, transport, encoding):
        self.transport = transport
        self.encoding = encoding

    def write_sentence(self, command, *words):
        """
        Write encoded sentence.

        :param command: Command word.
        :param words: Parameter words.
        """
        encoded = self.encode_sentence(self.encoding, command, *words)
        self.transport.write(encoded)

    def read_sentence(self):
        """
        Read every word until empty word (NULL byte) is received.

        :return: Reply word, tuple with read words.
        """
        sentence = tuple(word for word in iter(self.read_word, None))
        reply_word, words = sentence[0], sentence[1:]
        if reply_word == '!fatal':
            self.transport.close()
            raise FatalError(words[0])
        else:
            return reply_word, words

    def read_word(self):
        bytes = self.transport.read(1)
        read = self.determine_length(bytes)
        if read:
            bytes += self.transport.read(read)

        bytes = self.decode_bytes(bytes)
        if not bytes:
            return
        return self.transport.read(bytes).decode(encoding=self.encoding, errors='strict')

    def close(self):
        self.transport.close()
