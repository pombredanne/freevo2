#if 0 /*
# -----------------------------------------------------------------------
# main.py - This is the Freevo main application code
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
# Todo:        
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.29  2003/03/15 17:13:22  dischi
# store rom drive type in media
#
# Revision 1.28  2003/03/15 16:45:47  dischi
# make the shutdown look nicer for mga video
#
# Revision 1.27  2003/03/10 07:11:23  outlyer
# Just some fixes to prevent the idle bar from appearing on top of widescreen
# video.
#
# Revision 1.26  2003/03/02 22:09:19  dischi
# Reload main menu on skin change, too
#
# Revision 1.25  2003/03/02 21:33:17  dischi
# The main menu is a class of its own, all items in the main menu inherit
# from Item. If the new skin code is active, DISPLAY will pop up a skin
# selector.
#
# Revision 1.24  2003/02/24 04:03:25  krister
# Added a --trace option to see all function calls in freevo.
#
# Revision 1.23  2003/02/22 22:32:27  krister
# Removed debug code, cleanup
#
# Revision 1.22  2003/02/22 07:13:19  krister
# Set all sub threads to daemons so that they die automatically if the main thread dies.
#
# Revision 1.21  2003/02/21 18:43:50  outlyer
# Fixed the spelling from Enablind to Enabled :) Also commented out the
# code Krister added to prove a point. Consider it proven...
#
# I should mention that the idle tool does work fine on other skins, especially
# since it has no configuration information elsewhere.
#
# Revision 1.20  2003/02/21 16:25:10  dischi
# main items can have images
#
# Revision 1.19  2003/02/21 06:51:15  krister
# XXX Debug the event loop, remove later.
#
# Revision 1.18  2003/02/21 05:26:59  krister
# Enable the IdleTool if Aubins skin is used.
#
# Revision 1.17  2003/02/20 20:14:44  dischi
# needed for a new gentoo runtime with pylirc
#
# Revision 1.16  2003/02/19 08:08:30  krister
# Applied Aubins new pylirc code after testing it (seems to work with keyboard at least), and adding the pylircmodule to the runtime build environment (not required for keyboard operation).
#
# Revision 1.5  2003/02/18 23:47:56  outlyer
# Synced pylirc version of main to Rob's latest changes, added some
# error handling to weather checker.
#
# Revision 1.15  2003/02/18 23:08:25  rshortt
# Hooking up the code in src/gui.  Added osd.focused_app to keep track of
# what should first receive the events.  In main this is set to be the
# menuwidget which is the parent UI object.  I also made MenuWidget into
# a subclass of GUIObject so that it can closely take advantage of the
# parent / child relationship therein.
#
# -----------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2002 Krister Lagerstrom, et al. 
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
# ----------------------------------------------------------------------- */
#endif

# Must do this here to make sure no os.system() calls generated by module init
# code gets LD_PRELOADed
import os
os.environ['LD_PRELOAD'] = ''

import sys, socket, random, time
import traceback

sys.path.append('.')

# Gentoo runtime has some python files in runtime/python
if os.path.exists('./runtime/python'):
    sys.path.append('./runtime/python')
    
import config

import util    # Various utilities
import osd     # The OSD class, used to communicate with the OSD daemon
import menu    # The menu widget class
import skin    # The skin class
import mixer   # The mixer class
import rc      # The RemoteControl class.
import tv.tv   # The TV module

import identifymedia
import signal

import idle

from mediamenu import MediaMenu
from item import Item

DEBUG = config.DEBUG

TRUE  = 1
FALSE = 0

skin    = skin.get_singleton()


# Set up the mixer
# XXX Doing stuff to select correct device to manipulate.
mixer = mixer.get_singleton()

if config.MAJOR_AUDIO_CTRL == 'VOL':
    mixer.setMainVolume(config.DEFAULT_VOLUME)
    if config.CONTROL_ALL_AUDIO:
        mixer.setPcmVolume(config.MAX_VOLUME)
        # XXX This is for SB Live cards should do nothing to others
        # XXX Please tell if you have problems with this.
        mixer.setOgainVolume(config.MAX_VOLUME)
