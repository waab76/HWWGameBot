import json
import praw

def get_json_data(fname):
	with open(fname) as json_data:
		data = json.load(json_data)
	return data

class Config():
	def __init__(self, config_file_name):
		self.fname = "config/" + config_file_name.lower() + ".json"
		self.raw_config = get_json_data(self.fname)
		self.client_id = self.raw_config['client_id']
		self.client_secret = self.raw_config['client_secret']
		self.bot_username = self.raw_config['bot_username']
		self.bot_password = self.raw_config['bot_password']
		self.refresh_token = self.raw_config['refresh_token']
		self.reddit_object = praw.Reddit(client_id=self.client_id, client_secret=self.client_secret, user_agent='Mafia Game Bot v0.2 (by u/BourbonInExile)', refresh_token=self.refresh_token)
