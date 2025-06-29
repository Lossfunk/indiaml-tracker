#!/usr/bin/env python3
"""
Simple runner script for the Enhanced Tweet Generation Pipeline

Usage:
    python run_enhanced_pipeline.py icml-2025
    python run_enhanced_pipeline.py icml-2025 --force-restart
    python run_enhanced_pipeline.py icml-2025 --resume-from twitter_validation
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run the enhanced pipeline with the provided arguments."""
    if len(sys.argv) < 2:
        print("Usage: python run_enhanced_pipeline.py <conference> [options]")
        print("Example: python run_enhanced_pipeline.py icml-2025")
        print("Options:")
        print("  --force-restart    Start from the beginning")
        print("  --resume-from <step>    Resume from a specific step")
        sys.exit(1)
    
    # Get the script directory
    script_dir = Path(__file__).parent
    pipeline_script = script_dir / "pipeline" / "enhanced_pipeline.py"
    
    if not pipeline_script.exists():
        print(f"Error: Pipeline script not found at {pipeline_script}")
        sys.exit(1)
    
    # Build command
    cmd = ["python", str(pipeline_script)] + sys.argv[1:]
    
    print(f"🚀 Running Enhanced Tweet Generation Pipeline...")
    print(f"Command: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        # Run the pipeline
        result = subprocess.run(cmd, cwd=script_dir)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Failed to run pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
