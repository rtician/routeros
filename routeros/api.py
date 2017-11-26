from routeros.exc import TrapError


class Parser:
    @staticmethod
    def parse_word(word):
        """
        Split given attribute word to key, value pair.
        Values are casted to python equivalents.

        :param word: API word.
        :returns: Key, value pair.
        """
        _, key, value = word.split('=', 2)
        return key, value

    @staticmethod
    def compose_word(key, value):
        '''
        Create a attribute word from key, value pair.
        Values are casted to api equivalents.
        '''
        return '={0}={1}'.format(key, value)


class Query:
    def __init__(self, api, command):
        self.api = api
        self.command = command

    def has(self, *args):
        words = ['?{0}'.format(arg) for arg in args]
        return self.api(self.command, *words)

    def hasnot(self, *args):
        words = ['?-{0}'.format(arg) for arg in args]
        return self.api(self.command, *words)

    def equal(self, **kwargs):
        words = ['?={0}={1}'.format(key, value) for key, value in kwargs.items()]
        return self.api(self.command, *words)

    def lower(self, **kwargs):
        words = ['?<{0}={1}'.format(key, value) for key, value in kwargs.items()]
        return self.api(self.command, *words)

    def greater(self, **kwargs):
        words = ['?>{0}={1}'.format(key, value) for key, value in kwargs.items()]
        return self.api(self.command, *words)


class RouterOS(Parser):
    def __init__(self, protocol):
        self.protocol = protocol

    def __call__(self, command, *args, **kwargs):
        """
        Call Api with given command.

        :param command: Command word. eg. /ip/address/print
        :param args: List with optional arguments, most used for query commands.
        :param kwargs: Dictionary with optional arguments.
        """
        if kwargs:
            args = tuple(self.compose_word(key, value) for key, value in kwargs.items())

        self.protocol.write_sentence(command, *args)
        return self._read_response()

    def query(self, command):
        return Query(self, command)

    def _read_sentence(self):
        """
        Read one sentence and parse words.

        :returns: Reply word, dict with attribute words.
        """
        reply_word, words = self.protocol.read_sentence()
        words = dict(self.parse_word(word) for word in words)
        return reply_word, words

    def _read_response(self):
        """
        Read until !done is received.

        :throws TrapError: If one !trap is received.
        :returns: Full response
        """
        response = []
        reply_word = None
        while reply_word != '!done':
            reply_word, words = self._read_sentence()
            response.append((reply_word, words))

        if '!trap' in response:
            raise TrapError()
        # Remove empty sentences
        return tuple(words for reply_word, words in response if words)

    def close(self):
        self.protocol.close()
