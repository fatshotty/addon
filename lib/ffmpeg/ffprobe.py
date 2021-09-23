import subprocess,  os, platform
from platformcode import logger

from core import jsontools

def ffprobe_path():
  dirname = os.path.dirname(__file__)
  dirname = dirname.replace(' ', '\ ')
  # executable = os.path.join( dirname, '../../bin/ffprobe' )
  executable = os.path.join( dirname, '../../bin/ffmpeg_arm64' )
  # if platform.system() == 'Windows':
  #   executable = '{}.exe'.format( executable )
  # elif platform.system() == 'Android':
  #   executable = '{}_arm64'.format( executable )

  logger.info('platform: {} - script: {}'.format(platform.system(), executable))
  
  return executable



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
  except:
    if childproces == None:
      logger.error("Cannot execute ffprobe" )
    else:
      logger.error("Cannot use ffprobe - exit code is: {}".format(childproces.returncode) )
  


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