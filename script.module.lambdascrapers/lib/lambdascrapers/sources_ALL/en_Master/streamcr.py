# -*- coding: UTF-8 -*-
'''
    StreamCR scraper for Exodus forks.
    Oct 3 2018

    Created by someone.
'''
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
try:
    from urllib import quote_plus
    from urlparse import urlparse
except ImportError:
    from urllib.parse import quote_plus, urlparse

import xbmc

from resources.lib.modules.client import randomagent
from resources.lib.modules.cleantitle import getsearch
from resources.lib.modules.source_utils import label_to_quality


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['scr.cr']

        self.BASE_URL = 'https://scr.cr'
        self.SEARCH_URL = '/search.php?query=%s'
        self.AJAX_URL = 'https://ajax2.scr.cr/get-source.php?eid=%s'


    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            lowerTitle = title.lower()
            possibleTitles = set(
                (lowerTitle, getsearch(lowerTitle))
                + tuple((alias['title'].lower() for alias in aliases) if aliases else ())
            )
            return self._getSearchData(lowerTitle, possibleTitles, self._createSession(), season=None, episode=None)
        except:
            self._logException()
            return None


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            return tvshowtitle.lower(), aliases
        except:
            self._logException()
            return None


    def episode(self, data, imdb, tvdb, title, premiered, season, episode):
        try:
            lowerTitle, aliases = data
            possibleTitles = set(
                (lowerTitle, getsearch(lowerTitle))
                + tuple((alias['title'].lower() for alias in aliases) if aliases else ())
            )
            return self._getSearchData(lowerTitle, possibleTitles, self._createSession(), int(season), int(episode))
        except:
            self._logException()
            return None


    def sources(self, data, hostDict, hostprDict):
        try:
            session = self._createSession(data['headers'])
            pageURL = data['pageURL']

            r = self._sessionGET(pageURL, session, 1000)
            if not r.ok:
                self._logException('STREAMCR > Sources page request failed: ' + pageURL)
                return None

            itemA = None

            soup = BeautifulSoup(r.content, 'html.parser')
            mainUL = soup.find('div', class_='wpbc-server').ul
            if 'episode' in data:
                # This is a season page for a TV show. Find the link to the right episode.
                episodeNumber = data['episode']
                for a in mainUL.findAll('a'):
                    match = re.search(r'episode\s(.*?):\s', a.text.lower())
                    itemNumber = int(match.group(1)) if match else -1
                    if itemNumber == episodeNumber:
                        itemA = a
                        break
            else:
                # It's a movie page. Use the only link available.
                itemA = mainUL.a

            # Resolve the item right now.
            if itemA:
                session.headers.update(
                    {
                        'Accept': 'application/json, text/javascript, */*; q=0.01',
                        'Referer': self.BASE_URL + '/',
                        'Origin': self.BASE_URL
                    }
                )
                r2 = self._sessionGET(self.AJAX_URL % itemA['data-eid'], session, 500)
                if r2.ok:
                    jsonData = r2.json()
                    sources = [
                        {
                            'source': 'DirectLink',
                            'quality': label_to_quality(source['label']),
                            'language': 'en',
                            'url': source['file'],
                            'direct': True,
                            'debridonly': False
                        }
                        for source in jsonData['sources']
                    ]
                    return sources
            return None
        except:
            self._logException()
            return None


    def resolve(self, url):
        # The replace() call below is a silly way to circumvent a problem in sourcesResolve().
        # See the sourcesResolve() function in /modules/sources.py at line "elif url.startswith('http'):".
        # The client.request call was failing.
        return url.replace('http', 'HTTP', 1)


    def _sessionGET(self, url, session, delayAmount):
        try:
            startTime = datetime.now() if delayAmount else 0
            r = session.get(url, timeout=8)
            
            if delayAmount:
                elapsed = int((datetime.now() - startTime).total_seconds() * 1000)
                if elapsed < delayAmount and elapsed > 100:
                    xbmc.sleep(delayAmount - elapsed)
            return r
        except:
            return type('FailedResponse', (object,), {'ok': False})


    def _createSession(self, customHeaders={}):
        # Create a 'requests.Session' and try to spoof a header from a web browser.
        session = requests.Session()
        session.headers.update(
            {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'User-Agent': customHeaders.get('UA', randomagent()),
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': customHeaders.get('referer', self.BASE_URL + '/'),
                'Upgrade-Insecure-Requests': '1',
                'DNT': '1'
            }
        )
        if 'cookies' in customHeaders:
            session.cookies.update(customHeaders['cookies'])
        return session         
   

    def _getSearchData(self, lowerTitle, possibleTitles, session, season, episode):
        try:
            searchURL = self.BASE_URL + (self.SEARCH_URL % quote_plus(lowerTitle))
            r = self._sessionGET(searchURL, session, 1000)
            if not r.ok:
                return None

            isMovie = (episode == None)            
            soup = BeautifulSoup(r.content, 'html.parser')
            mainDIV = soup.find('div', class_='main-content')
            for a in mainDIV.findAll('a'):
                title = a.h2.text.lower()
                
                if isMovie:
                    if 'season' in title:
                        continue
                else:
                    if 'season' in title:
                        titleWords = title.split()
                        lenWords = len(titleWords)
                        match = re.search(r' - season (.*?)$', title)
                        if match and int(match.group(1)) == season:
                            title = re.sub(r'(.*?) - season .*', r'\1', title)
                        else:
                            continue
                    else:
                        continue
                
                if title == lowerTitle or title in possibleTitles or getsearch(title) in possibleTitles:
                    data = {
                        'pageURL': self.BASE_URL + a['href'],
                        'headers': {
                            'UA': session.headers['User-Agent'],
                            'referer': searchURL,
                            'cookies': session.cookies.get_dict(),
                        }
                    }
                    if episode:
                        data['episode'] = episode # Send only the episode number, the season is implicit in the URL.              
                    return data                    
            return None # No results found.
        except:
            self._logException()
            return None


    def _debug(self, name, val=None):
        xbmc.log('STREAMCR Debug > ' + name + (' %s' % repr(val) if val else ''), xbmc.LOGWARNING)


    def _logException(self, text=None):
        return # Comment this line to output errors to the Kodi log, useful for debugging this script.
        if text:
            xbmc.log(text, xbmc.LOGERROR)
        else:
            import traceback
            xbmc.log(traceback.format_exc(), xbmc.LOGERROR)
