
import pickle
import os
import argparse
import six
import txaio
import json
from configparser import ConfigParser

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.logger import Logger
from twisted.internet import threads

import autobahn
from autobahn.twisted.util import sleep
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from autobahn.wamp.exception import ApplicationError
from autobahn.websocket.protocol import WebSocketClientFactory
from autobahn.wamp.types import RegisterOptions
from autobahn.wamp import auth

from neuroarch_nlp.interface import Translator
from version import __version__


# Grab configuration from file
root = os.path.expanduser("/")
home = os.path.expanduser("~")
filepath = os.path.dirname(os.path.abspath(__file__))
config_files = []
config_files.append(os.path.join(home, ".ffbo/config", "ffbo.nlp_component.ini"))
config_files.append(os.path.join(root, ".ffbo/config", "ffbo.nlp_component.ini"))
config_files.append(os.path.join(home, ".ffbo/config", "config.ini"))
config_files.append(os.path.join(root, ".ffbo/config", "config.ini"))
config_files.append(os.path.join(filepath, "config.ini"))
config = ConfigParser()
configured = False
file_type = 0
for config_file in config_files:
    if os.path.exists(config_file):
        config.read(config_file)
        configured = True
        break
    file_type += 1
if not configured:
    raise Exception("No config file exists for this component")

user = config["USER"]["user"]
secret = config["USER"]["secret"]
ssl = eval(config["AUTH"]["ssl"])
websockets = "wss" if ssl else "ws"
if "ip" in config["SERVER"]:
    ip = config["SERVER"]["ip"]
else:
    ip = "localhost"
if ip in ["localhost", "127.0.0.1"]:
    port = config["NLP"]["port"]
else:
    port = config["NLP"]["expose-port"]
url = "%(ws)s://%(ip)s:%(port)s/ws" % {"ws":websockets, "ip":ip, "port":port}
realm = config["SERVER"]["realm"]
authentication = eval(config["AUTH"]["authentication"])
debug = eval(config["DEBUG"]["debug"])
ca_cert_file = config["AUTH"]["ca_cert_file"]
intermediate_cert_file = config["AUTH"]["intermediate_cert_file"]

class AppSession(ApplicationSession):

    log = Logger()

    def onConnect(self):
        setProtocolOptions(self._transport,
                           maxFramePayloadSize = 0,
                           maxMessagePayloadSize = 0,
                           autoFragmentSize = 65536)
        if self.config.extra['auth']:
            self.join(self.config.realm, [u"wampcra"], user)
        else:
            self.join(self.config.realm, [], user)

        self.app_name = str(self.config.extra['app'])
        self.dataset = str(self.config.extra['dataset'])
        self.name = str(self.config.extra['name'])

    def onChallenge(self, challenge):
        if challenge.method == "wampcra":
            #print("WAMP-CRA challenge received: {}".format(challenge))

            if 'salt' in challenge.extra:
                # salted secret
                key = auth.derive_key(secret,
                                      challenge.extra['salt'],
                                      challenge.extra['iterations'],
                                      challenge.extra['keylen'])
            else:
                # plain, unsalted secret
                key = secret

            # compute signature for challenge, using the key
            signature = auth.compute_wcs(key, challenge.extra['challenge'])

            # return the signature to the router for verification
            return signature

        else:
            raise Exception("Invalid authmethod {}".format(challenge.method))

    @inlineCallbacks
    def onJoin(self, details):
        server = Translator(self.app_name)

        translators = {}

        self.server_config = {six.u('name'): six.u(self.name),
                              six.u('dataset'): six.u(self.dataset),
                              six.u('autobahn'): autobahn.__version__,
                              six.u('version'): __version__}

        #@inlineCallbacks
        def nlp_query(query,language='en'):
            self.log.info("nlp_query() called with query {query} with supplied language {language} " , language=language, query=query)
            if language in  translators:
                # Translate to English
                query = translators[language](query)
                self.log.info("nlp_query() detected language {language}. Query translated to: {query}", language=language, query=query)
            else:
                # assume English. This will cover English queries tagged as a crazy language.
                pass

            res = server.nlp_query(query)
            return res

        uri = six.u('ffbo.nlp.query.%s' % (str(details.session)))
        yield self.register(nlp_query, uri,options=RegisterOptions(concurrency=10))
        self.log.info('procedure %s registered' % uri)

        # Listen for ffbo.processor.connected
        @inlineCallbacks
        def register_component():
            self.log.info( "Registering a component")
            # CALL server registration
            try:
                # registered the procedure we would like to call
                res = yield self.call(six.u('ffbo.server.register'), details.session,
                                      six.u('nlp'), self.server_config)
                self.log.info("register new server called with result: {result}",
                                                    result=res)

            except ApplicationError as e:
                if e.error != 'wamp.error.no_such_procedure':
                    raise e

        yield self.subscribe(register_component, six.u('ffbo.processor.connected'))
        self.log.info("subscribed to topic 'ffbo.processor.connected'")

        register_component()


