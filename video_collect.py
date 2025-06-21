import os
import re
import argparse
from pytubefix import YouTube
from pytubefix.cli import on_progress
from pytubefix.exceptions import PytubeFixError

def find_best_stream_itags(yt, resolution='1080p', prefer_fps=60):
    """
    주어진 YouTube 객체와 해상도에서 가장 좋은 품질의 오디오 및 비디오 스트림의 itag를 찾습니다.

    Args:
        yt (YouTube): PytubeFix의 YouTube 객체.
        resolution (str): 원하는 비디오 해상도 (예: '1080p', '720p').
        prefer_fps (int): 선호하는 프레임레이트 (예: 60, 30).

    Returns:
        tuple: (audio_itag, video_itag)를 반환합니다. 스트림을 찾지 못하면 None을 반환합니다.
    """
    audio_itag = None
    video_itag = None

    # 1. 최고 품질의 오디오 스트림 찾기 (DASH 오디오)
    try:
        best_audio = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()
        if best_audio:
            audio_itag = best_audio.itag
            print(f"Found best audio stream: itag={audio_itag}, abr={best_audio.abr}")
        else:
            print("Warning: No MP4 audio stream found.")
    except Exception as e:
        print(f"Error finding audio stream: {e}")
        return None, None

    # 2. 지정된 해상도와 프레임레이트의 비디오 스트림 찾기
    fps_options = [prefer_fps, 30, 24] if prefer_fps == 60 else [prefer_fps, 60, 30, 24]
    
    for fps in fps_options:
        try:
            video_stream = yt.streams.filter(
                res=resolution, 
                fps=fps, 
                file_extension='mp4',
                progressive=False
            ).first()
            
            if video_stream:
                video_itag = video_stream.itag
                print(f"Found video stream: itag={video_itag}, resolution={resolution}, fps={fps}fps")
                break
        except Exception as e:
            print(f"Could not check for {resolution} at {fps}fps. Error: {e}")
            continue

    if not video_itag:
        print(f"Warning: Could not find any video stream for resolution '{resolution}'.")

    return audio_itag, video_itag

def download_from_youtube(url, output_path='downloads', resolution='1080p'):
    """
    Download the Video, Audio, and Subtitle from a single URL. 
    
    Args:
        url (str): The URL of the YouTube video to download. 
        output_path (str): The folder path where the downloaded files will be saved. 
        resolution (str): The desired video resolution (e.g., "720p", "1080p"). 
    """
    
    try:
        print(f"\nProcessing URL: {url}")
        yt = YouTube(url, on_progress_callback=on_progress)

        sanitized_title = re.sub(r'[\\/*?:"<>|]', "_", yt.title)
        video_specific_path = os.path.join(output_path, sanitized_title)
        
        print(f"Video Title: {yt.title}")
        print(f"Files will be saved to: {video_specific_path}")

        os.makedirs(video_specific_path, exist_ok=True)

        audio_itag, video_itag = find_best_stream_itags(yt, resolution)

        
        # Audio 
        if audio_itag:
            print(f"\nDownloading audio (itag: {audio_itag})...")
            audio_stream = yt.streams.get_by_itag(audio_itag)
            audio_stream.download(output_path=video_specific_path, filename_prefix="audio_")
            print("Audio download completed.")
        else:
            print("Skipping audio download as no suitable stream was found.")

        # Video 
        if video_itag:
            print(f"\nDownloading video (itag: {video_itag})...")
            video_stream = yt.streams.get_by_itag(video_itag)
            video_stream.download(output_path=video_specific_path, filename_prefix="video_")
            print("Video download completed.")
        else:
            print("Skipping video download as no suitable stream was found.")
            
        # Subtitle (En)
        print("\nChecking for subtitles...")                
        caption = yt.captions.get_by_language_code('en')

        if caption:
            print(f"Downloading subtitle: {caption.name} ({caption.code})")
            # Create subtitles in SRT format.
            srt_captions = caption.generate_srt_captions()
            
            # Save subtitle file 
            caption_filename = os.path.join(video_specific_path, f"subtitle_{caption.code}.srt")
            with open(caption_filename, "w", encoding="utf-8") as f:
                f.write(srt_captions)
            print(f"Subtitle saved to: {caption_filename}")
        else:
            print("English subtitles found.")

    except PytubeFixError as e:
        print(f"PytubeFix error for URL '{url}': {e}. This might be a private or deleted video.")
    except Exception as e:
        print(f"An unexpected error occurred for URL '{url}': {e}")


def main():
    """
    This is the main fuction for downloading videos, audios, and subtitles based on a list of URLs. 
    """
    
    parser = argparse.ArgumentParser(description="Download YouTube videos, audios, and subtitles from a list of URLs.")
    parser.add_argument('--output_dir', type=str, default='video_benchmark_data', help='Directory to save downloaded files.')
    parser.add_argument('--resolution', type=str, default='1080p', help='Target video resolution (e.g., 1080p, 720p).')
    parser.add_argument('--url_list', type=str, default='./list_URLs.txt', help='Path to the file containing YouTube URLs.')
    args = parser.parse_args()
    
    with open(args.url_list, 'r', encoding='utf-8') as f:
        youtube_urls = [line.strip() for line in f if line.strip()]
    
        
    target_resolution = args.resolution
    base_output_folder = args.output_dir


    print("--- Starting YouTube Video, Audio & Subtitle Download Process ---")
    for url in youtube_urls:
        download_from_youtube(url, output_path=base_output_folder, resolution=target_resolution)
        print("-" * 60)
    print("--- All downloads attempted. Process finished. ---")


if __name__ == '__main__':
    main()