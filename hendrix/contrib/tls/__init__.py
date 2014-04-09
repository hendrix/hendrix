# #########################
# # Example code
# #########################
# from twisted.protocols.tls import TLSMemoryBIOFactory
# from twisted.internet.protocol import ServerFactory
# from twisted.internet.ssl import PrivateCertificate
# from twisted.internet import reactor
#
# from someapplication import ApplicationProtocol
#
# serverFactory = ServerFactory()
# serverFactory.protocol = ApplicationProtocol
# certificate = PrivateCertificate.loadPEM(certPEMData)
# contextFactory = certificate.options()
# tlsFactory = TLSMemoryBIOFactory(contextFactory, False, serverFactory)
# reactor.listenTCP(12345, tlsFactory)
# reactor.run()
#




# https://gist.github.com/wallrj/5911925
# """
# A systemd socket activated TLS twisted.web server.
#
# $ tree /srv/www/
# /srv/www/
# `-- www.example.com
#     |-- server.key
#     |-- server.pem
#     |-- server.tac.py
#     `-- static
#         `-- index.html
# """
# from twisted.internet import reactor
# from twisted.application import internet, service
# from twisted.internet.endpoints import serverFromString
# from twisted.internet.ssl import PrivateCertificate
# from twisted.protocols.tls import TLSMemoryBIOFactory
# from twisted.web import server, static
#
#
# endpoint = serverFromString(reactor, 'systemd:domain=INET:index=0')
#
# serverFactory = server.Site(static.File('.'))
#
# privateCert = PrivateCertificate.loadPEM(
#     open('server.pem').read() + open('server.key').read())
#
# tlsFactory = TLSMemoryBIOFactory(
#     privateCert.options(), False, serverFactory)
#
# application = service.Application('Twisted Web + systemd + TLS Example')
#
# s = internet.StreamServerEndpointService(endpoint, tlsFactory)
# s.setServiceParent(application)
