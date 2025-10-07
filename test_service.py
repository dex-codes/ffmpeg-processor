#!/usr/bin/env python3
"""
Quick test script for the video processing service.
Tests both local and cloud deployments.

Usage:
    python test_service.py --local                    # Test local service
    python test_service.py --cloud SERVICE_URL        # Test cloud service
    python test_service.py --full                     # Full test with video processing
"""

import requests
import json
import time
import argparse
import sys
from pathlib import Path


class ServiceTester:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def test_endpoint(self, endpoint, method='GET', data=None, description=""):
        """Test a single endpoint."""
        url = f"{self.base_url}{endpoint}"
        print(f"\n🧪 Testing {description or endpoint}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = self.session.get(url)
            elif method == 'POST':
                response = self.session.post(url, json=data)
            else:
                print(f"   ❌ Unsupported method: {method}")
                return False
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Success!")
                try:
                    result = response.json()
                    if isinstance(result, dict) and len(result) <= 5:
                        print(f"   Response: {json.dumps(result, indent=2)}")
                    else:
                        print(f"   Response: {type(result).__name__} with {len(result) if hasattr(result, '__len__') else 'data'}")
                except:
                    print(f"   Response: {response.text[:100]}...")
                return True
            else:
                print(f"   ❌ Failed!")
                print(f"   Error: {response.text[:200]}")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection failed! Is the service running?")
            return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def run_basic_tests(self):
        """Run basic endpoint tests."""
        print("🚀 Running Basic Service Tests")
        print("=" * 50)
        
        tests = [
            ("/", "GET", None, "Root endpoint"),
            ("/health", "GET", None, "Health check"),
            ("/presets", "GET", None, "Available presets"),
            ("/stats", "GET", None, "Processing statistics"),
            ("/videos/list", "GET", None, "List videos (requires GCS)"),
        ]
        
        passed = 0
        total = len(tests)
        
        for endpoint, method, data, description in tests:
            if self.test_endpoint(endpoint, method, data, description):
                passed += 1
        
        print(f"\n📊 Basic Tests Results: {passed}/{total} passed")
        return passed == total
    
    def run_video_processing_tests(self):
        """Run video processing tests (requires actual videos in GCS)."""
        print("\n🎬 Running Video Processing Tests")
        print("=" * 50)
        print("⚠️  These tests require videos in gs://bg-video-storage/raw-video-clips/")
        
        # First, try to list videos
        if not self.test_endpoint("/videos/list", "GET", None, "Check available videos"):
            print("❌ Cannot list videos. Skipping processing tests.")
            return False
        
        # Get video list
        try:
            response = self.session.get(f"{self.base_url}/videos/list")
            videos = response.json().get('videos', [])
            
            if not videos:
                print("❌ No videos found in GCS bucket. Upload some test videos first:")
                print("   gsutil cp your-video.mp4 gs://bg-video-storage/raw-video-clips/")
                return False
            
            print(f"✅ Found {len(videos)} videos")
            test_video = videos[0]['filename']
            print(f"   Using test video: {test_video}")
            
        except Exception as e:
            print(f"❌ Error getting video list: {e}")
            return False
        
        # Test single video processing
        process_data = {
            "video_filename": test_video,
            "preset": "mobile_vertical"
        }
        
        print(f"\n🎯 Testing single video processing...")
        if self.test_endpoint("/videos/process", "POST", process_data, "Process single video"):
            print("✅ Video processing test passed!")
            return True
        else:
            print("❌ Video processing test failed!")
            return False
    
    def run_full_tests(self):
        """Run complete test suite."""
        print("🧪 FULL SERVICE TEST SUITE")
        print("=" * 60)
        print(f"Testing service at: {self.base_url}")
        print()
        
        # Basic tests
        basic_passed = self.run_basic_tests()
        
        # Video processing tests
        video_passed = self.run_video_processing_tests()
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        print(f"Basic Tests:           {'✅ PASSED' if basic_passed else '❌ FAILED'}")
        print(f"Video Processing:      {'✅ PASSED' if video_passed else '❌ FAILED'}")
        
        if basic_passed and video_passed:
            print("\n🎉 ALL TESTS PASSED! Your service is working correctly.")
            return True
        elif basic_passed:
            print("\n⚠️  Basic tests passed, but video processing failed.")
            print("   This might be due to missing videos in GCS or configuration issues.")
            return False
        else:
            print("\n❌ Basic tests failed. Check your service configuration.")
            return False


def main():
    parser = argparse.ArgumentParser(description="Test the video processing service")
    parser.add_argument("--local", action="store_true", help="Test local service (localhost:8080)")
    parser.add_argument("--cloud", type=str, help="Test cloud service (provide service URL)")
    parser.add_argument("--full", action="store_true", help="Run full tests including video processing")
    parser.add_argument("--url", type=str, help="Custom service URL")
    
    args = parser.parse_args()
    
    # Determine service URL
    if args.local:
        service_url = "http://localhost:8080"
    elif args.cloud:
        service_url = args.cloud
    elif args.url:
        service_url = args.url
    else:
        print("❌ Please specify --local, --cloud SERVICE_URL, or --url SERVICE_URL")
        print("\nExamples:")
        print("  python test_service.py --local")
        print("  python test_service.py --cloud https://your-service-url.run.app")
        print("  python test_service.py --url http://localhost:8080 --full")
        sys.exit(1)
    
    # Create tester and run tests
    tester = ServiceTester(service_url)
    
    if args.full:
        success = tester.run_full_tests()
    else:
        success = tester.run_basic_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
