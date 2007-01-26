# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# __init__.py - Image interface
# -----------------------------------------------------------------------------
# $Id$
#
# This file imports everything needed to use this image module.  There
# is only one class provided for images, the PluginInterface from
# interface.py. It is a MimetypePlugin that can be accessed from
# plugin.mimetype(). It will also register an fxd handler for the
# <slideshow> tag.
#
# Image plugins are also allowed to use ImageItem to create a new
# ImageItem and viewer, the viewer application
#
#
# -----------------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2002 Krister Lagerstrom, 2003-2006 Dirk Meyer, et al.
#
# First edition: Dirk Meyer <dischi@freevo.org>
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

# image imports
from interface import *

# used by image plugins
from imageitem import ImageItem
from viewer import viewer
