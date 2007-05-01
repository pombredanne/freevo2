# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# scummvm.py - the scummvm player
# -----------------------------------------------------------------------------
# $Id$
#
# The scummvm player is a player for the scummvm. You need to have loaded
# the game previous with the scummvm. It will find all the configured
# games. In addition it will offer to run the scummvm without a game to
# configure a new game.
#
# -----------------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2007 Dirk Meyer, et al.
#
# First Edition: Mathias Weber <mweb@gmx.ch>
# Maintainer:    Mathias Weber <mweb@gmx.ch>
#
# Please see the file AUTHORS for a complete list of authors.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MER-
# CHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# -----------------------------------------------------------------------------

# python imports
import logging

# kaa imports
import kaa.utils

# Freevo imports
from freevo.ui.menu import ActionItem, Menu, Action
from freevo.ui import config

# games imports
from freevo.ui.games.emulator import EmulatorPlugin
import freevo.ui.games.player as gameplayer
from pcgames import PcGamePlayer, PcGameItem

# get logging object
log = logging.getLogger('games')

# get config object
config = config.games.plugin.scummvm

class ScummvmPlayer(PcGamePlayer):
    """
    The PcGamePlayer loader.
    """

    def open(self, item):
        """
        Open a PcGameItem, get executable and parameters for playing
        """
        self.emulator_item = item.binary


    def play(self):
        """
        Play PcGame
        """
        log.info('Start playing PcGame (Scummvm: %s)', self.emulator_item)
        parameters = '%s %s' % (config.parameters, self.emulator_item)
        self.child = kaa.notifier.Process(config.bin)
        self.child.start(parameters).connect(self.completed)
        self.signals = self.child.signals
        stop = kaa.notifier.WeakCallback(self.stop)
        self.child.set_stop_command(stop)


class ScummvmItem(PcGameItem):
    """
    A scummvm Item
    """

    def play(self):
        gameplayer.play(self, ScummvmPlayer())


class PluginInterface(EmulatorPlugin):
    """
    Add Scummvm games to the games menu
    """
    romlist = []
    finished = False
    parent = None
    items = None
    list_started = False

    def completed(self, exit_code):
        """
        The ScummVM returned all configured games, append them to the menu.
        Add an entry for the ScummVM it self to configure new games or the
        ScummVM it self.
        """
        if self.items == None:
            self.items = []
        self.items.append(ScummvmItem(self.parent, 'ScummVM', ''))
        self.parent.get_menustack().pushmenu(Menu(config.name, self.items, type='games'))
        self.parent = None


    def get_stdout(self, data):
        """
        Receive updates from the stdout of the ScummVM. Wait with parsing
        until a line that starts with '---'
        """
        if self.items == None:
            if data.startswith('---'):
                self.items = []
            return
        # since list was started there are now the configured games coming    
        name = data[:data.find(' ')]
        description = data[data.find(' '):].strip()
        self.items.append(ScummvmItem(self.parent, description, name))        


    def roms(self, parent):
        """
        Show all games.
        """
        # allready waiting for updated menu?
        if self.parent != None:
            return
        self.parent = parent
        self.items = None
        items = []
        # get list of scummvm start a new process
        self.child = kaa.notifier.Process(config.bin)
        self.child.start('-t').connect(self.completed)
        self.child.signals['stdout'].connect(self.get_stdout)
        

    def items(self, parent):
        """
        Return the main menu item.
        """
        if not config.bin or \
               (not config.bin.startswith('/') and not
                kaa.utils.which(config.bin)):
            # no binary defined or not found
            return []
        return [ ActionItem(config.name, parent, self.roms) ]
