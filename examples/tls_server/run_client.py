# This shows that your tls server is running and properly serving.  To test the TLS websocket via WSS, load the URL
# in a browser and allow a temporary verification exemption for the cert.

import requests

response = requests.get("https://localhost:8443/my_noodles", verify="rsa-certificate.pem")
assert response.status_code == 200
print(response.content)