def setProtocolOptions(transport,
                       version=None,
                       utf8validateIncoming=None,
                       acceptMaskedServerFrames=None,
                       maskClientFrames=None,
                       applyMask=None,
                       maxFramePayloadSize=None,
                       maxMessagePayloadSize=None,
                       autoFragmentSize=None,
                       failByDrop=None,
                       echoCloseCodeReason=None,
                       serverConnectionDropTimeout=None,
                       openHandshakeTimeout=None,
                       closeHandshakeTimeout=None,
                       tcpNoDelay=None,
                       perMessageCompressionOffers=None,
                       perMessageCompressionAccept=None,
                       autoPingInterval=None,
                       autoPingTimeout=None,
                       autoPingSize=None):
    """ from autobahn.websocket.protocol.WebSocketClientFactory.setProtocolOptions """

    transport.factory.setProtocolOptions(
            version = version,
            utf8validateIncoming = utf8validateIncoming,
            acceptMaskedServerFrames = acceptMaskedServerFrames,
            maskClientFrames = maskClientFrames,
            applyMask = applyMask,
            maxFramePayloadSize = maxFramePayloadSize,
            maxMessagePayloadSize = maxMessagePayloadSize,
            autoFragmentSize = autoFragmentSize,
            failByDrop = failByDrop,
            echoCloseCodeReason = echoCloseCodeReason,
            serverConnectionDropTimeout = serverConnectionDropTimeout,
            openHandshakeTimeout = openHandshakeTimeout,
            closeHandshakeTimeout = closeHandshakeTimeout,
            tcpNoDelay = tcpNoDelay,
            perMessageCompressionOffers = perMessageCompressionOffers,
            perMessageCompressionAccept = perMessageCompressionAccept,
            autoPingInterval = autoPingInterval,
            autoPingTimeout = autoPingTimeout,
            autoPingSize = autoPingSize)

    if version is not None:
        if version not in WebSocketProtocol.SUPPORTED_SPEC_VERSIONS:
            raise Exception("invalid WebSocket draft version %s (allowed values: %s)" % (version, str(WebSocketProtocol.SUPPORTED_SPEC_VERSIONS)))
        if version != transport.version:
            transport.version = version

    if utf8validateIncoming is not None and utf8validateIncoming != transport.utf8validateIncoming:
        transport.utf8validateIncoming = utf8validateIncoming

    if acceptMaskedServerFrames is not None and acceptMaskedServerFrames != transport.acceptMaskedServerFrames:
        transport.acceptMaskedServerFrames = acceptMaskedServerFrames

    if maskClientFrames is not None and maskClientFrames != transport.maskClientFrames:
        transport.maskClientFrames = maskClientFrames

    if applyMask is not None and applyMask != transport.applyMask:
        transport.applyMask = applyMask

    if maxFramePayloadSize is not None and maxFramePayloadSize != transport.maxFramePayloadSize:
        transport.maxFramePayloadSize = maxFramePayloadSize

    if maxMessagePayloadSize is not None and maxMessagePayloadSize != transport.maxMessagePayloadSize:
        transport.maxMessagePayloadSize = maxMessagePayloadSize

    if autoFragmentSize is not None and autoFragmentSize != transport.autoFragmentSize:
        transport.autoFragmentSize = autoFragmentSize

    if failByDrop is not None and failByDrop != transport.failByDrop:
        transport.failByDrop = failByDrop

    if echoCloseCodeReason is not None and echoCloseCodeReason != transport.echoCloseCodeReason:
        transport.echoCloseCodeReason = echoCloseCodeReason

    if serverConnectionDropTimeout is not None and serverConnectionDropTimeout != transport.serverConnectionDropTimeout:
        transport.serverConnectionDropTimeout = serverConnectionDropTimeout

    if openHandshakeTimeout is not None and openHandshakeTimeout != transport.openHandshakeTimeout:
        transport.openHandshakeTimeout = openHandshakeTimeout

    if closeHandshakeTimeout is not None and closeHandshakeTimeout != transport.closeHandshakeTimeout:
        transport.closeHandshakeTimeout = closeHandshakeTimeout

    if tcpNoDelay is not None and tcpNoDelay != transport.tcpNoDelay:
        transport.tcpNoDelay = tcpNoDelay

    if perMessageCompressionOffers is not None and pickle.dumps(perMessageCompressionOffers) != pickle.dumps(transport.perMessageCompressionOffers):
        if type(perMessageCompressionOffers) == list:
            #
            # FIXME: more rigorous verification of passed argument
            #
            transport.perMessageCompressionOffers = copy.deepcopy(perMessageCompressionOffers)
        else:
            raise Exception("invalid type %s for perMessageCompressionOffers - expected list" % type(perMessageCompressionOffers))

    if perMessageCompressionAccept is not None and perMessageCompressionAccept != transport.perMessageCompressionAccept:
        transport.perMessageCompressionAccept = perMessageCompressionAccept

    if autoPingInterval is not None and autoPingInterval != transport.autoPingInterval:
        transport.autoPingInterval = autoPingInterval

    if autoPingTimeout is not None and autoPingTimeout != transport.autoPingTimeout:
        transport.autoPingTimeout = autoPingTimeout

    if autoPingSize is not None and autoPingSize != transport.autoPingSize:
        assert(type(autoPingSize) == float or type(autoPingSize) == int)
        assert(4 <= autoPingSize <= 125)
        transport.autoPingSize = autoPingSize


