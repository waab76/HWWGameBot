from datetime import datetime, timezone
import logging
from logging.handlers import TimedRotatingFileHandler
import Config

handlers = set()
handlers.add(TimedRotatingFileHandler('HWWGameBot.log', when='W0', backupCount=4))

logging.basicConfig(level=logging.INFO, handlers=handlers, format='%(asctime)s %(levelname)s %(module)s:%(funcName)s %(message)s')
logging.Formatter.formatTime = (lambda self, record, datefmt=None: datetime.fromtimestamp(record.created, timezone.utc).astimezone().isoformat(sep="T",timespec="milliseconds"))

import json
import requests
from games.Matrix6 import Matrix6
from games.Test import Test

request_url = 'http://0.0.0.0:8800'

def get_game_data() -> dict:
    payload = requests.get(request_url + '/game-data/').json()
    if isinstance(payload, str):
        payload = json.loads(payload)
    logging.debug('Active game data is {}'.format(payload))
    return payload

def update_game_data(updates):
    requests.post(request_url + '/game-data/', {'json': json.dumps(updates)})

def get_phase_data() -> dict:
    payload = requests.get(request_url + '/phase-data/').json()
    if isinstance(payload, str):
        payload = json.loads(payload)
    logging.debug('Current phase data is {}'.format(payload))
    return payload

def update_phase_data(updates):
    requests.post(request_url + '/phase-data/', {'json': json.dumps(updates)})

def main():
    config = Config.Config('myconfig')
    reddit = config.reddit_object

    # Get the game config and phase data
    game_data = get_game_data()
    phase_data = get_phase_data()

    # Instantiate the game object based on what kind of game we're playing
    game = None
    if game_data['game_type'] == 'matrix6':
        game = Matrix6(reddit, game_data, phase_data)
    elif game_data['game_type'] == 'test':
        game = Test(reddit, game_data, phase_data)
    else:
        raise Exception('Unknown game type specified')

    if game.game_phase == 'init':
        logging.info('Init new game')
        game.init_new_game()
        update_game_data(game.get_game_data())
    elif game.game_phase == 'signup':
        logging.debug('Handle signups')
        game.handle_signups()
        update_game_data(game.get_game_data())
    elif game.game_phase == 'confirmation':
        logging.debug('Handle confirmations')
        # TODO: Add a confirmation timeout. If folks haven't confirmed in 24 hours
        # proceed without them confirming? Or re-send role PMs at 12 hours?
        game.handle_confirmations()
        update_game_data(game.get_game_data())
    elif game.game_phase == 'finale':
        pass
    else:
        logging.debug('Handle game phase')
        try:
            game.handle_main_sub_comments()
            game.handle_wolf_sub_comments()
            game.handle_private_messages()
            game.handle_turnover()
        except:
            logging.exception('Something went wrong processing comments and turnover')
        update_game_data(game.get_game_data())
        update_phase_data(game.get_phase_data())

if __name__ == '__main__':
	main()
