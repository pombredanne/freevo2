# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# base.py - The basic animation class for freevo
# Author: Viggo Fredriksen <viggo@katatonic.org>
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
# Todo:        
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.9  2004/10/12 11:31:58  dischi
# make animation frame selection timer based
#
# Revision 1.8  2004/08/27 14:15:25  dischi
# split animations into different files
#
# Revision 1.7  2004/08/23 20:35:33  dischi
# o support for displays too slow to do the animation.
# o add wait function to wait until an animation is finshed, or
#   until application fadinf animations are done
#
# Revision 1.6  2004/08/23 15:10:34  dischi
# remove callback and add wait function
#
# Revision 1.5  2004/08/23 14:28:23  dischi
# fix animation support when changing displays
#
# Revision 1.4  2004/08/23 12:37:13  dischi
# remove osd import
#
# Revision 1.3  2004/08/22 20:06:17  dischi
# Switch to mevas as backend for all drawing operations. The mevas
# package can be found in lib/mevas. This is the first version using
# mevas, there are some problems left, some popup boxes and the tv
# listing isn't working yet.
#
# Revision 1.2  2004/07/27 18:52:30  dischi
# support more layer (see README.txt in backends for details
#
# Revision 1.1  2004/07/22 21:11:40  dischi
# move the animation into gui, code needs update later
#
# Revision 1.3  2004/07/10 12:33:36  dischi
# header cleanup
#
# Revision 1.2  2004/05/13 12:33:42  dischi
# animation damage patch from Viggo Fredriksen
#
# Revision 1.1  2004/04/25 11:23:58  dischi
# Added support for animations. Most of the code is from Viggo Fredriksen
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

import render

class BaseAnimation:
    """
    Base class for animations, this should perhaps be changed to use sprites
    in the future (if one decides to go with a RenderGroup model)

     @rectstyle  : the rectangle defining the position on the screen
     @fps        : Desired fps
     @bg_update  : update the animation with background from screen
     @bg_wait    : initially wait for updated background before activating
     @bg_redraw  : set background to original screen bg when finished
    """

    def __init__(self, fps):
        self.set_fps(fps)
        self.active       = False  # Should it be updated in the poll
        self.delete       = False  # Delete from list on next poll
        self.next_update  = 0      # timestamp for next update
        self.application  = False  # True when it's for app show/hide
        self.__start_time = 0

    def set_fps(self, fps):
        """
        Sets the desired fps
        """
        self.interval  = 1.0/float(fps)


    def start(self):
        """
        Starts the animation
        """
        render.get_singleton().add_animation(self)
        self.active = True
        

    def stop(self):
        """
        Stops the animation from being polled
        """
        self.active = False


    def running(self):
        """
        Return status if the animation is still running
        """
        return self.active

    
    def remove(self):
        """
        Flags the animation to be removed from the animation list
        """
        self.active = False
        self.delete = True


    def poll(self, current_time):
        if not self.__start_time:
            self.__start_time = current_time
        if self.next_update < current_time:
            frame = int((current_time - self.__start_time) / self.interval) + 1
            self.next_update = current_time + self.interval
            self.update(frame)
            return True
        return False

    
    def update(self, frame):
        """
        Overload to do stuff with the surface
        """
        pass


    def finish(self):
        """
        Finish the animation and stops it. Overload to do stuff
        on the surface and call the parent function.
        """
        self.remove()


    def wait(self):
        """
        Wait for this animation to finish
        """
        render.get_singleton().wait([self])
