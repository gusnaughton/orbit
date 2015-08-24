import pyximport
pyximport.install()
from twisted.internet.defer import inlineCallbacks
from orbit.framing import TEXT
from flask import Flask, render_template, request, session
from orbit.server import WebSocketResource, WSGISiteResource
from orbit.transaction import Transaction, State, TransactionManager
from twisted.web.static import File
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource
from twisted.python import log
from twisted.web.resource import Resource
import cgi, urlparse, os, treq, sys

app = Flask(__name__)
app.root_path = os.path.join(os.path.dirname(__file__), '..')
app.static_folder = os.path.join(app.root_path, 'static')
app.template_folder = os.path.join(app.root_path, 'templates')
app.secret_key = 'example-secret-key'

imgur_folder = os.path.join(app.static_folder, 'imgur')

# The state is what holds all of the important data of our Transaction.
# In this case, the imgur filename to download.
class ImgurDownloadState(State):
	def __init__(self, imgur_filename):
		self.imgur_filename = imgur_filename.encode('utf8') # for treq

	@inlineCallbacks
	def onNewConnection(self, ws):
		ws.opcode = TEXT
		local_file = os.path.join(imgur_folder, self.imgur_filename)
		# If we don't already have the image downloaded, we download it in a non-blocking manner with treq
		# If the file is already downloaded, we can immediately send an update containing the location of the
		# downloaded image.
		if not os.path.isfile(local_file):
			print 'Downloading to %s' % local_file
			# We use treq to download the image, then we send an update with the image location
			resp = yield treq.get('http://i.imgur.com/%s' % self.imgur_filename)
			file_content = yield resp.content()
			with open(local_file, 'w') as out:
				print 'written!'
				out.write(file_content)
		self.transaction.sendUpdate('/static/imgur/%s' % self.imgur_filename)

	def onUpdate(self, ws, opcode, data, fin):
		# This occurs when the user presses "OK" to complete the transaction.
		if data == 'finish':
			self.transaction.finish()


# Our transaction manager allows us to create transactions with a unique ID that our user's session holds
# to be able to come back to the page and see the image after it has been downloaded.
transaction_manager = TransactionManager()
# This is the resource that defines how transactions are looked up (__call__ on TransactionManager) and the GET
# variable that is the unique ID used to look up the transaction.
imgur_resource = WebSocketResource(transaction_manager, 'transaction_id')

@app.route('/')
def index():
	if session.has_key('imgur_id'):
		# If their transaction already exists, it might not be done yet. they may have
		if transaction_manager.hasTransaction(session['imgur_id']):
			return render_template('imgur/index.html', transaction_id=session['imgur_id'])
		else:
			# Their transaction is finished, so we can allow them to download another image.
			del session['imgur_id']

	url = request.args.get('imgur', None)
	if not url:
		return 'Please enter a valid imgur link.'

	parsed_url = urlparse.urlparse(url)

	if parsed_url.netloc != 'i.imgur.com':
		return 'Please enter a valid imgur link.'

	# Create a transaction that will be used until the user receives their image and presses OK to dismiss the transaction
	# This way, if the user refreshes the page or
	transaction_id = transaction_manager.addTransaction(Transaction(ImgurDownloadState(parsed_url.path[1:])))
	session['imgur_id'] = transaction_id
	return render_template('imgur/index.html', transaction_id=transaction_id)

resource = WSGIResource(reactor, reactor.getThreadPool(), app)
static_resource = File(app.static_folder)

log.startLogging(sys.stdout)
ws = Resource()
ws.putChild('imgur', imgur_resource)
root_resource = WSGISiteResource(resource, {'static': static_resource, 'ws': ws})
site = Site(root_resource)
site.displayTracebacks = True

if __name__ == '__main__':
	app.debug = True
	log.startLogging(sys.stdout)
	reactor.listenTCP(8000, site, interface='0.0.0.0')
	reactor.run()