if __name__ == '__main__':
    from twisted.internet._sslverify import OpenSSLCertificateAuthorities
    from twisted.internet.ssl import CertificateOptions
    import OpenSSL.crypto



    # parse command line parameters
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output.')
    parser.add_argument('--url', dest='url', type=six.text_type, default=url,
                        help='The router URL (defaults to value from config.py)')
    parser.add_argument('--app', dest='app', type=six.text_type, default='hemibrain',
                        help='name of the application in neuroarch_nlp')
    parser.add_argument('--dataset', dest='dataset', type=six.text_type, default=None,
                        help='name of dataset, default to the same app name')
    parser.add_argument('--name', dest = 'name', type = six.text_type, default=None,
                        help='name of the server, default to the dataset name')
    parser.add_argument('--realm', dest='realm', type=six.text_type, default=realm,
                        help='The realm to join (defaults to value from config.py).')
    parser.add_argument('--ca_cert', dest='ca_cert_file', type=six.text_type,
                        default=ca_cert_file,
                        help='Root CA PEM certificate file (defaults to value from config.py).')
    parser.add_argument('--int_cert', dest='intermediate_cert_file', type=six.text_type,
                        default=intermediate_cert_file,
                        help='Intermediate PEM certificate file (defaults to value from config.py).')
    parser.add_argument('--no-ssl', dest='ssl', action='store_false')
    parser.add_argument('--no-auth', dest='authentication', action='store_false')
    parser.set_defaults(ssl=ssl)
    parser.set_defaults(authentication=authentication)
    parser.set_defaults(debug=debug)

    args = parser.parse_args()


    # start logging
    if args.debug:
        txaio.start_logging(level='debug')
    else:
        txaio.start_logging(level='info')

    # any extra info we want to forward to our ClientSession (in self.config.extra)
    if args.dataset is None:
        dataset = args.app
    else:
        dataset = args.dataset

    if args.name is None:
        name = dataset
    else:
        name = args.name

    extra = {'auth': args.authentication, 'app': args.app, 'dataset': dataset, 'name': name}

    if args.ssl:
        st_cert=open(args.ca_cert_file, 'rt').read()
        c=OpenSSL.crypto
        ca_cert=c.load_certificate(c.FILETYPE_PEM, st_cert)

        st_cert=open(args.intermediate_cert_file, 'rt').read()
        intermediate_cert=c.load_certificate(c.FILETYPE_PEM, st_cert)

        certs = OpenSSLCertificateAuthorities([ca_cert, intermediate_cert])
        ssl_con = CertificateOptions(trustRoot=certs)

        # now actually run a WAMP client using our session class ClientSession
        runner = ApplicationRunner(url=args.url, realm=args.realm, extra=extra, ssl=ssl_con)

    else:
        # now actually run a WAMP client using our session class ClientSession
        runner = ApplicationRunner(url=args.url, realm=args.realm, extra=extra)

    runner.run(AppSession, auto_reconnect=True)
