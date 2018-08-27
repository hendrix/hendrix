import datetime

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

ec_key = ec.generate_private_key(ec.SECP256K1, default_backend())

subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, u"hendrix-tls-example"),
])
cert = x509.CertificateBuilder().subject_name(
    subject
).issuer_name(
    issuer
).public_key(
    ec_key.public_key()
).serial_number(
    x509.random_serial_number()
).not_valid_before(
    datetime.datetime.utcnow()
).not_valid_after(
    datetime.datetime.utcnow() + datetime.timedelta(days=10)
).add_extension(
    x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
    critical=False,
).sign(ec_key, hashes.SHA256(), default_backend())

with open("ec-key.pem", "wb") as f:
    f.write(ec_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))

with open("ec-certificate.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))
