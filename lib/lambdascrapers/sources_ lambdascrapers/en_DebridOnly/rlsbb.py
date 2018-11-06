# -*- coding: UTF-8 -*-
#######################################################################
 # ----------------------------------------------------------------------------
 # "THE BEER-WARE LICENSE" (Revision 42):
 # @Daddy_Blamo wrote this file.  As long as you retain this notice you
 # can do whatever you want with this stuff. If we meet some day, and you think
 # this stuff is worth it, you can buy me a beer in return. - Muad'Dib
 # ----------------------------------------------------------------------------
#######################################################################

# Addon Name: Placenta
# Addon id: plugin.video.placenta
# Addon Provider: Mr.Blamo

# Updated for Lambdascrapers 2018-9-5

import re,traceback,urllib,urlparse,json

from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules import debrid
from resources.lib.modules import log_utils
from resources.lib.modules import source_utils

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['rlsbb.to']
        self.base_link = 'http://rlsbb.to'
        self.search_base_link = 'http://search.rlsbb.to'
        self.search_cookie = 'serach_mode=rlsbb'
        self.search_link = '/lib/search526049.php?phrase=%s&pindex=1&content=true'

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = {'imdb': imdb, 'title': title, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
            failure = traceback.format_exc()
            log_utils.log('RLSBB - Exception: \n' + str(failure))
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
            failure = traceback.format_exc()
            log_utils.log('RLSBB - Exception: \n' + str(failure))
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if url == None: return

            url = urlparse.parse_qs(url)
            url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
            url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
            url = urllib.urlencode(url)
            return url
        except:
            failure = traceback.format_exc()
            log_utils.log('RLSBB - Exception: \n' + str(failure))
            return

    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []

            if url == None: return sources

            if debrid.status() == False: raise Exception()

            data = urlparse.parse_qs(url)         
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])        
            title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
            hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']
            premDate = ''
            
            query = '%s S%02dE%02d' % (
            data['tvshowtitle'], int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else '%s %s' % (
            data['title'], data['year'])
            query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', '', query)

            query = query.replace("&", "and")
            query = query.replace("  ", " ")
            query = query.replace(" ", "-")
            
            url = self.search_link % urllib.quote_plus(query)
            url = urlparse.urljoin(self.base_link, url)

            url = "http://rlsbb.to/" + query                                # this overwrites a bunch of previous lines!
            if 'tvshowtitle' not in data: url = url + "-1080p"				# NB: I don't think this works anymore! 2b-checked. 

            r = client.request(url)                                         # curl as DOM object
            
            if r == None and 'tvshowtitle' in data:
                season = re.search('S(.*?)E', hdlr)
                season = season.group(1)
                query = title
                query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', '', query)
                query = query + "-S" + season
                query = query.replace("&", "and")
                query = query.replace("  ", " ")
                query = query.replace(" ", "-")
                url = "http://rlsbb.to/" + query
                r = client.request(url)

            # looks like some shows have had episodes from the current season released in s00e00 format before switching to YYYY-MM-DD
            # this causes the second fallback search above for just s00 to return results and stops it from searching by date (ex. http://rlsbb.to/vice-news-tonight-s02)
            # so loop here if no items found on first pass and force date search second time around
            for loopCount in range(0,2):
                if loopCount == 1 or (r == None and 'tvshowtitle' in data):                     # s00e00 serial failed: try again with YYYY-MM-DD
                    # http://rlsbb.to/the-daily-show-2018-07-24                                 ... example landing urls
                    # http://rlsbb.to/stephen-colbert-2018-07-24                                ... case and "date dots" get fixed by rlsbb
                    #query= re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)','',data['tvshowtitle'])   # this RE copied from above is just trash
                    
                    premDate = re.sub('[ \.]','-',data['premiered'])                            # date looks usually YYYY-MM-DD but dunno if always
                    query = re.sub('[\\\\:;*?"<>|/\-\']', '', data['tvshowtitle'])              # quadruple backslash = one backslash :p
                    query = query.replace("&", " and ").replace("  ", " ").replace(" ", "-")    # throw in extra spaces around & just in case
                    query = query + "-" + premDate                      
                    
                    url = "http://rlsbb.to/" + query            
                    url = url.replace('The-Late-Show-with-Stephen-Colbert','Stephen-Colbert')   # 
                    #url = url.replace('Some-Specific-Show-Title-No2','Scene-Title2')           # shows I want...
                    #url = url.replace('Some-Specific-Show-Title-No3','Scene-Title3')           #         ...but theTVDB title != Scene release

                    r = client.request(url)
                    
                posts = client.parseDOM(r, "div", attrs={"class": "content"})   # get all <div class=content>...</div>
                hostDict = hostprDict + hostDict                                # ?
                items = []
                for post in posts:
                    try:
                        u = client.parseDOM(post, 'a', ret='href')              # get all <a href=..... </a>
                        for i in u:                                             # foreach href url
                            try:
                                name = str(i)
                                if hdlr in name.upper(): items.append(name)
                                elif len(premDate) > 0 and premDate in name.replace(".","-"): items.append(name)      # s00e00 serial failed: try again with YYYY-MM-DD
                                # NOTE: the vast majority of rlsbb urls are just hashes! Future careful link grabbing would yield 2x or 3x results
                            except:
                                pass
                    except:
                        pass
                        
                if len(items) > 0: break

            seen_urls = set()

            for item in items:
                try:
                    info = []

                    url = str(item)
                    url = client.replaceHTMLCodes(url)
                    url = url.encode('utf-8')

                    if url in seen_urls: continue
                    seen_urls.add(url)

                    host = url.replace("\\", "")
                    host2 = host.strip('"')
                    host = re.findall('([\w]+[.][\w]+)$', urlparse.urlparse(host2.strip().lower()).netloc)[0]

                    if not host in hostDict: raise Exception()
                    if any(x in host2 for x in ['.rar', '.zip', '.iso']): continue

                    if '720p' in host2:
                        quality = 'HD'
                    elif '1080p' in host2:
                        quality = '1080p'
                    else:
                        quality = 'SD'

                    info = ' | '.join(info)
                    host = client.replaceHTMLCodes(host)
                    host = host.encode('utf-8')
                    sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': host2, 'info': info, 'direct': False, 'debridonly': True})
                    # why is this hardcoded to debridonly=True? seems like overkill but maybe there's a resource-management reason?
                except:
                    pass
            check = [i for i in sources if not i['quality'] == 'CAM']
            if check: sources = check
            return sources
        except:
            failure = traceback.format_exc()
            log_utils.log('RLSBB - Exception: \n' + str(failure))
            return sources

    def resolve(self, url):
        return url