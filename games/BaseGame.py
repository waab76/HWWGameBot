import logging
import random

class BaseGame:
    def __init__(self, reddit, game_data, phase_data):
        logging.info('Building game with game_data {} and phase data {}'.format(game_data, phase_data))
        self.game_phase = 'init' if 'game_phase' not in game_data else game_data['game_phase']
        self.phase_length_hours = 1 if 'phase_length_hours' not in game_data else game_data['phase_length_hours']
        self.main_sub_name = 'HWWBotTest' if 'main_sub_name' not in game_data else game_data['main_sub_name']
        self.wolf_sub_name = 'HWWBotTest' if 'wolf_sub_name' not in game_data else game_data['wolf_sub_name']
        self.main_post_id = '' if 'main_post_id' not in game_data else game_data['main_post_id']
        self.wolf_post_id = '' if 'wolf_post_id' not in game_data else game_data['wolf_post_id']
        self.confirmed_players = [] if 'confirmed_players' not in game_data else game_data['confirmed_players']
        self.roles = {} if 'roles' not in game_data else game_data['roles']
        self.live_players = [] if 'live_players' not in game_data else game_data['live_players']
        self.dead_players = [] if 'dead_players' not in game_data else game_data['dead_players']
        self.last_comment_time = 0 if 'last_comment_time' not in game_data else game_data['last_comment_time']

        self.votes = [] if 'votes' not in phase_data else phase_data['votes']
        self.actions = [] if 'actions' not in phase_data else phase_data['actions']

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

    def handle_actions(self):
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
                'last_comment_time': self.last_comment_time}

    def get_phase_data(self):
        return {'votes': self.votes,
                'actions': self.actions}

    def init_new_game(self):
        logging.info('Posting signups in {}'.format(self.main_sub.display_name))
        signup_title = self.signup_post_title()
        signup_text = self.signup_post_text()
        signup_post = self.main_sub.submit(title=signup_title, selftext=signup_text, send_replies=False)
        self.main_post_id = signup_post.id
        self.last_comment_time = signup_post.created_utc

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
            signup_post.mod.lock()
            self.game_phase = 'confirmation'
            confirmation_post = self.main_sub.submit(title='Confirmation Phase',
                selftext='Role PMs are being sent. Feel free to chat amongst yourselves while we wait for everyone to confirm.',
                send_replies=False)
            self.main_post_id = confirmation_post.id
            self.last_comment_time = confirmation_post.created_utc

            self.assign_roles()

    def handle_confirmations(self):
        logging.debug('Sending role PMs and processing confirmations')

        if len(self.live_players) > 0:
            player = self.live_players[0]
            self.send_role_pm(player)
            self.dead_players.append(player)
            self.live_players.remove(player)

        action_pattern = re.compile('!target u\/(\S*)( u\/(\S*))?')

        for message in reddit.inbox.unread():
            if 'confirm' in message.body.lower():
                player = message.author.name.lower()
                if player in self.dead_players:
                    message.reply('You have confirmed.  The game will start once all players have confirmed.')
                    self.confirmed_players.append(player)
            message.mark_read()

        if len(self.confirmed_players) == self.player_limit():
            self.game_phase = 0

            # Set the wolf sub to private and add the wolves
            self.wolf_sub.mod.update(subreddit_type='private')
            for user in self.confirmed_players:
                if 'Wolf' in self.roles['user']:
                    self.wolf_sub.contributor.add(user)
                self.live_players.append(user)
            self.dead_players = []

            main_phase_post = self.main_sub.submit(title=self.phase_post_title(), selftext=self.phase_post_text, send_replies=False)
            self.main_post_id = main_phase_post.id
            wolf_phase_post = self.wolf_sub.submit(title=self.phase_post_title(), selftext=self.phase_post_text, send_replies=False)
            self.wolf_post_id = wolf_phase_post.id

    def handle_votes(self):
        logging.debug('Processing votes for Phase {}'.format(self.game_phase))

        submission = self.reddit.submission(self.main_post_id)
        submission.comments.replace_more(limit=None)
        submission.comments_sort = "old"
        comments = submission.comments.list()

        vote_pattern = re.compile('!vote u\/(\S*)')

        for comment in comments:
            if comment.created_utc > self.last_comment_time:
                player = comment.author.name.lower()
                if match := vote_pattern.match(comment.body.lower()):
                    target = match.group(1).lower()
                    logging.info('Player {} declared a vote for {}'.format(player, target))
                    if target in self.live_players:
                        self.votes[player] = target
                        comment.reply('Recorded u/{}\'s vote for u/{} for Phase {}'.format(player, target, self.game_phase))
                    else:
                        comment.reply('u/{} is not a valid vote target'.format(target))
                self.last_comment_time = comment.created_utc

    def handle_actions(self):
        logging.debug('Processing actions for Phase {}'.format(self.game_phase))

        action_pattern = re.compile('!target u\/(\S*)( u\/(\S*))?')

        for message in reddit.inbox.unread():
            if match := action_pattern.match(message.body.lower()):
                player = message.author.name.lower()
                if player in self.live_players:
                    target1 = match.group(1).lower()
                    # target2 = match.group(3).lower
                    if target1 in self.live_players:
                        self.actions[player] = [target1]
                        message.reply('You have targeted u/{} for Phase {}'.format(target1, self.game_phase))
                    else:
                        message.reply('I\'m sorry, u/{} is already dead'.format(target1))
                else:
                    message.reply('I\'m sorry, you\'re already dead')
            message.mark_read()

    def handle_turnover(self):
        main_sub_post = self.reddit.submission(self.main_post_id)
        post_time = datetime.fromtimestamp(main_sub_post.created_utc, timezone.utc)
        if datetime.now(timezone.utc) - post_time < timedelta(hours=self.phase_length_hours):
            return()

        # Lock the threads in the main and wolf sub
        main_sub_post.mod.lock()
        wolf_sub_post = self.reddit.submission(self.wolf_post_id)
        wolf_sub_post.mod.lock()

        # Tally votes
        vote_totals = {}
        for player in live_players:
            vote_totals[player] = 0
        for player in live_players:
            vote_totals[self.votes[player]] += 1
        sorted_votes = sorted(vote_totals.items(), key=lambda x:x[1], reverse=True)
        max_votes = sorted_votes[0][1]
        tied_players = []
        for entry in sorted_votes:
            if entry[1] == max_votes:
                tied_players.append(entry[0])
        voted_out = random.choice(tied_players)
        self.dead_players.append(voted_out)
        self.live_players.remove(voted_out)
        self.reddit.redditor(voted_out).message('You have been voted out', 'The people of the town have voted you out.')

        # Handle actions
        wolf_kill = handle_actions()

        if self.wolf_count() > 0 and self.town_count() > self.wolf_count():
            self.game_phase += 1
            main_phase_post = self.main_sub.submit(title=self.phase_post_title(),
                selftext=self.phase_post_text(sorted_votes, voted_out, wolf_kill), send_replies=False)
            self.main_post_id = main_phase_post.id
            wolf_phase_post = self.wolf_sub.submit(title='WOLF SUB ' + self.phase_post_title(),
                selftext=self.phase_post_text(sorted_votes, voted_out, wolf_kill), send_replies=False)
            self.wolf_post_id = wolf_phase_post.id
        else:
            self.game_phase = 'finale'
            self.wolf_sub.mod.update(subreddit_type='public')
            for user in self.confirmed_players:
                if 'Wolf' in self.roles[user]:
                    self.wolf_sub.contributor.remove(user)
            if self.wolf_count() == 0:
                # Town won
                finale_post = self.main_sub.submit(title='Finale', selftext='The last wolf {} has been voted out. The town has won!'.format(voted_out), send_replies=False)
            else:
                # Wolves won
                finale_post = self.main_sub.submit(title='Finale', selftext='The wolves have won!', send_replies=False)
