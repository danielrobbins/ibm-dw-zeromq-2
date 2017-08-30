#!/usr/bin/python3

import os, os.path, sys

import zmq
import zmq.auth

#	KeyMonkey uses an OpenSSH-like key storage directory: ~/.curve/
#
#	Your public key is stored in the ~/.curve/id_curve.key file.
#	Your private key is stored in the ~/.curve/id_curve.key_secret file.
#
#	Remote servers you want to connect to as a client will require the server's key to be in:
#
#	~/.curve/servername.key
#
#	...and you will need to specify "servername" in your setupClient call:
#	self.async = key_monkey.setupClient(self.async, "tcp://127.0.0.1:5000", "servername")
#
#	At this point, assuming the server has just done a similar call to setupServer(), you will
#	be able to communicate with the remote server.

#	It is also possible to improve security even further! To do this, you will need to set up
#	an ZAP 'authenticator' thread on the server side, which will ensure that you will only allow
#	connections from authorized clients. This is NOT set up by default.
#
#	Clients that you want to authorize to connect to your server should have their public keys
#	stored in:
#
#	~/.curve/authorized_clients/clientname.key

class KeyMonkey(object):

	def __init__(self,myid="id_curve"):

		self.myid = myid
		self.curvedir = os.path.expanduser("~") + "/.curve"
		self.public_key = self.curvedir + "/%s.key" % self.myid
		self.private_key = self.curvedir + "/%s.key_secret" % self.myid
		self.authorized_clients_dir = self.curvedir + "/authorized_clients"

	def setupServer(self, server, endpoint):
		try:
			foo, bar = zmq.auth.load_certificate(self.private_key)
			server.curve_publickey = foo
			server.curve_secretkey = bar
		except IOError:
			print("Couldn't load private key: %s" % self.private_key)
			return None
		server.curve_server = True
		print("Set up server listening on %s using curve key '%s'." % (endpoint, self.myid))
		return server

	def setupClient(self, client, endpoint, servername):
		foo, bar = zmq.auth.load_certificate(self.private_key)
		client.curve_publickey = foo
		client.curve_secretkey = bar
		foo, _ = zmq.auth.load_certificate(self.curvedir + "/" + servername + ".key" )
		client.curve_serverkey = foo
		print("Set up client connecting to %s (key '%s') using curve key '%s'." % (endpoint, servername, self.myid))
		return client
		
# vim: ts=4 sw=4 noet
