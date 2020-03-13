import os
import io
from tempfile import TemporaryFile
import requests
from twisted.trial.unittest import TestCase
from .resources import application
from twisted.internet import reactor
from hendrix.deploy.base import HendrixDeploy
from twisted.internet import threads
from twisted.internet.defer import ensureDeferred
import pytest_twisted

@pytest_twisted.inlineCallbacks
def test_max_upload_bytes():
    options = {'wsgi': application, 'max_upload_bytes': 200, 'http_port': 9876}
    deployer = HendrixDeploy(options=options)
    deployer.addServices()
    deployer.start()

    def reject_large_uploads():

        # uploading 50 bytes is fine.
        byte_count = 50
        ok_data = io.BytesIO(os.urandom(byte_count))
        response = requests.post(
            "http://localhost:9876/",
            files={'data': ok_data}
        )
        assert 200 == response.status_code

        # upload more than our max bytes and we fail with a 413
        byte_count = 201
        too_big = io.BytesIO(os.urandom(byte_count))
        response = requests.post(
            "http://localhost:9876/",
            files={'data': too_big}
        )
        assert 413 == response.status_code
        assert response.reason == "Request Entity Too Large"

    yield threads.deferToThread(reject_large_uploads)
