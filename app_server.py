#!/usr/bin/python3

import sys
import time
import zmq
from datetime import datetime, timedelta

from zmq.auth.ioloop import IOLoopAuthenticator
from zmq.eventloop.ioloop import IOLoop, PeriodicCallback

from zmq.eventloop.zmqstream import ZMQStream
from zmq_msg_helo import *
from key_monkey import *

class AppServer(object):

	# This is the address and port we'll listen on. If clients are remote, listen on a public IP instead.
	bind_addr = "tcp://127.0.0.1:5556"

	# crypto = True means 'use CurveZMQ'. False means don't.

	crypto = True

	# zap_auth = True means 'use ZAP'. This will restrict connections to clients whose public keys are in
	# the ~/.curve/authorized-clients/ directory. Set this to false to allow any client with the server's
	# public key to connect, without requiring the server to posess each client's public key.

	zap_auth = True

	def __init__( self ):

		self.ctx = zmq.Context()
		self.loop = IOLoop.instance()
		self.client_identities = {}

		self.server = self.ctx.socket(zmq.ROUTER)
	
		if self.crypto:
			self.keymonkey = KeyMonkey("server")
			self.publisher = self.keymonkey.setupServer(self.server, self.bind_addr)

		self.server.bind(self.bind_addr)
		print("Server listening for new client connections at", self.bind_addr)
		self.server = ZMQStream(self.server)
		self.server.on_recv(self.on_recv)

		self.periodic = PeriodicCallback(self.periodictask, 1000)

	def start(self):

		# Setup ZAP:
		if self.zap_auth:
			if not self.crypto:
				print("ZAP requires CurveZMQ (crypto) to be enabled. Exiting.")
				sys.exit(1)
			self.auth = IOLoopAuthenticator(self.ctx)
			self.auth.deny(None)
			print("ZAP enabled.\nAuthorizing clients in %s." % self.keymonkey.authorized_clients_dir)
			self.auth.configure_curve(domain='*', location=self.keymonkey.authorized_clients_dir)
			self.auth.start()

		self.periodic.start()
		try:
			self.loop.start()
		except KeyboardInterrupt:
			pass

	def periodictask(self):
		stale_clients = []

		for client_id, last_seen in self.client_identities.items():
			if last_seen + timedelta(seconds=10) < datetime.utcnow():
				stale_clients.append(client_id)
			else:
				msg = HelloMessage()
				msg.send(self.server, client_id)

		for client_id in stale_clients:
			print("Haven't received a HELO from cliient %s recently. Dropping from list of connected clients." % client_id)
			del self.client_identities[client_id]

		sys.stdout.write(".")
		sys.stdout.flush()

	def on_recv(self, msg):
		identity = msg[0]

		self.client_identities[identity] = datetime.utcnow()

		msg_type = msg[1]
		print("Received message of type %s from client ID %s!" % (msg_type, identity))

def main():
	my_server = AppServer()
	my_server.start()

if __name__ == '__main__':
	main()

# vim: ts=4 sw=4 noet
