# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# db_sqlite.py - interface to sqlite
# -----------------------------------------------------------------------------
# $Id$
#
# -----------------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2002-2004 Krister Lagerstrom, Dirk Meyer, et al.
#
# First Edition: Dirk Meyer <dmeyer@tzi.de>
#                Rob Shortt <rob@infointeractive.com>
# Maintainer:    Dirk Meyer <dmeyer@tzi.de>
#                Rob Shortt <rob@infointeractive.com>
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

# python imports
import os
import logging

# notifier
import notifier

# sqlite
import sqlite
from sqlite import IntegrityError, OperationalError

# get logging object
log = logging.getLogger('pyepg')

latest_version = "0.1.1"

class Database:
    """
    Database class for sqlite usage
    """
    def __init__(self, dbpath):
        if not os.path.isfile(dbpath):
            log.warning('EPG database missing, creating it')
            scheme = os.path.join(os.path.dirname(__file__), 'epg_schema.sql')
            os.system('sqlite %s < %s 2>/dev/null >/dev/null' % \
                      (dbpath, scheme))
        while 1:
            try:
                self.db = sqlite.connect(dbpath, client_encoding='utf-8',
                                         timeout=10)
                break
            except OperationalError, e:
                notifier.step(False, False)
        self.cursor = self.db.cursor()
        ver = self.get_version()
        log.info('EPG database version %s' % ver)
        if ver != latest_version:
            log.warning('EPG database out of date, latest version is %s' % \
                        latest_version)
            self.upgrade_db(ver)


    def upgrade_db(self, ver):
        # TODO: finish this or change it 
        # Here's a quick hack for the current upgrade:

        if ver == "0.0.0" and latest_version == "0.1.1":
            log.info('Upgrading EPG database from %s to %s.' % \
                     (ver, latest_version))
            self.execute('drop table admin')
            self.execute('create table versioning (thing text primary key, version text)')
            self.execute('insert into versioning (thing, version) values ("sql", "0.1.1")')
            self.execute('create index programs_title on programs (title)')
            self.commit()
            return


    def commit(self):
        self.db.commit()

    def close(self):
        self.db.close()

    def execute(self, query):
        while 1:
            try:
                self.cursor.execute(query)
                return self.cursor.fetchall()
            except OperationalError, e:
                notifier.step(False, False)


    def get_version(self):
        if self.check_table('versioning'):
            return self.execute('select version from versioning where thing="sql"')[0][0]
        else:
            return "0.0.0"


    def check_table(self, table=None):
        if not table:
            return False
        # verify the table exists
        if not self.execute('select name from sqlite_master where ' + \
                            'name="%s" and type="table"' % table):
            return None
        return table


