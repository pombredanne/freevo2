# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# listing_area.py - A listing area for the Freevo skin
# -----------------------------------------------------------------------------
# $Id$
#
# This module include the ListingArea used in the area code for drawing the
# listing areas for menus. It inherits from Area (area.py) and the update
# function will be called to update this area.
#
# TODO: o fix icon code which is deactivated right now
#
# -----------------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2002-2004 Krister Lagerstrom, Dirk Meyer, et al.
#
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

__all__ = [ 'ListingArea' ]

# python imports
import copy
import os
import weakref

# external modules
import notifier

# freevo imports
import config
import util
from util.objectcache import ObjectCache
import util.thumbnail

# gui import
from area import Area
from gui.widgets import Image

import logging
log = logging.getLogger('gui')


class _Redraw(object):
    """
    Class handling redrawings in the listing area when a thumbnail
    was created.
    """
    def __init__(self, function, gui_objects, screen, *args):
        self.function = function
        self.args = args
        self.gui_objects = gui_objects
        self.screen = screen
        
    def redraw(self, filename, thumb):
        if not self.gui_objects:
            # no gui objects, must be cleaned
            return
        elif not self.gui_objects[0].get_parent():
            # object is hidden, so we shouldn't update
            return
        # delete current objects
        while len(self.gui_objects):
            o = self.gui_objects.pop()
            o.unparent()
        # call redraw function
        self.function(*self.args)
        # update the screen
        self.screen.canvas.update()

        
