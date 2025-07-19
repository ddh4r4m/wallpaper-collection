#!/usr/bin/env python3
"""
Setup script for wallpaper collection repository
Installs dependencies and sets up environment
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    # Check if requirements.txt exists
    if not Path('requirements.txt').exists():
        print("❌ requirements.txt not found")
        return False
    
    # Install dependencies
    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing Python dependencies"
    )

def setup_api_keys():
    """Setup API keys environment"""
    print("\n🔑 API Keys Setup")
    print("Please set the following environment variables for API access:")
    print("  - UNSPLASH_ACCESS_KEY: Your Unsplash API key")
    print("  - PEXELS_API_KEY: Your Pexels API key")
    print("  - PIXABAY_API_KEY: Your Pixabay API key")
    print("\nExample:")
    print("  export UNSPLASH_ACCESS_KEY='your-unsplash-key'")
    print("  export PEXELS_API_KEY='your-pexels-key'")
    print("  export PIXABAY_API_KEY='your-pixabay-key'")
    
    # Check if any keys are already set
    keys = {
        'UNSPLASH_ACCESS_KEY': os.getenv('UNSPLASH_ACCESS_KEY'),
        'PEXELS_API_KEY': os.getenv('PEXELS_API_KEY'),
        'PIXABAY_API_KEY': os.getenv('PIXABAY_API_KEY')
    }
    
    print("\n📊 Current API key status:")
    for key, value in keys.items():
        status = "✅ Set" if value else "❌ Not set"
        print(f"  {key}: {status}")

def make_scripts_executable():
    """Make all scripts executable"""
    scripts_dir = Path('scripts')
    if not scripts_dir.exists():
        print("❌ Scripts directory not found")
        return False
    
    for script in scripts_dir.glob('*.py'):
        try:
            script.chmod(0o755)
            print(f"✅ Made {script.name} executable")
        except Exception as e:
            print(f"❌ Failed to make {script.name} executable: {e}")
            return False
    
    return True

def create_env_file():
    """Create a sample .env file"""
    env_content = """# API Keys for wallpaper sources
UNSPLASH_ACCESS_KEY=your-unsplash-access-key-here
PEXELS_API_KEY=your-pexels-api-key-here
PIXABAY_API_KEY=your-pixabay-api-key-here

# GitHub repository configuration
GITHUB_OWNER=your-github-username
GITHUB_REPO=wallpaper-collection

# Processing settings
CRAWL_LIMIT_PER_CATEGORY=100
QUALITY_THRESHOLD=6.0
ENABLE_CLEANUP=true
"""
    
    env_file = Path('.env.example')
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Created sample environment file: {env_file}")
    print("   Copy this to .env and fill in your actual API keys")

def main():
    """Main setup function"""
    print("🚀 Setting up Wallpaper Collection Repository")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Make scripts executable
    if not make_scripts_executable():
        print("❌ Setup failed during script permission setup")
        sys.exit(1)
    
    # Create sample env file
    create_env_file()
    
    # API keys setup guide
    setup_api_keys()
    
    print("\n🎉 Setup completed successfully!")
    print("\n🔄 Next steps:")
    print("1. Copy .env.example to .env and add your API keys")
    print("2. Test the system: python scripts/crawl_images.py --category nature --limit 5")
    print("3. Run quality assessment: python scripts/review_images.py --input crawl_cache")
    print("4. Process approved images: python scripts/process_approved.py --input review_system/approved --category nature")
    print("5. Generate indexes: python scripts/generate_index.py --update-all")
    print("\nFor full automation, use: python scripts/batch_processor.py --categories nature,gaming --limit 50")

if __name__ == "__main__":
    main()