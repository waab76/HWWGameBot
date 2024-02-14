import datetime
import logging
from logging.handlers import TimedRotatingFileHandler

handlers = set()
handlers.add(TimedRotatingFileHandler('HWWGameBot.log', when='W0', backupCount=4))
logging.basicConfig(level=logging.INFO, handlers=handlers, format='%(asctime)s %(levelname)s %(module)s:%(funcName)s %(message)s')
logging.Formatter.formatTime = (lambda self, record, datefmt=None: datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc).astimezone().isoformat(sep="T",timespec="milliseconds"))

import json
import os
import sys
from flask import abort, Flask, jsonify, request
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
active_game_fname = 'database/active_game.json'
active_phase_fname = 'database/active_phase.json'

# Declare data file structures
active_game = {}
active_phase = {}

@app.route('/new-game/', methods=['POST'])
def reset_game():
    """
    Reset the HWW game
    """

    global active_game
    global active_phase

    if request.method == 'POST':
        active_game = {'game_type': 'matrix6'}
        json_helper.dump(active_game, active_game_fname)
        active_phase = {}
        json_helper.dump(active_phase, active_phase_fname)
        return(jsonify(active_game))
    else:
        logging.error('DAFUQ request')
        abort(400)


@app.route('/phase-data/', methods=['GET', 'POST'])
def phase_data():
    """
    Storage and retrieval for phase-level data
    """

    global active_phase
    logging.debug('Current phase data: {}'.format(active_phase))

    if request.method == 'GET':
        return(jsonify(active_phase))
    elif request.method == 'POST':
        active_phase = request.form['json']
        json_helper.dump(active_phase, active_phase_fname)
        return(jsonify(active_phase))
    else:
        logging.error('DAFUQ request')
        abort(400)

@app.route('/game-data/', methods=['GET', 'POST'])
def game_config():
    """
    Storage and retrieval for game-level data
    """

    global active_game

    if request.method == 'GET':
        return(jsonify(active_game))
    elif request.method == 'POST':
        active_game = request.form['json']
        json_helper.dump(active_game, active_game_fname)
        return(jsonify(active_game))
    else:
        logging.error('DAFUQ request')
        abort(400)

class MyRequestHandler(WSGIRequestHandler):
    def log_request(self, code='-', size='-'):
        if 200 == code:
            pass
        else:
            logging.info('"%s" %s %s', self.requestline, code, size)

def launch():
    logging.info('Starting server...')

    global active_game
    try:
        logging.debug('Loading active game data from {}'.format(active_game_fname))
        active_game = json_helper.get_db(active_game_fname, encode_ascii=False)
    except:
        logging.exception('Failed to load game config from file')
    logging.debug('Active game data: {}'.format(active_game))

    global active_phase
    try:
        logging.debug('Loading active phase data from {}'.format(active_phase_fname))
        active_phase = json_helper.get_db(active_phase_fname, encode_ascii=False)
    except:
        logging.exception('Failed to load phase data from file')
    logging.debug('Active phase data: {}'.format(active_phase))

if __name__ == "__main__":
    try:
        launch()
        app.run(host= '0.0.0.0', port=8800, request_handler=MyRequestHandler)
    except Exception as e:
        if str(e).lower() != '[Errno 98] Address already in use'.lower():
            logging.exception(e)
