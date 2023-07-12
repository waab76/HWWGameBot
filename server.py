import datetime
import logging
from logging.handlers import TimedRotatingFileHandler

handlers = set()
handlers.add(TimedRotatingFileHandler('HWWGameBotServer.log',
									  when='W0',
									  backupCount=4))
logging.basicConfig(level=logging.DEBUG, handlers=handlers,
					format='%(asctime)s %(levelname)s %(module)s:%(funcName)s %(message)s')
logging.Formatter.formatTime = (lambda self, record, datefmt=None: datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc).astimezone().isoformat(sep="T",timespec="milliseconds"))

import os
import sys
from flask import Flask, jsonify, request
from werkzeug.serving import WSGIRequestHandler

#https://stackoverflow.com/questions/54141751/how-to-disable-flask-app-run-s-default-message
cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None

app = Flask(__name__)

class JsonHelper:
	def ascii_encode_dict(self, data):
		ascii_encode = lambda x: x.encode('ascii') if isinstance(x, str) else x
		return dict(map(ascii_encode, pair) for pair in data.items())

	def get_db(self, fname, encode_ascii=True):
		with open(fname) as json_data:
			if encode_ascii:
				data = json.load(json_data, object_hook=self.ascii_encode_dict)
			else:
				data = json.load(json_data)
		return data

	def dump(self, db, fname):
		with open(fname, 'w') as outfile:
			outfile.write(str(db).replace("'", '"').replace('{u"', '{"').replace('[u"', '["').replace(' u"', ' "'))

json_helper = JsonHelper()

# Specify data file names

# Declare data file structures
the_chache = {}

@app.route('/get-test/', methods=["GET"])
def test_get():
    """
    What does this function do?

    Expected Form Params:
    None
    """

    logging.info('Call to /get-test/')
	return jsonify({'count': 4, 'foo': 'bar', 'baz': {'quick': ['brown','fox']}})

@app.route('/post-test/', methods=['POST'])
def post_test():
	"""
	Given a user name and karma data, stores it in the cache

	Requested Form Params:
	String key: The cache key
	String value: The cache value
	"""

    logging.info('Call to /post-test/')
	cache_key = request.form['key']
	cache_entry = json.loads(request.form['value'])
	cache_entry['timestamp'] = int(time.time())

    global the_cache
    the_cache[cache_key] = cache_entry

	logging.info('Update cache for [{}] to {}'.format(cache_key, cache_entry))

	return jsonify({'added': 1})

class MyRequestHandler(WSGIRequestHandler):
    def log_request(self, code='-', size='-'):
        if 200 == code:
            logging.info('"%s" %s %s', self.requestline, code, size)
            pass
        else:
            logging.info('"%s" %s %s', self.requestline, code, size)

def launch():
	logging.info('Starting server...')


if __name__ == "__main__":
	try:
		launch()
		app.run(host= '0.0.0.0', port=8000, request_handler=MyRequestHandler)
	except Exception as e:
		if str(e).lower() != '[Errno 98] Address already in use'.lower():
			logging.exception(e)
