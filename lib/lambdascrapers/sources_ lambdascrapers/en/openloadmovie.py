# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 10-10-2018 by JewBMX in Yoda.

import re
import urllib
import urlparse
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import proxy
# openloadmovie.ws opens to openloadmovie.org always.
# could remove it but o well it can go down first.

class source:
	def __init__(self):
		self.priority = 1
		self.language = ['en']
		self.domains = ['openloadmovie.org','openloadmovie.ws']
		self.base_link = 'https://openloadmovie.org'

	def movie(self, imdb, title, localtitle, aliases, year):
		try:
			title = cleantitle.geturl(title)
			url = self.base_link + '/movies/%s-%s' % (title,year)
			return url
		except:
			return
			
	def sources(self, url, hostDict, hostprDict):
		try:
			sources = []
			r = client.request(url)
			match = re.compile('<iframe class="metaframe rptss" src="(.+?)"').findall(r)
			for url in match: 
				sources.append({'source': 'Openload','quality': 'HD','language': 'en','url': url,'direct': False,'debridonly': False})
		except Exception:
			return
		return sources

	def resolve(self, url):
		return url