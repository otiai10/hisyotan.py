from system import *

class FirstOfStreaming:
  @classmethod
  def accept(self, tweet):
    if tweet['friends'] is not None:
      return False
    return True

class Retweet:
  @classmethod
  def accept(self, tweet):
    # cannot catch retweeted status :(
    for k,v in tweet.items():
      if k == 'user' or k == 'text':
        continue
    if tweet['retweeted'] is True or 0 < int(tweet['retweet_count']):
      return False
    return True

class Myself:
  @classmethod
  def accept(self, tweet):
    if tweet['user']['screen_name'] == conf.bot_name:
      return False
    return True
