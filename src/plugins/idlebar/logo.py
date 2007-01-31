# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# logo.py - IdleBarPlugin for showing a freevo logo
# -----------------------------------------------------------------------
# $Id:
#
# -----------------------------------------------------------------------
# $Log:
#
#
# -----------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2002-2005 Krister Lagerstrom, Dirk Meyer, et al.
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
# ----------------------------------------------------------------------- */

import os

from freevo.ui import config, gui
from freevo.ui.gui import theme, widgets
from freevo.ui.plugins.idlebar import IdleBarPlugin

class PluginInterface(IdleBarPlugin):
    """
    Display the freevo logo in the idlebar
    """
    def __init__(self, image=None):
        IdleBarPlugin.__init__(self)
        self.image  = image
        self.file   = file


    def draw(self, width, height):
        if not self.image:
            image = theme.image('logo')
        else:
            image = os.path.join(config.IMAGE_DIR, self.image)

        if self.objects and self.file == image:
            return self.NO_CHANGE

        self.file = image
        self.clear()

        i = widgets.Image((image, (None, height + 10)), (0, 0))
        self.objects.append(i)

        return i.width
