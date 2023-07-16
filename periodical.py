from datetime import datetime, timedelta, timezone
import logging
from logging.handlers import TimedRotatingFileHandler
import Config

handlers = set()
handlers.add(TimedRotatingFileHandler('HWWGameBot.log', when='W0', backupCount=4))

logging.basicConfig(level=logging.INFO, handlers=handlers, format='%(asctime)s %(levelname)s %(module)s:%(funcName)s %(message)s')
logging.Formatter.formatTime = (lambda self, record, datefmt=None: datetime.fromtimestamp(record.created, timezone.utc).astimezone().isoformat(sep="T",timespec="milliseconds"))

import praw
import re
import requests

request_url = 'http://0.0.0.0:8800'
check_time = datetime.now(timezone.utc)
vote_pattern = re.compile('!vote u\/(\S*)')
signup_text = '''
Welcome to another game of Automated Werewolves!

Signups are now open for the next game.  To sign up, simply comment on this post with the text `!signup`

Once 9 players have signed up, roles will be assigned and the game will begin immediately with P0.

If this was a real bot in a real sub, there'd be a wiki link here or something.
'''

def get_game_config():
    payload = requests.get(request_url + '/game-config/').json()
    logging.debug('Active game config is {}'.format(payload))
    return payload

def update_game_config(updates):
    requests.post(request_url + '/game-config/', updates)

def get_phase_data():
    payload = requests.get(request_url + '/phase_data/').json()
    logging.debug('Current phase data is {}'.format(payload))
    return payload

def update_phase_data(updates):
    requests.post(request_url + '/phase_data/', updates)

def get_active_phase(reddit):
    payload = requests.get(request_url + '/active-phase/').json()
    logging.debug('Active phase post is {}'.format(payload['post_id']))
    return reddit.submission(payload['post_id'])

def set_active_phase(submission):
    logging.debug('Updating active phase post to [{}]'.format(submission.id))
    requests.post(request_url + '/active-phase/', {'post_id': submission.id})

def get_phase_length():
    game_config = get_game_config()
    return timedelta(hours=game_config['phase_length'])

def process_signups(submission):
    logging.debug('Processing signups for [{}]'.format(submission.id))

    # Get comments from submission in chronological order
    submission.comments.replace_more(limit=None)
    submission.comments_sort = "old"
    comments = submission.comments.list()

    game_config = get_game_config()

    if 'live_players' not in game_config:
        game_config['live_players'] = []

    for comment in comments:
        if comment.created_utc > game_config['last_comment_time']:
            player = comment.author.name.lower()
            if '!signup' in comment.body.lower():
                if player not in game_config['live_players']:
                    if len(game_config['live_players']) < game_config['player_limit']:
                        logging.info('Player {} has signed up for the game'.format(player))
                        game_config['live_players'].append(player)
                        comment.reply('Added u/{} to the game!'.format(player))
                    else:
                        comment.reply('Sorry, the game is full')
                else:
                    comment.reply('You already signed up')
            game_config['last_comment_time'] = comment.created_utc
    update_game_config({'live_players': game_config['live_players'], 'last_comment_time': game_config['last_comment_time']})

    return len(game_config['live_players']) >= game_config['player_limit']

def process_votes(submission):
    logging.debug('Processing votes for phase [{}]'.format(submission.id))

    # Get comments from submission in chronological order
    submission.comments.replace_more(limit=None)
    submission.comments_sort = "old"
    comments = submission.comments.list()

    game_config = get_game_config()

    phase_data = get_phase_data()
    if 'votes' not in phase_data:
        votes = {}
    else:
        votes = phase_data['votes']

    for comment in comments:
        if comment.created_utc > game_config['last_comment_time']:
            player = comment.author.name.lower()
            match = vote_pattern.match(comment.body.lower())
            if match:
                target = match.group(1)
                logging.debug('Player {} declared a vote for {}'.format(player, target))
                if target in game_config['live_players']:
                    votes[player] = target
                    comment.reply('Recorded u/{}\'s vote for u/{}'.format(player, target))
                else:
                    comment.reply('u/{} is not a valid vote target'.format(target))
            game_config['last_comment_time'] = comment.created_utc

    update_phase_data({'votes': votes, 'last_comment_time': game_config['last_comment_time']})

def process_actions(reddit):
    logging.debug('Processing actions for current phase')

    # Get unread messages from inbox

    # for each message
        # if it is an action
            # add action to the actions payload
        # mark it as read

    # submit actions payload to the server

def handle_turnover(submission, subreddit, reddit):
    logging.info('Handling turnover for phase [{}]'.format(submission.id))

    # Lock the post
    logging.debug('Locking phase post [{}]'.format(submission.id))
    try:
        submission.mod.lock()
    except:
        logging.exception('Failed to lock phase post [{}]'.format(submission.id))

    # Process any final comments
    logging.debug('Processing final votes from phase post [{}]'.format(submission.id))
    process_votes(submission)

    # Process any final action submissions
    logging.debug('Processing final action submissions for phase [{}]'.format(submission.id))
    process_actions(reddit)

    # Get new phase title and text from server
    logging.debug('Handling turnover on server')
    new_phase_data = requests.get(request_url + '/handle_turnover/').json()
    logging.debug('New phase data from server:\n{}\n\n{}'.format(new_phase_data['title'], new_phase_data['body']))

    # Create a new phase post
    new_phase = subreddit.submit(title=new_phase_data['title'], selftext=new_phase_data['body'], send_replies=False)
    logging.debug('Posted new phase [{}]'.format(new_phase.id))

    # Store the new phase post id
    set_active_phase(new_phase)


def main():
    config = Config.Config('myconfig')
    reddit = config.reddit_object
    subreddit = config.subreddit_object

    # Get the game config
    game_config = get_game_config()

    if game_config['phase'].lower() == 'init':
        logging.info('Init new game')
        # Post signup sheet
        signup_post = subreddit.submit(title='New Game Signups', selftext=signup_text, send_replies=False)

        # Set game phase to 'signup' and current post to signup post
        config_update = {'phase': 'signup', 'post_id': signup_post.id, 'last_comment_time': 0}
        update_game_config(config_update)

    elif game_config['phase'].lower() == 'signup':
        logging.info('Handle signups')

        signup_post = get_active_phase(reddit)
        game_full = process_signups(signup_post, game_config)

        # if player count = limit
        if game_full:
            # lock signups
            signup_post.mod.lock()

            # assign roles
            # send role PMs
            # add wolves to private sub
            # post P0 and set to active post
            # set active phase to 0
    else:
        # Get the active game post
        active_game_post = get_active_phase(reddit)

        # Check whether or not it's time for turnover
        post_time = datetime.fromtimestamp(active_game_post.created_utc, timezone.utc)
        if check_time - post_time > get_phase_length():
            logging.debug('Time since phase was posted {}'.format(check_time - post_time))
            handle_turnover(active_game_post, subreddit, reddit)
        else:
            logging.debug('{} to turnover'.format(get_phase_length() - (check_time - post_time)))
            # Process any votes
            process_votes(active_game_post)

            # Process any action submissions
            process_actions(reddit)

if __name__ == '__main__':
	main()
