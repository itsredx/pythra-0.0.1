# media_scanner.py (High-Performance Version)

import subprocess
import json
from pathlib import Path
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

SUPPORTED_EXTENSIONS = {".mp3", ".m4a", ".flac", ".aac", ".ogg", ".wav", ".mp4"}

def _process_single_file(args):
    """
    Processes a single media file. Designed to be run in a parallel thread.
    Takes a tuple of arguments to be compatible with executor.map.
    """
    file_path, artwork_cache_dir, fallback_artwork_path = args
    
    # 1. Get Raw Metadata
    try:
        command = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", str(file_path)
        ]
        result = subprocess.run(command, check=True, capture_output=True, encoding='utf-8', errors='ignore')
        raw_meta = json.loads(result.stdout) if result.stdout else {}
    except Exception:
        raw_meta = {}

    if not raw_meta or 'format' not in raw_meta:
        return None # Indicate failure

    # 2. Extract Artwork
    artwork_path = None
    try:
        file_hash = hashlib.sha1(str(file_path.resolve()).encode()).hexdigest()
        artwork_path_candidate = artwork_cache_dir / f"{file_hash}.jpg"
        if not artwork_path_candidate.exists():
            command_art = ['ffmpeg', '-i', str(file_path), '-an', '-vcodec', 'copy', '-y', str(artwork_path_candidate)]
            subprocess.run(command_art, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        artwork_path = artwork_path_candidate
    except Exception:
        artwork_path = fallback_artwork_path
    
    # 3. Assemble Song Data
    tags = raw_meta.get('format', {}).get('tags', {})
    duration_s = float(raw_meta.get('format', {}).get('duration', 0.0))
    track_str = tags.get('track', '0')
    try:
        track_num = int(track_str.split('/')[0])
    except (ValueError, IndexError):
        track_num = 0

    return {
        "path": str(file_path.resolve()),
        "mtime": file_path.stat().st_mtime, # Store modification time for caching
        "title": tags.get('title', file_path.stem),
        "artist": tags.get('artist', 'Unknown Artist'),
        "album": tags.get('album', 'Unknown Album'),
        "genre": tags.get('genre', 'Unknown Genre'),
        "track_num": track_num,
        "duration_s": duration_s,
        "artwork_path": str(artwork_path.resolve()) if artwork_path else None
    }

def scan_media_library(
    library_path: str | Path,
    artwork_cache_dir: str | Path,
    library_cache_file: str | Path,
    fallback_artwork_path: str | Path | None = None,
    force_rescan: bool = False
) -> list[dict]:
    """
    Scans a library using caching and parallelism for high performance.
    """
    library_path = Path(library_path)
    artwork_cache_dir = Path(artwork_cache_dir)
    library_cache_file = Path(library_cache_file)

    artwork_cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Validate fallback artwork
    valid_fallback_path = None
    if fallback_artwork_path:
        fb_path = Path(fallback_artwork_path)
        if fb_path.is_file(): valid_fallback_path = fb_path

    # --- Caching Logic ---
    cached_songs = {}
    if library_cache_file.exists() and not force_rescan:
        print("Loading library from cache...")
        with open(library_cache_file, 'r', encoding='utf-8') as f:
            try:
                # Create a lookup dictionary for fast access
                cached_data = json.load(f)
                cached_songs = {item['path']: item for item in cached_data}
            except json.JSONDecodeError:
                print("Warning: Cache file is corrupt. Performing a full rescan.")

    print("Discovering files on disk...")
    all_disk_files = {
        str(p.resolve()): p.stat().st_mtime
        for p in library_path.rglob('*')
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    }
    
    cached_paths = set(cached_songs.keys())
    disk_paths = set(all_disk_files.keys())

    new_paths = disk_paths - cached_paths
    deleted_paths = cached_paths - disk_paths
    
    # Check for modified files among the potentially unchanged ones
    potential_updates = disk_paths.intersection(cached_paths)
    modified_paths = {
        p for p in potential_updates 
        if all_disk_files[p] > cached_songs[p].get('mtime', 0)
    }
    
    files_to_process_paths = new_paths.union(modified_paths)
    
    # --- Processing Logic ---
    final_library = []
    
    # 1. Add unchanged songs from cache
    up_to_date_paths = potential_updates - modified_paths
    for path in up_to_date_paths:
        final_library.append(cached_songs[path])
        
    print(f"Found {len(new_paths)} new, {len(modified_paths)} modified, and {len(deleted_paths)} deleted files.")
    
    # 2. Process new and modified files in parallel
    if files_to_process_paths:
        print(f"Processing {len(files_to_process_paths)} files...")
        
        # Prepare arguments for each thread
        tasks = [
            (Path(p), artwork_cache_dir, valid_fallback_path) for p in files_to_process_paths
        ]
        
        with ThreadPoolExecutor() as executor:
            # Use tqdm for a nice progress bar during the parallel processing
            results = list(tqdm(executor.map(_process_single_file, tasks), total=len(tasks)))
        
        # Add successfully processed songs to the library
        for song_data in results:
            if song_data:
                final_library.append(song_data)
    
    # 3. Save the updated cache
    # Assign unique incremental IDs to each song
    for idx, song in enumerate(final_library, start=1):
        song["id"] = idx

    # 3. Save the updated cache
    print("Saving updated library cache...")
    try:
        with open(library_cache_file, 'w', encoding='utf-8') as f:
            json.dump(final_library, f, indent=2)
    except Exception as e:
        print(f"Error: Could not write to cache file at {library_cache_file}. Reason: {e}")

    # 4. Sort and return
    final_library.sort(key=lambda x: (x['artist'].lower(), x['album'].lower(), x['track_num']))
    print("Library scan complete.")
    return final_library


# --- Example of how to use this module ---
if __name__ == '__main__':
    # 1. Define paths
    MUSIC_FOLDER = "C:/Users/SMILETECH COMPUTERS/Music" # Scan a larger directory to see the effect
    ARTWORK_CACHE = ".artwork_cache"
    LIBRARY_CACHE = "library_cache.json"
    FALLBACK_ARTWORK = "unknown.jpeg" 

    start_time = time.time()
    
    # 2. Run the scanner
    # To test a full rescan, change force_rescan to True
    my_music = scan_media_library(
        MUSIC_FOLDER, 
        ARTWORK_CACHE, 
        LIBRARY_CACHE, 
        FALLBACK_ARTWORK, 
        force_rescan=False
    )

    end_time = time.time()
    
    if my_music:
        print(f"\nSuccessfully loaded {len(my_music)} songs in {end_time - start_time:.2f} seconds.")