import urlparse
from lambdascrapers.modules import control
from lambdascrapers import providerSources, providerNames

params = dict(urlparse.parse_qsl(sys.argv[2].replace('?', '')))
mode = params.get('mode')

def ScraperChoice():
    from lambdascrapers import providerSources
    sourceList = sorted(providerSources())
    control.idle()
    select = control.selectDialog([i for i in sourceList])
    if select == -1: return
    module_choice = sourceList[select]
    control.setSetting('module.provider', module_choice)
    control.openSettings('0.1')

def ToggleProviderAll(enable):
    from lambdascrapers import providerNames
    sourceList = providerNames()
    (setting, open_id) = ('true', '0.3') if enable else ('false', '0.2')
    for i in sourceList:
        source_setting = 'provider.' + i
        control.setSetting(source_setting, setting)
    control.openSettings(open_id)

def toggleAll(setting, open_id=None, sourceList=None):
    from lambdascrapers import getAllHosters
    sourceList = getAllHosters() if not sourceList else sourceList
    for i in sourceList:
        source_setting = 'provider.' + i
        control.setSetting(source_setting, setting)
    control.openSettings(open_id)



if mode == "LambdaSettings":
    control.openSettings('0.0', 'script.module.lambdascrapers')

if mode == "ScraperChoice":
    ScraperChoice()

if mode == "ToggleProviderAll":
    ToggleProviderAll(False if params['action'] == "DisableModuleAll" else True)

if mode == "toggleAll":
    open_id = params['open_id'] if 'open_id' in params else '0.0'
    sourcelist = params['sourcelist'] if 'sourcelist' in params else None
    toggleAll(params['setting'], open_id, sourceList=sourcelist)

if mode == "toggleAllDebrid":
    sourcelist = ['2ddl','300mbfilms','bestmoviez','ddls','ddlvalley','directdl','gomovies','hevcfilm',
    'moviesonline','myvideolink','phazeddl','power','releasebb','RLSB','rlsbb','rlsmovies','rlsscn',
    'scenerls','sceper','seriescr','tvbmoviez','tvrelease','ultrahd','ultrahdindir','wrzcraft']
    toggleAll(params['setting'], params['open_id'], sourcelist)

if mode == "toggleAllGerman":
    sourcelist = ['allucde','animebase','animeloads','bs','cine','cinenator','ddl',
    'filmpalast','foxx','hdfilme','hdstreams','horrorkino','iload','kinodogs','kinoking',
    'kinow','kinox','lichtspielhaus','movie2k-ac','movie2k-ag','movie2z','movie4k','moviesever',
    'movietown','netzkino','proxer','pureanime','serienstream','seriesever','stream-to',
    'streamdream','streamflix','streamit','tata','video4k','view4u']
    toggleAll(params['setting'], params['open_id'], sourcelist)

if mode == "toggleAllPolish":
    sourcelist = ['alltube','boxfilm','cdahd','cdax','ekinomaniak','ekinotv','filiser',
    'filmwebbooster','iitv','movieneo','openkatalog','paczamy','segos','szukajkatv','trt']
    toggleAll(params['setting'], params['open_id'], sourcelist)

if mode == "toggleAllForeign":
    sourcelist = ['allucde','animebase','animeloads','bs','cine','cinenator','ddl',
    'filmpalast','foxx','hdfilme','hdstreams','horrorkino','iload','kinodogs','kinoking',
    'kinow','kinox','lichtspielhaus','movie2k-ac','movie2k-ag','movie2z','movie4k','moviesever',
    'movietown','netzkino','proxer','pureanime','serienstream','seriesever','stream-to',
    'streamdream','streamflix','streamit','tata','video4k','view4u',
    'alltube','boxfilm','cdahd','cdax','ekinomaniak','ekinotv','filiser',
    'filmwebbooster','iitv','movieneo','openkatalog','paczamy','segos','szukajkatv','trt']
    toggleAll(params['setting'], params['open_id'], sourcelist)

if mode == "Defaults":
    sourcelist = ['1080P','123movies','123moviesgold','123netflix','1movie',
    '4kmovieto','Hdmto','afdah','allrls','animeultima','bmoviez','bnwmovies','bob',
    'cartoonhd','cmovies','coolmoviezone','cooltv','darewatch','divxcrawler','dltube','einthusan',
    'filmxy','flenix','flixanity','fmovies','freefmovies','freeputlockers','furk','genvideos','gogoanime',
    'gowatchseries','hackimdb','hdpopcorns','icefilms','icouchtuner','iwatchflixxyz','kattv','l23movies','library',
    'm4ufree','megahd','movie4uch','moviesplanet','myputlock','mywatchseries','odb','openloadmovie','ororo',
    'plocker','popcorn','primewire','projectfree','pron','putlocker','rajahoki88','reddit','seehd','series9','seriesfree',
    'seriesonline','sezonlukdizi','showbox','solarmoviez','streamlord','tvbox','videoscraper','vidics',
    'vodly','watch32','watchonline','watchseries','xmovies','xwatchseries','ymovies']
    toggleAll(params['setting'], params['open_id'], sourcelist)
