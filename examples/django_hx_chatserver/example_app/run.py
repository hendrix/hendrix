from hendrix.deploy.base import HendrixDeploy
from hendrix.experience import hey_joe

deployer = HendrixDeploy(options={'wsgi': 'example_app.wsgi.application', 'http_port': 7575})

websocket_service = hey_joe.WebSocketService("127.0.0.1", 9000)
deployer.add_non_tls_websocket_service(websocket_service)

deployer.run()

