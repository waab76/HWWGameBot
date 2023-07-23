import logging
import random
import re
from datetime import datetime, timedelta, timezone

p1_main_text = '##Welcome to Phase 1!\n\n' + \
               'You are now free to begin having game discussions.\n\n' + \
               'To submit your votes, simply include the text "!vote u/yourVoteTarget" in a comment like so:\n\n' + \
               '`!vote u/AutoWolfBot`\n\n' + \
               'To submit your action, send a PM to the host bot account with the text "!target u/yourActionTarget" ' + \
               '(the subject line doesn\'t matter).\n\nFor convenience, you can use this [ACTION LINK]' + \
               '(https://www.reddit.com/message/compose/?to=AutoWolfBot&subject=Action&message=!target:%20u/)\n\n' + \
               'Votes and actions can be changed as many times as you want.  Only your most recent (pre-turnover) submission will count.\n\n' +\
               'I really should have put a phase end countdown in here... Maybe in the next bot update.\n\n' + \
               '##Good luck!'
p1_wolf_text = '##Welcome to Phase 1, wolves!\n\n' + \
               'You are now free to begin making wolfy plans.\n\n' + \
               'Vote submission only works in the main sub.\n\n' + \
               'Night Kills can be submitted by any wolf in this sub by commenting `!kill yourKillTarget` (similar to voting). ' + \
               'Only the last submission (by any wolf) will count and the kill will be carried out even if the wolf who submitted it gets voted out.\n\n' + \
               'To submit an action, send a PM to the host bot account with the text "!target u/yourActionTarget" ' + \
               '(the subject line doesn\'t matter).\n\nFor convenience, you can use this [ACTION LINK]' + \
               '(https://www.reddit.com/message/compose/?to=AutoWolfBot&subject=Action&message=!target:%20u/)\n\n' + \
               'Votes and actions can be changed as many times as you want.  Only your most recent (pre-turnover) submission will count.\n\n' +\
               'I really should have put a phase end countdown in here... Maybe in the next bot update.\n\n' + \
               '##Good luck!'

