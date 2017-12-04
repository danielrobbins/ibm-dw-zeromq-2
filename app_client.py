#!/usr/bin/python3

import sys
import zmq

from datetime import datetime, timedelta

from zmq.eventloop.ioloop import IOLoop, PeriodicCallback
from zmq.eventloop.zmqstream import ZMQStream

from zmq_msg_helo import *
from key_monkey import *

class AppClient(object):

	# where to connect to - point to another IP or hostname:5556 if running server on another machine
	endpoint = "tcp://127.0.0.1:5556"

	# crypto = True means 'use CurveZMQ'. False means don't. Must match server.

	crypto = True

	def __init__(self):

		self.ctx = zmq.Context()
		self.loop = IOLoop.instance()

		self.client = self.ctx.socket(zmq.DEALER)

		if self.crypto:
			self.keymonkey = KeyMonkey("client")
			self.client = self.keymonkey.setupClient(self.client, self.endpoint, "server")

		self.client.connect(self.endpoint)
		print("Connecting to", self.endpoint)
		self.client = ZMQStream(self.client)

		self.client.on_recv(self.on_recv)

		self.periodic = PeriodicCallback(self.periodictask, 1000)

		self.last_recv = None

	def periodictask(self):

		if not self.last_recv or self.last_recv + timedelta(seconds=5) < datetime.utcnow():
			print("Hmmm... haven't heard from the server in 5 seconds... Server unresponsive.")

		print("Sending HELLO to server")
		msg = HelloMessage()
		msg.send(self.client)

	def start(self):

		self.periodic.start()
		try:
			self.loop.start()
		except KeyboardInterrupt:
			pass

	def on_recv(self, msg):

		self.last_recv = datetime.utcnow()

		print("Received a message of type %s from server!" % msg[0])

if __name__ == '__main__':
	my_client = AppClient()
	my_client.start()

# vim: ts=4 sw=4 noet
