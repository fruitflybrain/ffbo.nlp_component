
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.logger import Logger
from twisted.internet import threads

from autobahn.twisted.util import sleep
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from autobahn.wamp.exception import ApplicationError

from autobahn.wamp.types import RegisterOptions

import os
import argparse
import six
import txaio

import json

from neuroarch_nlp.interface import Translator

from autobahn.wamp import auth

from configparser import ConfigParser

# Grab configuration from file
root = os.path.expanduser("/")
home = os.path.expanduser("~")
filepath = os.path.dirname(os.path.abspath(__file__))
config_files = []
config_files.append(os.path.join(home, "config", "ffbo.nlp_component.ini"))
config_files.append(os.path.join(root, "config", "ffbo.nlp_component.ini"))
config_files.append(os.path.join(home, "config", "config.ini"))
config_files.append(os.path.join(root, "config", "config.ini"))
config_files.append(os.path.join(filepath, "config.ini"))
config = ConfigParser()
configured = False
for config_file in config_files:
    if os.path.exists(config_file):
        config.read(config_file)
        configured = True
        break
if not configured:
    raise Exception("No config file exists for this component")

user = config["UserInfo"]["user"]
secret = config["UserInfo"]["secret"]
ssl = eval(config["ServerInfo"]["ssl"])
url = config["ServerInfo"]["url"]
realm = config["ServerInfo"]["realm"]
authentication = eval(config["ServerInfo"]["authentication"])
debug = eval(config["DebugInfo"]["debug"])
ca_cert_file = config["CertInfo"]["ca_cert_file"]
intermediate_cert_file = config["CertInfo"]["intermediate_cert_file"]

class AppSession(ApplicationSession):

    log = Logger()
    
    def onConnect(self):
        if self.config.extra['auth']:
            self.join(self.config.realm, [u"wampcra"], user)
        else:
            self.join(self.config.realm, [], user)
 
    def onChallenge(self, challenge):
        if challenge.method == u"wampcra":
            #print("WAMP-CRA challenge received: {}".format(challenge))
            
            if u'salt' in challenge.extra:
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
        server = Translator()
        
        translators = {}
        
        self.server_config = {'name': 'nlp_server'}

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
                                      'nlp', self.server_config['name'])
                self.log.info("register new server called with result: {result}",
                                                    result=res)

            except ApplicationError as e:
                if e.error != 'wamp.error.no_such_procedure':
                    raise e

        yield self.subscribe(register_component, six.u('ffbo.processor.connected'))
        self.log.info("subscribed to topic 'ffbo.processor.connected'")
        
        register_component()

if __name__ == '__main__':
    from twisted.internet._sslverify import OpenSSLCertificateAuthorities
    from twisted.internet.ssl import CertificateOptions
    import OpenSSL.crypto
    
                                           
    
    # parse command line parameters
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output.')
    parser.add_argument('--url', dest='url', type=six.text_type, default=url,
                        help='The router URL (defaults to value from config.py)')
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
    extra = {'auth': args.authentication}

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
