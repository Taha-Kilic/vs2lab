"""
Simple client server unit test
"""

import logging
import threading
import unittest

import clientserver
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)


class TestEchoService(unittest.TestCase):
    """The test"""
    _server = clientserver.Server()  # create single server in class variable
    _server_thread = threading.Thread(target=_server.serve)  # define thread for running server

    @classmethod
    def setUpClass(cls):
        cls._server_thread.start()  # start server loop in a thread (called only once)

    def setUp(self):
        super().setUp()
        self.client = clientserver.Client()  # create new client for each test

    #def test_srv_get(self):  # each test_* function is a test
        #"""Test simple call"""
        #msg = self.client.call("Hello VS2Lab")
        #self.assertEqual(msg, 'Hello VS2Lab*')

    def test_get(self):
        """Test GET call"""
        result = self.client.get("Bob")
        self.assertEqual(result, "0721 222")

    def test_getAll(self):
        """Test GET ALL calls"""
        result = self.client.get_all()
        self.assertEqual(result, "{'Alice': '0721 111', 'Bob': '0721 222', 'Chris': '0721 333'}")

    def tearDown(self):
        self.client.close()  # terminate client after each test

    @classmethod
    def tearDownClass(cls):
        cls._server._serving = False  # break out of server loop. pylint: disable=protected-access
        cls._server_thread.join()  # wait for server thread to terminate


if __name__ == '__main__':
    unittest.main()
