#!/usr/bin/env python
#-----------------------------------------------------------------------
# PopupBox - A dialog box for freevo.
#-----------------------------------------------------------------------
# $Id$
#
# Todo: o Add sanitychecking on all arguments.
#       o Add actual support for icons, not just brag about it.
#       o Start using the OSD imagecache for rectangles.
#
#-----------------------------------------------------------------------
# $Log$
# Revision 1.7  2003/03/09 21:37:06  rshortt
# Improved drawing.  draw() should now be called instead of _draw(). draw()
# will check to see if the object is visible as well as replace its bg_surface
# befire drawing if it is available which will make transparencies redraw
# correctly instead of having the colour darken on every draw.
#
# Revision 1.6  2003/03/05 03:53:34  rshortt
# More work hooking skin properties into the GUI objects, and also making
# better use of OOP.
#
# ListBox and others are working again, although I have a nasty bug regarding
# alpha transparencies and the new skin.
#
# Revision 1.5  2003/03/02 20:15:41  rshortt
# GUIObject and PopupBox now get skin settings from the new skin.  I put
# a test for config.NEW_SKIN in GUIObject because this object is used by
# MenuWidget, so I'll remove this case when the new skin is finished.
#
# PopupBox can not be used by the old skin so anywhere it is used should
# be inside a config.NEW_SKIN check.
#
# PopupBox -> GUIObject now has better OOP behaviour and I will be doing the
# same with the other objects as I make them skinnable.
#
# Revision 1.4  2003/02/23 18:21:50  rshortt
# Some code cleanup, better OOP, influenced by creating a subclass of RegionScroller called ListBox.
#
# Revision 1.3  2003/02/19 02:02:55  rshortt
# Fixed some bugs in the eventhandler.
#
# Revision 1.2  2003/02/18 13:40:53  rshortt
# Reviving the src/gui code, allso adding some new GUI objects.  Event
# handling will not work untill I make some minor modifications to main.py,
# osd.py, and menu.py.
#
# Revision 1.1  2002/12/07 15:21:31  dischi
# moved subdir gui into src
#
# Revision 1.3  2002/09/21 10:06:47  dischi
# Make it work again, the last change was when we used osd_sdl.py
#
# Revision 1.2  2002/08/18 21:57:00  tfmalt
# o Added margin handling.
# o Added support for Icons in popupboxes.
# o Addes support for vertical and horizontal alignment.
# o Added a ton more errorhandling.
# o Let Labels draw themselves independently.
#
# Revision 1.1  2002/08/15 22:45:42  tfmalt
# o Inital commit of Freevo GUI library. Files are put in directory 'gui'
#   under Freevo.
# o At the moment the following classes are implemented (but still under
#   development):
#     Border, Color, Label, GUIObject, PopupBox, ZIndexRenderer.
# o These classes are fully workable, any testing and feedback will be
#   appreciated.
#
#-----------------------------------------------------------------------
#
# Freevo - A Home Theater PC framework
#
# Copyright (C) 2002 Krister Lagerstrom, et al.
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
# ----------------------------------------------------------------------
"""
A Dialog box type class for Freevo.
""" 
__date__    = "$Date$"
__version__ = "$Revision$" 
__author__  = """Thomas Malt <thomas@malt.no>"""

import config

from GUIObject import *
from Color     import *
from Border    import *
from Label     import *
from types     import *

DEBUG = 0