class BaseGame:
    def __init__(self, reddit, game_data, phase_data):
        logging.debug('Building game with game_data {} and phase data {}'.format(game_data, phase_data))
        self.game_phase = 'init' if 'game_phase' not in game_data else game_data['game_phase']
        self.phase_length_hours = 24 if 'phase_length_hours' not in game_data else int(game_data['phase_length_hours'])
        self.main_sub_name = 'AutomatedWerewolves' if 'main_sub_name' not in game_data else game_data['main_sub_name']
        self.wolf_sub_name = 'AutomatedWolfSub' if 'wolf_sub_name' not in game_data else game_data['wolf_sub_name']
        self.main_post_id = '' if 'main_post_id' not in game_data else game_data['main_post_id']
        self.wolf_post_id = '' if 'wolf_post_id' not in game_data else game_data['wolf_post_id']
        self.confirmed_players = [] if 'confirmed_players' not in game_data else game_data['confirmed_players']
        self.roles = {} if 'roles' not in game_data else game_data['roles']
        self.live_players = [] if 'live_players' not in game_data else game_data['live_players']
        self.dead_players = [] if 'dead_players' not in game_data else game_data['dead_players']
        self.last_comment_time = 0 if 'last_comment_time' not in game_data else game_data['last_comment_time']
        self.last_wolf_comment_time = 0 if 'last_wolf_comment_time' not in game_data else game_data['last_wolf_comment_time']

        self.votes = {} if 'votes' not in phase_data else phase_data['votes']
        self.actions = {} if 'actions' not in phase_data else phase_data['actions']
        self.wolf_kill = '' if 'wolf_kill' not in phase_data else phase_data['wolf_kill']

        self.reddit = reddit
        self.main_sub = reddit.subreddit(self.main_sub_name)
        self.wolf_sub = reddit.subreddit(self.wolf_sub_name)

    def game_type(self):
        raise Exception('Method [game_type] must be implemented in game class')

    def player_limit(self):
        raise Exception('Method [player_limit] must be implemented in game class')

    def signup_post_title(self):
        raise Exception('Method [signup_post_text] must be implemented in game class')

    def signup_post_text(self):
        raise Exception('Method [signup_post_text] must be implemented in game class')

    def phase_post_title(self):
        raise Exception('Method [signup_post_text] must be implemented in game class')

    def phase_post_text(self, sorted_votes, voted_out, wolf_kill):
        raise Exception('Method [signup_post_text] must be implemented in game class')

    def assign_roles(self):
        raise Exception('Method [assign_roles] must be implemented in game class')

    def send_role_pm(self, player):
        raise Exception('Method [send_role_pm] must be implemented in game class')

    def process_actions(self):
        raise Exception('Method [handle_actions] must be implemented in game class')

    def wolf_count(self):
        wolf_count = 0
        for player in self.live_players:
            if "Wolf" in self.roles[player]:
                wolf_count += 1
        return wolf_count

    def town_count(self):
        town_count = 0
        for player in self.live_players:
            if "Town" in self.roles[player]:
                town_count += 1
        return town_count

    def get_sorted_votes(self):
        vote_totals = {}
        if len(self.votes) < 1:
            # If nobody voted, then everybody self voted
            for player in self.live_players:
                self.votes[player] = player
        for player in self.votes:
            if self.votes[player] not in vote_totals:
                vote_totals[self.votes[player]] = 1
            else:
                vote_totals[self.votes[player]] += 1
        return sorted(vote_totals.items(), key=lambda x:x[1], reverse=True)

    def get_game_data(self):
        return {'game_type': self.game_type(),
                'game_phase': self.game_phase,
                'phase_length_hours': self.phase_length_hours,
                'main_sub_name': self.main_sub_name,
                'wolf_sub_name': self.wolf_sub_name,
                'main_post_id': self.main_post_id,
                'wolf_post_id': self.wolf_post_id,
                'confirmed_players': self.confirmed_players,
                'roles': self.roles,
                'live_players': self.live_players,
                'dead_players': self.dead_players,
                'last_comment_time': self.last_comment_time,
                'last_wolf_comment_time': self.last_wolf_comment_time}

    def get_phase_data(self):
        return {'votes': self.votes,
                'actions': self.actions,
                'wolf_kill': self.wolf_kill}

    def init_new_game(self):
        logging.info('Posting signups in {}'.format(self.main_sub.display_name))
        signup_title = self.signup_post_title()
        signup_text = self.signup_post_text()
        signup_post = self.main_sub.submit(title=signup_title, selftext=signup_text, send_replies=False)
        self.main_post_id = signup_post.id
        self.last_comment_time = signup_post.created_utc
        self.game_phase = 'signup'

    def handle_signups(self):
        # Get comments from submission in chronological order
        submission = self.reddit.submission(self.main_post_id)
        submission.comments.replace_more(limit=None)
        submission.comments_sort = "old"
        comments = submission.comments.list()

        for comment in comments:
            if comment.created_utc > self.last_comment_time:
                player = comment.author.name.lower()
                if '!signup' in comment.body.lower():
                    if player not in self.live_players:
                        if len(self.live_players) < self.player_limit():
                            logging.info('Player {} has signed up for the game'.format(player))
                            self.live_players.append(player)
                            comment.reply('Added u/{} to the game!'.format(comment.author.name))
                        else:
                            comment.reply('Sorry, the game is full')
                    else:
                        comment.reply('u/{} already signed up'.format(comment.author.name))
                self.last_comment_time = comment.created_utc

        if len(self.live_players) == self.player_limit():
            # lock signups
            submission.mod.lock()
            self.game_phase = 'confirmation'
            confirmation_post = self.main_sub.submit(title='Confirmation Phase',
                selftext='Role PMs are being sent. Feel free to chat amongst yourselves while we wait for everyone to confirm. Game talk is not allowed.',
                send_replies=False)
            self.main_post_id = confirmation_post.id
            self.last_comment_time = confirmation_post.created_utc

            self.assign_roles()

    def handle_confirmations(self):
        logging.debug('Sending role PMs and processing confirmations')

        if len(self.live_players) > 0:
            player = self.live_players[0]
            logging.info('Sending role PM to {}'.format(player))
            self.send_role_pm(player)
            self.dead_players.append(player)
            self.live_players.remove(player)

        for message in self.reddit.inbox.unread():
            if 'confirm' in message.body.lower():
                player = message.author.name.lower()
                logging.info('Confirmation from {}'.format(player))
                if player in self.dead_players:
                    message.reply('You have confirmed. The game will start once all players have confirmed.')
                    self.confirmed_players.append(player)
            message.mark_read()

        if len(self.confirmed_players) == self.player_limit():
            self.game_phase = 1

            # Set the wolf sub to private and add the wolves
            self.wolf_sub.mod.update(subreddit_type='private')
            for user in self.confirmed_players:
                if 'Wolf' in self.roles[user]:
                    self.wolf_sub.contributor.add(user)
                self.live_players.append(user)
            self.dead_players = []

            main_phase_post = self.main_sub.submit(title=self.phase_post_title(), selftext=p1_main_text, send_replies=False)
            self.main_post_id = main_phase_post.id
            wolf_phase_post = self.wolf_sub.submit(title="WOLF SUB " + self.phase_post_title(), selftext=p1_wolf_text, send_replies=False)
            self.wolf_post_id = wolf_phase_post.id

    def handle_main_sub_comments(self):
        logging.debug('Processing votes for Phase {}'.format(self.game_phase))

        submission = self.reddit.submission(self.main_post_id)
        submission.comments.replace_more(limit=None)
        submission.comments_sort = "old"
        comments = submission.comments.list()

        for comment in comments:
            if comment.created_utc > self.last_comment_time:
                self.last_comment_time = comment.created_utc
                player = comment.author.name.lower()
                if player not in self.live_players and player not in ['autowolfbot', 'bourboninexile']:
                    comment.reply('Only living players are allowed to comment.')
                    comment.mod.remove()
                    continue
                if '!vote' in comment.body.lower():
                    logging.debug('Potential vote from {} in comment {}'.format(player, comment.body.lower()))
                    target = ''
                    for line in comment.body.lower().split('\n'):
                        if '!vote' in line:
                            parts = line.split()
                            for i in range(len(parts)):
                                word = parts[i]
                                if '!vote' in word:
                                    if i + 1 < len(parts):
                                        if parts[i+1].startswith('/u/'):
                                            target = parts[i+1][3:]
                                        elif parts[i+1].startswith('u/'):
                                            target = parts[i+1][2:]
                                        else:
                                            target = parts[i+1]
                    if target in self.live_players:
                        self.votes[player] = target
                        comment.reply('Recorded u/{}\'s vote for u/{} for Phase {}'.format(player, target, self.game_phase))
                        logging.info('Player {} voted for {} in Phase {}'.format(player, target, self.game_phase))
                    else:
                        comment.reply('u/{} is not an active player in this game'.format(target))
                if '!table' in comment.body.lower():
                    sorted_votes = self.get_sorted_votes()
                    vote_table = 'Player | Votes Against | Voters\n:- | :- | :-\n'
                    for entry in sorted_votes:
                        voters = ''
                        if player in self.votes:
                            for player in self.live_players:
                                if self.votes[player] == entry[0]:
                                    voters += '{} '.format(player)
                        vote_table += '{} | {} | {}\n'.format(entry[0], entry[1], voters)
                    comment.reply(vote_table)

    def handle_private_messages(self):
        logging.debug('Processing actions for Phase {}'.format(self.game_phase))
        for message in self.reddit.inbox.unread():
            if '!target' in message.body.lower():
                target = ''
                player = message.author.name.lower()
                if player in self.live_players:
                    for line in message.body.lower().split('\n'):
                        if '!target' in line:
                            parts = line.split()
                            for i in range(len(parts)):
                                word = parts[i]
                                if '!target' in word:
                                    if i + 1 < len(parts):
                                        if parts[i+1].startswith('/u/'):
                                            target = parts[i+1][3:]
                                        elif parts[i+1].startswith('u/'):
                                            target = parts[i+1][2:]
                                        else:
                                            target = parts[i+1]
                    if target in self.live_players:
                        logging.info('Player {}::{} targeting {}'.format(player, self.roles[player], target))
                        self.actions[player] = target
                        message.reply('You have targeted u/{} for Phase {}'.format(target, self.game_phase))
                    else:
                        message.reply('I\'m sorry, u/{} is not an active player in this game'.format(target))
                else:
                    message.reply('I\'m sorry, you\'re already dead')
            message.mark_read()

    def handle_commands(self):
        logging.debug('Handle in-sub commands')

    def handle_wolf_sub_comments(self):
        logging.debug('Processing Wolf Kill for Phase {}'.format(self.game_phase))
        submission = self.reddit.submission(self.wolf_post_id)
        submission.comments.replace_more(limit=None)
        submission.comments_sort = "old"
        comments = submission.comments.list()

        for comment in comments:
            if comment.created_utc > self.last_wolf_comment_time:
                self.last_wolf_comment_time = comment.created_utc
                player = comment.author.name.lower()
                if player not in self.live_players and player not in ['autowolfbot', 'bourboninexile']:
                    comment.reply('Only living players are allowed to comment.')
                    comment.mod.remove()
                    continue
                if '!kill' in comment.body.lower():
                    logging.debug('Potential kill from {} in comment {}'.format(player, comment.body.lower()))
                    target = ''
                    for line in comment.body.lower().split('\n'):
                        if '!kill' in line:
                            parts = line.split()
                            for i in range(len(parts)):
                                word = parts[i]
                                if '!kill' in word:
                                    if i + 1 < len(parts):
                                        if parts[i+1].startswith('/u/'):
                                            target = parts[i+1][3:]
                                        elif parts[i+1].startswith('u/'):
                                            target = parts[i+1][2:]
                                        else:
                                            target = parts[i+1]
                    if target in self.live_players:
                        self.wolf_kill = target
                        comment.reply('Recorded {}\'s wolf kill for {} for Phase {}'.format(player, target, self.game_phase))
                        logging.info('Player {} submitted kill for {} in Phase {}'.format(player, target, self.game_phase))
                    else:
                        comment.reply('{} is not an active player in this game'.format(target))

    def handle_turnover(self):
        logging.debug('Check for turnover')
        main_sub_post = self.reddit.submission(self.main_post_id)
        post_time = datetime.fromtimestamp(main_sub_post.created_utc, timezone.utc)
        if datetime.now(timezone.utc) - post_time < timedelta(hours=self.phase_length_hours):
            return()

        logging.info('Processing turnover')
        # Lock the threads in the main and wolf sub
        main_sub_post.mod.lock()
        wolf_sub_post = self.reddit.submission(self.wolf_post_id)
        wolf_sub_post.mod.lock()

        sorted_votes = self.get_sorted_votes()
        max_votes = sorted_votes[0][1]
        tied_players = []
        for entry in sorted_votes:
            if entry[1] == max_votes:
                tied_players.append(entry[0])
        voted_out = random.choice(tied_players)
        logging.info('Player {} has been voted out'.format(voted_out))
        self.dead_players.append(voted_out)
        self.live_players.remove(voted_out)
        self.reddit.redditor(voted_out).message('You have been voted out', 'The people of the town have voted you out.')

        # Handle actions
        wolf_kill = self.process_actions()

        if self.wolf_count() > 0 and self.town_count() > self.wolf_count():
            logging.info('Neither side has won the game')
            self.game_phase += 1
            main_phase_post = self.main_sub.submit(title=self.phase_post_title(),
                selftext=self.phase_post_text(sorted_votes, voted_out, wolf_kill), send_replies=False)
            self.main_post_id = main_phase_post.id
            wolf_phase_post = self.wolf_sub.submit(title='WOLF SUB ' + self.phase_post_title(),
                selftext=self.phase_post_text(sorted_votes, voted_out, wolf_kill), send_replies=False)
            self.wolf_post_id = wolf_phase_post.id
        else:
            logging.info('The game is over')
            self.game_phase = 'finale'
            self.wolf_sub.mod.update(subreddit_type='public')
            for user in self.confirmed_players:
                if 'Wolf' in self.roles[user]:
                    self.wolf_sub.contributor.remove(user)
            if self.wolf_count() == 0:
                logging.info('The town has won')
                finale_post = self.main_sub.submit(title='Finale', selftext='The last wolf {} has been voted out. The town has won!'.format(voted_out), send_replies=False)
            else:
                logging.info('The wolves have won')
                finale_post = self.main_sub.submit(title='Finale', selftext='The wolves have won!', send_replies=False)
        self.votes = {}
        self.actions = {}
