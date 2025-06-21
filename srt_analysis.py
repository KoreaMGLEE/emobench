import os
import openai
import json


def load_openai_api_key():
    """
    Load the OpenAI API key from the ../openai_key.txt file. 
    
    Returns:
        str: The API key if successful, or None if the file cannot be read. 
    """

    try:
        with open('../openai_key.txt', 'r', encoding='utf-8') as f:
            api_key = f.read().strip()
            if api_key:
                return api_key
            else:
                print("Error: API key file is empty.")
                return None
    except FileNotFoundError:
        print("Error: Could not find ../openai_key.txt file.")
        return None
    except Exception as e:
        print(f"Error reading API key file: {e}")
        return None

# API 키 로드 및 설정
api_key = load_openai_api_key()
if api_key:
    openai.api_key = api_key
else:
    print("Failed to load OpenAI API key. Please check ../openai_key.txt file.")
    exit(1)

def read_file_content(file_path):
    """
    Read and return the contents of the file at the specified path. 

    Args:
        file_path (str): Path for the file to read .

    Returns:
        str: The entire contents of the file.
    """
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"  [Error] Could not read file {file_path}: {e}")
        return None

def analyze_transcript_for_situation(srt_content, situation_description):
    """
    Analyze the timing of specific situations in the SRT subtitles using LLMs.

    Args:
        srt_content (str): The full contents of the SRT subtitles to analyze.
        situation_description (str): A description of the situation to detect.

    Returns:
        dict: A dictionary containing the analysis resutls, or None if an error occurs. 
    """

    system_prompt = (
        "You are an expert assistant specialized in video content analysis. "
        "Your task is to analyze video subtitles in SRT format and identify all time segments that match a specific situation. "
        "You must return the result in JSON format."
    )
    
    user_prompt = f"""
    Analyze the following SRT transcript to find all segments related to '{situation_description}'.
    This can include job interviews, expert Q&A sessions, testimonials, or any situation where one person is formally asking questions and another is providing detailed answers.

    Please return a JSON object with a single key "relevant_segments". The value should be an array of objects.
    Each object in the array must have the following keys:
    - "start_time": The start time of the relevant segment in "HH:MM:SS,ms" format.
    - "end_time": The end time of the relevant segment in "HH:MM:SS,ms" format.
    - "summary": A brief one-sentence summary explaining why this segment matches the situation.

    If no matching segments are found, return an empty array for the "relevant_segments" key.

    Here is the SRT transcript:
    ---
    {srt_content}
    ---
    """
    
    print("  Sending request to GPT-4o for analysis...")
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        analysis_result = json.loads(response.choices[0].message.content)
        print("  Analysis received successfully.")
        return analysis_result
    except Exception as e:
        print(f"  [Error] An error occurred while calling the OpenAI API: {e}")
        return None


def find_and_analyze_srt_files(base_directory, situation_description):
    """
    Traverse the directory to fine SRT files, then analyze each file. 
    

    Args:
        base_directory (str): Path for the root director where the search begins.
        situation_description (str): Description of the situation to detect.
    """
    print(f"--- Starting SRT analysis for '{situation_description}' in directory: {base_directory} ---")
    all_results = {}

    for dirpath, _, filenames in os.walk(base_directory):
        for filename in filenames:
            if filename.endswith(".srt"):
                srt_file_path = os.path.join(dirpath, filename)
                print(f"\nProcessing file: {srt_file_path}")

                srt_content = read_file_content(srt_file_path)
                if not srt_content:
                    continue

                analysis = analyze_transcript_for_situation(srt_content, situation_description)
                
                # Use the video folder name as the key of results
                video_folder_name = os.path.basename(dirpath)
                all_results[video_folder_name] = {
                    "source_srt": srt_file_path,
                    "analysis": analysis if analysis else {"error": "Failed to get analysis."}
                }
            
    # Save the final results to a JSON file.      
    output_filename = 'analysis_results.json'
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=4)
        print(f"\n--- Analysis complete. All results saved to '{output_filename}' ---")
    except Exception as e:
        print(f"\n[Error] Could not save results to {output_filename}: {e}")


def main():
    """
    This file analyzes SRT subtitle files in a given directory to detect and extract segments matching a specified situation (e.g., interviews).
    """
    
    
    # Specifiy the base folder where STT results saved 
    data_folder = 'video_benchmark_data'
    
    # Provide a description of the target situation to analyze. 
    target_situation = "Interview or interview (Q&A format)"
    
    if not os.path.isdir(data_folder):
        print(f"Error: The specified directory '{data_folder}' does not exist.")
        return
        
    if 'YOUR_OPENAI_API_KEY' in openai.api_key:
        print("Error: OpenAI API key is not set.")
        print("Please edit the script and replace 'YOUR_OPENAI_API_KEY' with your actual key.")
        return

    find_and_analyze_srt_files(data_folder, target_situation)


if __name__ == '__main__':
    main()
