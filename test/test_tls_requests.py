import os
import io
from tempfile import TemporaryFile

from OpenSSL.crypto import X509 as openssl_X509
from OpenSSL.crypto import dump_certificate, FILETYPE_PEM
from OpenSSL.SSL import TLSv1_2_METHOD

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from ipaddress import IPv4Address

import datetime

import requests
from twisted.trial.unittest import TestCase
from .resources import application
from twisted.internet import reactor
from hendrix.deploy.tls import HendrixDeployTLS
from twisted.internet import threads
from twisted.internet.defer import ensureDeferred
import pytest_twisted

from hendrix.facilities.services import ExistingKeyTLSContextFactory
from hendrix.facilities.resources import MediaResource


def get_certificate():

    private_key = ec.generate_private_key(ec.SECP384R1, default_backend())
    public_key = private_key.public_key()
    host = '127.0.0.1'

    now = datetime.datetime.utcnow()

    fields = [
        x509.NameAttribute(NameOID.COMMON_NAME, host),
    ]

    subject = issuer = x509.Name(fields)
    cert = x509.CertificateBuilder().subject_name(subject)
    cert = cert.issuer_name(issuer)
    cert = cert.public_key(public_key)
    cert = cert.serial_number(x509.random_serial_number())
    cert = cert.not_valid_before(now)
    cert = cert.not_valid_after(now + datetime.timedelta(days=1))
    cert = cert.add_extension(x509.SubjectAlternativeName([x509.IPAddress(IPv4Address(host))]), critical=False)
    cert = cert.sign(private_key, hashes.SHA512(), default_backend())

    return cert, private_key


def test_get_certificate():
    get_certificate()


@pytest_twisted.inlineCallbacks
def test_ssl_request():

    port = 9252
    pem_path = 'public.pem'

    statics_path = 'path_on_disk/to/files'
    os.makedirs(statics_path, exist_ok=True)

    cert, pk = get_certificate()

    options = {
        'wsgi': application,
        'max_upload_bytes': 200,
        'https_port': port,
        'resources': [MediaResource(statics_path, namespace='statics')],
    }
    deployer = HendrixDeployTLS(
        key=pk,
        cert=openssl_X509.from_cryptography(cert),
        context_factory=ExistingKeyTLSContextFactory,
        context_factory_kwargs={
            "curve_name": ec.SECP384R1.name,
            "sslmethod": TLSv1_2_METHOD
        },
        options=options
    )
    deployer.addServices()
    deployer.start()

    def test_ssl_static_files():

        js_file = 'showmethisfile.js'
        filepath = os.path.join(statics_path, js_file)

        with open(pem_path, "w") as pub_file:
            pub_file.write(cert.public_bytes(serialization.Encoding.PEM).decode('utf-8'))

        with open(filepath, 'w') as js_write:
            js_write.write('//console.log("Hello World");')

        response = requests.get(
            f"https://127.0.0.1:{port}/statics/{js_file}",
            verify=pem_path
        )

        assert response.status_code == 200
        assert '//console.log("Hello World");' in response.text
        os.remove(filepath)
        os.removedirs(statics_path)
        os.remove(pem_path)

    d = threads.deferToThread(test_ssl_static_files)
    yield d
