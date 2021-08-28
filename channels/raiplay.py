# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Rai Play
# ------------------------------------------------------------

from core.item import Item
import datetime, xbmc
import requests, sys

from core import jsontools, support
from platformcode import logger

if sys.version_info[0] >= 3:
    from concurrent import futures
else:
    from concurrent_py2 import futures

host = support.config.get_channel_url()

@support.menu
def mainlist(item):
    top =  [('Dirette {bold}', ['/dirette', 'live', '/palinsesto/onAir.json']),
            ('Replay {bold}', ['/guidatv', 'replayMenu', '/guidatv.json'])]

    menu = [('Film {bullet bold}', ['/film', 'menu', '/tipologia/film/index.json']),
            ('Serie TV {bullet bold}', ['/serietv', 'menu', '/tipologia/serietv/index.json']),
            ('Fiction {bullet bold}', ['/fiction', 'menu', '/tipologia/fiction/index.json']),
            ('Documentari {bullet bold}', ['/documentari', 'menu', '/tipologia/documentari/index.json']),
            ('Programmi TV{bullet bold}', ['/programmi', 'menu', '/tipologia/programmi/index.json']),
            ('Programmi per Bambini {bullet bold}', ['/bambini', 'menu', '/tipologia/bambini/index.json']),
            ('Teen {bullet bold}', ['/teen', 'menu', '/tipologia/teen/index.json']),
            ('Learning {bullet bold}', ['/learning', 'menu', '/tipologia/learning/index.json']),
            ('Teche Rai {bullet bold storia}', ['/techerai', 'menu', '/tipologia/techerai/index.json']),
            ('Musica e Teatro {bullet bold}', ['/musica-e-teatro', 'menu', '/tipologia/musica-e-teatro/index.json'])
           ]

    search = ''

    return locals()


def menu(item):
    logger.debug()
    itemlist = []
    item.disable_videolibrary = True
    action = 'peliculas'

    if item.data:
        for it in item.data:
            url = getUrl(it['path_id'])
            action = 'genres'
            itemlist.append(item.clone(title=support.typo(it['name'], 'bold'), url=url.replace('.json','.html'), genre_url=url, data='', action=action))
        support.thumb(itemlist, mode='genre')
    else:
        items = item.data if item.data else requests.get(host + item.args).json()['contents']
        for it in items:
            if 'RaiPlay Slider Block' in it['type'] or 'RaiPlay Slider Generi Block' in it['type']:
                thumb = item.thumbnail
                if 'RaiPlay Slider Generi Block' in it['type']:
                    action = 'menu'
                    thumb = support.thumb('genres')
                itemlist.append(item.clone(title=support.typo(it['name'], 'bold'), data=it.get('contents', item.data), thumbnail=thumb, action=action))

    return itemlist


def genres(item):
    itemlist = []
    items = requests.get(getUrl(item.genre_url)).json()['contents']
    for title, it in items.items():
        if it: itemlist.append(item.clone(title=support.typo(title, 'bold'), data=it, action='peliculas', thumbnail=support.thumb('az')))
    return itemlist


def search(item, text):
    logger.debug(text)
    post = {'page':0, 'pagesize': 1000, 'param':text}

    try:
        item.data = requests.post(host + '/atomatic/raiplay-search-service/api/v3/search', json=post).json()['agg']['titoli']['cards']
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


def peliculas(item):
    logger.debug()
    return addinfo(item.data, item)


def episodios(item):
    logger.debug()
    itemlist = []

    if item.data:
        items = item.data
    elif item.season_url:
        items = requests.get(item.season_url).json()['items']
    elif item.video_url:
        items = requests.get(item.video_url).json()['blocks']

    if 'sets' in items[0]:
        if len(items) > 1:
            itemlist = epMenu(item.clone(data=items))
        else:
            if len(items[0]['sets']) > 1:
                itemlist = epMenu(item.clone(data=items[0]['sets']))
            else:
                items = requests.get(getUrl(items[0]['sets'][0]['path_id'])).json()['items']

    if not itemlist:
        itemlist = addinfo(items, item)

    return itemlist


def epMenu(item):
    video_url = ''
    itemlist = []
    for it in item.data:
        if 'sets' in it:
            itemlist.append(item.clone(title=support.typo(it['name'], 'bold'), data=[it]))
        else:
            itemlist.append(item.clone(title=support.typo(it['name'], 'bold'), season_url=getUrl(it['path_id']), data=''))
    return itemlist


def live(item):
    logger.debug()
    itemlist = []
    item.forcethumb = True
    items = requests.get(getUrl(item.args)).json()['on_air']
    for it in items:
        title = it['channel']
        url = '{}/dirette/{}'.format(host, title.lower().replace(' ',''))
        fanart = getUrl(it['currentItem']['image'])
        current = it['currentItem']
        next = it['nextItem']
        plot = '[B]{}[/B]\n{}\n\nA Seguire: [B]{}[/B]\n{}'.format(current['name'], current['description'], next['name'], next['description'])
        itemlist.append(item.clone(title=title, fulltitle=title, fanart=fanart, plot=plot, url=url, video_url=url + '.json', action='play'))
    itemlist.sort(key=lambda it: support.channels_order.get(it.fulltitle, 999))
    support.thumb(itemlist, mode='live')
    return itemlist


