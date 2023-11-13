import logging
import random
from datetime import datetime, timedelta, timezone
from games.BaseGame import BaseGame
from pytz import timezone

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

    def game_type(self):
        return 'matrix6'

    def player_limit(self):
        return 9

    def signup_post_title(self):
        return "New Game Signup, Rules & Roles - Matrix6"

    def signup_post_text(self):
        return ' Welcome to a new game of Automated Werewolves!\n\n' + \
            'This will be a [Matrix6](https://www.mafiauniverse.com/forums/threads/6604-Modbot-Supported-Setups-Game-Formats) game.\n\n' + \
            '**Matrix6** is a 9-player semi-open setup designed by Cogito Ergo Sum of ' + \
            'MafiaScum, where this is used as their newbie setup. No one is able to ' + \
            'know which setup the game has from the beginning, which can make ' + \
            'producing lies and fake claims interesting.\n\n' + \
            'To set up the game, the bot will randomly select one of the rows or columns ' + \
            'from the following table in order to decide which PRs will be assigned:\n\n' + \
            '. | A | B | C\n' + \
            '-: | :-: | :-: | :-:\n' + \
            '**1** | Town Jailkeeper | Vanilla Townie | Vanilla Wolf\n' + \
            '**2** | Wolf Roleblocker | Town Seer | Town Doctor\n' + \
            '**3** | 1-Shot Bulletproof Townie | Vanilla Wolf | Town Tracker\n\n' + \
            'In addition to the roles from the table, 5 Vanilla Town and 1 Vanilla Wolf will be assigned.\n\n' + \
            'Town will win by eliminating all wolves. Wolves will win when their number equals or exceeds town.\n\n' + \
            'In the event of a tie vote, one of the tied players will be randomly selected for removal.\n\n' + \
            'Wolf kills can be performed by any living wolf via a command in the wolf sub.\n\n' + \
            'To sign up for the game, simply comment with the text `!signup`. Once 9 ' + \
            'players have signed up, role assignment PMs will go out.\n\n' + \
            'Phase 1 will be posted once all players have confirmed their role PMs.'

    def phase_post_title(self):
        return 'Phase {}'.format(self.game_phase)

    def phase_post_text(self, sorted_votes, voted_out, wolf_kill, is_wolf_sub):
        phase_post = '##Phase {}\n\n'.format(self.game_phase)
        phase_post += ' -- Insert semi-randomized flavor here --\n\n'
        if self.game_phase > 1:
            phase_post += 'Player | Votes Against\n:- | -:\n'
            for entry in sorted_votes:
                phase_post += '{} | {}\n'.format(entry[0], entry[1])
            phase_post += '\n\n'
            voted_out_align = 'the Town' if 'Town' in self.roles[voted_out] else 'the Wolves'
            phase_post += '{} has been voted out. They were affiliated with {}.\n\n'.format(voted_out, voted_out_align)
        if len(wolf_kill) > 0:
            wolf_kill_align = 'the Town' if 'Town' in self.roles[wolf_kill] else 'the Wolves'
            phase_post += '{} has been killed in the night. They were affiliated with {}\n\n'.format(wolf_kill, wolf_kill_align)

        phase_post += 'Living Players:\n\n* {}\n\n'.format('\n* '.join(self.live_players))
        phase_post += 'Dead Players:\n\n* {}\n\n'.format('\n* '.join(self.dead_players))

        if is_wolf_sub:
            phase_post += 'To submit the kill, include the text "!kill theKillTarget" in a comment like so:\n\n`!kill AutoWolfBot`\n\n' + \
            'Kills may be submitted by any living wolf. The last submission will take precedence. If the wolf who submitted the kill gets ' + \
            'voted out, the kill will not go through.\n\n'
        else:
            phase_post += 'To submit your votes, include the text "!vote u/yourVoteTarget" in a comment like so:\n\n`!vote u/AutoWolfBot`\n\n'
        phase_post += 'To submit your action, send a PM to the host bot account with the text "!target u/yourActionTarget" ' + \
            '(the subject line doesn\'t matter).\n\nFor convenience, you can use this [ACTION LINK]' + \
            '(https://www.reddit.com/message/compose/?to=AutoWolfBot&subject=Action&message=!target:%20u/)\n\n' + \
            'Votes and actions can be changed as many times as you want.  Only your most recent (pre-turnover) submission will count.\n\n'

        turnover_time = datetime.now(timezone('US/Eastern')) + timedelta(hours=self.phase_length_hours)
        iso_str = turnover_time.strftime('%Y%m%dT%H%M')
        phase_post += 'Countdown to turnover: [LINK](https://www.timeanddate.com/countdown/generic?iso={}&p0=179&msg=Automated+Werewolves+Phase+End+&font=sanserif)'.format(iso_str)

        return phase_post

    def assign_roles(self):
        power_roles = random.choice(role_lists)
        random.shuffle(self.live_players)

        for i in range(9):
            self.roles[self.live_players[i]] = power_roles[i]

    def send_role_pm(self, player):
        role_descriptions = {
            'Town Jailkeeper': 'As Town Jailkeeper, you have access to the Jailkeeping Night Action. \
                Jailkeeping another player will both protect that player from being killed as well as \
                prevent that player from being able to successfully use their Night Action that night. \
                You will not learn whether your target was successfully protected from any kills, nor \
                will you learn whether your target had a Night Action. Submit your Night Action each \
                night by sending a PM to the bot account with the text: "!target u/YourTargetHere". \
                You may change your target as many times as you want. The last action submitted will be \
                used. If you do not submit an action, you will forego your action on that night.',
            'Wolf Roleblocker': 'As Wolf Roleblocker, you have access to the Roleblock Night Action. \
                Roleblocking another player prevents them from being able to successfully use any Night \
                Action that they might have that night. You will not learn whether your target had a Night \
                Action. Submit your Night Action each night by sending a PM to the bot account with the \
                text: "!target u/YourTargetHere". You may change your target as many times as you want. \
                The last action submitted will be used. If you do not submit an action, you will forego \
                your action on that night.\n\n You may also submit the night kill in \
                the wolf sub using the `!kill yourKillTarget` command',
            'Bulletproof Townie': 'As 1-Shot Bulletproof Townie, you will not die the first time \
                the wolf team uses their factional kill on you. You will be informed when your ability has \
                been used up and your role will revert to Vanilla Town.',
            'Vanilla Town': 'As Vanilla Town, you have no Night Action.',
            'Town Seer': 'As Town Seer, you have access to the Alignment Inspection Night Action. \
                Alignment Inspection will reveal a target\'s alignment. Submit your Night Action each \
                night by sending a PM to the bot account with the text: "!target u/YourTargetHere". \
                You may change your target as many times as you want. The last action submitted will be used.',
            'Vanilla Wolf': 'As a Vanilla Wolf, you have no Night Action. You may submit the night kill in \
                the wolf sub using the `!kill yourKillTarget` command',
            'Town Doctor': 'As Town Doctor, you have access to the Protection Night Action. \
                Protection will protect your target from being killed. You will not learn whether \
                you successfully protected someone. Submit your Night Action each \
                night by sending a PM to the bot account with the text: "!target u/YourTargetHere". \
                You may change your target as many times as you want. The last action submitted will be used.',
            'Town Tracker': 'As Town Tracker, you have access to the Tracking Night Action. \
                Tracking another player informs you who that player used a Night Action on \
                that night, if any. You will not learn what type of Night Action your target has. \
                Submit your Night Action each night by sending a PM to the bot account with the \
                text: "!target u/YourTargetHere". You may change your target as many times \
                as you want. The last action submitted will be used.'}

        role_pm = 'You role is **{}**!\n\n{}Please respond to this PM with the word `confirm` to confirm your participation in the game.'.format(self.roles[player], role_descriptions[self.roles[player]])

        self.reddit.redditor(player).message('Role Assignment', role_pm)

    def process_actions(self):
        role_holders = {}
        for player in self.live_players:
            if self.roles[player] in role_holders:
                role_holders[self.roles[player]].append(player)
            else:
                role_holders[self.roles[player]] = [player]

        # Wolf Roleblocker
        blocker = '' if not 'Wolf Roleblocker' in role_holders else role_holders['Wolf Roleblocker'][0]
        if blocker in self.live_players and blocker in self.actions:
            block_target = '' if blocker not in self.live_players or blocker not in self.actions else self.actions[blocker]
            if len(block_target) > 0:
                logging.info('The Wolf Roleblocker {} has blocked {}'.format(blocker, block_target))
                self.actions[block_target] = ''

        # Town Jailkeeper
        keeper = '' if not 'Town Jailkeeper' in role_holders else role_holders['Town Jailkeeper'][0]
        in_jail = ''
        if keeper in self.live_players and keeper in self.actions:
            logging.info('The Town Jailkeeper {} has jailed {}'.format(keeper, in_jail))
            in_jail = self.actions[keeper]
            self.actions[in_jail] = ''
            if self.wolf_killer in in_jail:
                self.wolf_kill = ''

        # Town Seer
        seer = '' if not 'Town Seer' in role_holders else role_holders['Town Seer'][0]
        if seer in self.live_players and seer in self.actions:
            seen = self.actions[seer]
            if 'Wolf' in self.roles[seen]:
                logging.info('The Town Seer {} has seen the wolf {}'.format(seer, seen))
                self.reddit.redditor(seer).message('Seer Result', '{} is a Wolf'.format(seen))
            elif 'Town' in self.roles[seen]:
                logging.info('The Town Seer {} has seen the townie {}'.format(seer, seen))
                self.reddit.redditor(seer).message('Seer Result', '{} is Town'.format(seen))
            else:
                logging.info('The Town Seer {} has failed'.format(seer))
                self.reddit.redditor(seer_target[1]).message('Action Failed', 'Your action has failed')

        # Town Doctor
        doc = '' if not 'Town Doctor' in role_holders else role_holders['Town Doctor'][0]
        doctored = ''
        if doc in self.live_players and doc in self.actions:
            doctored = self.actions[doc]
            logging.info('The Town Doctor {} has protected {}'.format(doc, doctored))

        # Town Tracker
        tracker = '' if not 'Town Tracker' in role_holders else role_holders['Town Tracker'][0]
        if tracker in self.live_players and tracker in self.actions:
            tracked = self.actions[tracker]
            if tracked in self.live_players:
                if (tracked in self.wolf_killer):
                    logging.info('The Town Tracker {} has seen {} kill {}'.format(tracker, tracked, self.wolf_kill))
                    self.reddit.redditor(tracker).message('Tracker Result', '{}\'s Night Action target was {}'.format(tracked, self.wolf_kill))
                elif (tracked in self.actions and not '' == self.actions[tracked]) or tracked in self.wolf_killer:
                    logging.info('The Town Tracker {} has seen {} target {}'.format(tracker, tracked, self.actions[tracked]))
                    self.reddit.redditor(tracker).message('Tracker Result', '{}\'s Night Action target was {}'.format(tracked, self.actions[tracked]))
                else:
                    logging.info('The Town Tracker {} did not see {} target anyone'.format(tracker, tracked))
                    self.reddit.redditor(tracker).message('Tracker Result', '{} did not take a Night Action'.format(tracked))

        # Handle Wolf Kill
        wolf_kill = ''
        if self.wolf_killer in self.live_players:
            kill_target = '' if not len(self.wolf_kill) > 0 else self.wolf_kill
            if not kill_target in [in_jail, doctored] and kill_target in self.live_players:
                bulletproof = '' if not 'Bulletproof Townie' in role_holders else role_holders['Bulletproof Townie'][0]
                if kill_target == bulletproof:
                    logging.info('The wolves have hit the Bulletproof Townie {}'.format(bulletproof))
                    self.roles[bulletproof] = 'Vanilla Town'
                    self.reddit.redditor(bulletproof).message('Close Call', 'The wolves nearly got you. That was close. You are now Vanilla Town')
                else:
                    logging.info('The wolves have killed {}'.format(kill_target))
                    wolf_kill = kill_target
                    self.reddit.redditor(wolf_kill).message('You Have Been Killed', 'You keep running but the howling keeps getting closer. You have been killed by the wolves.')
                    self.live_players.remove(wolf_kill)
                    self.dead_players.append(wolf_kill)

        return wolf_kill
