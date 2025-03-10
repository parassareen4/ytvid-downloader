import yt_dlp

def download_video(url, save_path, quality="highest"):
    formats = {
        "highest": "bestvideo+bestaudio/best",
        "1080p": "bestvideo[height=1080]+bestaudio/best",
        "720p": "bestvideo[height=720]+bestaudio/best",
        "audio": "bestaudio"  # Audio only
    }

    if quality not in formats:
        print("Invalid quality option. Using highest quality.")
        quality = "highest"

    ydl_opts = {
        'format': formats[quality],  
        'outtmpl': f"{save_path}/%(title)s.%(ext)s",
        'merge_output_format': 'mp4' if quality != "audio" else 'mp3',  # Ensure MP4 for video, MP3 for audio
        'postprocessors': []
    }

    # Add FFmpeg processor for audio conversion if only downloading audio
    if quality == "audio":
        ydl_opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',  # Change to 'm4a' if you prefer
            'preferredquality': '192'
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# User inputs
url = input("Enter YouTube URL: ")
print("Select download option:\n1. Highest Quality\n2. 1080p\n3. 720p\n4. Audio Only")
choice = input("Enter choice (1/2/3/4): ")

quality_map = {
    "1": "highest",
    "2": "1080p",
    "3": "720p",
    "4": "audio"
}

quality = quality_map.get(choice, "highest")  # Default to highest if invalid input
save_path = "saved"

download_video(url, save_path, quality)
