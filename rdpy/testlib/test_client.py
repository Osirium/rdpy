from rdpy.protocol.rdp import rdp
import rdpy.core.log as log
from threading import Event
import socket


class RDPTestClient(rdp.RDPClientObserver):
    """
    @summary: Connection Object that receives session events from the twisted
    stack and the remote server
    """

    def __init__(self, controller,
                 width, height,
                 startedEvent, stoppedEvent):
        rdp.RDPClientObserver.__init__(self, controller)
        controller.setScreen(width, height)

        self.hasInitialised = False
        self.hasSession = False
        self._startedEvent = startedEvent
        self._stoppedEvent = stoppedEvent

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
        self._startedEvent.set()

    def onClose(self):
        """
        @summary: Called when the connection parts are closed and sets the
        stoppedEvent
        """
        self.hasSession = False
        self.hasInitialised = False
        self._stoppedEvent.set()

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
        self._controller.close()


class RDPTestClientFactory(rdp.ClientFactory):
    """
    @summary: Builds connection to an RDP Server.
    """

    def __init__(self, username, password, startedEvent):
        self._username = username
        self._passwod = password

        self.stopped = False
        self.reason = None
        self._startedEvent = startedEvent
        self._stoppedEvent = Event()

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
            self._startedEvent, self._stoppedEvent
        )
        controller.setUsername(self._username)
        controller.setPassword(self._passwod)
        controller.setDomain(".")
        controller.setKeyboardLayout("en")
        controller.setHostname(socket.gethostname())

        controller.setSecurityLevel(rdp.SecurityLevel.RDP_LEVEL_NLA)
        return self._client

    def clientConnectionLost(self, connector, reason):
        """
        @summary: Connection Lost event, will set both events
        @param connector: twisted connector use for rdp connection
        @param reason: FailureInstance explaining why the connection is lost
        """
        log.info("Lost connection : %s" % reason.msg)

        self.stopped = True
        self.reason = reason
        self._stoppedEvent.set()
        self._startedEvent.set()

    def clientConnectionFailed(self, connector, reason):
        """
        @summary: Connection failed event
        @param connector: twisted connector use for rdp connection (use
        reconnect to restart connection)
        @param reason: str use to advertise reason of lost connection
        """
        log.info("Connection failed : %s" % reason)

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
        self._client.close()
        if self._stoppedEvent.wait(5.0):
            raise RuntimeError("Could not close connection")
