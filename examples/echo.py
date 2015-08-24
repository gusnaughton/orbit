import pyximport
pyximport.install()
import os, sys
from orbit.framing import TEXT
from flask import Flask, render_template
from orbit.server import WebSocketResource, WSGISiteResource
from orbit.transaction import Transaction, State, TransactionManager
from twisted.web.static import File
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource
from twisted.python import log
from twisted.web.resource import Resource
import cgi

app = Flask(__name__)
app.root_path = os.path.join(os.path.dirname(__file__), '..')
app.static_folder = os.path.join(app.root_path, 'static')
app.template_folder = os.path.join(app.root_path, 'templates')

class EchoState(State):
	def onNewConnection(self, ws):
		ws.opcode = TEXT

	def onUpdate(self, ws, opcode, data, fin):
		print 'Opcode: %s' % opcode
		print 'Data: %s' % data
		ws.write(cgi.escape(data).encode('utf8'))

	def onEndConnection(self, ws):
		self.transaction.finish()


test_manager = TransactionManager()
test_resource = WebSocketResource(test_manager, 'echo_id')

@app.route('/')
def index():
	echo_id = test_manager.addTransaction(Transaction(EchoState()))
	return render_template('echo/index.html', echo_id=echo_id)

resource = WSGIResource(reactor, reactor.getThreadPool(), app)
static_resource = File(app.static_folder)

log.startLogging(sys.stdout)
ws = Resource()
ws.putChild('echo', test_resource)
root_resource = WSGISiteResource(resource, {'static': static_resource, 'ws': ws})
site = Site(root_resource)

if __name__ == '__main__':
	app.debug = True
	log.startLogging(sys.stdout)
	reactor.listenTCP(8000, site, interface='0.0.0.0')
	reactor.run()