import os
import pathlib
import cv2
import shutil
from config import *
from PIL import Image
import moviepy.editor as moviepy
from image_convert import get_nice_timestamp, convert_image


def slice_frames(path, skip_factor=2):
    vid_caption = cv2.VideoCapture(str(path))
    success, image = vid_caption.read()
    if VIDEO_ORIGIN_TMP in os.listdir():
        shutil.rmtree(VIDEO_ORIGIN_TMP)
    os.mkdir(VIDEO_ORIGIN_TMP)
    os.chdir(VIDEO_ORIGIN_TMP)
    frame_count = 1
    total_count = 1
    print("Slicing started")
    while success:
        if total_count % skip_factor == 0:
            cv2.imwrite(f"frame {frame_count}.jpg", image)
            frame_count += 1
        total_count += 1
        success, image = vid_caption.read()
    print("Slicing completed")
    os.chdir('..')
    return total_count, frame_count


def convert_frame(frame_path):
    img = Image.open(frame_path)
    return img


def make_video(result_frames, result_fps):
    img_array = []
    size = None
    for frame_i in range(1, result_frames):
        print(f'Adding {frame_i} of {result_frames} frame')

        filename = f'{VIDEO_RESULT_TMP}/frame {frame_i}.jpg'
        img = cv2.imread(filename)
        height, width, layers = img.shape
        size = (width, height)
        img_array.append(img)

    if MUTE_VIDEO_TMP in os.listdir():
        shutil.rmtree(MUTE_VIDEO_TMP)
    os.mkdir(MUTE_VIDEO_TMP)
    out = cv2.VideoWriter(f'{MUTE_VIDEO_TMP}/mute.avi', cv2.VideoWriter_fourcc(*'DIVX'), result_fps, size)

    for i in range(len(img_array)):
        out.write(img_array[i])
    out.release()

    print("Converting AVI to MP4")
    clip = moviepy.VideoFileClip(f'{MUTE_VIDEO_TMP}/mute.avi')
    clip.write_videofile(f'{MUTE_VIDEO_TMP}/mute.mp4')
    print("Video converted")


def extract_audio_from_original(path):
    print("Extracting audio")
    clip = moviepy.VideoFileClip(str(path))
    if VIDEO_SOUND_TMP in os.listdir():
        shutil.rmtree(VIDEO_SOUND_TMP)
    os.mkdir(VIDEO_SOUND_TMP)
    clip.audio.write_audiofile(f'{VIDEO_SOUND_TMP}/audio.mp3')
    print("Audio Extracted")


def add_audio_to_video():
    print("Adding audio to video")
    video_clip = moviepy.VideoFileClip(f'{MUTE_VIDEO_TMP}/mute.mp4')
    audio_clip = moviepy.AudioFileClip(f'{VIDEO_SOUND_TMP}/audio.mp3')

    new_audio_clip = moviepy.CompositeAudioClip([audio_clip])
    video_clip.audio = new_audio_clip
    video_clip.write_videofile(f'{OUTPUT}/{get_nice_timestamp()}.mp4')
    print("Audio added")


def clear_tmp():
    for some_dir in os.listdir():
        if some_dir.endswith('tmp'):
            shutil.rmtree(some_dir)


def convert_video(path, target_fps=25, matrix_size=(100, 100), image_size=(2000, 2000), random_score=50):
    vid_caption = cv2.VideoCapture(str(path))

    fps = vid_caption.get(cv2.CAP_PROP_FPS)
    print(f'Origin FPS: {fps}')
    skip_factor = round(fps / target_fps)
    origin_frames, result_frames = slice_frames(path, skip_factor=skip_factor)

    if VIDEO_RESULT_TMP in os.listdir():
        shutil.rmtree(VIDEO_RESULT_TMP)
    os.mkdir(VIDEO_RESULT_TMP)
    print("Converting frames")
    for frame_i in range(1, result_frames):
        print(f'Converting {frame_i} of {result_frames} frame')

        frame_file_path = f'{VIDEO_ORIGIN_TMP}/frame {frame_i}.jpg'
        convert_image(frame_file_path,
                      matrix_size=matrix_size,
                      image_size=image_size,
                      random_score=random_score,
                      save_path=f'{VIDEO_RESULT_TMP}/frame {frame_i}.jpg')
    print("All frames converted")

    result_fps = fps / (origin_frames / result_frames)
    make_video(result_frames, result_fps)

    extract_audio_from_original(path)
    add_audio_to_video()
    print("Video converted!")
    print("Clearing tmp")
    clear_tmp()
    print("Tmp cleaned")


if __name__ == '__main__':
    vid_paths = list(pathlib.Path(VIDEO_INPUT).iterdir())
    for vid_path in vid_paths:
        print(vid_path)
        convert_video(vid_path)
    # for frame_i in range(1, 3287):
    #     print(f'Resizing {frame_i} of {3287} frame')
    #     filename = f'{VIDEO_RESULT_TMP}/frame {frame_i}.jpg'
    #     img = Image.open(filename)
    #     img.thumbnail((1000, 1000), Image.ANTIALIAS)
    #     os.remove(filename)
    #     img.save(filename)
