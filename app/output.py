from config import config
import subprocess

command = [ config.VIDEO.FFMPEG_BIN,
  '-y', # (optional) overwrite output file if it exists
  '-f', 'rawvideo',
  '-vcodec','rawvideo',
  '-s', str(config.WINDOW.WIDTH) + 'x' + str(config.WINDOW.HEIGHT), # size of one frame
  '-pix_fmt', 'rgba',
  '-r', '10', # frames per second
  '-i', '-', # The imput comes from a pipe
  '-f', 'x11grab',
  '-s', str(config.EMULATOR.WIDTH) + 'x' + str(config.EMULATOR.HEIGHT),
  '-r', '10',
  '-i', ':0.0',
  '-f', 'alsa',
  '-i', 'pulse',
  '-f', 'flv',
  '-r', '10',
  '-filter_complex', '[0:v][1:v]overlay=86:24[a]; [a][0:v]overlay=0:0',
  '-ac', '2',
  '-ar', '44100',
  '-vcodec', 'libx264',
  '-g', '20',
  '-keyint_min', '15',
  '-b', '900k',
  '-bufsize', '900k',
  '-minrate', '900k',
  '-maxrate', '900k',
  '-pix_fmt', 'yuv420p',
  '-crf', '30',
  '-force_key_frames', 'expr:gte(t,n_forced*2)',
  '-s', str(config.WINDOW.WIDTH) + 'x' + str(config.WINDOW.HEIGHT),
  '-preset', 'ultrafast',
  '-tune', 'film',
  '-acodec', 'libmp3lame',
  '-threads', '0',
  '-strict', 'normal',
  config.VIDEO.OUTPUT ]

output_stream_pipe = subprocess.Popen(command, stdin=subprocess.PIPE)
