from rdpy.protocol.rdp import rdp
import rdpy.core.log as log
from twisted.internet import defer
import socket


def raiseTimeout(failure):
    raise RuntimeError("Unable to connect to server")


class RDPTestClient(rdp.RDPClientObserver):
    """
    @summary: Connection Object that receives session events from the twisted
    stack and the remote server
    """

    def __init__(self, controller,
                 width, height,
                 startedDefer):
        rdp.RDPClientObserver.__init__(self, controller)
        controller.setScreen(width, height)

        self.hasInitialised = False
        self.hasSession = False
        self._startedDefer = startedDefer
        self._startedDefer.addErrback(raiseTimeout)

    def onReady(self):
        """
        @summary: Called when stack is ready
        """
        self.hasInitialised = True

    def onSessionReady(self):
        """
        @summary: Windows Session Reported Ready
        """
        self.hasSession = True
        try:
            self._startedDefer.callback(self)
        # onSessionReady is called twice
        except defer.AlreadyCalledError:
            pass

    def onClose(self):
        """
        @summary: Called when the connection parts are closed and sets the
        stoppedEvent
        """
        self.hasSession = False
        self.hasInitialised = False

        self._stoppedDefer.callback(self)

    def onUpdate(self, destLeft, destTop, destRight, destBottom, width, height, bitsPerPixel, isCompress, data):
        """
        @summary: callback use when bitmap is received
        """
        pass

    @property
    def loggedIn(self):
        """
        Reports that we have a session with the target server
        """
        return self.hasInitialised and self.hasSession

    def close(self):
        """
        @summary close this connection
        """
        log.info("Stopping client")
        self._controller.close()


class RDPTestClientFactory(rdp.ClientFactory):
    """
    @summary: Builds connection to an RDP Server.
    """

    def __init__(self, username, password):
        self._username = username
        self._passwod = password

        self.stopped = False
        self.reason = None
        self.startDeferred = defer.Deferred()

    def buildObserver(self, controller, addr):
        """
        @summary: Builds a RDPClientTest
        @param controller: build factory and needed by observer
        @param addr: destination address
        @return: RDPTestClient
        """
        self._client = RDPTestClient(
            controller,
            1024, 768,
            self.startDeferred
        )
        controller.setUsername(self._username)
        controller.setPassword(self._passwod)
        controller.setDomain(".")
        controller.setKeyboardLayout("en")
        controller.setHostname(socket.gethostname())

        controller.setSecurityLevel(rdp.SecurityLevel.RDP_LEVEL_NLA)
        return self._client

    @property
    def loggedIn(self):
        """
        @summary: Reports the connection state of the client.
        """
        return self._client.loggedIn

    def stop(self):
        """
        @summary: Calls to stop the client and waits for the stopped event.
        @raises RuntimeError: If the client is not closed in 5s
        """
        return self._client.close()
