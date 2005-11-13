# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# generic - Generic 'get' function for mediadb object
# -----------------------------------------------------------------------------
# $Id$
#
# TODO: o add InfoItem for / and network url
#
# -----------------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2002-2005 Krister Lagerstrom, Dirk Meyer, et al.
#
# First Edition: Dirk Meyer <dischi@freevo.org>
# Maintainer:    Dirk Meyer <dischi@freevo.org>
#
# Please see the file doc/CREDITS for a complete list of authors.
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

__all__ = [' get' ]

# python imports
import os
import logging

# kaa.metadata
from kaa.metadata.disc.discinfo import cdrom_disc_id

# freevo imports
import sysconfig
import util.vfs as vfs

# mediadb imports
from db import FileCache
from item import ItemInfo
from listing import FileListing

# get logging object
log = logging.getLogger('mediadb')


class DiscInfo(ItemInfo):
    """
    Item for a disc.
    """
    def __init__(self, disc_ok, media, cache=None):
        if cache:
            ItemInfo.__init__(self, '', '', cache.data, cache)
        else:
            ItemInfo('', '', None)
        self.disc_ok = disc_ok
        self.media = media
        self.filename = ''
        
    def __str__(self):
        return 'mediadb.DiscInfo() object for %s' % self.media.mountdir

            
def disc_info(media):
    """
    Return information for the media
    """
    type, id  = cdrom_disc_id(media.devicename)
    if not id:
        # bad disc, e.g. blank disc
        return DiscInfo(False, media)
    cachefile = os.path.join(vfs.BASE, 'disc/metadata/%s.db' % id)
    cache = FileCache(media.devicename, cachefile)
    info = DiscInfo(True, media, cache)

    try:
        info.url = info['mime'][6:] + '://'
        if info['mime'] in ('video/vcd', 'video/dvd'):
            return info
    except:
        log.error('Please report this: mime=%s' % info['mime'])
        info.url = ''
    # Disc is data of some sort. Mount it to get the file info
    media.mount()
    if os.path.isdir(os.path.join(media.mountdir, 'VIDEO_TS')) or \
           os.path.isdir(os.path.join(media.mountdir, 'video_ts')):
        # looks like a DVD but is not detected as one, check again
        log.info('Undetected DVD, checking again')
        cache = FileCache(media.devicename, cachefile)
        info = DiscInfo(True, media, cache)
        info.filename = info['mime'][6:] + '://'
        if info['mime'] in ('video/vcd', 'video/dvd'):
            media.umount()
            return info
    # save directory listing in item
    info['listing'] = os.listdir(media.mountdir)
    media.umount()
    # set correct dirname / filename
    info.dirname = media.mountdir
    info.filename = info.dirname + '/' + info.basename
    info.url = 'file://' + info.filename
    return info


def get(filename):
    """
    Get information about filename. Filename can be a real filename, an url
    or a media object for disc detection.
    """
    if hasattr(filename, 'mountdir'):
        # filename is a media object
        return disc_info(filename)
    if filename.startswith('file://'):
        filename = filename[7:]
    elif filename.find('://')> 0:
        # FIXME: some url we don't handle yet like cdda:// from AudioDiscItem
        return ItemInfo('', '', None)
    if filename != '/':
        # get normal info using directory listing
        listing = FileListing( [ filename ] )
        if listing.num_changes:
            listing.update()
        return listing.get_by_name(os.path.basename(filename))
    # filename is either '/' or an url
    # FIXME: create cache for these types
    return ItemInfo('', '', None)
