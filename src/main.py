# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# main.py - This is the Freevo main application code
# -----------------------------------------------------------------------------
# $Id$
#
# This file is the python start file for Freevo. It handles the init phase like
# checking the python modules, loading the plugins and starting the main menu.
#
# It also contains the splashscreen and the skin chooser.
#
# First edition: Krister Lagerstrom <krister-freevo@kmlager.com>
# Maintainer:    Dirk Meyer <dmeyer@tzi.de>
#
# -----------------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2002-2004 Krister Lagerstrom, Dirk Meyer, et al. 
# Please see the file freevo/Docs/CREDITS for a complete list of authors.
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
import os
import sys, time
import traceback
import signal

try:
    import notifier
except ImportError:
    print 'This version of freevo requires pyNotifier 0.2.0rc1 or newer!'
    print 'You can find the current release at:'
    print 'http://www.crunchy-home.de/download/'
    sys.exit( 1 )
    
# init notifier
notifier.init( notifier.GENERIC )
    
try:
    # i18n support

    # First load the xml module. It's not needed here but it will mess
    # up with the domain we set (set it from freevo 4Suite). By loading it
    # first, Freevo will override the 4Suite setting to freevo
    from xml.utils import qp_xml
    from xml.dom import minidom
    
    # now load other modules to check if all requirements are installed
    import Image
    try:
        import twisted
    except ImportError, e:
        print e

    import config
    import system

    try:
        import Imlib2
    except:
        print 'The python Imlib2 bindings could not be loaded!'
        print 'Maybe you did not install Imlib2.'
        print 'You can find Imlib2 at: http://enlightenment.org'
        sys.exit( 1 )

    if config.OSD_DISPLAY == 'SDL':
        import pygame
        import Numeric

    if not config.CONF.lsdvd:
        print
        print 'Can\'t find lsdvd. DVD support will be limited and maybe not'
        print 'all discs are detected. Please install lsdvd, you can get it'
        print 'from http://acidrip.thirtythreeandathird.net/lsdvd.html'
        print
        print 'After installing it, you should run \'freevo cache --rebuild\''
    else:
        os.environ['LSDVD'] = config.CONF.lsdvd
        
    import mmpython

    
except ImportError, i:
    print 'Can\'t find all Python dependencies:'
    print i
    if str(i)[-7:] == 'Numeric':
        print 'You need to recompile pygame after installing Numeric!'
    print
    print 'Not all requirements of Freevo are installed on your system.'
    print 'Please check the INSTALL file for more informations.'
    print
    sys.exit(0)


# check if mmpython is up to date to avoid bug reports
# for already fixed bugs
try:
    import mmpython.version
    if mmpython.version.CHANGED < 20040629:
        raise ImportError
except ImportError:
    print 'Error: Installed mmpython version is too old.'
    print 'Please update mmpython to version 0.4.3 or higher'
    print
    sys.exit(0)


# freevo imports
import eventhandler
import childapp
import gui
import util
import menu
import plugin

from item import Item
from event import *
from cleanup import shutdown

# load the fxditem to make sure it's the first in the
# mimetypes list
import fxditem


class SkinSelectItem(Item):
    """
    Item for the skin selector
    """
    def __init__(self, parent, name, image, skin):
        Item.__init__(self, parent)
        self.name  = name
        self.image = image
        self.skin  = skin

        
    def actions(self):
        """
        Return the select function to load that skin
        """
        return [ ( self.select, '' ) ]


    def select(self, arg=None, menuw=None):
        """
        Load the new skin and rebuild the main menu
        """
        # load new theme
        theme = gui.theme_engine.set_base_fxd(self.skin)
        # set it to the main menu as used theme
        pos = menuw.menustack[0].theme = theme
        # and go back
        menuw.back_one_menu()


class MainMenu(Item):
    """
    This class handles the main menu
    """
    def getcmd(self):
        """
        Setup the main menu and handle events (remote control, etc)
        """
        menuw = menu.MenuWidget()
        items = []
        for p in plugin.get('mainmenu'):
            items += p.items(self)

        for i in items:
            i.is_mainmenu_item = True

        mainmenu = menu.Menu(_('Freevo Main Menu'), items, item_types='main',
                             umount_all = 1)
        mainmenu.item_types = 'main'
        mainmenu.theme = gui.get_theme()
        menuw.pushmenu(mainmenu)
        menuw.show()
        

    def get_skins(self):
        """
        return a list of all possible skins with name, image and filename
        """
        ret = []
        skindir = os.path.join(config.SKIN_DIR, 'main')
        skin_files = util.match_files(skindir, ['fxd'])

        # image is not usable stand alone
        skin_files.remove(os.path.join(config.SKIN_DIR, 'main/image.fxd'))
        skin_files.remove(os.path.join(config.SKIN_DIR, 'main/basic.fxd'))
        
        for skin in skin_files:
            name  = os.path.splitext(os.path.basename(skin))[0]
            if os.path.isfile('%s.png' % os.path.splitext(skin)[0]):
                image = '%s.png' % os.path.splitext(skin)[0]
            elif os.path.isfile('%s.jpg' % os.path.splitext(skin)[0]):
                image = '%s.jpg' % os.path.splitext(skin)[0]
            else:
                image = None
            ret += [ ( name, image, skin ) ]
        return ret


    def eventhandler(self, event = None, menuw=None, arg=None):
        """
        Automatically perform actions depending on the event, e.g. play DVD
        """
        # pressing DISPLAY on the main menu will open a skin selector
        # (only for the new skin code)
        if event == MENU_CHANGE_STYLE:
            items = []
            for name, image, skinfile in self.get_skins():
                items += [ SkinSelectItem(self, name, image, skinfile) ]

            menuw.pushmenu(menu.Menu(_('Skin Selector'), items))
            return True

        # give the event to the next eventhandler in the list
        return Item.eventhandler(self, event, menuw)
        
    

