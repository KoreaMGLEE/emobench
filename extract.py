import os
import json
from moviepy import VideoFileClip, AudioFileClip
import re

def srt_time_to_seconds(time_str):
    """Convert an SRT time string (HH:MM:SS,ms) to seconds"""    
    h, m, s_ms = time_str.split(':')
    s, ms = s_ms.split(',')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

def find_media_files(directory):
    """Find video and audio files in the specified directory."""
    video_file, audio_file = None, None
    for f in os.listdir(directory):
        if f.startswith("video_") and f.endswith(('.mp4', '.mkv', '.webm')):
            video_file = os.path.join(directory, f)
        elif f.startswith("audio_") and f.endswith(('.mp4', '.m4a', '.mp3')):
            audio_file = os.path.join(directory, f)
    return video_file, audio_file

def parse_srt_for_segment(srt_path, start_sec, end_sec):
    """Extract text from an SRT file within a specified time range"""
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse SRT blocks using regular expressions 
    srt_pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)\n\n', re.DOTALL)
    matches = srt_pattern.findall(content)
    
    segment_text = []
    for match in matches:
        start_time_sec = srt_time_to_seconds(match[1])
        end_time_sec = srt_time_to_seconds(match[2])
        text = match[3].replace('\n', ' ').strip()
        
        # Include all subtitle blocks that overlap with the given time range. 
        if max(start_sec, start_time_sec) < min(end_sec, end_time_sec):
            segment_text.append(text)
            
    return " ".join(segment_text)

def process_analysis_data(analysis_file, base_data_dir, output_dir, frame_interval=1):
    """
    Generate the final datasets by chunking the video, audio, and text according to the analysis results.
    """
    print(f"--- Starting data preprocessing from '{analysis_file}' ---")
    os.makedirs(output_dir, exist_ok=True)

    with open(analysis_file, 'r', encoding='utf-8') as f:
        all_results = json.load(f)

    for video_folder_name, result in all_results.items():
        analysis = result.get('analysis')
        if not analysis or "relevant_segments" not in analysis:
            print(f"\nSkipping '{video_folder_name}': No valid analysis found.")
            continue

        video_data_dir = os.path.join(base_data_dir, video_folder_name)
        srt_path = result.get('source_srt')
        
        # Load both video and audio files from the directory. 
        video_path, audio_path = find_media_files(video_data_dir)

        if not all([os.path.exists(video_data_dir), srt_path and os.path.exists(srt_path), video_path, audio_path]):
            print(f"\nSkipping '{video_folder_name}': Missing one or more source files (video, audio, srt).")
            continue

        print(f"\nProcessing video: {video_folder_name}")

        for i, segment in enumerate(analysis['relevant_segments']):
            try:
                start_time_str = segment['start_time']
                end_time_str = segment['end_time']
                
                start_sec = srt_time_to_seconds(start_time_str)
                end_sec = srt_time_to_seconds(end_time_str)

                segment_output_dir = os.path.join(output_dir, video_folder_name, f"segment_{i}")
                images_dir = os.path.join(segment_output_dir, "images")
                os.makedirs(images_dir, exist_ok=True)
                
                print(f"  Processing segment {i} ({start_time_str} -> {end_time_str})...")

                
                # 1. Extract frames from the video. 
                print(f"    - Extracting frames from '{os.path.basename(video_path)}'...")
                image_paths = []
                with VideoFileClip(video_path) as video_clip:
                    for t in range(int(start_sec), int(end_sec), frame_interval):
                        frame_filename = f"frame_{t:06d}.jpg"
                        frame_path = os.path.join(images_dir, frame_filename)
                        video_clip.save_frame(frame_path, t=t)
                        image_paths.append(frame_path)
                
                # 2. Trim audio from a separate audio file. 
                print(f"    - Slicing audio from '{os.path.basename(audio_path)}'...")
                sliced_audio_path = os.path.join(segment_output_dir, "audio.mp3")
                with AudioFileClip(audio_path) as audio_clip:
                    audio_subclip = audio_clip.subclipped(start_sec, end_sec)
                    audio_subclip.write_audiofile(sliced_audio_path, codec='mp3', logger=None)


                # 3. Trim the script. 
                print("    - Slicing transcript...")
                segment_transcript = parse_srt_for_segment(srt_path, start_sec, end_sec)

                # 4. Generate the metadata JSON file. 
                metadata = {
                    "original_video": video_folder_name,
                    "time_range_sec": {"start": start_sec, "end": end_sec},
                    "time_range_str": {"start": start_time_str, "end": end_time_str},
                    "transcript": segment_transcript,
                    "audio_path": sliced_audio_path,
                    "image_paths": image_paths,
                    "summary": segment.get("summary", "")
                }
                
                metadata_path = os.path.join(segment_output_dir, "metadata.json")
                with open(metadata_path, 'w', encoding='utf-8') as meta_f:
                    json.dump(metadata, meta_f, ensure_ascii=False, indent=4)

                print(f"  Segment {i} processed successfully. Data saved to: {segment_output_dir}")

            except Exception as e:
                print(f"  [Error] Failed to process segment {i} for '{video_folder_name}': {e}")
    
    print("\n--- All data processing complete. ---")


def main():
    """
    Main function that orchestrates the data extraction pipeline.

    - Extract frames, slice audio, trim transcripts, and generate metadata for each video segment as specified in the analysis file.
    """
    analysis_file = 'analysis_results.json'
    base_data_dir = 'video_benchmark_data'
    output_dir = 'processed_benchmark_data'
    
    if not os.path.exists(analysis_file):
        print(f"Error: Analysis file '{analysis_file}' not found.")
        print("Please run the situation analyzer script first.")
        return

    process_analysis_data(analysis_file, base_data_dir, output_dir, frame_interval=1)


if __name__ == '__main__':
    main()
