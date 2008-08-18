# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# base.py - Basic Application
# -----------------------------------------------------------------------------
# $Id$
#
# -----------------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2005-2007 Dirk Meyer, et al.
#
# First Edition: Dirk Meyer <dischi@freevo.org>
# Maintainer:    Dirk Meyer <dischi@freevo.org>
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

__all__ = [ 'Application' ]

# python imports
import logging

# kaa imports
import kaa

# freevo imports
from freevo.resources import ResourceHandler
from freevo.ui.gui import show_application as gui_show
from freevo.ui.gui.application import Application as ApplicationWidget

# application imports
from handler import handler

# get logging object
log = logging.getLogger()

STATUS_IDLE     = 'idle'
STATUS_RUNNING  = 'running'
STATUS_STOPPING = 'stopping'
STATUS_STOPPED  = 'stopped'

CAPABILITY_TOGGLE     = 1
CAPABILITY_PAUSE      = 2
CAPABILITY_FULLSCREEN = 4

class Application(ResourceHandler):
    """
    A basic application
    """

    Widget = ApplicationWidget

    def __init__(self, name, eventmap, capabilities=[]):
        """
        Init the Application object.
        """
        self.__name    = name
        self._eventmap = eventmap
        self._visible  = False
        self.signals   = kaa.Signals('show', 'hide', 'start', 'stop')
        self._status   = STATUS_IDLE
        self._capabilities = 0
        self.__widget  = None
        for cap in capabilities:
            self._capabilities |= cap
        self.gui_context = {}
        

    def has_capability(self, capability):
        """
        Return True if the application has the given capability.
        """
        return (self._capabilities & capability) != 0


    def get_status(self):
        """
        Return the current application status.
        """
        return self._status


    def set_status(self, status):
        """
        Set application status and react on some changes.
        """
        if status in (STATUS_STOPPED, STATUS_IDLE):
            self.free_resources()
        if status == STATUS_RUNNING and self._status == STATUS_IDLE:
            handler.show_application(self)
            self._status = status
            self.signals['start'].emit()
        elif status == STATUS_IDLE:
            handler.hide_application(self)
            self.free_resources(resume=True)
            self._status = status
            self.signals['stop'].emit()
        else:
            self._status = status

    status = property(get_status, set_status, None, "application status")


    def _show_app(self):
        """
        Show the application on the screen. This function should only be called
        from the application handler.
        """
        self._visible = True
        self.signals['show'].emit()
        self.__widget = gui_show(self.__name, self.gui_context)

    def _hide_app(self):
        """
        Hide the application. This function should only be called from
        the application handler.
        """
        self._visible = False
        self.signals['hide'].emit()
        self.__widget = None

    def gui_update(self):
        """
        Update the gui
        """
        if self.__widget:
            self.__widget.set_context(self.gui_context)

    def eventhandler(self, event):
        """
        Eventhandler for this application
        """
        error = 'Error, no eventhandler defined for %s' % self.application
        raise AttributeError(error)


    def stop(self):
        """
        Stop the application. If it is not shown again in the same cycle, the
        hide() function will be called. If the app isn't really stopped now
        (e.g. a child needs to be stopped), do not call this function.
        """
        self._status = STATUS_STOPPED


    def is_visible(self):
        """
        Return if the application is visible right now.
        """
        return self._visible


    def set_eventmap(self, eventmap):
        """
        Set a new eventmap for the event handler
        """
        self._eventmap = eventmap
        handler.set_focus()


    def get_eventmap(self):
        """
        Return the eventmap for the application.
        """
        return self._eventmap

    eventmap = property(get_eventmap, set_eventmap, None, "eventmap")

    def get_name(self):
        """
        Get the name of the application.
        """
        return self.__name


    def __repr__(self):
        """
        String for debugging.
        """
        return self.__name
