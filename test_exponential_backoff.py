#!/usr/bin/env python3
"""
Test script to demonstrate exponential backoff functionality.
This simulates network failures to show the retry system in action.
"""

import time
from batch_video_processor import BatchVideoProcessor

def test_exponential_backoff():
    """Test the exponential backoff system with a simulated failure."""
    
    print("🧪 TESTING EXPONENTIAL BACKOFF SYSTEM")
    print("=" * 50)
    
    # Create processor with demo settings (override backoff times for testing)
    processor = BatchVideoProcessor(
        source_directory="test_downloads",
        destination_directory="test_processed",
        frame_width=1080,
        frame_height=1920,
        frame_rate=29.97,
        bitrate="6M",
        max_workers=1,
        min_delay=1.0,
        max_delay=3.0,
        batch_size=5,
        batch_pause_min=0.1,
        batch_pause_max=0.2
    )

    # Override backoff times for demo (use seconds instead of minutes)
    processor.failure_backoff_minutes = [0.1, 0.2, 0.3, 0.4]  # 6s, 12s, 18s, 24s
    
    # Initialize session
    processor.initialize_gdown_session()
    
    # Test the backoff system directly
    test_file_id = "TEST_FAILURE_ID"
    
    print(f"\n🎯 Testing exponential backoff for: {test_file_id}")
    print(f"   Backoff schedule: {processor.failure_backoff_minutes} minutes")
    
    # Simulate multiple failures
    for attempt in range(5):
        print(f"\n--- Simulating failure #{attempt + 1} ---")
        
        if processor.should_retry_failed_download(test_file_id):
            print(f"✅ Should retry: {processor.should_retry_failed_download(test_file_id)}")
            should_retry = processor.handle_download_failure(test_file_id)
            print(f"   Backoff handler returned: {should_retry}")
            
            if not should_retry:
                print(f"   ❌ Max retries reached - would add to permanent failures")
                break
        else:
            print(f"❌ Should not retry (max attempts reached)")
            break
    
    # Show final state
    print(f"\n📊 Final State:")
    print(f"   Retry attempts: {processor.retry_attempts}")
    print(f"   Failed downloads: {processor.failed_downloads}")
    
    # Cleanup
    processor.cleanup_session()
    
    print(f"\n✅ Exponential backoff test complete!")

if __name__ == "__main__":
    test_exponential_backoff()
