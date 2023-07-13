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

@app.route('/active-phase/', methods=['GET', 'POST'])
def active_game_post():
    """
    Handles queries/updates related to the currently active game phase post

    Expected Form Params:
    String post_id: The ID of the active game post
    """

    global active_game
    logging.debug('Active game data: {}'.format(active_game))

    if request.method == 'GET':
        return(jsonify({'post_id': active_game['active_post_id']}))
    elif request.method == 'POST':
        logging.debug('POST request')
        active_game['active_post_id'] = request.form['post_id']
        json_helper.dump(active_game, active_game_fname)
        logging.debug('Active game data: {}'.format(active_game))
        return(jsonify({'post_id': active_game['active_post_id']}))
    else:
        logging.error('DAFUQ request')
        abort(500)

# TODO: Add route to fetch list of live players

# TODO: Add route for game config

@app.route('/actions/', methods=['POST'])
def handle_actions():
    """
    Handles updates to the votes for the current phase

    Expected Form Params:
    String actions: The actions to update as a JSON map of the form {actor: [target1, target2], etc}
    """

    global active_game
    global active_phase

    actions = json.load(request.form['actions'])

    # for actor in actions:
        # if actor is alive
            # if targets are alive
                # active_phase['actions'][actor] = actions[actor]
            # else
                # add error to response for dead targets
        # else
            # add error to response for dead actor

    json_helper.dump(active_phase, active_phase_fname)

    # return errors to caller

@app.route('/votes/', methods=['POST'])
def handle_votes():
    """
    Handles updates to the votes for the current phase

    Expected Form Params:
    String votes: The votes to update as a JSON map of the form {voter1: target1, etc}
    """

    global active_game
    global active_phase

    votes = json.load(request.form['votes'])

    # for voter in votes:
        # if voter is alive
            # if target is alive
                # active_phase['votes'][voter] = votes[voter]
            # else
                # add error to response for dead target
        # else
            # add error to response for dead voter

    json_helper.dump(active_phase, active_phase_fname)

    # return errors to caller

@app.route('/handle_turnover/', methods=['GET'])
def handle_turnover():

    global active_phase
    global active_game

    # Tally votes from active_phase
    logging.debug('Tallying votes for phase {}'.format(active_game['active_post_id']))

    # Handle inactivity removals
    logging.debug('Handling inactivity removals')

    # Process actions from active_phase
    logging.debug('Handling actions')

    # Generate new phase title
    phase_title = 'New phase title'

    # Generate new phase text
    phase_body = 'Hey look, a new phase.  Someone probably got voted out. Someone else probably got killed.'

    # Roll over the active phase database
    active_phase = {'votes':{}, 'actions':{}}
    json_helper.dump(active_phase, active_phase_fname)

    return(jsonify({'title': phase_title, 'body': phase_body}))

class MyRequestHandler(WSGIRequestHandler):
    def log_request(self, code='-', size='-'):
        if 200 == code:
            pass
        else:
            logging.info('"%s" %s %s', self.requestline, code, size)

def launch():
    logging.info('Starting server...')

    logging.debug('Loading active game data from {}'.format(active_game_fname))
    global active_game
    active_game = json_helper.get_db(active_game_fname, encode_ascii=False)
    logging.debug('Active game data: {}'.format(active_game))

    logging.debug('Loading active phase data from {}'.format(active_phase_fname))
    global active_phase
    active_phase = json_helper.get_db(active_phase_fname, encode_ascii=False)
    logging.debug('Active phase data: {}'.format(active_phase))

if __name__ == "__main__":
    try:
        launch()
        app.run(host= '0.0.0.0', port=8800, request_handler=MyRequestHandler)
    except Exception as e:
        if str(e).lower() != '[Errno 98] Address already in use'.lower():
            logging.exception(e)
