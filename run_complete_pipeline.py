#!/usr/bin/env python3
"""
Complete Video Processing Pipeline Launcher

This script runs the complete workflow from sequence generation to video concatenation.
It uses the existing individual scripts to provide a seamless experience.

Author: Your Assistant
Date: 2025-01-06
"""

import subprocess
import sys
import os

def main():
    print("🎬 COMPLETE VIDEO PROCESSING PIPELINE")
    print("=" * 60)
    print("This tool will take you through the complete workflow:")
    print("1. Generate custom video sequence from CSV inventory")
    print("2. Concatenate videos based on the sequence")
    print("3. Create your final video output")
    
    # Check if required scripts exist
    required_scripts = ['generate_my_sequence.py', 'video_concatenator.py']
    missing_scripts = []
    
    for script in required_scripts:
        if not os.path.exists(script):
            missing_scripts.append(script)
    
    if missing_scripts:
        print(f"\n❌ Missing required scripts: {missing_scripts}")
        print("   Please ensure all scripts are in the current directory.")
        return
    
    print(f"\n✅ All required scripts found")
    
    # Phase 1: Sequence Generation
    print(f"\n" + "="*60)
    print("PHASE 1: SEQUENCE GENERATION")
    print("="*60)
    
    try:
        print("🎯 Starting interactive sequence generation...")
        result = subprocess.run([sys.executable, 'generate_my_sequence.py'], 
                              capture_output=False, text=True)
        
        if result.returncode != 0:
            print("❌ Sequence generation failed or was cancelled")
            return
        
        print("✅ Sequence generation completed")
        
    except Exception as e:
        print(f"❌ Error running sequence generation: {e}")
        return
    
    # Ask user for the generated sequence file
    print(f"\n📋 SEQUENCE FILE SELECTION")
    print("-" * 30)
    
    # Look for recently created CSV files
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and f != 'initial-video-data.csv']
    
    if csv_files:
        print("Found these sequence files:")
        for i, file in enumerate(csv_files, 1):
            print(f"   {i}. {file}")
        
        while True:
            try:
                choice = input(f"\nSelect sequence file (1-{len(csv_files)}) or enter filename: ").strip()
                
                if choice.isdigit():
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(csv_files):
                        sequence_file = csv_files[choice_num - 1]
                        break
                    else:
                        print(f"❌ Please enter a number between 1 and {len(csv_files)}")
                else:
                    if os.path.exists(choice):
                        sequence_file = choice
                        break
                    else:
                        print(f"❌ File '{choice}' not found")
                        
            except ValueError:
                print("❌ Please enter a valid number or filename")
    else:
        sequence_file = input("Enter path to your generated sequence CSV file: ").strip()
        if not os.path.exists(sequence_file):
            print(f"❌ File '{sequence_file}' not found")
            return
    
    print(f"✅ Using sequence file: {sequence_file}")
    
    # Phase 2: Video Concatenation
    print(f"\n" + "="*60)
    print("PHASE 2: VIDEO CONCATENATION")
    print("="*60)
    
    try:
        print("🎬 Starting video concatenation...")
        
        # Create a modified version of video_concatenator that uses the sequence file
        # We'll pass the sequence file as an environment variable
        env = os.environ.copy()
        env['SEQUENCE_FILE'] = sequence_file
        
        result = subprocess.run([sys.executable, 'video_concatenator.py'], 
                              env=env, capture_output=False, text=True)
        
        if result.returncode != 0:
            print("❌ Video concatenation failed or was cancelled")
            return
        
        print("✅ Video concatenation completed")
        
    except Exception as e:
        print(f"❌ Error running video concatenation: {e}")
        return
    
    print(f"\n🎉 COMPLETE SUCCESS!")
    print(f"   Your video processing pipeline is complete!")
    print(f"   Check your output video file.")

if __name__ == "__main__":
    main()