elif config.MAJOR_AUDIO_CTRL == 'PCM':
    mixer.setPcmVolume(config.DEFAULT_VOLUME)
    if config.CONTROL_ALL_AUDIO:
        mixer.setMainVolume(config.MAX_VOLUME)
        # XXX This is for SB Live cards should do nothing to others
        # XXX Please tell if you have problems with this.
        mixer.setOgainVolume(config.MAX_VOLUME)
else:
    if DEBUG: print "No appropriate audio channel found for mixer"

if config.CONTROL_ALL_AUDIO:
    mixer.setLineinVolume(0)
    mixer.setMicVolume(0)

# Create the remote control object
rc = rc.get_singleton()

# Create the OSD object
osd = osd.get_singleton()

# Create the MenuWidget object
menuwidget = menu.get_singleton()

# Identify_Thread
im_thread = None




def shutdown(menuw=None, arg=None, allow_sys_shutdown=1):
    """
    function to shut down freevo or the whole system
    """
    osd.clearscreen(color=osd.COL_BLACK)
    osd.drawstring('shutting down...', osd.width/2 - 90, osd.height/2 - 10,
                   fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
    osd.update()

    time.sleep(0.5)

    if arg == None:
        sys_shutdown = allow_sys_shutdown and 'ENABLE_SHUTDOWN_SYS' in dir(config)
    else:
        sys_shutdown = arg

    # XXX temporary kludge so it won't break on old config files
    if sys_shutdown:  
        if config.ENABLE_SHUTDOWN_SYS:
            # shutdown dual head for mga
            if config.CONF.display == 'mga':
                os.system('./fbcon/matroxset/matroxset -f /dev/fb1 -m 0')
                time.sleep(1)
                os.system('./fbcon/matroxset/matroxset -f /dev/fb0 -m 1')
                time.sleep(1)

            os.system(config.SHUTDOWN_SYS_CMD)
        
            # let freevo be killed by init, looks nicer for mga
            return

    # SDL must be shutdown to restore video modes etc
    osd.shutdown()

    #
    # Here are some different ways of exiting freevo for the
    # different ways that it could have been started.
    #
    
    # XXX kludge to shutdown the runtime version (no linker)
    util.killall('freevo_python')
    util.killall('freevo_loader')
    util.killall('freevo_xwin')
    # XXX Kludge to shutdown if started with "python main.py"
    os.system('kill -9 `pgrep -f "python.*main.py" -d" "` 2&> /dev/null') 

    # Just wait until we're dead. SDL cannot be polled here anyway.
    while 1:
        time.sleep(1)
        


def get_main_menu(parent):
    """
    function to get the items on the main menu based on the settings
    in the skin
    """

    items = []
    menu_items = skin.settings.mainmenu.items

    for i in menu_items:
        if menu_items[i].visible:

            # if it's has actions() it is an item already
            if hasattr(eval(menu_items[i].action), 'actions'):
                item = eval(menu_items[i].action)(None)
                if menu_items[i].icon:
                    item.icon = menu_items[i].icon
                if menu_items[i].name:
                    item.name = menu_items[i].name
                item.parent = parent
                items += [ item ]

            else:
                items += [ MainMenuItem(parent, menu_items[i].name,
                                        menu_items[i].icon,
                                        menu_items[i].image,
                                        eval(menu_items[i].action),
                                        menu_items[i].arg) ]
    return items
    

class ShutdownItem(Item):
    """
    Item for shutdown
    """
    def actions(self):
        """
        return a list of actions for this item
        """
        items = [ ( self.shutdown_freevo, 'Shutdown Freevo' ),
                  ( self.shutdown_system, 'Shutdown system' ) ]
        if config.ENABLE_SHUTDOWN_SYS:
            items.reverse()
        return items


    def shutdown_freevo(self, arg=None, menuw=None):
        """
        shutdown freevo, don't shutdown the system
        """
        shutdown(menuw=menuw, arg=FALSE)

        
    def shutdown_system(self, arg=None, menuw=None):
        """
        shutdown the complete system
        """
        shutdown(menuw=menuw, arg=TRUE)
    

class MainMenuItem(Item):
    """
    Default item for the main menu actions
    """
    def __init__(self, parent, name, icon, image, action, arg):
        Item.__init__(self, parent)
        self.name     = name
        self.icon     = icon
        self.image    = image
        self.function = action
        self.arg      = arg
        self.type     = 'main'
        
    def actions(self):
        return [ ( self.select, '' ) ]

    def select(self, arg=None, menuw=None):
        self.function(arg=self.arg, menuw=menuw)


class SkinSelectItem(Item):
    """
    Icon for the skin selector
    """
    def __init__(self, parent, name, image, skin):
        Item.__init__(self, parent)
        self.name  = name
        self.image = image
        self.skin  = skin
        
    def actions(self):
        return [ ( self.select, '' ) ]

    def select(self, arg=None, menuw=None):
        """
        Load the new skin and rebuild the main menu
        """
        skin.settings = skin.LoadSettings(self.skin, copy_content = FALSE)
        pos = menuw.menustack[0].choices.index(menuw.menustack[0].selected)
        menuw.menustack[0].choices = get_main_menu(self.parent)
        menuw.menustack[0].selected = menuw.menustack[0].choices[pos]
        menuw.back_one_menu()

        
class MainMenu(Item):
    """
    this class handles the main menu
    """
    
    def getcmd(self):
        """
        Setup the main menu and handle events (remote control, etc)
        """
        
        items = get_main_menu(self)

        mainmenu = menu.Menu('FREEVO MAIN MENU', items, packrows=0, umount_all = 1)
        menuwidget.pushmenu(mainmenu)
        osd.focused_app = menuwidget

        muted = 0
        mainVolume = 0 # XXX We are using this for PcmVolume as well.


    def eventhandler(self, event = None, menuw=None, arg=None):
        """
        Automatically perform actions depending on the event, e.g. play DVD
        """

        global im_thread
        
        # if we are at the main menu and there is an IDENTIFY_MEDIA event,
        # try to autorun the media
        if event == rc.IDENTIFY_MEDIA and im_thread and im_thread.last_media and \
           menuw and len(menuw.menustack) == 1:
            media = im_thread.last_media
            if media.info and media.info.actions():
                media.info.actions()[0][0](menuw=menuw)
            else:
                menuw.refresh()
            return TRUE

        # pressing DISPLAY on the main menu will open a skin selector
        # (only for the new skin code)
        if event == rc.DISPLAY and config.NEW_SKIN:
            items = []
            for name, image, skinfile in skin.GetSkins():
                items += [ SkinSelectItem(self, name, image, skinfile) ]

            menuwidget.pushmenu(menu.Menu('SKIN SELECTOR', items))

        print 'main.py:eventhandler(): event=%s, arg=%s' % (event, arg)
    

class RemovableMedia:

    def __init__(self, mountdir='', devicename='', drivename=''):
        # This is read-only stuff for the drive itself
        self.mountdir = mountdir
        self.devicename = devicename
        self.drivename = drivename

        # Dynamic stuff
        self.tray_open = 0
        self.drive_status = None  # return code from ioctl for DRIVE_STATUS

        self.id    = ''
        self.label = ''
        self.info  = None
        self.type  = 'empty_cdrom'

    def is_tray_open(self):
        return self.tray_open

    def move_tray(self, dir='toggle', notify=1):
        """Move the tray. dir can be toggle/open/close
        """

        if dir == 'toggle':
            if self.tray_open:
                dir = 'close'
            else:
                dir = 'open'

        if dir == 'open':
            if DEBUG: print 'Ejecting disc in drive %s' % self.drivename
            if notify:
                skin.PopupBox('Ejecting disc in drive %s' % self.drivename)
                osd.update()
            os.system('eject %s' % self.devicename)
            self.tray_open = 1
            rc.post_event(rc.REFRESH_SCREEN)
        
        elif dir == 'close':
            if DEBUG: print 'Inserting %s' % self.drivename
            if notify:
                skin.PopupBox('Reading disc in drive %s' % self.drivename)
                osd.update()

            # close the tray, identifymedia does the rest,
            # including refresh screen
            os.system('eject -t %s' % self.devicename)
            self.tray_open = 0
    
    def mount(self):
        """Mount the media
        """

        if DEBUG: print 'Mounting disc in drive %s' % self.drivename
        skin.PopupBox('Locking disc in drive %s' % self.drivename)
        osd.update()
        util.mount(self.mountdir)
        return

    
    def umount(self):
        """Mount the media
        """

        if DEBUG: print 'Unmounting disc in drive %s' % self.drivename
        skin.PopupBox('Releasing disc in drive %s' % self.drivename)
        osd.update()
        util.umount(self.mountdir)
        return
    

def signal_handler(sig, frame):
    if sig == signal.SIGTERM:
        osd.clearscreen(color=osd.COL_BLACK)
        osd.shutdown() # SDL must be shutdown to restore video modes etc

        # XXX kludge to shutdown the runtime version (no linker)
        util.killall('freevo_python')
        util.killall('freevo_loader')
        util.killall('freevo_xwin')
        # XXX Kludge to shutdown if started with "python main.py"
        os.system('kill -9 `pgrep -f "python.*main.py" -d" "` 2&> /dev/null') 


#
# Main init
#
def main_func():

    # Add the drives to the config.removable_media list. There doesn't have
    # to be any drives defined.
    if config.ROM_DRIVES != None: 
        for i in range(len(config.ROM_DRIVES)):
            (dir, device, name) = config.ROM_DRIVES[i]
            media = RemovableMedia(mountdir=dir, devicename=device,
                                   drivename=name)
            # close the tray without popup message
            media.move_tray(dir='close', notify=0)
            osd.clearscreen(color=osd.COL_BLACK)
            osd.update()
            config.REMOVABLE_MEDIA.append(media)

    # Remove the ROM_DRIVES member to make sure it is not used by
    # legacy code!
    del config.ROM_DRIVES   # XXX Remove later
    
    signal.signal(signal.SIGTERM, signal_handler)

    # Start identifymedia thread
    global im_thread
    im_thread = identifymedia.Identify_Thread()
    im_thread.setDaemon(1)
    im_thread.start()
    
    # scan for plugins
    for t in ('video', 'audio', 'image', 'games'):
        config.FREEVO_PLUGINS[t] = []
        dirname = 'src/%s/plugins' % t
        if os.path.isdir(dirname):
            for plugin in [ os.path.splitext(fname)[0] for fname in os.listdir(dirname)
                            if os.path.isfile(os.path.join(dirname, fname))\
                            and os.path.splitext(fname)[1].lower()[1:] == 'py' \
                            and not fname == '__init__.py']:
                try:
                    exec('import %s.plugins.%s' % (t, plugin))
                    if hasattr(eval('%s.plugins.%s'  % (t, plugin)), 'actions'):
                        print 'load %s plugin %s ' % (t, plugin)
                    config.FREEVO_PLUGINS[t] += [ eval('%s.plugins.%s.actions'\
                                                       % (t, plugin)) ]
                except:
                    traceback.print_exc()

    main = MainMenu()
    main.getcmd()

    # XXX TEST CODE
    if config.SKIN_XML_FILE.find('aubin_round') != -1:
        print 'Enabled the IdleTool'
        m = idle.IdleTool()
    else:
        m = None
    m and m.refresh()


    # Kick off the main menu loop
    print 'Main loop starting...'

    while 1:

        # Get next command
        while 1:

            event = osd._cb()
            if event:
                break
            event = rc.poll()
            if event:
                break
            if not rc.func:
                m and m.poll()
            time.sleep(0.1)

        if not rc.func:
            m and m.refresh()
        # Handle volume control   XXX move to the skin
        if event == rc.VOLUP:
            print "Got VOLUP in main!"
            if( config.MAJOR_AUDIO_CTRL == 'VOL' ):
                mixer.incMainVolume()
            elif( config.MAJOR_AUDIO_CTRL == 'PCM' ):
                mixer.incPcmVolume()

        elif event == rc.VOLDOWN:
            if( config.MAJOR_AUDIO_CTRL == 'VOL' ):
                mixer.decMainVolume()
            elif( config.MAJOR_AUDIO_CTRL == 'PCM' ):
                mixer.decPcmVolume()

        elif event == rc.MUTE:
            if muted:
                if config.MAJOR_AUDIO_CTRL == 'VOL':
                    mixer.setMainVolume(mainVolume)
                elif config.MAJOR_AUDIO_CTRL == 'PCM':
                    mixer.setPcmVolume(mainVolume)
                muted = 0
            else:
                if config.MAJOR_AUDIO_CTRL == 'VOL':
                    mainVolume = mixer.getMainVolume()
                    mixer.setMainVolume(0)
                elif config.MAJOR_AUDIO_CTRL == 'PCM':
                    mainVolume = mixer.getPcmVolume()
                    mixer.setPcmVolume(0)
                muted = 1

        # Handle the EJECT key for the main menu
        elif event == rc.EJECT and len(menuwidget.menustack) == 1:

            # Are there any drives defined?
            if not config.REMOVABLE_MEDIA: continue

            # The default is the first drive in the list
            media = config.REMOVABLE_MEDIA[0]  
            media.move_tray(dir='toggle')

        # Send events to either the current app or the menu handler
        if rc.app:
            rc.app(event)
        else:
            if osd.focused_app:
                osd.focused_app.eventhandler(event)


#
# Main function
#
if __name__ == "__main__":
    def tracefunc(frame, event, arg, _indent=[0]):
        if event == 'call':
            filename = frame.f_code.co_filename
            funcname = frame.f_code.co_name
            lineno = frame.f_code.co_firstlineno
            if 'self' in frame.f_locals:
                try:
                    classinst = frame.f_locals['self']
                    classname = repr(classinst).split()[0].split('(')[0][1:]
                    funcname = '%s.%s' % (classname, funcname)
                except:
                    pass
            here = '%s:%s:%s()' % (filename, lineno, funcname)
            _indent[0] += 1
            tracefd.write('%4s %s%s\n' % (_indent[0], ' ' * _indent[0], here))
            tracefd.flush()
        elif event == 'return':
            _indent[0] -= 1

        return tracefunc

    if len(sys.argv) >= 2 and sys.argv[1] == '--trace':
        tracefd = open(os.path.join(os.environ['FREEVO_STARTDIR'],
                                    'trace.txt'), 'w')
        sys.settrace(tracefunc)
    
    try:
        main_func()
    except KeyboardInterrupt:
        print 'Shutdown by keyboard interrupt'
        # Shutdown the application
        shutdown(allow_sys_shutdown=0)

    except:
        print 'Crash!'
        try:
            tb = sys.exc_info()[2]
            fname, lineno, funcname, text = traceback.extract_tb(tb)[-1]
            
            for i in range(1, 0, -1):
                osd.clearscreen(color=osd.COL_BLACK)
                osd.drawstring('Freevo crashed!', 70, 70,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                osd.drawstring('Filename: %s' % fname, 70, 130,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                osd.drawstring('Lineno: %s' % lineno, 70, 160,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                osd.drawstring('Function: %s' % funcname, 70, 190,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                osd.drawstring('Text: %s' % text, 70, 220,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                osd.drawstring('Please see the logfiles for more info', 70, 280,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                
                osd.drawstring('Exit in %s seconds' % i, 70, 340,
                               fgcolor=osd.COL_ORANGE, bgcolor=osd.COL_BLACK)
                osd.update()
                time.sleep(1)
                
        except:
            pass
        traceback.print_exc()

        # Shutdown the application, but not the system even if that is
        # enabled
        shutdown(allow_sys_shutdown=0)
