# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# fthread.py - Freevo threading module
# -----------------------------------------------------------------------------
# $Id$
#
# This module contains some wrapper classes for threading in Freevo. It should
# only be used when non blocking handling is not possible. Freevo itself is not
# thread save, the the function called in the thread should not touch any
# variables inside Freevo. Since the main loop needs to be kept alive and some
# Python functions may block too long, the function call can we wrapped in a
# Freevo thread. Only add the blocking function to the thread and remeber that
# the Freevo main loop is alive during the call (e.g. timer can expire).
#
# In most cases this module is not needed, please add a good reason why you
# wrap a function in a thread.
#
# -----------------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2002-2004 Krister Lagerstrom, Dirk Meyer, et al.
#
# First Version: Dirk Meyer <dmeyer@tzi.de>
# Maintainer:    Dirk Meyer <dmeyer@tzi.de>
#
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

__all__ = [ 'call' ]

import threading
import notifier

class _FThread(threading.Thread):
    """
    Thread to handle the function with *args, **kargs.
    """
    def __init__(self, function, *args, **kargs):
        threading.Thread.__init__(self)
        self.function = function
        self.args     = args
        self.kargs    = kargs
        self.result   = None
        self.finished = False

    def run(self):
        """
        Call the function and store the result
        """
        self.result = self.function(*self.args, **self.kargs)
        self.finished = True


def call(function, *args, **kargs):
    """
    Run function(*args, **kargs) in a thread and return the result. Keep
    the main loop alive during that time.
    """
    thread = _FThread(function, *args, **kargs)
    thread.start()
    while not thread.finished:
        # Calling notifier.step with the first argument True could block Freevo
        # forever. But we know that there are many timers running so this will
        # return.
        # FIXME: maybe add a max timer to pyNotifier to be sure that the step
        # function will return at some point.
        notifier.step(True, False)
    thread.join()
    return thread.result
