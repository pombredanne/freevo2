# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# videolibrary.py - jsonrpc interface for XBMC-compatible remotes
# -----------------------------------------------------------------------
# $Id$
#
# JSONRPC and XBMC eventserver to be used for XBMC-compatible
# remotes. Only tested with Yatse so far. If something is not working,
# do not blame the remote, blame this plugin.
#
# Not all API calls are implemented yet.
#
# -----------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2014 Dirk Meyer, et al.
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
# ----------------------------------------------------------------------- */

# python imports
import logging

# kaa imports
import kaa
import kaa.beacon
import kaa.webmetadata
import kaa.metadata

# jsonrpc imports
import utils

# get logging object
log = logging.getLogger('freevo')
tvdb = kaa.webmetadata.tv.backends['thetvdb']

def _fill_episode_details(f, properties):
    """
    Helper function to provide episode details
    """
    info = {
        'episodeid': f._beacon_id[1],
        'label': '%s %sx%02d - %s' % (f.get('series'), f.get('season'), f.get('episode'), f.get('title'))
    }
    for prop in properties:
        if prop == 'season':
            info[prop] = f.get('season')
        elif prop == 'episode':
            info[prop] = f.get('episode')
        elif prop == 'showtitle':
            info[prop] = f.get('series')
        elif prop == 'title':
            info[prop] = f.get('title')
        elif prop == 'thumbnail':
            info[prop] = utils.register_image(f.thumbnail, f)
        elif prop in ('rating',):
            info[prop] = 0.0
        elif prop == 'file':
            info[prop] = f.url
        elif prop == 'plot':
            info[prop] = f.get('description')
        elif prop == 'playcount':
            info[prop] = 0
        elif prop == 'resume':
            info[prop] = False
        elif prop in ('firstaired', 'dateadded', 'originaltitle'):
            info[prop] = ''
        elif prop in ('cast', ):
            info[prop] = []
        elif prop == 'streamdetails':
            # Filled correctly later for on episode details
            info[prop] = {
                'audio': [],
                'subtitle': [],
                'video': [] }
        else:
            log.error('no support for %s' % prop)
            info[prop] = ''
    return info


@kaa.coroutine()
def GetTVShows(properties, limits):
    """
    JsonRPC Callback VideoLibrary.GetTVShows
    """
    tvshows = []
    for name in sorted((yield kaa.beacon.query(attr='series', type='video'))):
        series = kaa.webmetadata.tv.series(name)
        if not series:
            continue
        info = {}
        for prop in properties:
            if prop == 'art':
                info[prop] = {}
                if series.banner:
                    info[prop]['banner'] = utils.register_image(series.banner)
                if series.image:
                    info[prop]['fanart'] = utils.register_image(series.image)
                if series.poster:
                    info[prop]['poster'] = utils.register_image(series.poster)
            elif prop in ('watchedepisodes', 'playcount'):
                info[prop] = 0
            elif prop in ('season',):
                info[prop] = -1
            elif prop in ('year',):
                info[prop] = series.year
            elif prop in ('rating',):
                info[prop] = 0.0
            elif prop == 'plot':
                info[prop] = series.overview
            elif prop in ('genre', 'studio'):
                info[prop] = []
            elif prop in ('title', 'originaltitle', 'sorttitle'):
                info[prop] = name
            elif prop in ('mpaa', 'lastplayed', 'dateadded'):
                info[prop] = ''
            elif prop in ('episode'):
                info[prop] = len((yield kaa.beacon.query(series=series.name, type='video')))
            else:
                log.error('no support for %s' % prop)
                info[prop] = ''
        info['tvshowid'] = series.id
        tvshows.append(info)
    start = limits['start']
    end = min(limits['end'], len(tvshows))
    yield {
        'limits': {'start': start, 'end': end, 'total': len(tvshows)},
        'tvshows': tvshows[start:end+1] }
    yield None

@kaa.coroutine()
def GetSeasons(tvshowid, properties):
    """
    JsonRPC Callback VideoLibrary.GetSeasons
    """
    seasons = []
    result = {'seasons': [] }
    for series in tvdb.series:
        if series.id == tvshowid:
            for season in sorted((yield kaa.beacon.query(attr='season', series=series.name, type='video'))):
                season = series.seasons[season-1]
                info = { 'label': 'Season %s' % season.number, 'tvshowid': tvshowid, 'seasonid': season.number }
                for prop in properties:
                    if prop == 'season':
                        info[prop] = season.number
                    elif prop == 'tvshowid':
                        info[prop] = tvshowid
                    elif prop == 'showtitle':
                        info[prop] = season.series.name
                    elif prop in ('watchedepisodes', 'playcount'):
                        info[prop] = 0
                    elif prop == 'thumbnail':
                        if season.poster:
                            info[prop] = utils.register_image(season.poster)
                    elif prop in ('episode'):
                        info[prop] = len((yield kaa.beacon.query(series=season.series.name, season=season.number, type='video')))
                    else:
                        log.error('no support for %s' % prop)
                        info[prop] = ''
                result['seasons'].append(info)
    result['limits'] = {'start': 0, 'end': len(result['seasons']), 'total': len(result['seasons'])}
    yield result

