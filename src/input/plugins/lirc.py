# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# lirc.py - A lirc input plugin for Freevo.
# -----------------------------------------------------------------------
# $Id$
#
# This file handles the lirc input device and maps it to freevo events.
# If /dev/lirc is present, this plugin will be actiavted by
# freevo_config.py.
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.4  2004/10/06 19:24:02  dischi
# switch from rc.py to pyNotifier
#
# Revision 1.3  2004/09/27 18:40:34  dischi
# reworked input handling again
#
# Revision 1.2  2004/09/25 23:38:15  mikeruelle
# more missing imports
#
# Revision 1.1  2004/09/25 04:39:07  rshortt
# An input plugin for lirc: plugin.activate('input.lirc')
#
# -----------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2003 Krister Lagerstrom, et al. 
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
import notifier

import config
import plugin
import time
import os

try:
    import pylirc
except ImportError:
    print 'WARNING: PyLirc not found, lirc remote control disabled!'
    raise Exception


class PluginInterface(plugin.InputPlugin):
    """
    Input plugin for lirc
    """
    def __init__(self):
        plugin.InputPlugin.__init__(self)
        self.plugin_name = 'LIRC'
        self.__fd = None
        try:
            if os.path.isfile(config.LIRCRC):
                self.__fd = pylirc.init('freevo', config.LIRCRC)
                pylirc.blocking(0)
            else:
                raise IOError
        except RuntimeError, e:
            print 'WARNING: Could not initialize PyLirc!'
            raise e
        except IOError, e:
            print 'WARNING: %s not found!' % config.LIRCRC
            raise e

        self.nextcode = pylirc.nextcode
        self.previous_returned_code   = None
        self.previous_code            = None;
        self.repeat_count             = 0
        self.firstkeystroke           = 0.0
        self.lastkeystroke            = 0.0
        self.lastkeycode              = ''

        # FIXME: register socket to pynotifier
        notifier.addSocket( self.__fd, self.handle )


    def config(self):
        return [('LIRCRC', '/etc/freevo/lircrc', 
                           'Location of Freevo lircrc file.'),
                ('LIRC_DELAY1', 0.25, 'Repeat delay 1.'),
                ('LIRC_DELAY2', 0.25, 'Repeat delay 2.'),
               ]


    def get_last_code(self):
        """
        read the lirc interface
        """
        result = None

        if self.previous_code != None:
            # Let's empty the buffer and return the most recent code
            while 1:
                list = self.nextcode();
                if list != []:
                    break
        else:
            list = self.nextcode()

        if list == []:
            # It's a repeat, the flag is 0
            list   = self.previous_returned_code
            result = list

        elif list != None:
            # It's a new code (i.e. IR key was released), the flag is 1
            self.previous_returned_code = list
            result = list

        self.previous_code = result
        return result



    def handle( self ):
        """
        return next event
        """
        list = self.get_last_code()

        if list == None:
            nowtime = 0.0
            nowtime = time.time()
            if (self.lastkeystroke + config.LIRC_DELAY2 < nowtime) and \
                   (self.firstkeystroke != 0.0):
                self.firstkeystroke = 0.0
                self.lastkeystroke = 0.0
                self.repeat_count = 0

        if list != None:
            nowtime = time.time()

            if list:
                for code in list:
                    if ( self.lastkeycode != code ):
                        self.lastkeycode = code
                        self.lastkeystroke = nowtime
                        self.firstkeystoke = nowtime

            if self.firstkeystroke == 0.0 :
                self.firstkeystroke = time.time()
            else:
                if (self.firstkeystroke + config.LIRC_DELAY1 > nowtime):
                    list = []
                else:
                    if (self.lastkeystroke + config.LIRC_DELAY2 < nowtime):
                        self.firstkeystroke = nowtime

            self.lastkeystroke = nowtime
            self.repeat_count += 1

            for code in list:
                self.post_key(code)

        return True