class PopupBox(GUIObject):
    """
    left      x coordinate. Integer
    top       y coordinate. Integer
    width     Integer
    height    Integer
    text      String to print.
    bg_color  Background color (Color)
    fg_color  Foreground color (Color)
    icon      icon
    border    Border
    bd_color  Border color (Color)
    bd_width  Border width Integer
    
    Trying to make a standard popup/dialog box for various usages.
    """
    
    def __init__(self, text=" ", left=None, top=None, width=None, height=None,
                 bg_color=None, fg_color=None, icon=None, border=None, 
                 bd_color=None, bd_width=None):

        GUIObject.__init__(self, left, top, width, height, bg_color, fg_color)


        self.border   = border
        self.bd_color = bd_color
        self.bd_width = bd_width

        # In the future we will support duration where the popup
        # will destroy() after x seconds.
        self.duration = 0

        # XXX: skin settings
        ((bg_type, skin_bg), BLAH, BLAH, skin_font, BLAH, BLAH) = \
         self.skin.GetPopupBoxStyle()


        if not self.width:    self.width  = 360
        if not self.height:   self.height = 60

        if not self.left:     self.left   = self.osd.width/2 - self.width/2
        if not self.top:      self.top    = self.osd.height/2 - self.height/2


        if not self.bd_color: 
            if skin_bg.color:
                self.bd_color = Color(skin_bg.color)
            else:
                self.bd_color = Color(self.osd.default_fg_color)

        if not self.bd_width: 
            if skin_bg.size:
                self.bd_width = skin_bg.size
            else:
                self.bd_width = 2

        if not self.border:   
            self.border = Border(self, Border.BORDER_FLAT,
                                 self.bd_color, self.bd_width)

        
        if type(text) is StringType:
            if text: self.set_text(text)
        elif not text:
            self.text = None
        else:
            raise TypeError, text

        if skin_font:       
            self.set_font(skin_font.name, 
                          skin_font.size, 
                          Color(skin_font.color))
        else:
            self.set_font(config.OSD_DEFAULT_FONTNAME,
                          config.OSD_DEFAULT_FONTSIZE)
                
        self.label.set_h_align(Align.CENTER)
        self.label.set_v_align(Align.TOP)
 

        if icon:
            self.set_icon(icon)
                

    def get_text(self):
        """
        Get the text to display

        Arguments: None
          Returns: text
        """
        return self.text


    def set_text(self, text):
        """
        text  Text to display.
        
        Set text to display. If a Label is not not instanced a Label object
        is created.

        """
        if DEBUG: print "Text: ", text
        # XXX Hm.. I should try to do more intelligent parsing and quessing
        # XXX here.
        if type(text) is StringType:
            self.text = text
        else:
            raise TypeError, type(text)

        if not self.label:
            self.label = Label(text)
            self.label.set_parent(self)
            # XXX Set the background color to none so it is transparent.
            self.label.set_background_color(None)
            self.label.set_h_margin(self.h_margin)
            self.label.set_v_margin(self.v_margin)
        else:
            self.label.set_text(text)

        self.label.set_h_align(Align.CENTER)


    def get_font(self):
        """
        Does not return OSD.Font object, but the filename and size as list.
        """
        return (self.label.font.filename, self.label.font.ptsize)


    def set_font(self, file, size, color):
        """
        Set the font.

        Just hands the info down to the label. Might raise an exception.
        """
        if self.label:
            self.label.set_font(file, size, color)
        else:
            raise TypeError, file


    def get_icon(self):
        """
        Returns the icon of the popupbox (if set).
        """
        return self.icon


    def set_icon(self, image):
        """
        Set the icon of the popupbox.
        Also scales the icon to fit the size of the box.
        
        Can either be a string with filename or a pygame Surface object.
        """
        if type(image) is StringType:
            self.icon = pygame.image.load(image).convert_alpha()
        else:
            self.icon = image

        bx,by = self.get_size()
        ix,iy = self.icon.get_size()
        
        aspect = (ix/iy)

        if(bx > by):
            iy = by-(self.v_margin*2)
            ix = iy*aspect
        else:
            ix = bx-(self.h_margin*2)
            iy = ix/aspect
        
        self.icon = pygame.transform.scale(self.icon, (ix, iy))


    def set_border(self, bs):
        """
        bs  Border style to create.
        
        Set which style to draw border around object in. If bs is 'None'
        no border is drawn.
        
        Default for PopubBox is to have no border.
        """
        if isinstance(self.border, Border):
            self.border.set_style(bs)
        elif not bs:
            self.border = None
        else:
            self.border = Border(self, bs)
            

    def set_position(self, left, top):
        """
        Overrides the original in GUIBorder to update the border as well.
        """
        GUIObject.set_position(self, left, top)
        if isinstance(self.border, Border):
            if DEBUG: print "updating borders set_postion as well"
            self.border.set_position(left, top)
        

    def _draw(self):
        """
        The actual internal draw function.

        """
        if not self.width or not self.height or not self.text:
            raise TypeError, 'Not all needed variables set.'

        c   = self.bg_color.get_color_sdl()
        a   = self.bg_color.get_alpha()

        box = pygame.Surface(self.get_size(), 0, 32)

        box.fill(c)
        box.set_alpha(a)

        self.osd.screen.blit(box, self.get_position())
        
        if self.icon:
            ix,iy = self.get_position()
            self.osd.screen.blit(self.icon, (ix+self.h_margin,iy+self.v_margin)) 

        if self.label:  self.label.draw()
        if self.border: self.border.draw()

        if self.children:
            for child in self.children:
                child.draw()

    
    def _erase(self):
        """
        Erasing us from the canvas without deleting the object.
        """

        if DEBUG: print "  Inside PopupBox._erase..."
        # Only update the part of screen we're at.
        self.osd.screen.blit(self.bg_surface, self.get_position(),
                        self.get_rect())
        
        if self.border:
            if DEBUG: print "    Has border, doing border erase."
            self.border._erase()

        if DEBUG: print "    ...", self


    def eventhandler(self, event):
        if DEBUG: print 'PopupBox: event = %s' % event

        trapped = [self.rc.UP, self.rc.DOWN, self.rc.LEFT, self.rc.RIGHT,
                   self.rc.ENTER, self.rc.SELECT]

        if trapped.count(event) > 0:
            return
        elif [self.rc.EXIT, ].count(event) > 0:
            self.destroy()
        else:
            return self.parent.eventhandler(event)

