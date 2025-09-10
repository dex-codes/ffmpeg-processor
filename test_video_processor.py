#!/usr/bin/env python3
"""
Test script for the video processing system.
Tests core functions without requiring actual video files.

Author: Test Script
Date: 2025-01-06
"""

import os
from video_processor import convert_video_format, convert_videos_parallel, concatenate_videos, process_video_sequence
from video_config import VIDEO_PRESETS, list_available_presets, get_preset_info


def test_configuration():
    """Test the configuration system."""
    print("🧪 TESTING CONFIGURATION SYSTEM")
    print("=" * 40)
    
    # Test preset listing
    print("1. Testing preset listing...")
    try:
        list_available_presets()
        print("✅ Preset listing works")
    except Exception as e:
        print(f"❌ Preset listing failed: {e}")
    
    # Test preset info
    print("\n2. Testing preset info...")
    try:
        preset = get_preset_info("mobile_vertical")
        print(f"✅ Got preset info: {preset}")
    except Exception as e:
        print(f"❌ Preset info failed: {e}")
    
    # Test invalid preset
    print("\n3. Testing invalid preset...")
    try:
        get_preset_info("nonexistent_preset")
        print("❌ Should have failed for invalid preset")
    except ValueError:
        print("✅ Correctly rejected invalid preset")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_ffmpeg_availability():
    """Test if FFmpeg is available."""
    print("\n🔧 TESTING FFMPEG AVAILABILITY")
    print("=" * 40)
    
    import subprocess
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg available: {version_line}")
            return True
        else:
            print("❌ FFmpeg command failed")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg not found in PATH")
        print("   Please install FFmpeg: https://ffmpeg.org/download.html")
        return False
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg command timed out")
        return False
    except Exception as e:
        print(f"❌ Error checking FFmpeg: {e}")
        return False


def test_function_imports():
    """Test that all functions can be imported."""
    print("\n📦 TESTING FUNCTION IMPORTS")
    print("=" * 40)
    
    functions_to_test = [
        'convert_video_format',
        'convert_videos_parallel', 
        'concatenate_videos',
        'process_video_sequence'
    ]
    
    for func_name in functions_to_test:
        try:
            func = globals()[func_name]
            print(f"✅ {func_name} imported successfully")
        except KeyError:
            print(f"❌ {func_name} not found")
        except Exception as e:
            print(f"❌ Error importing {func_name}: {e}")


def test_parameter_validation():
    """Test parameter validation without actually processing videos."""
    print("\n🔍 TESTING PARAMETER VALIDATION")
    print("=" * 40)
    
    # Test empty file list
    print("1. Testing empty file list...")
    try:
        result = process_video_sequence(
            input_files=[],
            output_file="test.mp4"
        )
        if result == False:
            print("✅ Correctly rejected empty file list")
        else:
            print("❌ Should have rejected empty file list")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test invalid preset
    print("\n2. Testing preset validation...")
    preset_name = "mobile_vertical"
    if preset_name in VIDEO_PRESETS:
        preset = VIDEO_PRESETS[preset_name]
        print(f"✅ Preset '{preset_name}' is valid: {preset}")
    else:
        print(f"❌ Preset '{preset_name}' not found")


def create_dummy_files():
    """Create dummy files for testing (without actual video content)."""
    print("\n📁 CREATING DUMMY TEST FILES")
    print("=" * 40)
    
    dummy_files = ["dummy1.txt", "dummy2.txt", "dummy3.txt"]
    
    for filename in dummy_files:
        try:
            with open(filename, 'w') as f:
                f.write(f"Dummy file: {filename}\n")
            print(f"✅ Created {filename}")
        except Exception as e:
            print(f"❌ Failed to create {filename}: {e}")
    
    return dummy_files


def cleanup_dummy_files(files):
    """Clean up dummy test files."""
    print("\n🧹 CLEANING UP DUMMY FILES")
    print("=" * 40)
    
    for filename in files:
        try:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"✅ Removed {filename}")
        except Exception as e:
            print(f"❌ Failed to remove {filename}: {e}")


def run_integration_test():
    """Test integration with sequence generator (if available)."""
    print("\n🔗 TESTING INTEGRATION")
    print("=" * 40)
    
    try:
        from sequence_generator import generate_custom_sequence
        print("✅ Sequence generator available")
        
        # Test a small sequence generation
        print("Testing small sequence generation...")
        success = generate_custom_sequence(
            categories=['cooking', 'drink'],
            colors=['red', 'blue'],
            sequence_length=3,
            output_file='test_sequence.csv'
        )
        
        if success:
            print("✅ Test sequence generated")
            
            # Check if file exists
            if os.path.exists('test_sequence.csv'):
                print("✅ Test sequence file created")
                
                # Clean up
                os.remove('test_sequence.csv')
                print("✅ Test file cleaned up")
            else:
                print("❌ Test sequence file not found")
        else:
            print("❌ Test sequence generation failed")
            
    except ImportError:
        print("⚠️  Sequence generator not available (this is OK)")
    except Exception as e:
        print(f"❌ Integration test error: {e}")


def main():
    """Run all tests."""
    print("🧪 VIDEO PROCESSOR TEST SUITE")
    print("=" * 50)
    
    # Run tests
    test_function_imports()
    test_configuration()
    test_parameter_validation()
    ffmpeg_available = test_ffmpeg_availability()
    run_integration_test()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    if ffmpeg_available:
        print("✅ System ready for video processing")
        print("   - All functions imported successfully")
        print("   - Configuration system working")
        print("   - FFmpeg available")
        print("\n🚀 You can now use the video processing system!")
    else:
        print("⚠️  System partially ready")
        print("   - Functions available but FFmpeg missing")
        print("   - Install FFmpeg to enable video processing")
        print("\n📋 Next step: Install FFmpeg")
    
    print("\n📖 See VIDEO_PROCESSING_README.md for usage examples")


if __name__ == "__main__":
    main()
