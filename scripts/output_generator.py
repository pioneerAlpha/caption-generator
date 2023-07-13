import os
import whisper
import torch
from moviepy.editor import *
from mutagen.mp3 import MP3
from mutagen.wave import WAVE


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


def get_model(model_sz):
    print("\nLoading whisper model")
    whisper_model = whisper.load_model(model_sz, device="cpu")
    print("Done loading whisper model\n")
    return whisper_model


def generate_transcribe(model, audio_file):

    print("\nGenerating transcribe")
    result = model.transcribe(audio_file)
    print("Done generating transcribe")

    text = result['text']

    print("\nSaving transcribe")
    transcribed = os.path.dirname(__file__) + "/../outputs/Transcribed.txt"
    with open(transcribed, "w", encoding="utf-8") as f:
        f.write(text)
        print("Done saving transcribe")


def generate_translation(model, audio_file:str):

    options = dict(beam_size=5, best_of=5)
    translate_options = dict(task="translate", **options)

    print("\nGenerating translation")
    result = model.transcribe(audio_file, **translate_options)
    print("Done generating translation")
    text = result['text']
    segments = result['segments']

    translated = os.path.dirname(__file__) + "/../outputs/Translated.txt"
    print("\nSaving translation")
    with open(translated, 'w', encoding="utf-8") as f:
        f.write(text)
        print("Done saving translation")

    print("\nSaving subtitle")
    subtitle = os.path.dirname(__file__) + "/../Subtitle.srt"
    with open(subtitle, 'w', encoding="utf-8") as f:
        for i, segment in enumerate(segments, start=1):
            f.write(
                f"{i}\n"
                f"{format_timestamp(segment['start'], always_include_hours=True, decimal_marker=',')} --> "
                f"{format_timestamp(segment['end'], always_include_hours=True, decimal_marker=',')}\n"
                f"{segment['text'].strip().replace('-->', '->')}\n")
        print("Done saving subtitle")
            

def generate_video(audio_file: str):

    if audio_file.endswith(".mp3"):
        audio = MP3(audio_file)
    else:
        audio = WAVE(audio_file)

    duration = int(audio.info.length) + 3
    video_size = (1400, 800)
    output_video = os.path.dirname(__file__) + "/../videos/Blank.mp4"
    fps=15
    color=(255,255,255)

    print("\nGenerating blank video")
    ColorClip(size=video_size, duration=duration, color=color).write_videofile(output_video, fps=fps)
    print("Done generating blank video")

    video_clip = VideoFileClip(output_video)
    audio_clip = AudioFileClip(audio_file)

    video_with_audio = os.path.dirname(__file__) + "/../videos/Video_with_audio.mp4"

    print("\nAdding voice to the blank video")
    final_clip = video_clip.set_audio(audio_clip)
    final_clip.write_videofile(video_with_audio)
    print("Done adding voice to the blank video")
    
    audio_file_name = audio_file.split("\\")[-1]
    audio_file_name = audio_file_name.split(".")[0].replace("%2B", "+")
    final_video = os.path.dirname(__file__) + f"/../outputs/{audio_file_name}.mp4"
    subtitle = "Subtitle.srt"

    print("\nGenerating the final video")
    os.system(f"""ffmpeg -y -i {video_with_audio} -c:v h264_amf -vf "subtitles={subtitle}:force_style='MarginV=50,Fontsize=20'" {final_video}""")
    print("Done generating the final video")




    
