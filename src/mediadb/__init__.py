# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# mediadb
# -----------------------------------------------------------------------------
# $Id$
#
# TODO: o add SQLListing
#       o maybe preload whole cache? Expire cache?
#       o add InfoItem for / and network url
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

__all__ = [ 'Cache', 'FileCache', 'save', 'ItemInfo', 'Listing', 'FileListing',
            'cache', 'get' ]

from db import Cache, FileCache, save
from item import ItemInfo
from listing import Listing, FileListing
from parser import cache, init
from generic import get
from watcher import Watcher as _Watcher
from globals import *

watcher = _Watcher()

# init parsing module
init()

def item():
    return ItemInfo('', '', {})

# make sure we save the db on exit
import kaa.notifier
kaa.notifier.signals['shutdown'].connect(save)
