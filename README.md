# Orbit

Orbit is a transactional WebSockets library written in Python. Built on top of the Twisted networking engine, Orbit can support high user load and can be used within even non-Python applications. With Twisted Web's WSGI features, Orbit can seamlessly integrate with almost any given Python web framework, although the examples in this repository use Flask.

Orbit was written to fill a gap in current WebSocket frameworks. Many current libraries are not able to flawlessly relay the results of long-running or concurrent operations to N amount of users, regardless of user interruption. A plus of using Orbit is access to the vast array of networking tools that Twisted leaves at your disposal.  
  
It would be wise to get familiar with Twisted before using this library, as there can be many "gotchas" associated with using Twisted and libraries that don't use Twisted as their networking backend. SQLAlchemy's ORM is a good example of this, as it forcibly blocks the main thread during its usage. Alchimia is a library that circumvents that using the SQLAlchemy engine-based query system with Twisted's deferToThread mechanism, but unfortunately the ORM can't be used. Another good example is the requests library, for which the Twisted maintainers have written treq for HTTP requests.  
  
  
Here is an example of what your protocol code may look like:

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