@kaa.coroutine()
def GetEpisodes(properties, limits, tvshowid=-1, season=-1):
    """
    JsonRPC Callback VideoLibrary.GetEpisodes
    """
    episodes = []
    for name in sorted((yield kaa.beacon.query(attr='series', type='video'))):
        for f in (yield kaa.beacon.query(series=name, type='video')):
            episodes.append(_fill_episode_details(f, properties))
    start = limits['start']
    end = min(limits['end'], len(episodes))
    yield {
        'limits': {'start': start, 'end': end, 'total': len(episodes)},
        'episodes': episodes[start:end+1] }

@kaa.coroutine()
def GetEpisodeDetails(episodeid, properties):
    """
    JsonRPC Callback VideoLibrary.GetEpisodeDetails
    """
    result = (yield kaa.beacon.query(id=episodeid, type='video'))
    if len(result) != 1:
        log.error('bad query')
        yield {}
    details = _fill_episode_details(result[0], properties)
    if 'streamdetails' in properties:
        metadata = kaa.metadata.parse(result[0].url)
        value = {
            'audio': [],
            'subtitle': [],
            'video': [] }
        if metadata:
            for v in metadata.video:
                value['video'].append(utils.fill_video_details(v, metadata))
            for a in metadata.audio:
                value['audio'].append(utils.fill_audio_details(a))
            for s in metadata.subtitles:
                value['subtitle'].append(utils.fill_subtitle_details(s))
        details['streamdetails'] = value
    yield {'episodedetails': details}



###################################################################################################
# Movie
###################################################################################################


def _fill_movie_details(f, properties):
    """
    Helper function to provide episode details
    """
    info = {
        'movieid': f._beacon_id[1],
        'label': f.get('title')
    }
    # it kind of sucks, but we have to ask kaa.(web)metadata again for
    # each movie to get the details.
    metadata = kaa.metadata.parse(f.url[7:])
    webmetadata = kaa.webmetadata.parse(f.url[7:], metadata)
    for prop in properties:
        if prop == 'title':
            info[prop] = f.get('title')
        elif prop == 'thumbnail':
            info[prop] = utils.register_image(f.get('poster'), f)
        elif prop in ('rating',):
            info[prop] = 0.0
        elif prop == 'file':
            info[prop] = f.url
        elif prop == 'plot':
            info[prop] = f.get('description')
        elif prop in ('playcount', 'setid'):
            info[prop] = 0
        elif prop == 'resume':
            info[prop] =  { 'position': 0, 'total': 0 }
        elif prop == 'set':
            info[prop] = ''
        elif prop == 'fanart':
            info[prop] = utils.register_image((webmetadata and webmetadata.image) or '')
        elif prop == 'imdbnumber':
            info[prop] = (webmetadata and webmetadata.imdb) or ''
        elif prop == 'genre':
            info[prop] = (webmetadata and webmetadata.genre) or []
        elif prop == 'year':
            info[prop] = (webmetadata and webmetadata.year) or 0
        elif prop == 'runtime':
            info[prop] = f.get('length')
        elif prop in ('firstaired', 'dateadded', 'originaltitle', 'sorttitle', 'trailer'):
            info[prop] = ''
        elif prop in ('cast', 'mpaa', 'studio', 'director', 'tag'):
            info[prop] = []
        elif prop == 'streamdetails':
            info[prop] = {
                'audio': [],
                'subtitle': [],
                'video': [] }
            if metadata:
                for v in metadata.video:
                    info[prop]['video'].append(utils.fill_video_details(v, metadata))
                for a in metadata.audio:
                    info[prop]['audio'].append(utils.fill_audio_details(a))
                for s in metadata.subtitles:
                    info[prop]['subtitle'].append(utils.fill_subtitle_details(s))
        else:
            log.error('no support for %s' % prop)
            info[prop] = ''
    return info

def GetMovieSets(properties, limits):
    """
    JsonRPC Callback VideoLibrary.GetMovieSets
    """
    moviesets = []
    start = limits['start']
    end = min(limits['end'], len(moviesets))
    return {
        'limits': {'start': start, 'end': end, 'total': len(moviesets)},
        'moviesets': moviesets[start:end+1] }

@kaa.coroutine()
def GetMovies(properties, limits):
    """
    JsonRPC Callback VideoLibrary.GetMovies
    """
    movies = []
    # only provide the once kaa.webmetadata detected as movie
    for info in (yield kaa.beacon.query(type='video', movie=True)):
        movies.append(_fill_movie_details(info, properties))
    movies.sort(lambda x,y: cmp(x['movieid'], y['movieid']))
    start = limits['start']
    end = min(limits['end'], len(movies))
    yield {
        'limits': {'start': start, 'end': end, 'total': len(movies)},
        'movies': movies[start:end+1] }

@kaa.coroutine()
def GetMovieDetails(movieid, properties):
    """
    JsonRPC Callback VideoLibrary.GetMovieDetails
    """
    info = (yield kaa.beacon.query(type='video', id=movieid))
    yield {'moviedetails': _fill_movie_details(info[0], properties) }
