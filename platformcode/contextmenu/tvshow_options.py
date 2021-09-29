# -*- coding: utf-8 -*-
import xbmc, sys, xbmcgui, os, xbmcvfs, traceback
from platformcode import config, logger

librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
sys.path.insert(0, librerias)

from core.item import Item
from lib.sambatools import libsmb as samba
from core import scrapertools, support

path = ''
mediatype = ''


def exists(path, silent=False, vfs=True):
    path = xbmc.translatePath(path)
    try:
        if vfs:
            result = bool(xbmcvfs.exists(path))
            if not result and not path.endswith('/') and not path.endswith('\\'):
                result = bool(xbmcvfs.exists(join(path, ' ').rstrip()))
            return result
        elif path.lower().startswith("smb://"):
            return samba.exists(path)
        else:
            return os.path.exists(path)
    except:
        logger.error("ERROR when checking the path: %s" % path)
        if not silent:
            logger.error(traceback.format_exc())
        return False


def join(*paths):
    list_path = []
    if paths[0].startswith("/"):
        list_path.append("")
    for path in paths:
        if path:
            list_path += path.replace("\\", "/").strip("/").split("/")

    if scrapertools.find_single_match(paths[0], r'(^\w+:\/\/)'):
        return str("/".join(list_path))
    else:
        return str(os.sep.join(list_path))


def search_paths(Id):
    records = execute_sql('SELECT idPath FROM tvshowlinkpath WHERE idShow LIKE "%s"' % Id)
    if len(records) >= 1:
        for record in records:
            path_records = execute_sql('SELECT strPath FROM path WHERE idPath LIKE "%s"' % record[0])
            for path in path_records:
                if config.get_setting('videolibrarypath') in path[0] and exists(join(path[0], 'tvshow.nfo')):
                    return path[0]
    return ''


def execute_sql(sql):
    logger.debug()
    file_db = ""
    records = None

    # We look for the archive of the video database according to the version of kodi
    video_db = config.get_platform(True)['video_db']
    if video_db:
        file_db = os.path.join(xbmc.translatePath("special://userdata/Database"), video_db)

    # alternative method to locate the database
    if not file_db or not os.path.exists(file_db):
        file_db = ""
        for f in os.path.listdir(xbmc.translatePath("special://userdata/Database")):
            path_f = os.path.join(xbmc.translatePath("special://userdata/Database"), f)

            if os.path.pathoos.pathols.isfile(path_f) and f.lower().startswith('myvideos') and f.lower().endswith('.db'):
                file_db = path_f
                break

    if file_db:
        logger.debug("DB file: %s" % file_db)
        conn = None
        try:
            import sqlite3
            conn = sqlite3.connect(file_db)
            cursor = conn.cursor()

            logger.debug("Running sql: %s" % sql)
            cursor.execute(sql)
            conn.commit()

            records = cursor.fetchall()
            if sql.lower().startswith("select"):
                if len(records) == 1 and records[0][0] is None:
                    records = []

            conn.close()
            logger.debug("Query executed. Records: %s" % len(records))

        except:
            logger.error("Error executing sql query")
            if conn:
                conn.close()

    else:
        logger.debug("Database not found")

    return records


def get_id():
    global mediatype

    mediatype = xbmc.getInfoLabel('ListItem.DBTYPE')
    if mediatype == 'tvshow':
        dbid = xbmc.getInfoLabel('ListItem.DBID')
    elif mediatype in ('season', 'episode'):
        dbid = xbmc.getInfoLabel('ListItem.TvShowDBID')
    else:
        dbid = ''
    return dbid

def check_condition():
    # logger.dbg()
    global path
    path = search_paths(get_id())
    return path


def get_menu_items():
    logger.debug('get menu item')
    if check_condition():
        items = [(config.get_localized_string(70269), update)]
        from core.videolibrarytools import read_nfo
        nfo = path + 'tvshow.nfo'
        item = read_nfo(nfo)[1]
        if item:
            item.nfo = nfo
            item_url = item.tourl()
            # Context menu: Automatically search for new episodes or not
            if item.active and int(item.active) > 0:
                update_text = config.get_localized_string(60022)
                value = 0
            else:
                update_text = config.get_localized_string(60023)
                value = 1
            items.append((update_text, lambda: xbmc.executebuiltin("RunPlugin(plugin://plugin.video.kod/?{}&title={}&action=mark_tvshow_as_updatable&channel=videolibrary&active={})".format(item_url, update_text, str(value)))))
            if item.local_episodes_path == "":
                items.append((config.get_localized_string(80048), lambda: xbmc.executebuiltin("RunPlugin(plugin://plugin.video.kod/?{}&action=add_local_episodes&channel=videolibrary&path={})".format(item_url, path))))
            else:
                items.append((config.get_localized_string(80049), lambda: xbmc.executebuiltin("RunPlugin(plugin://plugin.video.kod/?{}&action=remove_local_episodes&channel=videolibrary&path={})".format(item_url, path))))

        return items
    else:
        return []


def update():
    dbid = get_id()
    path = search_paths(dbid)
    if path:
        item = Item(action="update_tvshow", channel="videolibrary", path=path)
        # Why? I think it is not necessary, just commented
        # item.tourl()
        xbmc.executebuiltin("RunPlugin(plugin://plugin.video.kod/?" + item.tourl() + ")")
