# -*- coding: UTF-8 -*-
'''
    PutLocker scraper for Exodus forks.
    Sep 22 2018

    Updated and refactored by someone.
    Originally created by others.
'''
import re
import requests
import traceback
from bs4 import BeautifulSoup
try:
    from urllib import urlencode, quote_plus # Python 2
except ImportError:
    from urllib.parse import urlencode, quote_plus # Python 3

import xbmc

from resources.lib.modules.client import randomagent


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['putlocker.se', 'putlockertv.to']

        self.ALL_JS_PATTERN = '<script src=\"(/assets/min/public/all.js?.*?)\"'
        self.DEFAULT_ACCEPT = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'

        self.BASE_URL = 'https://www5.putlockertv.to'

        # Path to search for either a film or season from a tvshow.
        self.SEARCH_PATH = '/ajax/film/search?ts=%s&_=%i&keyword=%s&sort=year%%3Adesc'

        # Paths to retrieve a list of host names and internal URLs.
        self.UPDATE_PATH = 'ajax/film/update-views?ts=%s&_=%i&id=%s&random=1'
        self.SERVERS_PATH = '/ajax/film/servers/%s?ts=%s&_=%i'

        # Path to retrieve an unresolved host, to be sent to the ResolveURL plugin.
        self.INFO_PATH = '/ajax/episode/info?ts=%s&_=%i&id=%s&server=%s&update=0'

        # Used in sources() to map lowercase host names to debrid-friendly host names.
        self.DEBRID_HOSTS = {
            'openload': 'openload.co',
            'rapidvideo': 'rapidvideo.com',
            'streamango': 'streamango.com'
        }


    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            session = self._createSession(randomagent())

            lowerTitle = title.lower()
            stringConstant, searchHTML = self._getSearch(lowerTitle, session)

            possibleTitles = set(
                (lowerTitle,) + tuple((alias['title'].lower() for alias in aliases) if aliases else ())
            )
            soup = BeautifulSoup(searchHTML, 'html.parser')
            for div in soup.findAll('div', recursive=False):
                if div.span and year in div.span.text and div.a.text.lower() in possibleTitles:
                    # The return value doesn't need to be url-encoded or even a string. Exodus forks accept
                    # anything that can be converted with repr() and be stored in the local database.
                    return {
                        'type': 'movie',
                        'pageURL': self.BASE_URL + div.a['href'],
                        'sConstant': stringConstant,
                        'UA': session.headers['User-Agent'],
                        'cfCookies': self._cloudflareCookiesToDict(session)
                    }
            return None # No results found.
        except:
            self._logException()
            return None


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            return tvshowtitle.lower()
        except:
            self._logException()
            return None


    def episode(self, data, imdb, tvdb, title, premiered, season, episode):
        try:
            session = self._createSession(randomagent())

            # Search with the TV show name and season number string.
            lowerTitle = data
            stringConstant, searchHTML = self._getSearch(lowerTitle + ' ' + season, session)

            soup = BeautifulSoup(searchHTML, 'html.parser')
            for div in soup.findAll('div', recursive=False):
                resultName = div.a.text.lower()
                if lowerTitle in resultName and season in resultName:
                    return {
                        'type': 'episode',
                        'episode': episode,
                        'pageURL': self.BASE_URL + div.a['href'],
                        'sConstant': stringConstant,
                        'UA': session.headers['User-Agent'],
                        'cfCookies': self._cloudflareCookiesToDict(session)
                    }
            return None # No results found.
        except:
            self._logException()
            return None


    def sources(self, data, hostDict, hostprDict):
        try:
            isMovie = (data['type'] == 'movie')
            episode = data.get('episode', '')
            pageURL = data['pageURL']
            stringConstant = data['sConstant']

            session = self._createSession(data['UA'], data['cfCookies'])

            xbmc.sleep(1000)
            r = self._sessionGET(pageURL, session)
            if not r.ok:
                self._logException('PLOCKER > %s Sources page request failed' % data['type'].capitalize())
                return None
            pageHTML = r.text
            timeStamp = self._getTimeStamp(pageHTML)

            # Get a HTML block with a list of host names and internal links to them.

            session.headers['Referer'] = pageURL # Refer to this page that "we're on" right now to avoid suspicion.
            pageID = pageURL.rsplit('.', 1)[1]
            token = self._makeToken({'ts': timeStamp}, stringConstant)
            xbmc.sleep(200)
            serversHTML = self._getServers(pageID, timeStamp, token, session)

            # Go through the list of hosts and create a source entry for each.

            sources = [ ]
            tempTokenData = {'ts': timeStamp, 'id': None, 'server': None, 'update': '0'}
            baseInfoURL = self.BASE_URL + self.INFO_PATH

            soup = BeautifulSoup(serversHTML, 'html.parser')
            for serverDIV in soup.div.findAll('div', {'class': 'server row', 'data-id': True}, recursive=False):
                tempTokenData['server'] = serverDIV['data-id']
                hostName = serverDIV.label.text.strip().lower()
                hostName = self.DEBRID_HOSTS.get(hostName, hostName)

                for a in serverDIV.findAll('a', {'data-id': True}):
                    # The text in the <a> tag can be the movie quality ("HDRip", "CAM" etc.) or for TV shows
                    # it's the episode number with a one-zero-padding, like "09", for each episode in the season.
                    label = a.text.lower().strip()
                    hostID = a['data-id'] # A string identifying a host embed to be retrieved from putlocker's servers.

                    if isMovie or episode == str(int(label)):
                        if isMovie:
                            if 'hd' in label:
                                quality = 'HD'
                            else:
                                quality = 'SD' if ('ts' not in label and 'cam' not in label) else 'CAM'
                        else:
                            quality = 'SD'

                        tempTokenData['id'] = hostID
                        tempToken = self._makeToken(tempTokenData, stringConstant)

                        # Send data for the resolve() function below to use later, when the user plays an item.
                        # We send the CF cookies from the session (instead of reusing them from data['cfCookies'])
                        # because they might've changed.
                        unresolvedData = {
                            'url': baseInfoURL % (timeStamp, tempToken, hostID, tempTokenData['server']),
                            'UA': data['UA'],
                            'cfCookies': self._cloudflareCookiesToDict(session),
                            'referer': pageURL + '/' + hostID
                        }
                        sources.append(
                            {
                                'source': hostName,
                                'quality': quality,
                                'language': 'en',
                                'url': unresolvedData, # Doesn't need to be a string, just repr()-able.
                                'direct': False,
                                'debridonly': False
                            }
                        )
            return sources
        except:
            self._logException()
            return None


    def resolve(self, data):
        # The 'data' parameter is the 'unresolvedData' dictionary sent from sources().
        try:
            session = self._createSession(data['UA'], data['cfCookies'], data['referer'])
            xbmc.sleep(500) # Give some room between requests (_getHost() -> _requestJSON() will also sleep some more).
            return self._getHost(data['url'], session) # Return a host URL for use with ResolveURL and play.
        except:
            self._logException()
            return None


    def _sessionGET(self, url, session):
        try:
            return session.get(url, timeout=10) # Goes through a Cloudflare challenge, if necessary.
        except:
            return type('FailedResponse', (object,), {'ok': False})


    def _requestJSON(self, url, session):
        try:
            oldAccept = session.headers['Accept']
            session.headers.pop('Upgrade-Insecure-Requests', None)
            session.headers.update(
                {
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            )
            xbmc.sleep(1500)
            r = self._sessionGET(url, session)
            session.headers['Accept'] = oldAccept
            session.headers['Upgrade-Insecure-Requests'] = '1'
            del session.headers['X-Requested-With']
            return r.json() if r.ok and r.text else None
        except:
            self._logException()
            return None


    def _getHost(self, url, session):
        jsonData = self._requestJSON(url, session)
        if jsonData:
            return jsonData['target']
        else:
            self._logException('PLOCKER > _getHost JSON request failed')
            return ''


    def _getServers(self, pageID, timeStamp, token, session):
        jsonData = self._requestJSON(
            self.BASE_URL + (self.SERVERS_PATH % (pageID, timeStamp, token)), session
        )
        if jsonData:
            return jsonData['html']
        else:
            self._logException('PLOCKER > _getServers JSON request failed')
            return ''


    def _getSearch(self, lowerTitle, session):
        '''
        All the code in here assumes a certain website structure.
        If they change it in the future, it'll crash.
        '''
        # Get the homepage HTML.
        r = self._sessionGET(self.BASE_URL, session)
        if not r.ok:
            self._logException('PLOCKER > Homepage request failed')
            return ''
        homepageHTML = r.text
        timeStamp = self._getTimeStamp(homepageHTML)

        # Get the minified main javascript file.
        jsPath = re.search(self.ALL_JS_PATTERN, homepageHTML, re.DOTALL).group(1)
        session.headers['Accept'] = '*/*' # Use the same 'Accept' for JS files as web browsers do.
        xbmc.sleep(200)
        allJS = self._sessionGET(self.BASE_URL + jsPath, session).text
        session.headers['Accept'] = self.DEFAULT_ACCEPT

        # Some unknown cookie flag that they use, set after 'all.js' is loaded.
        # Doesn't seem to make a difference, but it might help with staying unnoticed.
        session.cookies.set('', '__test')

        # Get the underscore token used to verify all requests. It's calculated from all parameters on JSON requests.
        # The value for 'keyword' is the search query, it should have normal spaces (like a movie title).
        data = {'ts': timeStamp, 'keyword': lowerTitle, 'sort': 'year:desc'}
        stringConstant = self._makeStringConstant(allJS)
        token = self._makeToken(data, stringConstant)

        # We use their JSON api as it's much less data needed from their servers. Easier on them, faster for us too.
        jsonData = self._requestJSON(
            self.BASE_URL + (self.SEARCH_PATH % (timeStamp, token, quote_plus(lowerTitle))), session
        )
        if jsonData:
            return stringConstant, jsonData['html']
        else:
            self._logException('PLOCKER > _getSearch JSON request failed')
            return ''


    def _createSession(self, userAgent=None, cookies=None, referer=None):
        # Try to spoof a header from a web browser.
        session = CloudflareSession.create_scraper()
        session.headers.update(
            {
                'Accept': self.DEFAULT_ACCEPT,
                'User-Agent': userAgent if userAgent else randomagent(),
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': referer if referer else self.BASE_URL + '/',
                'Upgrade-Insecure-Requests': '1',
                'DNT': '1'
            }
        )
        if cookies:
            session.cookies.update(cookies)
            session.cookies[''] = '__test' # See _getSearch() for more info on this.
        return session


    def _cloudflareCookiesToDict(self, session):
        return {
            '__cfduid': session.cookies['__cfduid'],
            'cf_clearance': session.cookies['cf_clearance']
        }


    def _debug(self, name, val=None):
        xbmc.log('PLOCKER Debug > %s %s' % (name, repr(val) if val else ''), xbmc.LOGWARNING)


    def _logException(self, text=None):
        #return # (Un)Comment this line to (not) output errors in the Kodi log, useful for debugging this script.
        # ------------------
        if text:
            xbmc.log(text, xbmc.LOGERROR)
        else:
            xbmc.log(traceback.format_exc(), xbmc.LOGERROR)


    # Token algorithm, present in "all.js".
    # ----------------------------------------------------------
    # You can get to it more quickly by searching for "Number(" in that JS file, one of
    # the occurrences will be in that section.
    # The references in the functions below were beautified with https://beautifier.io.
    #
    # To actually find it in the future in case they change it, you need to use the
    # Javascript debugger of your browser (like Firefox etc.), setting a breakpoint
    # at a specific query handler of an ajax request. It's called every time you type
    # something in the search field.
    # From then on you go step by step with the debugger, using Step-Overs mostly, and
    # then start to Step-In when you reach a part with "encode URI", as it's getting close.
    # Keep stepping until your reach some functions that that use the Math and Number classes.

    def _getTimeStamp(self, html):
        return re.search(r'<html data-ts="(.*?)"', html, re.DOTALL).group(1)


    def _r(self, c):
        '''
        Reference:
        function r() {
            return Jf + Jd + Iy + Jd + y + Jd + Su
        }
        '''
        return c['Jf'] + c['Jd'] + c['Iy'] + c['Jd'] + c['y'] + c['Jd'] + c['Su']


    def _e(self, t):
        '''
        Reference:
        function e(t) {
            var i, n = 0;
            for (i = 0; i < t[R]; i++) n += t[Sb + Jd + yc + Jd + dl](i) + i;
            return n
        }
        '''
        return sum(ord(t[i]) + i for i in xrange(len(t)))


    def _makeStringConstant(self, allJS):
        '''
        Assumes the key names of the constants will stay the same.
        If they change 'all.js' in the future you'll need to update these names
        to the ones used in the r() function.
        '''
        return self._r(
            {
                key: re.search(r'\b%s=\"(.*?)\"' % key, allJS, re.DOTALL).group(1)
                for key in ('Jf', 'Jd', 'Iy', 'y', 'Su')
            }
        )


    def _makeToken(self, params, stringConstant):
        '''
        Reference:
        i[u](function(t) {
            var n = function(t) {
                var n, o, s = e(r()),
                    u = {},
                    f = {};
                f[c] = Jd + a, o = i[Eh](!0, {}, t, f);
                for (n in o) Object[In][rf + Jd + sg + Jd + _p][Hp](o, n) && (s += e(function(t, i) {
                    var n, r = 0;
                    for (n = 0; n < Math[Xe](t[R], i[R]); n++) r += n < i[R] ? i[Sb + Jd + yc + Jd + dl](n) : 0, r += n < t[R] ? t[Sb + Jd + yc + Jd + dl](n) : 0;
                    return Number(r)[ku + Jd + ix](16)
                }(r() + n, o[n])));
                return u[c] = a, u[h] = s, u

        :returns: An integer token.
        '''
        def __convolute(t, i):
            iLen = len(i)
            tLen = len(t)
            r = 0
            for n in xrange(max(tLen, iLen)):
                r += ord(i[n]) if n < iLen else 0
                r += ord(t[n]) if n < tLen else 0
            return self._e(hex(r)[2:]) # Skip two characters to ignore the '0x' from the Python hex string.

        s = self._e(stringConstant)
        for key in params.iterkeys():
            s += __convolute(stringConstant + key, params[key])
        return s


# ==================================================================================================
# Cloudflare scraper taken from Team Universal's UniversalScrapers. It extends 'requests.Session'.
# https://github.com/teamuniversal/scrapers/tree/master/_modules4all/script.module.universalscrapers
# (The local one from resources.lib.modules.client wasn't working.)
import random
import re
'''''''''
Disables InsecureRequestWarning: Unverified HTTPS request is being made warnings.
'''''''''
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
''''''
from requests.sessions import Session
from copy import deepcopy
from time import sleep
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse


class CloudflareSession(Session):
    def __init__(self, *args, **kwargs):
        super(CloudflareSession, self).__init__(*args, **kwargs)

        if "requests" in self.headers["User-Agent"]:
            # Spoof Firefox on Linux if no custom User-Agent has been set
            self.headers["User-Agent"] = randomagent()


    def request(self, method, url, *args, **kwargs):
        resp = super(CloudflareSession, self).request(method, url, *args, **kwargs)

        # Check if Cloudflare anti-bot is on
        if ( resp.status_code == 503
             and resp.headers.get("Server", "").startswith("cloudflare")
             and b"jschl_vc" in resp.content
             and b"jschl_answer" in resp.content
        ):
            return self.solve_cf_challenge(resp, **kwargs)

        # Otherwise, no Cloudflare anti-bot detected
        return resp


    def solve_cf_challenge(self, resp, **original_kwargs):
        sleep(8)  # Cloudflare requires a delay before solving the challenge

        body = resp.text
        parsed_url = urlparse(resp.url)
        domain = parsed_url.netloc
        submit_url = "%s://%s/cdn-cgi/l/chk_jschl" % (parsed_url.scheme, domain)

        cloudflare_kwargs = deepcopy(original_kwargs)
        params = cloudflare_kwargs.setdefault("params", {})
        headers = cloudflare_kwargs.setdefault("headers", {})
        headers["Referer"] = resp.url

        try:
            params["jschl_vc"] = re.search(r'name="jschl_vc" value="(\w+)"', body).group(1)
            params["pass"] = re.search(r'name="pass" value="(.+?)"', body).group(1)

            # Extract the arithmetic operation
            init = re.findall('setTimeout\(function\(\){\s*var.*?.*:(.*?)}', body)[-1]
            builder = re.findall(r"challenge-form\'\);\s*(.*)a.v", body)[0]
            if '/' in init:
                init = init.split('/')
                decryptVal = self.parseJSString(init[0]) / float(self.parseJSString(init[1]))
            else:
                decryptVal = self.parseJSString(init)
            lines = builder.split(';')

            for line in lines:
                if len(line)>0 and '=' in line:
                    sections=line.split('=')
                    if '/' in sections[1]:
                        subsecs = sections[1].split('/')
                        line_val = self.parseJSString(subsecs[0]) / float(self.parseJSString(subsecs[1]))
                    else:
                        line_val = self.parseJSString(sections[1])
                    decryptVal = float(eval(('%.16f'%decryptVal)+sections[0][-1]+('%.16f'%line_val)))

            answer = float('%.10f'%decryptVal) + len(domain)

        except Exception as e:
            # Something is wrong with the page.
            # This may indicate Cloudflare has changed their anti-bot
            # technique. If you see this and are running the latest version,
            # please open a GitHub issue so I can update the code accordingly.
            xbmc.log("[!] %s Unable to parse Cloudflare anti-bots page. "
                     "Try upgrading cloudflare-scrape, or submit a bug report "
                     "if you are running the latest version. Please read "
                     "https://github.com/Anorov/cloudflare-scrape#updates "
                     "before submitting a bug report." % e, xbmc.LOGERROR)
            raise

        try: params["jschl_answer"] = str(answer) #str(int(jsunfuck.cfunfuck(js)) + len(domain))
        except: pass

        # Requests transforms any request into a GET after a redirect,
        # so the redirect has to be handled manually here to allow for
        # performing other types of requests even as the first request.
        method = resp.request.method
        cloudflare_kwargs["allow_redirects"] = False

        redirect = self.request(method, submit_url, **cloudflare_kwargs)
        redirect_location = urlparse(redirect.headers["Location"])

        if not redirect_location.netloc:
            redirect_url = "%s://%s%s" % (parsed_url.scheme, domain, redirect_location.path)
            return self.request(method, redirect_url, **original_kwargs)
        return self.request(method, redirect.headers["Location"], **original_kwargs)


    def parseJSString(self, s):
        try:
            offset=1 if s[0]=='+' else 0
            val = int(eval(s.replace('!+[]','1').replace('!![]','1').replace('[]','0').replace('(','str(')[offset:]))
            return val
        except:
            pass


    @classmethod
    def create_scraper(cls, sess=None, **kwargs):
        """
        Convenience function for creating a ready-to-go requests.Session (subclass) object.
        """
        scraper = cls()

        if sess:
            attrs = ["auth", "cert", "cookies", "headers", "hooks", "params", "proxies", "data"]
            for attr in attrs:
                val = getattr(sess, attr, None)
                if val:
                    setattr(scraper, attr, val)

        return scraper


    ## Functions for integrating cloudflare-scrape with other applications and scripts

    @classmethod
    def get_tokens(cls, url, user_agent=None, **kwargs):
        scraper = cls.create_scraper()
        if user_agent:
            scraper.headers["User-Agent"] = user_agent

        try:
            resp = scraper.get(url, **kwargs)
            resp.raise_for_status()
        except Exception as e:
            xbmc.log("'%s' returned an error. Could not collect tokens." % url, xbmc.LOGERROR)
            raise

        domain = urlparse(resp.url).netloc
        cookie_domain = None

        for d in scraper.cookies.list_domains():
            if d.startswith(".") and d in ("." + domain):
                cookie_domain = d
                break
        else:
            raise ValueError("Unable to find Cloudflare cookies. Does the site actually have Cloudflare IUAM (\"I'm Under Attack Mode\") enabled?")

        return ({
                    "__cfduid": scraper.cookies.get("__cfduid", "", domain=cookie_domain),
                    "cf_clearance": scraper.cookies.get("cf_clearance", "", domain=cookie_domain)
                },
                scraper.headers["User-Agent"]
               )

    @classmethod
    def get_cookie_string(cls, url, user_agent=None, **kwargs):
        """
        Convenience function for building a Cookie HTTP header value.
        """
        tokens, user_agent = cls.get_tokens(url, user_agent=user_agent, **kwargs)
        return "; ".join("=".join(pair) for pair in tokens.items()), user_agent
