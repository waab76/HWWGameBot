import logging
from games.BaseGame import BaseGame

role_lists = [['Town Jailkeeper', 'Wolf Roleblocker', 'Bulletproof Townie', 'Vanilla Town', 'Vanilla Town', 'Vanilla Town', 'Vanilla Wolf', 'Vanilla Town', 'Vanilla Town'],
              ['Vanilla Town', 'Town Seer', 'Vanilla Wolf', 'Vanilla Town', 'Vanilla Town', 'Vanilla Town', 'Vanilla Wolf', 'Vanilla Town', 'Vanilla Town'],
              ['Vanilla Wolf', 'Town Doctor', 'Town Tracker', 'Vanilla Town', 'Vanilla Town', 'Vanilla Town', 'Vanilla Wolf', 'Vanilla Town', 'Vanilla Town'],
              ['Town Jailkeeper', 'Vanilla Townie', 'Vanilla Wolf', 'Vanilla Town', 'Vanilla Town', 'Vanilla Town', 'Vanilla Wolf', 'Vanilla Town', 'Vanilla Town'],
              ['Wolf Roleblocker', 'Town Seer', 'Town Doctor', 'Vanilla Town', 'Vanilla Town', 'Vanilla Town', 'Vanilla Wolf', 'Vanilla Town', 'Vanilla Town'],
              ['Bulletproof Townie', 'Vanilla Wolf', 'Town Tracker', 'Vanilla Town', 'Vanilla Town', 'Vanilla Town', 'Vanilla Wolf', 'Vanilla Town', 'Vanilla Town']]

class Matrix6(BaseGame):
    def __init__(self, reddit, game_config, phase_data):
        logging.debug('Building Matrix6 game')
        BaseGame.__init__(self, reddit, game_config, phase_data)

    def player_limit(self):
        return 9
