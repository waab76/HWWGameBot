from datetime import datetime, timedelta, timezone
import logging
from logging.handlers import TimedRotatingFileHandler
import Config

handlers = set()
handlers.add(TimedRotatingFileHandler('HWWGameBot.log', when='W0', backupCount=4))

logging.basicConfig(level=logging.INFO, handlers=handlers, format='%(asctime)s %(levelname)s %(module)s:%(funcName)s %(message)s')
logging.Formatter.formatTime = (lambda self, record, datefmt=None: datetime.fromtimestamp(record.created, timezone.utc).astimezone().isoformat(sep="T",timespec="milliseconds"))

import praw
import requests

request_url = 'http://0.0.0.0:8800'
check_time = datetime.now(timezone.utc)

def get_active_phase(reddit):
    payload = requests.get(request_url + '/active-phase/').json()
    logging.debug('Active phase post is {}'.format(payload['post_id']))
    return reddit.submission(payload['post_id'])

def set_active_phase(submission):
    logging.debug('Updating active phase post to [{}]'.format(submission.id))
    requests.post(request_url + '/active-phase/', {'post_id': submission.id})

def get_phase_length():
    return timedelta(hours=1)

def process_votes(submission):
    logging.debug('Processing votes for phase [{}]'.format(submission.id))

    # Get comments from submission in chronological order

    # for each comment
        # if not already seen
            # if it's a vote
                # add vote to votes payload
            # mark comment as seen

    # submit votes payload to server

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
