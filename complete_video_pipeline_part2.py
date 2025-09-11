# Additional functions for complete_video_pipeline.py
# This file contains the remaining helper functions

def generate_sequence_with_custom_mapping(
    csv_file: str,
    field_mapping: Dict[str, str],
    category_filters: Dict[str, List[str]],
    sequence_length: int,
    min_spacing: int,
    output_file: str
) -> bool:
    """Generate a sequence using custom field mappings."""
    try:
        print(f"📊 Loading clips from {csv_file}...")
        
        # Load and filter clips based on category selections
        clips = []
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Check if this clip matches our category filters
                matches = True
                for column_name, allowed_values in category_filters.items():
                    if column_name in row:
                        if row[column_name].strip() not in allowed_values:
                            matches = False
                            break
                    else:
                        matches = False
                        break
                
                if matches:
                    clips.append({
                        'unique_id': row[field_mapping['unique_id']].strip(),
                        'name': row[field_mapping['name']].strip(),
                        'category': row[field_mapping['category_1']].strip()
                    })
        
        print(f"✅ Found {len(clips)} clips matching your criteria")
        
        if len(clips) < sequence_length:
            print(f"⚠️  Warning: Only {len(clips)} clips available, but {sequence_length} requested")
            print(f"   Generating sequence with available clips...")
            sequence_length = len(clips)
        
        # Group clips by category
        clips_by_category = {}
        for clip in clips:
            category = clip['category']
            if category not in clips_by_category:
                clips_by_category[category] = []
            clips_by_category[category].append(clip)
        
        print(f"📋 Clips by category:")
        for category, category_clips in clips_by_category.items():
            print(f"   {category}: {len(category_clips)} clips")
        
        # Generate sequence with spacing constraints
        print(f"🎲 Generating randomized sequence with {min_spacing} minimum spacing...")
        sequence = generate_spaced_sequence(clips_by_category, sequence_length, min_spacing)
        
        if not sequence:
            print(f"❌ Could not generate sequence with current constraints")
            return False
        
        # Write output CSV
        print(f"💾 Writing sequence to {output_file}...")
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Write header
            writer.writerow(['item_no', 'unique_id', 'name', 'category'])
            
            # Write sequence
            for i, clip in enumerate(sequence, 1):
                writer.writerow([
                    i,
                    clip['unique_id'],
                    clip['name'],
                    clip['category']
                ])
        
        print(f"✅ Successfully generated {len(sequence)} clip sequence!")
        return True
        
    except Exception as e:
        print(f"❌ Error generating sequence: {e}")
        return False

def generate_spaced_sequence(clips_by_category: Dict[str, List], target_length: int, min_spacing: int) -> List[Dict]:
    """Generate a sequence with minimum spacing between same categories."""
    if not clips_by_category:
        return []
    
    # Create a pool of all clips
    all_clips = []
    for category_clips in clips_by_category.values():
        all_clips.extend(category_clips)
    
    if len(all_clips) < target_length:
        target_length = len(all_clips)
    
    # Simple approach: try multiple times to generate a valid sequence
    for attempt in range(100):  # Try up to 100 times
        sequence = []
        available_clips = all_clips.copy()
        random.shuffle(available_clips)
        
        for _ in range(target_length):
            # Find a clip that satisfies spacing constraint
            for i, clip in enumerate(available_clips):
                if can_place_clip(sequence, clip, min_spacing):
                    sequence.append(clip)
                    available_clips.pop(i)
                    break
            else:
                # No valid clip found, try next attempt
                break
        
        if len(sequence) == target_length:
            return sequence
    
    # If we couldn't generate full sequence with spacing, generate without strict spacing
    print(f"⚠️  Could not maintain {min_spacing} spacing for all clips, using best effort...")
    random.shuffle(all_clips)
    return all_clips[:target_length]

def can_place_clip(sequence: List[Dict], clip: Dict, min_spacing: int) -> bool:
    """Check if a clip can be placed at the end of sequence with spacing constraint."""
    if not sequence:
        return True
    
    category = clip['category']
    
    # Check last min_spacing positions
    check_positions = min(len(sequence), min_spacing)
    for i in range(check_positions):
        if sequence[-(i+1)]['category'] == category:
            return False
    
    return True

# Video concatenation functions
def get_video_location() -> str:
    """Ask user for video directory and validate it exists."""
    while True:
        print("\n📁 VIDEO LOCATION SELECTION")
        print("-" * 30)
        video_dir = input("Enter path to your processed videos directory: ").strip()
        
        if not video_dir:
            print("❌ Please enter a directory path.")
            continue
            
        if not os.path.exists(video_dir):
            print(f"❌ Directory '{video_dir}' not found.")
            continue
            
        if not os.path.isdir(video_dir):
            print(f"❌ '{video_dir}' is not a directory.")
            continue
            
        # Check if directory has video files
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
        video_files = []
        for file in os.listdir(video_dir):
            if Path(file).suffix.lower() in video_extensions:
                video_files.append(file)
        
        if not video_files:
            print(f"⚠️  No video files found in '{video_dir}'")
            response = input("Continue anyway? (y/n): ").lower().strip()
            if response != 'y':
                continue
        else:
            print(f"✅ Found {len(video_files)} video files in directory")
        
        return video_dir

