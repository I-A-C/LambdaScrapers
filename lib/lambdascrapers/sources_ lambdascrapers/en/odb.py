# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 10-10-2018 by JewBMX in Yoda.
# Note: anyone that reads this should take a second and visit https://odb.to its pretty cool compared to most lol.

import re
import urllib
import urlparse
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import proxy


class source:
	def __init__(self):
		self.priority = 1
		self.language = ['en']
		self.domains = ['odb.to']
		self.base_link = 'https://api.odb.to'
		self.movie_link = '/embed?imdb_id=%s'
		self.tv_link = '/embed?imdb_id=%s&s=%s&e=%s'

	def movie(self, imdb, title, localtitle, aliases, year):
		try:
			url = self.base_link + self.movie_link % imdb
			return url
		except:
			return
			
	def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
		try:
			url = imdb
			return url
		except:
			return
 
	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if not url: return
			imdb = url
			url = self.base_link + self.tv_link % (imdb,season,episode)
			return url
		except:
			return

	def sources(self, url, hostDict, hostprDict):
		try:
			sources = []
			r = client.request(url)
			try:
				match = re.compile('<iframe src="(.+?)" width').findall(r)
				for url in match:
					host = url.replace('https://','').replace('http://','').replace('www.','')
					sources.append({
						'source': host,
						'quality': 'HD',
						'language': 'en',
						'url': url,
						'direct': False,
						'debridonly': False
					})
			except:
				return
		except Exception:
			return
		return sources

	def resolve(self, url):
		return url