class ListingArea(Area):
    """
    This class defines the ListingArea to draw menu listings for the area
    part of the gui code.
    """
    def __init__(self):
        """
        Create the Area and define some needed variables
        """
        Area.__init__(self, 'listing')
        self.last_listing      = []
        self.last_settings_type = ''
        self.last_selection    = None
        self.last_start        = -1
        self.last_max_len      = -1
        self.empty_listing     = None
        self.arrows            = []
        self.__default_val     = None


    def clear(self, keep_settings=False):
        """
        Clear the listing area. All objects are removed from the screen and
        the list of used objects is resetted.
        """
        # delete the listing
        for c in self.last_listing:
            for o in c[2]:
                o.unparent()
        self.last_listing = []
        # delete the arrows
        for a in self.arrows:
            a.unparent()
        self.arrows = []
        # reset variables
        if not keep_settings:
            self.last_settings_type = ''
            self.last_selection    = None
            self.last_start        = -1
            self.last_max_len      = -1
        # delete 'empty listing' message
        if self.empty_listing:
            self.empty_listing.unparent()
            self.empty_listing = None


    def __text_or_icon(self, string, x, width, font):
        """
        Helper function for the table-mode. This function will check if there
        is an image for this string and will return it.
        """
        l = string.split('_') # FIXME: l is not a good name in monofonts
        if len(l) != 4:
            return string
        try:
            height = font.height
            image = os.path.join(self.settings.icon_dir, l[2].lower())
            if os.path.isfile(image + '.jpg'):
                image += '.jpg'
            if os.path.isfile(image + '.png'):
                image += '.png'
            else:
                image = None
            if image:
                image = self.imagelib.load(image, (None, height))

                x_mod = 0
                if l[1] == 'CENTER':
                    x_mod = (width - image.width) / 2
                if l[1] == 'RIGHT':
                    x_mod = width - image.width
                return x_mod, image

        except KeyError:
            log.info('no image %s' % l[2])
            pass

        mod_x = width - font.stringsize(l[3])
        if mod_x < 0:
            mod_x = 0
        if l[1] == 'CENTER':
            return mod_x / 2, l[3]
        if l[1] == 'RIGHT':
            return mod_x, l[3]
        return 0, l[3]


    def __get_items_geometry(self, menu):
        """
        Get the geometry of the items. How many items per row/col, spaces
        between each item, etc
        """
        if hasattr(menu, '_skin_info_listing_area') and \
           menu._skin_info_listing_area[0] == self.settings:
            # return cache
            return menu._skin_info_listing_area[1]

        settings = self.settings

        if settings.type == 'text':
            items_w = settings.width
            items_h = 0
        elif settings.type == 'image' or settings.type == 'image+text':
            items_w = 0
            items_h = 0

        # get the list of possible types we need for this
        # menu to draw correctly
        possible_types = {}
        for i in menu.choices:
            if hasattr(i, 'display_type') and i.display_type:
                x = i.display_type
                if settings.types.has_key(x) and not possible_types.has_key(x):
                    possible_types[x] = settings.types[x]
                x = '%s selected' % i.display_type
                if settings.types.has_key(x) and not possible_types.has_key(x):
                    possible_types[x] = settings.types[x]
        if settings.types.has_key('default'):
            possible_types['default'] = settings.types['default']
        if settings.types.has_key('selected'):
            possible_types['selected'] = settings.types['selected']

        hskip = 0
        vskip = 0
        # get the max height of a text item
        if settings.type == 'text':
            for t in possible_types:
                ct = possible_types[t]

                rh = 0
                rw = 0
                if ct.rectangle:
                    rw, rh, r = ct.rectangle.calculate(settings.width,
                                                       ct.font.height)
                    hskip = min(hskip, r.x)
                    vskip = min(vskip, r.y)
                    items_w = max(items_w, r.width)

                items_h = max(items_h, ct.font.height, rh)

        elif settings.type == 'image' or settings.type == 'image+text':
            for t in possible_types:
                ct = possible_types[t]
                rh = 0
                rw = 0
                if ct.rectangle:
                    if settings.type == 'image+text':
                        mh = max(ct.height, int(ct.font.height * 1.1))
                    else:
                        mh = ct.height
                    rw, rh, r = ct.rectangle.calculate(ct.width, mh)
                    hskip = min(hskip, r.x)
                    vskip = min(vskip, r.y)

                addh = 0
                if settings.type == 'image+text':
                    addh = int(ct.font.height * 1.1)

                items_w = max(items_w, ct.width, rw)
                items_h = max(items_h, ct.height + addh, rh + addh)


        else:
            log.warning('unknown settings type %s' % settings.type)
            return None

        # shrink width for text menus
        width = settings.width

        if items_w > width:
            width, items_w = width - (items_w - width), width

        cols = 0
        rows = 0

        while (cols + 1) * (items_w + settings.spacing) - \
              settings.spacing <= settings.width:
            cols += 1

        while (rows + 1) * (items_h + settings.spacing) - \
              settings.spacing <= settings.height:
            rows += 1

        info = cols, rows, items_w + settings.spacing, items_h + \
               settings.spacing, -hskip, -vskip, width
        menu._skin_info_listing_area = self.settings, info
        return info


    def __draw_text_listing_item(self, choice, (x,y), settings, val, hspace,
                                 vspace, gui_objects, width, hskip, vskip):
        """
        Draw an item for the text menu. This function is called from update
        and is only used once to split the huge update function into smaller
        once.
        """
        icon_x = 0
        icon   = None
        align  = val.align or settings.align
        menu   = self.menu
        x_icon = 0

        icon_type = None
        if hasattr(val, 'icon'):
            icon_type = val.icon

        text = choice.name
        if not text:
            text = "unknown"

        if not choice.icon and not icon_type:
            if choice.type == 'playlist':
                text = 'PL: %s' % text

            if choice.type == 'dir' and choice.parent and \
               choice.parent.type != 'mediamenu':
                text = '[%s]' % text

        # FIXME: there is no self.loadimage anymore
        # if choice != menu.selected and hasattr( choice, 'outicon' ) and \
        #        choice.outicon:
        #     icon = self.loadimage(choice.outicon, (vspace-content.spacing,
        #                                             vspace-content.spacing))
        # elif choice.icon:
        #     icon = self.loadimage(choice.icon, (vspace-content.spacing,
        #                                          vspace-content.spacing))
        # if not icon and icon_type:
        #     icon = self.loadimage(settings.icon_dir + '/' + icon_type,
        #           (vspace-content.spacing, vspace-content.spacing))

        #
        # display an icon for the item
        #
        # x_icon = 0
        # if icon:
        #     mx = x
        #     icon_x = vspace
        #     x_icon = icon_x
        #     if align == 'right':
        #         # know how many pixels to offset (dammed negative and max+X
        #         # values in (x,y,width) from skin!)
        #         r1 = r2 = None
        #         if s_val.rectangle:
        #             r1 = self.calc_rectangle(s_val.rectangle,
        #                                          width, s_val.font.height)[2]
        #         if n_val.rectangle:
        #             r2 = self.calc_rectangle(n_val.rectangle,
        #                                          width, n_val.font.height)[2]
        #         min_rx = 0
        #         max_rw = width
        #         if r1:
        #             min_rx = min( min_rx, r1.x )
        #             max_rw = max( max_rw, r1.width )
        #         if r2:
        #             min_rx = min( min_rx, r2.x )
        #             max_rw = max( max_rw, r2.width )
        #
        #         mx = x + width + hskip + ( max_rw + min_rx - width ) - \
        #              icon_x
        #         x_icon = 0
        #     gui_objects.append(self.drawimage(icon, (mx, y)))

        #
        # draw the rectangle below the item
        #
        if val.rectangle:
            r = val.rectangle.calculate(width, val.font.height)[2]
            b = self.drawbox(x + hskip + r.x + x_icon - \
                             self.settings.box_under_icon * x_icon,
                             y + vskip + r.y,
                             r.width - icon_x + \
                             self.settings.box_under_icon * icon_x,
                             r.height, r)
            gui_objects.append(b)

        #
        # special handling for tv shows
        #
        if choice.type == 'video' and choice.tv_show and \
               (val.align=='left' or val.align=='') and \
               (settings.align=='left' or settings.align==''):
            sn = choice.show_name

            if self.last_tvs[0] == sn[0]:
                tvs_w = self.last_tvs[1]
            else:
                season  = 0
                episode = 0
                for c in menu.choices:
                    if c.type == 'video' and hasattr(c,'tv_show') and \
                       c.tv_show and c.show_name[0] == sn[0]:
                        # do not use val.font.stringsize because this will
                        # add shadow and outline values we add later for the
                        # normal text again. So just use
                        # val.font.font.stringsize
                        stringsize = val.font.font.stringsize
                        season  = max(season, stringsize(c.show_name[1]))
                        episode = max(episode, stringsize(c.show_name[2]))
                        if self.tvs_shortname and not c.image:
                            self.tvs_shortname = False
                    else:
                        self.all_tvs = False

                if self.all_tvs and not self.tvs_shortname and \
                       len(menu.choices) > 5:
                    self.tvs_shortname = True

                if sn[1]:
                    if self.all_tvs and self.tvs_shortname:
                        tvs_w = val.font.stringsize('x') + season + episode
                    else:
                        tvs_w = val.font.stringsize('%s x' % sn[0]) + \
                                season + episode
                else:
                    if self.all_tvs and self.tvs_shortname:
                        tvs_w = season + episode
                    else:
                        tvs_w = val.font.stringsize('%s ' % sn[0]) + \
                                season + episode
                self.last_tvs = (sn[0], tvs_w)

            s = self.drawstring(' - %s' % sn[3], val.font, settings,
                                x=x + hskip + icon_x + tvs_w,
                                y=y + vskip, width=width-icon_x-tvs_w,
                                height=-1, align_h='left', dim=False,
                                mode='hard')
            gui_objects.append(s)
            s = self.drawstring(sn[2], val.font, settings,
                                x=x + hskip + icon_x + tvs_w - 100,
                                y=y + vskip, width=100, height=-1,
                                align_h='right', dim=False, mode='hard')
            gui_objects.append(s)
            if sn[1]:
                if self.all_tvs and self.tvs_shortname:
                    text = '%sx' % sn[1]
                else:
                    text = '%s %sx' % (sn[0], sn[1])
            else:
                if self.all_tvs and self.tvs_shortname:
                    text = ''
                else:
                    text = sn[0]

        #
        # if the menu has an attr table, the menu is a table. Each
        # item _must_ have that many tabs as the table needs!!!
        #
        if hasattr(menu, 'table'):
            table_x = x + hskip + x_icon
            table_text = text.split('\t')
            for i in range(len(menu.table)):
                table_w = ((width-icon_x-len(table_text)*5)*\
                           menu.table[i]) / 100
                if i != len(menu.table) - 1:
                    table_w += 5
                x_mod = 0
                if table_text[i].find('ICON_') == 0:
                    toi = self.__text_or_icon(table_text[i], table_x,
                                              table_w, val.font)
                    x_mod, table_text[i] = toi
                    if not isinstance(table_text[i], (str, unicode)):
                        img = self.drawimage(table_text[i],
                                             (table_x + x_mod, y + vskip))
                        gui_objects.append(img)
                        table_text[i] = ''

                if table_text[i]:
                    s = self.drawstring(table_text[i], val.font, settings,
                                        x=table_x + x_mod, y=y + vskip,
                                        width=table_w, height=-1,
                                        align_h=val.align, mode='hard',
                                        dim=False)
                    gui_objects.append(s)
                table_x += table_w + 5

        else:
            #
            # draw the text
            #
            s = self.drawstring(text, val.font, settings, x=x + hskip + x_icon,
                                y=y + vskip, width=width-icon_x, height=-1,
                                align_h=val.align, mode='hard', dim=True)
            if s:
                gui_objects.append(s)


    def __draw_image_listing_item(self, choice, (x, y), settings, val, hspace,
                                  vspace, gui_objects, use_cache = True):
        """
        Draw an item for the image menu. This function is called from update
        and is only used once to split the huge update function into smaller
        once.
        """
        cb = _Redraw(self.__draw_image_listing_item, gui_objects, self.screen,
                     choice, (x, y), settings, val, hspace, vspace,
                     gui_objects, False)

        height = val.height
        if settings.type == 'image+text':
            height += int(1.1 * val.font.height)

        if val.align == 'center':
            x += (hspace - val.width) / 2
        else:
            x += hskip

        if val.valign == 'center':
            y += (vspace - height) / 2
        else:
            y += vskip

        if val.rectangle:
            if settings.type == 'image+text':
                max_h = max(height, int(val.font.height * 1.1))
                r = val.rectangle.calculate(val.width, max_h)[2]
            else:
                r = val.rectangle.calculate(val.width, height)[2]
            b = self.drawbox(x + r.x, y + r.y, r.width, r.height, r)
            gui_objects.append(b)

        image = self.imagelib.item_image(choice, (val.width, val.height),
                                         self.settings.icon_dir, force=True,
                                         bg=True, callback=cb.redraw)
        if image:
            i_w, i_h = image.width, image.height

            addx = 0
            addy = 0
            if val.align == 'center' and i_w < val.width:
                addx = (val.width - i_w) / 2

            if val.align == 'right' and i_w < val.width:
                addx = val.width - i_w

            if val.valign == 'center' and i_h < val.height:
                addy = (val.height - i_h) / 2

            if val.valign == 'bottom' and i_h < val.height:
                addy = val.height - i_h

            if val.shadow and val.shadow.visible and not image.has_alpha:
                i = Image(image, (x + addx, y + addy),
                          shadow=(val.shadow.x, val.shadow.y,
                                  val.shadow.color))
            else:
                i = Image(image, (x + addx, y + addy))
            self.layer.add_child(i)
            gui_objects.append(i)

        if settings.type == 'image+text':
            s = self.drawstring(choice.name, val.font, settings, x=x,
                                y=y + val.height, width=val.width, height=-1,
                                align_h=val.align, mode='hard',
                                ellipses='', dim=False)
            gui_objects.append(s)




    def __cache_next_image(self):
        """
        Cache the next images used in image view so they are in memory when
        the user scrolls down. This function gets called by the notifier
        and will only cache one image and than return. By that we make sure
        we won't use needed cpu time.
        """
        if not self.__cache_listing:
            return False

        image = self.__cache_listing[0].image
        
        if image and util.thumbnail.need_thumbnailing(image):
            # create thumbnail
            util.thumbnail.load(image)

        if len(self.__cache_listing) == 1:
            # Nothing more to cache, return False to stop this callback
            self.__cache_listing = []
            return False
        # Remove current item from the list and return True so that this
        # function gets called again.
        self.__cache_listing = self.__cache_listing[1:]
        return True



    def update(self):
        """
        Update the listing area. This function will be called from Area to
        do the real update.
        """
        menu     = self.menu
        settings = self.settings

        if not len(menu.choices):
            if not self.empty_listing:
                self.clear()
                t = _('This directory is empty')
                self.empty_listing = self.drawstring(t, settings.font,
                                                     settings)
            return

        # delete 'empty listing' message
        if self.empty_listing:
            self.empty_listing.unparent()
            self.empty_listing = None

        cols, rows, hspace, vspace, hskip, vskip, width = \
              self.__get_items_geometry(menu)

        menu.rows = rows
        menu.cols = cols

        if settings.align == 'center':
            x = settings.x + (settings.width - cols * hspace) / 2
        else:
            x = settings.x

        if settings.valign == 'center':
            y = settings.y + (settings.height - rows * vspace) / 2
        else:
            y = settings.y

        current_col = 1

        if settings.type == 'image':
            width  = hspace - settings.spacing
            height = vspace - settings.spacing

        self.last_tvs      = ('', 0)
        self.all_tvs       = True
        self.tvs_shortname = True

        start   = (menu.selected_pos / (cols * rows)) * (cols * rows)
        end     = start + cols * rows
        listing = menu.choices[start:end]
        self.__cache_listing = []
        if settings.type != 'text' and end < len(menu.choices):
            self.__cache_listing = menu.choices[end:end + cols * rows]
            notifier.addTimer(100, notifier.Callback(self.__cache_next_image))

        # do some checking if we have to redraw everything
        # or only update because the selection changed
        if self.last_settings_type != settings.type or \
           len(listing) != len(self.last_listing) or \
           self.last_start != start or self.last_max_len != len(menu.choices):
            self.last_settings_type = settings.type
            self.last_start        = start
            self.last_max_len      = len(menu.choices)
            redraw = True
        else:
            redraw = False

        if redraw:
            # delete all current gui objects
            self.clear(keep_settings=True)

        for index, choice in enumerate(listing):
            draw_this_item = True

            #
            # check if this items needs to be drawn or not
            #
            if redraw:
                gui_objects  = []
                listing_info = [ choice.name, None, gui_objects ]
                self.last_listing.append(listing_info)
            else:
                # check if the item is still the same
                if self.last_listing[index][:2] != [choice.name, choice.image]:
                    for o in self.last_listing[index][2]:
                        o.unparent()
                    gui_objects = []
                    listing_info = [ choice.name, None, gui_objects ]
                    self.last_listing[index] = listing_info
                elif choice == self.last_selection or choice == menu.selected:
                    listing_info = self.last_listing[index]
                    gui_objects  = listing_info[2]
                    while len(gui_objects):
                        o = gui_objects.pop()
                        o.unparent()
                else:
                    draw_this_item = False


            # init the 'val' settings
            if draw_this_item:
                if settings.types.has_key( '%s selected' % choice.type ):
                    s_val = settings.types[ '%s selected' % choice.type ]
                else:
                    s_val = settings.types[ 'selected' ]

                if settings.types.has_key( choice.type ):
                    n_val = settings.types[ choice.type ]
                else:
                    n_val = settings.types['default']

                if choice == menu.selected:
                    val = s_val
                else:
                    val = n_val
                    self.__default_val = val

                if settings.type == 'text':
                    # draw item for text listing
                    self.__draw_text_listing_item(choice, (x,y), settings, val,
                                                  hspace, vspace, gui_objects,
                                                  width, hskip, vskip)

                elif settings.type == 'image' or \
                         settings.type == 'image+text':
                    # draw item for image listing
                    self.__draw_image_listing_item(choice, (x,y), settings,
                                                   val, hspace, vspace,
                                                   gui_objects)

                listing_info[1] = choice.image

                if config.INPUT_MOUSE_SUPPORT:
                    for g in gui_objects:
                        g.action = weakref.ref(choice)
                    
            # calculate next item position
            if current_col == cols:
                # max number of cols reached, skip to next row
                if settings.align == 'center':
                    x = settings.x + (settings.width - cols * hspace) / 2
                else:
                    x = settings.x
                y += vspace
                current_col = 1
            else:
                # set x to fill the next item in the row
                x += hspace
                current_col += 1


        # remember last selection
        self.last_selection = menu.selected

        if redraw:
            # draw the arrows
            try:
                if start > 0 and settings.images['uparrow']:
                    i = settings.images['uparrow'].filename
                    i = self.drawimage(i, settings.images['uparrow'])
                    if config.INPUT_MOUSE_SUPPORT:
                        i.action = 'PAGE_UP'
                    self.arrows.append(i)
                if end < len(menu.choices):
                    if isinstance(settings.images['downarrow'].y, str):
                        v = copy.copy(settings.images['downarrow'])
                        v.y = eval(v.y, {'MAX':(y-vskip)})
                    else:
                        v = settings.images['downarrow']
                    i = settings.images['downarrow'].filename
                    i = self.drawimage(i, v)
                    if config.INPUT_MOUSE_SUPPORT:
                        i.action = 'PAGE_DOWN'
                    self.arrows.append(i)
            except Exception, e:
                log.error(e)
