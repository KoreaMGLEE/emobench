import os
import re
import openai
from pydub import AudioSegment
import tempfile
import math
from datetime import timedelta
from dotenv import load_dotenv


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

def transcribe_single_chunk(chunk_path):
    """    
    Transcribe a single audio file into text using the Whisper API.
    
    Args:
        chunk_path (str): Path for the audio chunck file.

    Returns:
        str or None: The transcribed subtitle in SRT format. Return None if an error occurs. 
    """

    try:
        with open(chunk_path, "rb") as audio_file:
            # Request that timestamp information be returned in 'SRT' format.
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="srt"
            )
        return transcript
    except Exception as e:
        print(f"  [Error] Could not transcribe chunk {os.path.basename(chunk_path)}. Error: {e}")
        return None

def offset_srt(srt_content, offset_ms):
    """
    Adjust the timestamps in the SRT subtitles by the given offset.


    Args:
        srt_content (str): The original SRT subtitle content. 
        offset_ms (int): The time offset in milliseconds to apply.

    Returns:
        list: A list of SRT blocks adjusted timestamps.
    """
    

    offset = timedelta(milliseconds=offset_ms)
    srt_blocks = srt_content.strip().split('\n\n')
    adjusted_blocks = []

    for block in srt_blocks:
        lines = block.split('\n')
        if len(lines) < 2:
            continue
        
        time_line = lines[1]
        start_str, end_str = time_line.split(' --> ')
                
        # Parse SRT timestamps and return them as timedelta objects. 
        start_time = datetime_from_srt_time(start_str)
        end_time = datetime_from_srt_time(end_str)

        # Apply the offsets. 
        new_start = start_time + offset
        new_end = end_time + offset
        
        # Return the result in SRT formats. 
        lines[1] = f"{format_timedelta_to_srt(new_start)} --> {format_timedelta_to_srt(new_end)}"
        adjusted_blocks.append('\n'.join(lines))
        
    return adjusted_blocks

def datetime_from_srt_time(time_str):    
    """Convert an SRT time sequence to a timedelta object"""
    h, m, s_ms = time_str.split(':')
    s, ms = s_ms.split(',')
    return timedelta(hours=int(h), minutes=int(m), seconds=int(s), milliseconds=int(ms))

def format_timedelta_to_srt(td):
    """ Format a timedelta object as an SRT time sequence."""
    total_seconds = int(td.total_seconds())
    ms = int(td.microseconds / 1000)
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def transcribe_large_audio(file_path, chunk_length_ms=60000):
    """
    Split a long audio file into multiple small chunck, perform STT sequentially on each chunk, 
    adjust their timestamps, and finally merge them into a single SRT file. 
    """
    print(f"  Loading audio file: {os.path.basename(file_path)}")
    try:
        audio = AudioSegment.from_file(file_path)
    except Exception as e:
        print(f"  [Error] Could not load audio file. Make sure ffmpeg is installed. Error: {e}")
        return None

    num_chunks = math.ceil(len(audio) / chunk_length_ms)
    print(f"  Audio duration: {len(audio) / 1000:.2f}s. Splitting into {num_chunks} chunk(s).")
    
    full_srt_blocks = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        for i in range(num_chunks):
            start_ms = i * chunk_length_ms
            end_ms = start_ms + chunk_length_ms
            chunk = audio[start_ms:end_ms]
            
            chunk_file_path = os.path.join(temp_dir, f"chunk_{i}.mp3")
            chunk.export(chunk_file_path, format="mp3")
            
            print(f"  Transcribing chunk {i+1}/{num_chunks}...")
            srt_chunk_content = transcribe_single_chunk(chunk_file_path)
            
            if srt_chunk_content:            
                # Adjust the timestamps based on the start time of the current chunck.                 
                adjusted_blocks = offset_srt(srt_chunk_content, start_ms)
                full_srt_blocks.extend(adjusted_blocks)
    
    
    # Renumber all SRT blocks sequentially    
    final_srt_content = []
    for i, block in enumerate(full_srt_blocks, 1):
        lines = block.split('\n')
        lines[0] = str(i) 
        final_srt_content.append('\n'.join(lines))

    print("  All chunks transcribed. Combining results into a single SRT file.")
    return "\n\n".join(final_srt_content)


def process_audio_files_in_directory(base_directory):
    """    
    Traverse the given directory and its sub-directories to find audio files and perform STT.
    """
    print(f"--- Starting STT process in directory: {base_directory} ---")
    for dirpath, _, filenames in os.walk(base_directory):
        # if 'devil' not in filenames
        for filename in filenames:
            if filename.startswith("audio_") and filename.endswith(('.mp4', '.m4a', '.mp3', '.webm')):
                audio_file_path = os.path.join(dirpath, filename)
                # Rename the result file to have a .srt extension 
                transcript_filename = os.path.splitext(audio_file_path)[0] + ".srt"

                if os.path.exists(transcript_filename):
                    print(f"Skipping '{filename}', transcript file already exists.")
                    continue

                print(f"\nProcessing audio file: {audio_file_path}")
                
                transcribed_srt = transcribe_large_audio(audio_file_path)

                if transcribed_srt:
                    try:
                        with open(transcript_filename, "w", encoding="utf-8") as f:
                            f.write(transcribed_srt)
                        print(f"  Saved full transcript to: {transcript_filename}")
                    except Exception as e:
                        print(f"  [Error] Could not write transcript to file: {e}")

    print("\n--- STT process finished for all found audio files. ---")


def main():
    """
    Checks prerequisites (data folder existence and OpenAI API key),
    then processes all audio files in the data folder and its subdirectories,
    transcribing them to SRT subtitle files using the Whisper API.
    """
    
    
    video_data_folder = 'video_benchmark_data'
    
    if not os.path.isdir(video_data_folder):
        print(f"Error: The specified directory '{video_data_folder}' does not exist.")
        return
        
    if 'YOUR_OPENAI_API_KEY' in openai.api_key:
        print("Error: OpenAI API key is not set.")
        print("Please edit the script and replace 'YOUR_OPENAI_API_KEY' with your actual key.")
        return

    process_audio_files_in_directory(video_data_folder)


if __name__ == '__main__':
    main()
