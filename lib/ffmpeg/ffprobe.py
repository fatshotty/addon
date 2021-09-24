import subprocess,  os, platform
from platformcode import logger
import tempfile
import shutil

from core import jsontools

def ffprobe_path():

  TEMP_DIR = None

  try:
      import xbmc
      TEMP_DIR = xbmc.translatePath("special://temp/")
      logger.info('use kodi for tempdir: {}'.format(TEMP_DIR) )
  except:
      TEMP_DIR = os.getenv("TEMP") or os.getenv("TMP") or os.getenv("TMPDIR")
      logger.info('use ENV for tempdir: {}'.format(TEMP_DIR) )

  executable = 'ffmpeg_arm64'
  # executable = os.path.join( dirname, '../../bin/ffprobe' )
  # if platform.system() == 'Windows':
  #   executable = '{}.exe'.format( executable )
  # elif platform.system() == 'Android':
  #   executable = '{}_arm64'.format( executable )

  # move file into tempfolder
  logger.info('tempdir is: {}'.format(TEMP_DIR))
  temporaryfile = os.path.join(TEMP_DIR, executable)
  logger.info('tempfile is: {}'.format(temporaryfile))

  if not os.path.exists(temporaryfile):

    logger.info('executable temp not exists, copy to temp')

    dirname = os.path.dirname(__file__)
    dirname = dirname.replace(' ', '\ ')

    fullexepath = os.path.abspath( os.path.join( dirname, '../../bin/', executable ) )

    logger.info('Original exe is: {}'.format(fullexepath) )

    shutil.copy(fullexepath, temporaryfile)

  status = os.stat(temporaryfile)
  permissions = oct(status.st_mode)
  logger.info('current permission: {}'.format(permissions) )

  os.chmod(temporaryfile, 0o755)
  status = os.stat(temporaryfile)
  permissions = oct(status.st_mode)

  logger.info('platform: {} - script: {} - perm: {}'.format(platform.system(), temporaryfile, permissions))
  
  return temporaryfile



def get_metadata_from_url(url):
  
  # ffmpegpath = os.path.join(os.path.dirname(__file__), '../bin/ffprobe')
  # '/Users/fatshotty/Library/Application\ Support/Kodi/addons/plugin.video.kod/core/../bin/ffprobe'
  ffmpegpath = ffprobe_path()
  command = '{} -i "{}"'.format(ffmpegpath, url)

  logger.info("COMMAND new path: {}".format(command) )
  
  childproces = None
  try:
    childproces = subprocess.run(command, shell=True, capture_output=True, check=True)
    logger.info("RET-CODE: {}".format(childproces.returncode) )
    response = childproces.stdout
    # logger.info(response)
    responsestr = response.decode('utf-8')
    logger.info("RET-STR: {}".format(responsestr) )
    json = jsontools.load(responsestr)
    return parse_response(json)
  except Exception  as ex:
    if childproces == None:
      logger.error("Cannot execute ffprobe", ex)
    else:
      logger.error("Cannot use ffprobe - exit code is: {}".format(childproces.returncode), ex )
    raise ex
  


def parse_response(data):
  response = {'video': {}, 'audio': [], 'duration': 0, 'raw': data}

  if 'streams' in data:
    streams = data['streams']

    for stream in streams:
      if 'codec_type' in stream:
        if stream['codec_type'] == 'video':
          response['video']['codec'] = stream['codec_name']
          response['video']['width'] = stream['width']
          response['video']['height'] = stream['height']
          response['video']['aspect_ratio'] = stream['display_aspect_ratio']
          # if 'tags' in stream and 'variant_bitrate' in stream['tags']:
            # audio['bitrate'] = stream['tags']['variant_bitrate']
            
        elif stream['codec_type'] == 'audio':
          audio =  {}
          audio['codec'] = stream['codec_name']
          audio['sample_rate'] = stream['sample_rate']
          audio['channels'] = stream['channels']
          response['audio'].append( audio )
          # if 'tags' in stream and 'variant_bitrate' in stream['tags']:
            # audio['bitrate'] = stream['tags']['variant_bitrate']
  
  if 'format' in data:
    if 'duration' in data['format']:
      response['duration'] = data['format']['duration']
  
  return response