import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
import Config

handlers = set()
handlers.add(TimedRotatingFileHandler('HWWGameBot.log', when='W0', backupCount=4))

logging.basicConfig(level=logging.INFO, handlers=handlers, format='%(asctime)s %(levelname)s %(module)s:%(funcName)s %(message)s')
logging.Formatter.formatTime = (lambda self, record, datefmt=None: datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc).astimezone().isoformat(sep="T",timespec="milliseconds"))

import praw

request_url = "http://0.0.0.0:8000"
check_time = datetime.datetime.utcnow().time()

def main():
    config = Config.Config('myconfig')
    reddit = config.reddit_object
    sub = config.subreddit_object

    logging.info('Logged into Reddit as {}'.format(reddit.user.me()))

if __name__ == "__main__":
	main()
