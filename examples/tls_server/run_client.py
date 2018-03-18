import requests

response = requests.get("https://localhost:8443", verify="rsa-certificate.pem")
assert response.status_code == 200
print(response.content)