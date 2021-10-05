# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# XBMC entry point
# ------------------------------------------------------------

import os
import sys

import xbmc

# functions that on kodi 19 moved to xbmcvfs
try:
    import xbmcvfs
    xbmc.translatePath = xbmcvfs.translatePath
    xbmc.validatePath = xbmcvfs.validatePath
    xbmc.makeLegalFilename = xbmcvfs.makeLegalFilename
except:
    pass
from platformcode import config, logger
import platform

logger.info("init...")
logger.info('python version {}'.format(sys.version))

librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
sys.path.insert(0, librerias)

from platformcode import launcher

# logger.info('start ABI')
# import abi
# binmodule = abi.load("plugin.video.kod", "_core")
# logger.info('END ABI {}'.format( dir(binmodule) ) )





# container_video = av.open('http://techslides.com/demos/sample-videos/small.mp4')
# logger.info( 'bitrate: {}'.format(container_video.bit_rate) )
# video = container_video.streams.video[0]
# logger.info( 'video {}'.format(video.codec_context.codec.name))


if sys.argv[2] == "":
    launcher.start()

launcher.run()