def load_sequence_list(csv_file: str) -> List[Dict]:
    """Load sequence list from CSV file."""
    sequence = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                sequence.append({
                    'item_no': int(row['item_no']),
                    'unique_id': row['unique_id'].strip(),
                    'name': row['name'].strip(),
                    'category': row.get('category', '').strip()
                })
        return sequence
    except Exception as e:
        print(f"❌ Error loading sequence: {e}")
        return []

def find_video_files(video_dir: str, sequence: List[Dict]) -> Tuple[List[str], List[Dict]]:
    """Find video files matching the sequence list."""
    print(f"\n🔍 FINDING VIDEO FILES")
    print("-" * 30)
    
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
    found_videos = []
    missing_items = []
    
    # Get all video files in directory
    all_video_files = {}
    for file in os.listdir(video_dir):
        if Path(file).suffix.lower() in video_extensions:
            # Use filename without extension as key
            name_key = Path(file).stem
            all_video_files[name_key] = file
    
    print(f"📁 Found {len(all_video_files)} video files in directory")
    
    # Match sequence items to video files
    for item in sequence:
        name = item['name']
        unique_id = item['unique_id']
        
        # Try different matching strategies
        video_file = None
        
        # Strategy 1: Exact name match
        if name in all_video_files:
            video_file = all_video_files[name]
        
        # Strategy 2: Exact unique_id match
        elif unique_id in all_video_files:
            video_file = all_video_files[unique_id]
        
        # Strategy 3: Partial name match
        else:
            for file_key, file_name in all_video_files.items():
                if name in file_key or file_key in name:
                    video_file = file_name
                    break
        
        # Strategy 4: Partial unique_id match
        if not video_file:
            for file_key, file_name in all_video_files.items():
                if unique_id in file_key or file_key in unique_id:
                    video_file = file_name
                    break
        
        if video_file:
            video_path = os.path.join(video_dir, video_file)
            found_videos.append(video_path)
            print(f"✅ {item['item_no']:3d}. Found: {video_file}")
        else:
            missing_items.append(item)
            print(f"❌ {item['item_no']:3d}. Missing: {name} (ID: {unique_id})")
    
    return found_videos, missing_items

def get_output_settings() -> Dict:
    """Get output file settings from user."""
    print(f"\n⚙️  OUTPUT SETTINGS")
    print("-" * 30)
    
    # Output filename
    while True:
        output_file = input("Output video filename (default: final_video.mp4): ").strip()
        if not output_file:
            output_file = "final_video.mp4"
        
        if not output_file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            output_file += '.mp4'
        
        # Check if file exists
        if os.path.exists(output_file):
            response = input(f"File '{output_file}' exists. Overwrite? (y/n): ").lower().strip()
            if response == 'y':
                break
        else:
            break
    
    # Video quality settings
    print(f"\nVideo quality options:")
    print(f"   1. High quality (slower, larger file)")
    print(f"   2. Medium quality (balanced)")
    print(f"   3. Fast encoding (faster, larger file)")
    
    while True:
        choice = input("Select quality option (1-3, default: 2): ").strip()
        if not choice:
            choice = '2'
        
        if choice in ['1', '2', '3']:
            break
        print("❌ Please enter 1, 2, or 3")
    
    quality_settings = {
        '1': ['-c:v', 'libx264', '-preset', 'slow', '-crf', '18'],
        '2': ['-c:v', 'libx264', '-preset', 'medium', '-crf', '23'],
        '3': ['-c:v', 'libx264', '-preset', 'fast', '-crf', '23']
    }
    
    return {
        'output_file': output_file,
        'ffmpeg_args': quality_settings[choice]
    }

def concatenate_videos(video_files: List[str], output_settings: Dict) -> bool:
    """Concatenate videos using FFmpeg."""
    if not video_files:
        print("❌ No video files to concatenate")
        return False
    
    print(f"\n🎬 CONCATENATING VIDEOS")
    print("-" * 30)
    print(f"📹 Processing {len(video_files)} videos...")
    print(f"📁 Output: {output_settings['output_file']}")
    
    try:
        # Create temporary file list for FFmpeg
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            for video_file in video_files:
                # Convert to absolute path and escape for FFmpeg
                abs_path = os.path.abspath(video_file)
                # Escape backslashes for Windows paths and single quotes
                escaped_path = abs_path.replace('\\', '/').replace("'", "'\"'\"'")
                temp_file.write(f"file '{escaped_path}'\n")
            temp_file_path = temp_file.name
        
        # Build FFmpeg command
        ffmpeg_cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', temp_file_path,
        ] + output_settings['ffmpeg_args'] + [
            '-y',  # Overwrite output file
            output_settings['output_file']
        ]
        
        print(f"🔄 Running FFmpeg concatenation...")
        
        # Run FFmpeg
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        if result.returncode == 0:
            print(f"✅ Successfully created: {output_settings['output_file']}")
            
            # Show file size
            if os.path.exists(output_settings['output_file']):
                file_size = os.path.getsize(output_settings['output_file'])
                size_mb = file_size / (1024 * 1024)
                print(f"📊 Output file size: {size_mb:.1f} MB")
            
            return True
        else:
            print(f"❌ FFmpeg failed with return code: {result.returncode}")
            print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ FFmpeg timed out after 1 hour")
        return False
    except Exception as e:
        print(f"❌ Error during concatenation: {e}")
        return False