class Splashscreen(gui.Area):
    """
    A simple splash screen for osd startup
    """
    def __init__(self, text, max_value):
        gui.Area.__init__(self, 'content')
        self.max_value = max_value
        self.text      = text
        self.bar       = None
        self.engine    = gui.AreaHandler('splashscreen', ('screen', self))
        self.engine.show()

        
    def clear(self):
        """
        clear all content objects
        """
        self.bar.unparent()
        self.text.unparent()
            
        
    def update(self):
        """
        update the splashscreen
        """
        if self.bar:
            return

        content = self.calc_geometry(self.layout.content, copy_object=True)
        x0, x1 = content.x, content.x + content.width
        y = content.y + content.font.font.height + content.spacing

        self.text = self.drawstring(self.text, content.font, content,
                                    height=-1, align_h='center')
        self.bar = gui.Progressbar((x0, y), (x1-x0, 20), 2, (0,0,0),
                                   None, 0, None, (0,0,0,95), 0,
                                   self.max_value)
        self.layer.add_child(self.bar)


    def progress(self):
        """
        set the progress position and refresh the screen
        """
        if self.bar:
            self.bar.tick()
        if self.engine:
            self.engine.draw(None)


    def hide(self):
        """
        fade out
        """
        self.engine.hide(config.OSD_FADE_STEPS)

        
    def destroy(self):
        """
        destroy the object
        """
        del self.engine



def signal_handler(sig, frame):
    """
    the signal handler to shut down freevo
    """
    if sig in (signal.SIGTERM, signal.SIGINT):
        shutdown(exit=True)



#
# Freevo main function
#

# parse arguments
if len(sys.argv) >= 2:

    # force fullscreen mode
    # deactivate screen blanking and set osd to fullscreen
    if sys.argv[1] == '-force-fs':
        os.system('xset -dpms s off')
        config.START_FULLSCREEN_X = 1

try:
    # signal handler
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # prepare the skin
    gui.get_theme().prepare()

    # Fire up splashscreen and load the plugins
    splash = Splashscreen(_('Starting Freevo, please wait ...'),
                          plugin.get_number()-1)
    plugin.init(splash.progress)

    # Fire up splashscreen and load the cache
    if config.MEDIAINFO_USE_MEMORY == 2:
        # delete previous splash screen object
        splash.destroy()
        splash = Splashscreen(_('Reading cache, please wait ...'), 1)

        cachefiles = []
        for type in ('video', 'audio', 'image', 'games'):
            if plugin.is_active(type):
                n = 'config.%s_ITEMS' % type.upper()
                x = eval(n)
                for item in x:
                    if os.path.isdir(item[1]):
                        cachefiles += [ item[1] ] + \
                                      util.get_subdirs_recursively(item[1])

        cachefiles = util.unique(cachefiles)
        splash.bar.set_max_value(len(cachefiles))
        
        for f in cachefiles:
            splash.progress()
            util.mediainfo.load_cache(f)

    # fade out the splash screen
    splash.hide()
    
    # prepare again, now that all plugins are loaded
    gui.get_theme().prepare()

    # start menu
    MainMenu().getcmd()

    # Wait for the startup animation. This is a bad hack but we won't
    # be able to remove our splashscreen otherwise. Big FIXME!
    gui.animation.render().wait()

    # delete splash screen
    splash.destroy()
    del splash
    
    # kick off the main menu loop
    notifier.addDispatcher( eventhandler.get_singleton().handle )
    notifier.addDispatcher( childapp.watcher.step )

    # start main loop
    notifier.loop()

    
except KeyboardInterrupt:
    print 'Shutdown by keyboard interrupt'
    # Shutdown Freevo
    shutdown()

except SystemExit:
    pass

except:
    print 'Crash!'
    try:
        tb = sys.exc_info()[2]
        fname, lineno, funcname, text = traceback.extract_tb(tb)[-1]

        if config.FREEVO_EVENTHANDLER_SANDBOX:
            secs = 5
        else:
            secs = 1
        # for i in range(secs, 0, -1):
        #     osd.clearscreen(color=osd.COL_BLACK)
        #     osd.drawstring(_('Freevo crashed!'), 70, 70)
        #     osd.drawstring(_('Filename: %s') % fname, 70, 130)
        #     osd.drawstring(_('Lineno: %s') % lineno, 70, 160)
        #     osd.drawstring(_('Function: %s') % funcname, 70, 190)
        #     osd.drawstring(_('Text: %s') % text, 70, 220)
        #     osd.drawstring(str(sys.exc_info()[1]), 70, 280)
        #     osd.drawstring(_('Please see the logfiles for more info'),
        #                    70, 350)
        #     osd.drawstring(_('Exit in %s seconds') % i, 70, 410)
        #     osd.update()
        #     time.sleep(1)
    except:
        pass
    traceback.print_exc()

    # Shutdown freevo
    shutdown()
