from config import config

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

# system imports
import time, sys
from heapq import nlargest

class Vote():
  # options is a dict
  def __init__(self, options, restrict=True, multiple=False):
    self.voters = set()
    self.options = options
    self.restrict = restrict
    self.allow_multiple = allow_multiple

  def vote(self, voter, option_name):
    if self.multiple == False and voter in self.voters:
      return
    if option not in self.options:
      if self.restrict:
        return
      else:
        self.options[option_name] = 0

    self.voters.add(voter)
    self.options[option_name] += 1

  def winner(self):
    return nlargest(1, self.options.iteritems(), key=lambda (k, v): (v, k))[0][0]

  def __repr__(self):
    largest = nlargest(3, self.options.iteritems(), key=lambda (k, v): (v, k))
    if len(self.options) == 0:
      return "Vote: empty";
    elif len(self.options) == 1:
      return "Vote: 1st {0}({1})".format(largest[0], self.options[largest[0]]);

    return "Vote: 1st {0}({1}), 2nd {1}({2})".format(largest[0], self.options[largest[0]], largest[1], self.options[largest[1]]);


class VoteBot(irc.IRCClient):
  nickname = config.BOT.NICKNAME
  password = config.BOT.PASSWORD

  def connectionMade(self):
    irc.IRCClient.connectionMade(self)

  def connectionLost(self, reason):
    irc.IRCClient.connectionLost(self, reason)


  # callbacks for events
  def signedOn(self):
    """Called when bot has succesfully signed on to server."""
    self.join(config.BOT.CHANNEL)

  def privmsg(self, user, channel, msg):
    """This will get called when the bot receives a message."""
    user = user.split('!', 1)[0]

    # Otherwise check to see if it is a message directed at me
    if msg.startswith(self.nickname):
      option_name = msg[:len(self.nickname)]
      self.vote(user, option_name)

  # Voting related methods
  def startVote(self):
    if self.vote:
      return

    self.vote = Vote()

  def endVote(self):
    winner = self.vote.winner()
    self.vote = None
    return winner

class VoteBotFactory(protocol.ClientFactory):
  """A factory for VoteBots.

  A new protocol instance will be created each time we connect to the server.
  """

  def buildProtocol(self, addr):
    p = VoteBot()
    p.factory = self
    return p

  def clientConnectionLost(self, connector, reason):
    """If we get disconnected, reconnect to server."""
    connector.connect()

  def clientConnectionFailed(self, connector, reason):
    print "connection failed:", reason
    reactor.stop()

bot = VoteBotFactory()
reactor.connectTCP(config.BOT.SERVER, config.BOT.PORT, bot)
reactor.run()
