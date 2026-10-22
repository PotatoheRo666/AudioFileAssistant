import subprocess
import re
import imageio_ffmpeg

def test():
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    print("FFMPEG:", ffmpeg_exe)
    
    cmd_detect = [ffmpeg_exe, "-i", "test.mp3", "-af", "volumedetect", "-f", "null", "-"]
    # I don't have an mp3 file here, but let's test if the command format works if we use a dummy
    # Actually I can't test without an audio file easily, but the regex and command structure is standard.
