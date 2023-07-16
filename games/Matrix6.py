import logging
from games.BaseGame import BaseGame

class Matrix6(BaseGame):
    def __init__(self, reddit, game_config, phase_data):
        logging.debug('Building Matrix6 game')
        BaseGame.__init__(self, reddit, game_config, phase_data)

    def player_limit(self):
        return 9
