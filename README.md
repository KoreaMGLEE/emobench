# EmoBench Video Analysis Project

This is a Python-based analysis pipeline that collects videos from a given list of YouTube URLs and sequentially performs Speech-to-Text (STT), subtitle analysis, and data extraction.

## Prerequisites

To run this project, you must have [Docker](https://www.docker.com/get-started/) installed on your machine.

## Key File Structure

* `list_URLs.txt`: A text file where you list the YouTube video URLs to be analyzed.
* `openai_key.txt`: A text file containing your OpenAI API key (required for STT and analysis).
* `video_collect.py`: A script that reads the URLs from `list_URLs.txt` and collects the corresponding videos.
* `stt.py`: A script that extracts audio from the collected videos and performs Speech-to-Text (STT) to generate subtitles.
* `srt_analysis.py`: A script for analyzing the generated subtitle (SRT) files.
* `extract.py`: A script that extracts the final data based on the analysis results.

## Installation and Setup

This project provides a consistent development environment using Docker. Follow the steps below to set up and run the environment.

1.  **Download the Project**
    Prepare the project folder on your local machine (e.g., by using `git clone` or downloading a zip file).

2.  **Navigate to the Project Directory**
    ```bash
    cd emobench
    ```

3.  **Set up OpenAI API Key**
    Create a file named `openai_key.txt` in the project root and add your OpenAI API key:
    ```bash
    echo "your-openai-api-key-here" > openai_key.txt
    ```
    **Note**: You need an OpenAI API key to use the Whisper (STT) and GPT-4 (analysis) services.

4.  **Prepare YouTube URLs**
    Edit the `list_URLs.txt` file and add YouTube video URLs, one per line:
    ```
    https://www.youtube.com/watch?v=example1
    https://www.youtube.com/watch?v=example2
    ```

5.  **Build the Docker Image**
    From the root of the project directory, run the following command to build the Docker image. This process automatically configures the execution environment, including all Python packages specified in `requirements.txt`.
    ```bash
    docker build -t emobench-python-app .
    ```

6.  **Run the Docker Container**
    Execute the command below to run the container and access its internal bash shell. This will also mount your current project directory to the `/app` directory inside the container, allowing for real-time file synchronization.
    ```bash
    docker run -it -v $(pwd):/app emobench-python-app
    ```
    Once the command prompt changes to something like `root@...:/app#`, you have successfully connected to the container's environment.

## Usage

Follow the steps below in order to run the project.

#### Step 1: Prepare the Input Data

Before or after starting the container, open the `list_URLs.txt` file **on your local machine** and enter the YouTube video URLs you wish to analyze, one URL per line. Save the file. (Changes will be reflected inside the container instantly due to real-time synchronization).

#### Step 2: Sequentially Execute Scripts Inside the Container

While connected to the container (with the `root@...:/app#` prompt), run the following scripts **in the specified order**. Each script uses the output from the previous step as its input.

```bash
# 1. Collect YouTube videos
python video_collect.py

# 2. Extract audio and perform STT
python stt.py

# 3. Analyze subtitle files
python srt_analysis.py

# 4. Extract final data
python extract.py
```

## Configuration Options

### Video Collection (`video_collect.py`)
```bash
python video_collect.py --output_dir video_benchmark_data --resolution 1080p --url_list list_URLs.txt
```
- `--output_dir`: Directory to save downloaded files (default: `video_benchmark_data`)
- `--resolution`: Video resolution (default: `1080p`)
- `--url_list`: Path to file containing YouTube URLs (default: `list_URLs.txt`)

## Output Structure

After running all scripts, you'll find the following structure:

```
processed_benchmark_data/
└── video_name/
    └── segment_0/
        ├── images/
        │   ├── frame_000001.jpg
        │   ├── frame_000002.jpg
        │   └── ...
        ├── audio.mp3
        └── metadata.json
```

### Key Output Files:
- `analysis_results.json`: Contains detected interview segments with timestamps
- `processed_benchmark_data/`: Final extracted data organized by video and segment
- `video_benchmark_data/`: Raw downloaded videos and generated SRT files


## Dependencies

### Python Packages
- `moviepy==2.2.1` - Video processing and frame extraction
- `openai==1.90.0` - OpenAI API client for GPT-4 and Whisper
- `pydub==0.25.1` - Audio processing
- `pytubefix==9.2.0` - YouTube video downloading
- `ffmpeg-python==0.2.0` - FFmpeg integration via pip

### System Dependencies
- Python 3.10+ - Runtime environment
- FFmpeg (installed via pip in Docker, may need system installation for local use)
