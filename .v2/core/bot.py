from twitter import *
import sys

from core.interpreter import Interpreter
from system import *

from asset import Asset

rest = Twitter(auth=OAuth(
  conf.access_token_key,
  conf.access_token_secret,
  conf.consumer_key,
  conf.consumer_secret
))
strm = TwitterStream(auth=OAuth(
  conf.access_token_key,
  conf.access_token_secret,
  conf.consumer_key,
  conf.consumer_secret
))

class Bot:

  with_init_tw = False
  __name    = ''
  __filters = ['FirstOfStreaming','Retweet','Myself']
  bot       = None
  console   = False

  def __init__(self, name):
    self.__name = name
    self.bot = dict(screen_name=name)

  def listen(self, with_init_tw=False):
    tl = strm.user(**self.bot)
    if with_init_tw:
      rest.statuses.update(status=Asset('serif').load('common','Initd').get_text(time_footer=True))
    for t in tl:
      Logger('default').execute(t)
      tw = util.convert_twitter_format(t)
      try:
        self.tweet_by_tweet(tw)
      except:
        Logger('error').execute(t)
        Alert(info=sys.exc_info(),twtxt=tw['text']).send_mail()

  def draw(self, key='all', console=False):
    self.console = console
    test_tweets = Asset('test.tw').get_dict()
    if key == 'all':
      for k,tw in test_tweets.items():
        _executed = self.tweet_by_tweet(tw)
        self._presentation(k,tw,_executed)
    else:
      tw = test_tweets[key]
      _executed = self.tweet_by_tweet(tw)
      self._presentation(key,tw,_executed)

  def remind(self, mode):
    context = { 'proc'   : {'module' : '.'.join(['remind',mode]), 'class'  : 'Execute' },'params' : {} }
    res = self.proc_this_context(context)
    if len(res['args']['masters']) is 0:
      print("There is No Master Needs %s Remind" % mode)
    for m in res['args']['masters']:
      _res = {'resp':res['resp'],'args':{'user':m}}
      msg_args = self.generate_message(_res)
      result = self.dispatch_action(msg_args)
      print("%s\t%s\tREMIND DONE" % (m['name'], mode))

  def monologue(self, console=False):
    self.console = console
    context = { 'proc'   : {'module' : 'monologue', 'class'  : 'Execute' }, 'params' : {} }
    res = self.proc_this_context(context)
    if res is None:
      if self.console:
        return self._presentation('Monologue',{'text':'-----'}, {'Actions':{'message':'Pass by monologue rate'}})
      return None
    msg_args = self.generate_message(res)
    if self.console:
      return self._presentation('Monologue',{'text':'-----'}, {'Actions':msg_args})
    result = self.dispatch_action(msg_args)

  # core function
  def tweet_by_tweet(self, tweet):
    if self.pass_this_tw(tweet):
      return None
    context = self.interpret_this_tw(tweet)
    _executed = {}
    if context['proc'] is None:
      return None
    res = self.proc_this_context(context)
    _executed['Procedure'] = context['proc']
    if res['resp'] is None:
      return None
    msg_args = self.generate_message(res)
    _executed['Response'] = res['resp']
    if msg_args['actions'] is None or len(msg_args['actions']) is 0:
      return None
    if self.console:
      if 'message' in msg_args:
        _executed['Actions'] = msg_args
      return _executed
    result = self.dispatch_action(msg_args)
    _executed['Actions'] = result
    print({'EXECUTED':_executed})
    return None

  def pass_this_tw(self, tweet):
    mod = __import__('core.filters',globals(),locals(), self.__filters)
    for f in self.__filters:
      Fltr = getattr(mod, f)
      if Fltr.accept(tweet) is False:
        return True
    return False

  def interpret_this_tw(self,tweet):
    return Interpreter(tweet).execute()

  def proc_this_context(self, context):
    mod_name = context['proc']['module']
    cls_name = context['proc']['class']
    mod = __import__('.'.join(['core','procedure',mod_name]),globals(),locals(),[cls_name])
    Proc = getattr(mod, cls_name)
    return Proc().perform(context['params'])

  def generate_message(self, res):
    mod_name = res['resp']['module']
    cls_name = res['resp']['class']
    mod = __import__('.'.join(['core','response',mod_name]),globals(),locals(),[cls_name])
    Resp = getattr(mod, cls_name)
    return Resp().generate(res['args'])

  def dispatch_action(self, args):
    _finally = []
    if 'update_status' in args['actions']     and args['message'] is not None:
      if 'origin' in args:
        rest.statuses.update(status=args['message'], in_reply_to_status_id=args['origin']['id'])
      else:
        rest.statuses.update(status=args['message'])
      _finally.append('update_status')
    if 'friendships_create'  in args['actions'] and args['tw_id'] is not None:
      rest.friendships.create(id=args['tw_id'])
      _finally.append('friendships_create')
    if 'friendships_destroy' in args['actions'] and args['tw_id'] is not None:
      rest.friendships.destroy(id=args['tw_id'])
      _finally.append('friendships_destroy')
    return _finally

  def _presentation(self, k, tw, _executed):
    if _executed is None:
      print('=> %s\n\t|------\t"%s"\n\t|------\t%s\n\t`------\t"%s"' % (k,tw['text'], _executed,''))
      return True
    if 'message' in _executed['Actions']:
      mess = _executed['Actions']['message']
      _executed.pop('Actions')
      print('=> %s\n\t|------\t"%s"\n\t|------\t%s\n\t`------\t"%s"' % (k,tw['text'], _executed, mess))
      return True
    _executed.pop('Actions')
    print('=> %s\n\t|------\t"%s"\n\t`------\t%s' % (k,tw['text'], _executed, mess))
    return True