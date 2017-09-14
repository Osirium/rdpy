from .test_client import RDPTestClientFactory
import rdpy.core.log as log
from threading import Event

from twisted.internet import reactor, threads


def connect(host, port, username, password, connect_timeout=10.0):
    """
    @summary: Connect to a RDP server with the provided details, waits until as
    session has been established, or times out.
    @param host: server
    @param port: port
    @param username:
    @param password:
    @param connect_timeout: Time to wait for the connection.
    @return: RDPClientTestFactory which holds the connection to the
    server. use factory.loggedIn to determine if it is connected.
    """
    log.info("Connecting to %s@%s:%d" % (username, host, port))
    started_cond = Event()
    factory = RDPTestClientFactory(
        username, password,
        started_cond)
    reactor.callFromThread(reactor.connectTCP, host, port, factory)
    started_cond.wait(connect_timeout)
    return factory


class RDPTestConnManager(object):
    """
    @summary: Handles multiple connections to a server, can be used in a with
    statement.
    """

    def __init__(self):
        self.factories = []

    def connect(self, host, port, username, password):
        """
        @summary: Calls connect with given params, holding the factory created.
        """
        assert reactor.running, "Twisted reactor is not running"

        factory = connect(host, port, username, password)
        self.factories.append(factory)
        return factory

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if reactor.running:
            self.end()

    def end(self):
        """
        @summary: Closes all connections
        """
        for factory in self.factories:
            threads.deferToThread(factory.stop)
