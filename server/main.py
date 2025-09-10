from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import subprocess
import tempfile
import random
import string
from pathlib import Path
from typing import Optional, List, Dict, Any
import asyncio
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FFmpeg Randomizer API",
    description="A FastAPI server for randomizing video/audio files using FFmpeg",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
TEMP_DIR = Path("temp")

# Create directories if they don't exist
for directory in [UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR]:
    directory.mkdir(exist_ok=True)

def generate_random_string(length: int = 8) -> str:
    """Generate a random string for file naming."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def check_ffmpeg():
    """Check if FFmpeg is available."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

@app.on_event("startup")
async def startup_event():
    """Check system requirements on startup."""
    if not check_ffmpeg():
        logger.warning("FFmpeg not found in PATH. Some features may not work.")
    logger.info("FFmpeg Randomizer API started successfully")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "FFmpeg Randomizer API is running",
        "ffmpeg_available": check_ffmpeg()
    }

@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "ffmpeg_available": check_ffmpeg(),
        "upload_dir": str(UPLOAD_DIR.absolute()),
        "output_dir": str(OUTPUT_DIR.absolute())
    }

@app.post("/randomize")
async def randomize_media(
    file: UploadFile = File(...),
    effect_type: Optional[str] = "basic",
    intensity: Optional[float] = 0.5
):
    """
    Randomize a media file using FFmpeg.
    
    - **file**: Media file to randomize
    - **effect_type**: Type of randomization effect (basic, glitch, audio, etc.)
    - **intensity**: Effect intensity (0.0 to 1.0)
    """
    if not check_ffmpeg():
        raise HTTPException(status_code=500, detail="FFmpeg not available")
    
    # Generate unique filename
    random_id = generate_random_string()
    file_extension = Path(file.filename).suffix if file.filename else ".mp4"
    input_filename = f"input_{random_id}{file_extension}"
    output_filename = f"output_{random_id}{file_extension}"
    
    input_path = UPLOAD_DIR / input_filename
    output_path = OUTPUT_DIR / output_filename
    
    try:
        # Save uploaded file
        with open(input_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Apply randomization effect based on type
        ffmpeg_cmd = build_ffmpeg_command(
            str(input_path), 
            str(output_path), 
            effect_type, 
            intensity
        )
        
        # Execute FFmpeg command
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise HTTPException(status_code=500, detail=f"FFmpeg processing failed: {result.stderr}")
        
        # Check if output file was created
        if not output_path.exists():
            raise HTTPException(status_code=500, detail="Output file was not created")
        
        return {
            "status": "success",
            "message": "Media file randomized successfully",
            "output_file": output_filename,
            "download_url": f"/download/{output_filename}",
            "effect_applied": effect_type,
            "intensity": intensity
        }
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Processing timeout")
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    finally:
        # Clean up input file
        if input_path.exists():
            input_path.unlink()

@app.post("/randomize-batch")
async def randomize_batch(
    files: List[UploadFile] = File(...),
    effect_type: Optional[str] = "basic",
    intensity: Optional[float] = 0.5,
    same_effect: Optional[bool] = True
):
    """
    Randomize multiple media files using FFmpeg.

    - **files**: List of media files to randomize
    - **effect_type**: Type of randomization effect (used if same_effect=True)
    - **intensity**: Effect intensity (used if same_effect=True)
    - **same_effect**: If True, apply same effect to all files; if False, randomize effects
    """
    if not check_ffmpeg():
        raise HTTPException(status_code=500, detail="FFmpeg not available")

    if len(files) > 10:  # Limit batch size
        raise HTTPException(status_code=400, detail="Maximum 10 files per batch")

    results = []
    available_effects = ["basic", "glitch", "audio", "visual", "temporal", "psychedelic"]

    for i, file in enumerate(files):
        try:
            # Generate unique filename
            random_id = generate_random_string()
            file_extension = Path(file.filename).suffix if file.filename else ".mp4"
            input_filename = f"batch_input_{i}_{random_id}{file_extension}"
            output_filename = f"batch_output_{i}_{random_id}{file_extension}"

            input_path = UPLOAD_DIR / input_filename
            output_path = OUTPUT_DIR / output_filename

            # Save uploaded file
            with open(input_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)

            # Determine effect for this file
            if same_effect:
                current_effect = effect_type
                current_intensity = intensity
            else:
                current_effect = random.choice(available_effects)
                current_intensity = random.uniform(0.2, 0.8)

            # Apply randomization effect
            ffmpeg_cmd = build_ffmpeg_command(
                str(input_path),
                str(output_path),
                current_effect,
                current_intensity
            )

            # Execute FFmpeg command
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per file
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg error for file {i}: {result.stderr}")
                results.append({
                    "file_index": i,
                    "original_filename": file.filename,
                    "status": "error",
                    "error": f"FFmpeg processing failed: {result.stderr[:200]}..."
                })
            elif not output_path.exists():
                results.append({
                    "file_index": i,
                    "original_filename": file.filename,
                    "status": "error",
                    "error": "Output file was not created"
                })
            else:
                results.append({
                    "file_index": i,
                    "original_filename": file.filename,
                    "status": "success",
                    "output_file": output_filename,
                    "download_url": f"/download/{output_filename}",
                    "effect_applied": current_effect,
                    "intensity": current_intensity
                })

            # Clean up input file
            if input_path.exists():
                input_path.unlink()

        except subprocess.TimeoutExpired:
            results.append({
                "file_index": i,
                "original_filename": file.filename,
                "status": "error",
                "error": "Processing timeout"
            })
        except Exception as e:
            logger.error(f"Error processing batch file {i}: {str(e)}")
            results.append({
                "file_index": i,
                "original_filename": file.filename,
                "status": "error",
                "error": f"Processing error: {str(e)}"
            })

    # Summary statistics
    successful = len([r for r in results if r["status"] == "success"])
    failed = len([r for r in results if r["status"] == "error"])

    return {
        "status": "completed",
        "message": f"Batch processing completed: {successful} successful, {failed} failed",
        "total_files": len(files),
        "successful_files": successful,
        "failed_files": failed,
        "results": results,
        "batch_settings": {
            "effect_type": effect_type if same_effect else "randomized",
            "intensity": intensity if same_effect else "randomized",
            "same_effect": same_effect
        }
    }

def build_ffmpeg_command(input_path: str, output_path: str, effect_type: str, intensity: float) -> List[str]:
    """Build FFmpeg command based on effect type and intensity."""
    base_cmd = ["ffmpeg", "-i", input_path, "-y"]  # -y to overwrite output

    if effect_type == "basic":
        # Basic randomization: slight speed and pitch changes
        speed_factor = 0.8 + (intensity * 0.4)  # 0.8 to 1.2
        base_cmd.extend([
            "-filter:v", f"setpts={1/speed_factor}*PTS",
            "-filter:a", f"atempo={speed_factor}",
            output_path
        ])

    elif effect_type == "glitch":
        # Glitch effect: noise and corruption
        noise_strength = int(intensity * 20)
        base_cmd.extend([
            "-filter_complex",
            f"[0:v]noise=alls={noise_strength}:allf=t,hue=s={0.5 + intensity}[v];"
            f"[0:a]aecho=0.8:0.88:{int(60 * intensity)}:0.4,volume={0.7 + intensity * 0.3}[a]",
            "-map", "[v]", "-map", "[a]",
            output_path
        ])

    elif effect_type == "audio":
        # Audio-focused randomization with multiple effects
        volume_factor = 0.5 + intensity * 0.5
        echo_delay = int(60 + intensity * 40)
        base_cmd.extend([
            "-filter:a", f"volume={volume_factor},aecho=0.8:0.88:{echo_delay}:0.4,highpass=f=100",
            "-c:v", "copy",  # Copy video without re-encoding
            output_path
        ])

    elif effect_type == "visual":
        # Visual-focused effects: color shifts, blur, etc.
        hue_shift = intensity * 0.5
        saturation = 0.5 + intensity * 1.0
        base_cmd.extend([
            "-filter:v", f"hue=h={hue_shift}:s={saturation},unsharp=5:5:{intensity * 2}:5:5:{intensity}",
            "-c:a", "copy",  # Copy audio without re-encoding
            output_path
        ])

    elif effect_type == "temporal":
        # Time-based effects: reverse segments, speed variations
        if intensity < 0.5:
            # Variable speed
            speed_var = 0.5 + intensity
            base_cmd.extend([
                "-filter:v", f"setpts={1/speed_var}*PTS",
                "-filter:a", f"atempo={speed_var}",
                output_path
            ])
        else:
            # Reverse effect with original
            base_cmd.extend([
                "-filter_complex",
                "[0:v]split[v1][v2];[v2]reverse[vr];[v1][vr]concat=n=2:v=1[v];"
                "[0:a]asplit[a1][a2];[a2]areverse[ar];[a1][ar]concat=n=2:v=0:a=1[a]",
                "-map", "[v]", "-map", "[a]",
                output_path
            ])

    elif effect_type == "psychedelic":
        # Psychedelic effects: color cycling, kaleidoscope-like
        base_cmd.extend([
            "-filter_complex",
            f"[0:v]hue=H=2*PI*t:s={1 + intensity},eq=contrast={1 + intensity}:brightness={intensity * 0.1}[v];"
            f"[0:a]aecho=0.8:0.9:{int(100 * intensity)}:0.6,chorus=0.5:0.9:{int(50 * intensity)}:0.4:0.25:2[a]",
            "-map", "[v]", "-map", "[a]",
            output_path
        ])

    else:
        # Default to basic
        speed_factor = 0.8 + (intensity * 0.4)
        base_cmd.extend([
            "-filter:v", f"setpts={1/speed_factor}*PTS",
            "-filter:a", f"atempo={speed_factor}",
            output_path
        ])

    return base_cmd

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download a processed file."""
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # In a real implementation, you'd want to serve the file properly
    # For now, return file info
    return {
        "filename": filename,
        "size": file_path.stat().st_size,
        "path": str(file_path.absolute()),
        "message": "File ready for download"
    }

@app.get("/effects")
async def list_effects():
    """List available randomization effects."""
    return {
        "effects": [
            {
                "name": "basic",
                "description": "Basic speed and pitch randomization",
                "parameters": ["intensity"],
                "intensity_range": "0.0-1.0 (0.5 = normal speed)"
            },
            {
                "name": "glitch",
                "description": "Digital glitch effects with noise and corruption",
                "parameters": ["intensity"],
                "intensity_range": "0.0-1.0 (higher = more corruption)"
            },
            {
                "name": "audio",
                "description": "Audio-focused effects: echo, volume, filtering",
                "parameters": ["intensity"],
                "intensity_range": "0.0-1.0 (affects echo delay and volume)"
            },
            {
                "name": "visual",
                "description": "Visual effects: color shifts, saturation, sharpening",
                "parameters": ["intensity"],
                "intensity_range": "0.0-1.0 (affects color and sharpness)"
            },
            {
                "name": "temporal",
                "description": "Time-based effects: speed variations or reverse segments",
                "parameters": ["intensity"],
                "intensity_range": "0.0-0.5 = speed variation, 0.5-1.0 = reverse effects"
            },
            {
                "name": "psychedelic",
                "description": "Psychedelic effects: color cycling, enhanced audio",
                "parameters": ["intensity"],
                "intensity_range": "0.0-1.0 (higher = more trippy effects)"
            }
        ],
        "usage_tips": [
            "Start with intensity 0.3-0.7 for most effects",
            "Temporal effects behave differently at different intensity ranges",
            "Higher intensities may significantly increase processing time",
            "Some effects work better with certain media types"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
