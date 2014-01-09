from clarent import certificate, exercise, path
from twisted.internet import endpoints, protocol, reactor
from twisted.protocols import amp
from txampext import multiplexing


class Protocol(multiplexing.ProxyingAMPLocator, amp.AMP):
    """Stanczyk's client AMP protocol.

    """
    @property
    def namespace(self):
        return self.factory.namespace


    @exercise.NotifySolved.responder
    def notifySolved(self, identifier, title):
        """Notifies the user that they have completed an exercise.

        """
        template = "\nCongratulations! You have solved the {} excercise ({})."
        line = template.format(identifier, title)
        self.namespace["manhole"].overwriteLine(line)
        return {}



class Factory(protocol.ReconnectingClientFactory):
    """A factory that will reconnect (with exponential backoff).

    """
    protocol = Protocol

    def __init__(self, namespace):
        self.namespace = namespace



def connect(namespace, _reactor=reactor):
    """Connects to the Crypto 101 exercise server.

    """
    endpoint = _makeEndpoint(_reactor)
    d = endpoint.connect(Factory(namespace))
    d.addCallback(_storeRemote, namespace=namespace)

    return None # don't return the deferred, or the REPL will display it


def _storeRemote(remote, namespace):
    """Stores the remote in the namespace; reports success to console.

    """
    namespace["remote"] = remote
    namespace["manhole"].overwriteLine("Connected to the exercise server!")


def _makeEndpoint(reactor):
    ctxFactory = certificate.getContextFactory(path.getDataPath())
    return endpoints.SSL4ClientEndpoint(reactor, "localhost", 4430, ctxFactory)
