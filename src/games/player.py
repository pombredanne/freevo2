
__all__ = [ 'gamesplayer' ]
from freevo.ui.application import Application, STATUS_RUNNING, STATUS_STOPPING, \
	 STATUS_STOPPED, STATUS_IDLE, CAPABILITY_TOGGLE, CAPABILITY_PAUSE, \
	 CAPABILITY_FULLSCREEN
from freevo.ui.event import *
from freevo.ui import plugin

_singleton = None

def gamesplayer():
    """
    return the global game player object
    """
    global _singleton
    if _singleton == None:
        _singleton = GamesPlayer()
    return _singleton

class GameRunningException:
    def __init__(self, title = None):
        self.title = title

    def __str__(self):
        return 'There is a game currently running named', self.title

class GamesPlayer(Application):
    """
    basic object to handle the different player
    """
    def __init__(self):
        capabilities = ()
        Application.__init__(self, 'games', 'games', capabilities)
        self.player     = None
        self.running    = False
        self.title      = None
        self.item       = None


    def play(self, item, player=None):
        """
        Start the appropriate emulator...
        """
        if self.player and self.player.is_playing():
            raise GameRunningException(self.title)

        self.item = item
        
        if player:
            self.player = player
        else:
            registerd_players = plugin.getbyname(plugin.GAMES, True)
            # Only ZSNES plugin exists for now....
            self.player = registerd_players[0]

        self.running = True
        error = self.player.play(self.item, self)
        if error:
            self.running = False
            self.item.eventhandler(PLAY_END)
        #else:
        #    self.refresh()

    def stop(self):
        """
        Stop running a emulator...
        """
        try:
            self.player.stop()
        finally:
            self.player = None
            self.running = False

    def eventhandler(self, event):
        print "Games Player eventhandler: ", event
        if event == STOP:
            self.stop()
            self.item.eventhandler(event)
            return True

        elif event == PLAY_END:
            Application.stop(self)
            Application.show(self)
            self.item.eventhandler(event)
            return True

        elif self.player and self.player.eventhandler(event):
            return True

        return self.item.eventhandler(event)
        
