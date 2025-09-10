import random
import subprocess
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

def convert_video_format(input_file, output_file, target_format="mp4", video_codec="libx264", audio_codec="aac",
                        frame_width=1080, frame_height=1920, frame_rate=29.97, bitrate="6M"):
    command = [
        "ffmpeg", "-y", "-i", input_file,
        "-c:v", video_codec,
        "-c:a", audio_codec,
        "-vf", f"scale={frame_width}:{frame_height}",
        "-r", str(frame_rate),
        "-b:v", bitrate,
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        output_file
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"[✓] Converted {input_file} -> {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"[✗] Conversion failed for {input_file}\nError: {e.stderr}")
        return None


def convert_video_format_parallel(input_files, target_format="mp4",
                                  frame_width=1080, frame_height=1920,
                                  frame_rate=30, bitrate="6M", max_workers=4):
    futures = []
    converted_files = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i, input_file in enumerate(input_files):
            output_file = f"temp_clip_{i}.{target_format}"
            future = executor.submit(
                convert_video_format,
                input_file, output_file, target_format,
                "libx264", "aac", frame_width, frame_height,
                frame_rate, bitrate
            )
            futures.append((future, output_file))

        for future, output_file in futures:
            result = future.result()
            if result:
                converted_files.append(result)
            else:
                print(f"[!] Skipping {output_file} due to error.")

    return converted_files


def combine_videos_ffmpeg(variables_dict, output_filename="combinedVideos.mp4", target_format="mp4",
                        frame_width=1080, frame_height=1920, frame_rate=29.97, bitrate="6M"):
    input_files = [f"Clip ({value}).mp4" for value in variables_dict.values()]
    if not input_files:
        print("Error: No valid input files found.")
        return

    print("🔄 Converting videos in parallel...")
    converted_files = convert_video_format_parallel(
        input_files,
        target_format=target_format,
        frame_width=frame_width,
        frame_height=frame_height,
        frame_rate=frame_rate,
        bitrate=bitrate,
        max_workers=min(8, len(input_files))
    )

    if not converted_files:
        print("❌ No videos were successfully converted.")
        return

    input_list_filename = "input_files.txt"
    output_path = os.path.abspath(output_filename)

    try:
        with open(input_list_filename, "w") as f:
            for converted_file in converted_files:
                f.write(f"file '{converted_file}'\n")
    except Exception as e:
        print(f"❌ Could not create input list file: {e}")
        return

    print("🎬 Combining videos...")

    command = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", input_list_filename,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-r", str(frame_rate),
        "-b:v", bitrate,
        "-avoid_negative_ts", "make_zero",
        output_path
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ Successfully combined videos into {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ ffmpeg command failed:\n{e.stderr}")
    finally:
        if os.path.exists(input_list_filename):
            os.remove(input_list_filename)
        for f in converted_files:
            if os.path.exists(f):
                os.remove(f)


if __name__ == "__main__":
    try:
        num_vars = int(input("Enter the number of videos to combine: "))
        variables = generate_variables(num_vars)
        print("\n🎲 Selected video clips:")
        print(variables)
        combine_videos_ffmpeg(
            variables,
            frame_width=1080,
            frame_height=1920,
            frame_rate=30,
            bitrate="6M"
        )
    except (ValueError, TypeError) as e:
        print(f"Error: {e}")



#  ________        ___          ___       __   ________  ________           ___  ___  _______   ________  _______
# |\   ____\      |\  \        |\  \     |\  \|\   __  \|\   ____\         |\  \|\  \|\  ___ \ |\   __  \|\  ___ \
# \ \  \___|      \ \  \       \ \  \    \ \  \ \  \|\  \ \  \___|_        \ \  \\\  \ \   __/|\ \  \|\  \ \   __/|
#  \ \  \       __ \ \  \       \ \  \  __\ \  \ \   __  \ \_____  \        \ \   __  \ \  \_|/_\ \   _  _\ \  \_|/__
#   \ \  \____ |\  \\_\  \       \ \  \|\__\_\  \ \  \ \  \|____|\  \        \ \  \ \  \ \  \_|\ \ \  \\  \\ \  \_|\ \
#    \ \_______\ \________\       \ \____________\ \__\ \__\____\_\  \        \ \__\ \__\ \_______\ \__\\ _\\ \_______\
#     \|_______|\|________|        \|____________|\|__|\|__|\_________\        \|__|\|__|\|_______|\|__|\|__|\|_______|
#                                                          \|_________|

                                                                              
