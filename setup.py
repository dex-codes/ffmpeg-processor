#!/usr/bin/env python3
"""
Setup script for local development environment.

This script sets up the local development environment for the video processing service,
including dependencies, configuration, and testing.

Author: Cloud Migration
Date: 2025-01-07
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import argparse
import json


def run_command(command, check=True, capture_output=False):
    """Run a shell command."""
    print(f"Running: {command}")
    if capture_output:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if check and result.returncode != 0:
            print(f"Error: {result.stderr}")
            sys.exit(1)
        return result.stdout.strip()
    else:
        result = subprocess.run(command, shell=True)
        if check and result.returncode != 0:
            sys.exit(1)


def check_prerequisites():
    """Check if required tools are installed."""
    print("🔍 Checking prerequisites...")
    
    required_tools = {
        'python3': 'Python 3.8+',
        'pip': 'Python package manager',
        'ffmpeg': 'FFmpeg for video processing',
        'gcloud': 'Google Cloud CLI (optional for cloud deployment)'
    }
    
    missing_tools = []
    
    for tool, description in required_tools.items():
        if not shutil.which(tool):
            missing_tools.append(f"{tool} ({description})")
    
    if missing_tools:
        print("❌ Missing required tools:")
        for tool in missing_tools:
            print(f"  - {tool}")
        print("\nPlease install the missing tools and try again.")
        return False
    
    print("✅ All prerequisites are installed")
    return True


def setup_virtual_environment():
    """Set up Python virtual environment."""
    print("🐍 Setting up Python virtual environment...")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("Virtual environment already exists")
        return
    
    # Create virtual environment
    run_command(f"{sys.executable} -m venv venv")
    
    # Activate and upgrade pip
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        pip_cmd = "venv/bin/pip"
    
    run_command(f"{pip_cmd} install --upgrade pip")
    print("✅ Virtual environment created")


def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing Python dependencies...")
    
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        pip_cmd = "venv/bin/pip"
    
    # Install main dependencies
    run_command(f"{pip_cmd} install -r requirements-cloudrun.txt")
    
    # Install development dependencies
    dev_deps = [
        "pytest>=7.4.3",
        "pytest-asyncio>=0.21.1",
        "black>=23.0.0",
        "flake8>=6.0.0",
        "mypy>=1.0.0",
        "httpx>=0.25.2"
    ]
    
    for dep in dev_deps:
        run_command(f"{pip_cmd} install {dep}")
    
    print("✅ Dependencies installed")


def setup_configuration():
    """Set up configuration files."""
    print("⚙️ Setting up configuration...")
    
    # Create .env file for local development
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# Local development environment variables
ENVIRONMENT=development
GCS_BUCKET_NAME=bg-video-storage
GCP_PROJECT_ID=your-project-id
LOG_LEVEL=DEBUG
DEBUG=true
MAX_CONCURRENT_JOBS=2
MAX_WORKERS_PER_JOB=1
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
"""
        env_file.write_text(env_content)
        print("✅ Created .env file for local development")
    else:
        print("✅ .env file already exists")
    
    # Create local directories
    directories = [
        "temp",
        "logs",
        "test_videos",
        "test_output"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Local directories created")


def setup_git_hooks():
    """Set up Git hooks for code quality."""
    print("🔧 Setting up Git hooks...")
    
    hooks_dir = Path(".git/hooks")
    if not hooks_dir.exists():
        print("⚠️ Not a Git repository, skipping Git hooks setup")
        return
    
    # Pre-commit hook
    pre_commit_hook = hooks_dir / "pre-commit"
    pre_commit_content = """#!/bin/bash
# Pre-commit hook for code quality checks

echo "Running pre-commit checks..."

# Run black formatter
echo "Checking code formatting with black..."
if ! black --check .; then
    echo "❌ Code formatting issues found. Run 'black .' to fix them."
    exit 1
fi

# Run flake8 linter
echo "Running flake8 linter..."
if ! flake8 .; then
    echo "❌ Linting issues found. Please fix them."
    exit 1
fi

# Run type checking
echo "Running mypy type checking..."
if ! mypy --ignore-missing-imports *.py; then
    echo "❌ Type checking issues found. Please fix them."
    exit 1
fi

echo "✅ All pre-commit checks passed"
"""
    
    pre_commit_hook.write_text(pre_commit_content)
    pre_commit_hook.chmod(0o755)
    
    print("✅ Git hooks set up")


def run_tests():
    """Run tests to verify setup."""
    print("🧪 Running tests...")
    
    if os.name == 'nt':  # Windows
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        python_cmd = "venv/bin/python"
    
    # Run basic import tests
    test_imports = [
        "import fastapi",
        "import google.cloud.storage",
        "import uvicorn",
        "import pydantic",
        "from video_config import VIDEO_PRESETS"
    ]
    
    for test_import in test_imports:
        try:
            run_command(f"{python_cmd} -c \"{test_import}\"")
        except:
            print(f"❌ Failed to import: {test_import}")
            return False
    
    print("✅ All import tests passed")
    
    # Test FFmpeg
    try:
        version = run_command("ffmpeg -version", capture_output=True)
        print(f"✅ FFmpeg is working: {version.split()[2]}")
    except:
        print("❌ FFmpeg test failed")
        return False
    
    return True


def create_sample_files():
    """Create sample files for testing."""
    print("📄 Creating sample files...")
    
    # Create sample test script
    test_script = Path("test_local.py")
    test_content = '''#!/usr/bin/env python3
"""
Local testing script for video processing service.
"""

import asyncio
import os
from pathlib import Path

# Set environment for testing
os.environ["ENVIRONMENT"] = "development"
os.environ["GCS_BUCKET_NAME"] = "bg-video-storage"

from config import init_config
from cloud_storage import CloudStorageManager
from video_processing_service import VideoProcessingService


async def test_service():
    """Test the video processing service locally."""
    print("🧪 Testing video processing service...")
    
    # Initialize configuration
    config = init_config("development")
    print(f"✅ Configuration loaded for {config.environment}")
    
    # Test storage manager (will fail without GCS credentials)
    try:
        storage = CloudStorageManager(bucket_name="test-bucket")
        print("✅ Storage manager initialized")
    except Exception as e:
        print(f"⚠️ Storage manager test skipped (no GCS credentials): {e}")
    
    print("✅ Local tests completed")


if __name__ == "__main__":
    asyncio.run(test_service())
'''
    
    test_script.write_text(test_content)
    test_script.chmod(0o755)
    
    # Create sample configuration
    sample_config = Path("config.sample.json")
    config_content = {
        "development": {
            "gcs_bucket": "bg-video-storage-dev",
            "max_concurrent_jobs": 2,
            "debug": True
        },
        "production": {
            "gcs_bucket": "bg-video-storage",
            "max_concurrent_jobs": 5,
            "debug": False
        }
    }
    
    sample_config.write_text(json.dumps(config_content, indent=2))
    
    print("✅ Sample files created")


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Setup local development environment")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--skip-git-hooks", action="store_true", help="Skip Git hooks setup")
    args = parser.parse_args()
    
    print("🚀 Setting up Video Processing Service development environment")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Setup steps
    setup_virtual_environment()
    install_dependencies()
    setup_configuration()
    
    if not args.skip_git_hooks:
        setup_git_hooks()
    
    create_sample_files()
    
    # Run tests
    if not args.skip_tests:
        if not run_tests():
            print("❌ Setup completed with test failures")
            sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Activate the virtual environment:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("2. Update .env file with your GCP project details")
    print("3. Set up Google Cloud credentials:")
    print("   gcloud auth application-default login")
    print("4. Run the service locally:")
    print("   python main.py")
    print("5. Test the API at http://localhost:8080")


if __name__ == "__main__":
    main()
