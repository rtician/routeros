# -*- coding: UTF-8 -*-
from socket import create_connection, error as SOCKET_ERROR, timeout as SOCKET_TIMEOUT
from binascii import unhexlify, hexlify
from hashlib import md5

from routeros.exc import TrapError, FatalError, ConnectionError
from routeros.utils import API, Socket
from routeros.api import RouterOS


def login(username, password, host, port=8728, use_old_login_method=False):
    """
    Connect and login to routeros device.
    Upon success return a RouterOS class.

    :param username: Username to login with.
    :param password: Password to login with. Only ASCII characters allowed.
    :param host: Hostname to connect to. May be ipv4,ipv6, FQDN.
    :param port: Destination port to be used. Defaults to 8728.
    """
    transport = create_transport(host, port)
    protocol = API(transport=transport, encoding='ASCII')
    routeros = RouterOS(protocol=protocol)

    try:
        if use_old_login_method:                # Login method pre-v6.43
            sentence = routeros('/login')
            token = sentence[0]['ret']
            encoded = encode_password(token, password)
            routeros('/login', **{'name': username, 'response': encoded})
        else:                                   # Login method post-v6.43
            routeros('/login', **{'name': username, 'password': password})
    except (ConnectionError, TrapError, FatalError):
        transport.close()
        raise

    return routeros


def create_transport(host, port):
    """
    Create a connection with host and return a open Socket
    :param host: Hostname to connect to. May be ipv4,ipv6, FQDN.
    :param port: Destination port to be used.
    :return: Socket.
    """
    try:
        sock = create_connection(address=(host, port), timeout=10)
    except (SOCKET_ERROR, SOCKET_TIMEOUT) as error:
        raise ConnectionError(error)
    return Socket(sock=sock)


def encode_password(token, password):
    """
    Encode a password token receive from routeros login attempt.
    :param token: token returned from routeros.
    :param password: password to login with. Only ASCII characters allowed.
    :return: A valid password to connect on routeros. 
    """
    token = token.encode('ascii', 'strict')
    token = unhexlify(token)
    password = password.encode('ascii', 'strict')
    md = md5()
    md.update(b'\x00' + password + token)
    password = hexlify(md.digest())
    return '00' + password.decode('ascii', 'strict')
