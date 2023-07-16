import logging
from games.BaseGame import BaseGame

class Test(BaseGame):
    def __init__(self, reddit, game_data, phase_data):
        logging.info('Building Test game instance')
        BaseGame.__init__(self, reddit, game_data, phase_data)

    def player_limit(self):
        return 1
