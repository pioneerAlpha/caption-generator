import os
import whisper
import torch
from moviepy.editor import *
from mutagen.mp3 import MP3

BASE_DIR = "./outputs"
SUBTITLE = "Subtitle.srt"
BLANK_VIDEO = "Blank.mp4"
AUDIO_FILE = "IDANTZ+_Or_Amit_vows.mp3"
TRANSLATION = "Translation.txt"
VIDEO_WITH_ORIGINAL_AUDIO = "Video_with_original_audio.mp4"
FINAL_VIDEO = "Video_with_subtitle.mp4"


def format_timestamp(seconds: float, always_include_hours: bool = False, decimal_marker: str = '.'):
    assert seconds >= 0, "non-negative timestamp expected"
    milliseconds = round(seconds * 1000.0)

    hours = milliseconds // 3_600_000
    milliseconds -= hours * 3_600_000

    minutes = milliseconds // 60_000
    milliseconds -= minutes * 60_000

    seconds = milliseconds // 1_000
    milliseconds -= seconds * 1_000

    hours_marker = f"{hours:02d}:" if always_include_hours or hours > 0 else ""
    return f"{hours_marker}{minutes:02d}:{seconds:02d}{decimal_marker}{milliseconds:03d}"


def translate():
  
  device = "cuda" if torch.cuda.is_available() else "cpu"
  whisper_model = whisper.load_model("tiny", device=device)

  options = dict(beam_size=5, best_of=5)
  translate_options = dict(task="translate", **options)
  result = whisper_model.transcribe(AUDIO_FILE, **translate_options)
  return result


def generate_subtitle(segments):

    with open(os.path.join(BASE_DIR, SUBTITLE), 'w', encoding="utf-8") as f:
        for i, segment in enumerate(segments, start=1):
            f.write(
                f"{i}\n"
                f"{format_timestamp(segment['start'], always_include_hours=True, decimal_marker=',')} --> "
                f"{format_timestamp(segment['end'], always_include_hours=True, decimal_marker=',')}\n"
                f"{segment['text'].strip().replace('-->', '->')}\n")


def generate_blank_video():
    VIDEO_SIZE = (1280, 1280)
    color=(255,255,255)
    fps=25
    audio = MP3(AUDIO_FILE)
    duration = int(audio.info.length)
    ColorClip(size=VIDEO_SIZE, duration=duration, color=color).write_videofile(os.path.join(BASE_DIR, BLANK_VIDEO), fps=fps)


ext = os.path.splitext(AUDIO_FILE)[-1].lower()

if ext == ".mp3" or ext == ".wav":

    print("Translating")
    translated = translate()
    text = translated['text']
    segments = translated['segments']

    # saving the translated text
    print("Saving the translation")
    with open(os.path.join(BASE_DIR, TRANSLATION), 'w', encoding="utf-8") as file:
        file.write(text)


    #generating the subtitle
    print("Generating subtitle")
    generate_subtitle(segments=segments)

    #generating blank video
    print("Generating video")
    generate_blank_video()


    #Adding original audio to the blank video
    video_clip = VideoFileClip(os.path.join(BASE_DIR, BLANK_VIDEO))
    audio_clip = AudioFileClip(AUDIO_FILE)

    print("Adding original audio to the blank video")
    final_clip = video_clip.set_audio(audio_clip)
    final_clip.write_videofile(os.path.join(BASE_DIR, VIDEO_WITH_ORIGINAL_AUDIO)) 


    # Generating final video
    print("Generating final video")
    #For nvidia
    # os.system(f"ffmpeg -y -i {os.path.join(BASE_DIR, VIDEO_WITH_ORIGINAL_AUDIO)} -c:v h264_nvenc -vf subtitles={BASE_DIR + '/' + SUBTITLE} {os.path.join(BASE_DIR, FINAL_VIDEO)}")
    os.system(f"ffmpeg -y -i {os.path.join(BASE_DIR, VIDEO_WITH_ORIGINAL_AUDIO)} -c:v h264_amf -vf subtitles={BASE_DIR + '/' + SUBTITLE} {os.path.join(BASE_DIR, FINAL_VIDEO)}")
    
    #Removing unnecessary files
    print("Removing unnecessary files")
    os.remove(os.path.join(BASE_DIR, BLANK_VIDEO))
    os.remove(os.path.join(BASE_DIR, SUBTITLE))
    os.remove(os.path.join(BASE_DIR, VIDEO_WITH_ORIGINAL_AUDIO))

    print("Freeing the GPU memory")
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

else:
    print("File is not valid")



