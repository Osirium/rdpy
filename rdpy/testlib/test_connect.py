from .test_client import RDPTestClientFactory
import rdpy.core.log as log

from twisted.internet import reactor, defer


@defer.inlineCallbacks
def connect(host, port, username, password):
    """
    @summary: Connect to a RDP server with the provided details, waits until as
    session has been established, or times out.
    @param host:
    @param port:
    @param username:
    @param password:
    @param connect_timeout: Time to wait for the connection.
    @return: RDPClientTestFactory which holds the connection to the
    server. use factory.loggedIn to determine if it is connected.
    """
    log.info("Connecting to %s:%d" % (host, port))
    factory = RDPTestClientFactory(username, password)
    reactor.callLater(10, factory.startDeferred.cancel)

    reactor.connectTCP(host, port, factory)
    result = yield factory.startDeferred
    defer.returnValue(result)
