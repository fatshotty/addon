# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertoolsV2
from lib import jsunpack
from platformcode import config, logger
import ast
from core import support

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url, cookies=False).data
    if 'File you are looking for is not found.' in data:
        return False, config.get_localized_string(70449) % "Onlystream"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    block = scrapertoolsV2.find_single_match(data, r'sources: \[([^\]]+)\]')
    sources = scrapertoolsV2.find_multiple_matches(block, r'file:\s*"([^"]+)"(?:,label:\s*"([^"]+)")?')
    for url, quality in sources:
        quality = 'auto' if not quality else quality
        video_urls.append(['.' + url.split('.')[-1] + ' [' + quality + '] [Onlystream]', url])
    video_urls.sort(key=lambda x: x[0].split()[1])
    return video_urls