def replayMenu(item):
    logger.debug()

    # create day and month list
    days = []
    months = []
    try:
        days.append(xbmc.getLocalizedString(17))
        for day in range(11, 17): days.append(xbmc.getLocalizedString(day))
        for month in range(21, 33): months.append(xbmc.getLocalizedString(month))
    except:  # per i test, xbmc.getLocalizedString non è supportato
        days.append('dummy')
        for day in range(11, 17): days.append('dummy')
        for month in range(21, 33): months.append('dummy')

    # make menu
    itemlist = []
    today = datetime.date.today()
    for d in range(7):
        day = today - datetime.timedelta(days=d)
        dayName = days[int(day.strftime("%w"))]
        dayNumber = day.strftime("%d")
        monthName = months[int(day.strftime("%m"))-1]
        title = '{} {} {}'.format(dayName, dayNumber, monthName)
        itemlist.append(item.clone(title = support.typo(title, 'bold'),
                                   action='replayChannels',
                                   date=day.strftime("%d-%m-%Y")))
    return itemlist


def replayChannels(item):
    logger.debug()
    itemlist = []
    items = requests.get(getUrl(item.args)).json()['channels']

    for it in items:
        if 'RaiPlay' in it['name']: continue
        url = '{}?channel={}&date={}'.format(item.url, it['absolute_path'], item.date)
        channel_url = '{}/palinsesto/app/{}/{}.json'.format(host, it['absolute_path'], item.date)
        itemlist.append(item.clone(title=support.typo(it['label'], 'bold'),
                                   fulltitle=it['label'],
                                   url=url,
                                   channel_url=channel_url,
                                   action='replay'))
    itemlist.sort(key=lambda it: support.channels_order.get(it.fulltitle, 999))
    support.thumb(itemlist, mode='live')
    return itemlist

def replay(item):
    logger.debug()

    def itInfo(it):
        info = requests.get(getUrl(it['program']['info_url'])).json()
        image = getUrl(info['images']['landscape'])
        return item.clone(title = '{} - {}'.format(it['hour'], it['name']),
                         thumbnail = image,
                         fanart = image,
                         plot = info['description'],
                         url = getUrl(it['weblink']),
                         video_url = getUrl(it['path_id']),
                         action = 'play',
                         forcethumb = True)


    itemlist = []
    items = requests.get(item.channel_url).json().get('events', {})
    now = datetime.datetime.now()
    h = int('{}{:02d}'.format(now.hour, now.minute))

    with futures.ThreadPoolExecutor() as executor:
        itlist = [executor.submit(itInfo, it) for it in items if it['has_video'] and int(it['hour'].replace(':','')) <= h]
        for res in futures.as_completed(itlist):
            if res.result():
                itemlist.append(res.result())
    if not itemlist:
        return [Item(title='Non ci sono Replay per questo Canale')]
    return itemlist

def play(item):
    logger.debug()

    res = requests.get(item.video_url).json()

    if 'first_item_path' in res:
        res = requests.get(getUrl(res['first_item_path'])).json()

    url, lic = support.match(res['video']['content_url'] + '&output=56', patron=r'content"><!\[CDATA\[([^\]]+)(?:.*?"WIDEVINE","licenceUrl":"([^"]+))?').match

    if lic:
        item.drm = 'com.widevine.alpha'
        item.license = lic + '|' + host + '|R{SSM}|'

    item = item.clone(server='directo', url=url, no_return=True, manifest='hls')

    return [item]


def getUrl(url):
    logger.debug()

    if url.startswith("/raiplay/"): url = url.replace("/raiplay/", host +'/')
    elif url.startswith("//"): url = "https:" + url
    elif url.startswith("/"): url = host + url

    url = url.replace(".html?json", ".json").replace("/?json",".json").replace("?json",".json").replace(" ", "%20")

    return url


def addinfo(items, item):
    def itInfo(key, item):
        logger.debug(jsontools.dump(key))
        item.forcethumb = True
        if key.get('titolo', ''):
            key = requests.get(getUrl(key['path_id'])).json()['program_info']


        info = requests.get(getUrl(key['info_url'])).json() if 'info_url' in key else {}

        images = info.get('images', {})
        fanart = images.get('landscape', '')
        thumb = images.get('portrait_logo', '')
        if not thumb: thumb = fanart
        title = key.get('name', '')

        it = item.clone(title=support.typo(title, 'bold'),
                        data='',
                        fulltitle=title,
                        show=title,
                        thumbnail= getUrl(thumb),
                        fanart=getUrl(fanart),
                        url=getUrl(key.get('weblink', '')),
                        video_url=getUrl(key['path_id']),
                        plot=info.get('description', ''))

        if 'Genere' not in key.get('sub_type', '') and ('layout' not in key or key['layout'] == 'single'):
            it.action = 'play'
            it.contentTitle = it.fulltitle
        else:
            it.action = 'episodios'
            it.contentSerieName = it.fulltitle
        return it

    itemlist = []
    with futures.ThreadPoolExecutor() as executor:
        itlist = [executor.submit(itInfo, it, item) for it in items]
        for res in futures.as_completed(itlist):
            if res.result():
                itemlist.append(res.result())
    return itemlist