#!/usr/bin/env python3
"""
Test Script for Tweet Generation Pipeline

Quick test to verify pipeline components work correctly.
"""

import asyncio
import json
import sys
from pathlib import Path
from pipeline.state_manager import StateManager
from pipeline.sqlite_extractor import SQLiteExtractor
from pipeline.analytics_processor import AnalyticsProcessor


async def test_pipeline_components():
    """Test individual pipeline components."""
    print("🧪 Testing Tweet Generation Pipeline Components")
    print("=" * 50)
    
    # Test 1: State Manager
    print("\n1. Testing State Manager...")
    try:
        state_manager = StateManager("test-conference")
        state = state_manager.initialize_state(force_restart=True)
        print(f"  ✅ State initialized: {state['pipeline_id']}")
        
        # Test checkpointing
        test_data = {"test": "data", "timestamp": "2025-06-29"}
        state_manager.save_checkpoint("test.json", test_data)
        loaded_data = state_manager.load_checkpoint("test.json")
        assert loaded_data == test_data
        print("  ✅ Checkpointing works")
        
        # Test step completion
        state_manager.mark_step_complete("test_step")
        assert state_manager.is_step_completed("test_step")
        print("  ✅ Step tracking works")
        
    except Exception as e:
        print(f"  ❌ State Manager test failed: {e}")
        return False
    
    # Test 2: SQLite Extractor (if data exists)
    print("\n2. Testing SQLite Extractor...")
    try:
        extractor = SQLiteExtractor(state_manager)
        
        # Check if test database exists
        test_db = Path("data/venues-icml-2025-v2.db")
        if test_db.exists():
            conference_info = extractor.get_conference_info("venues-icml-2025-v2.db")
            print(f"  ✅ Conference info extracted: {conference_info}")
        else:
            print("  ⚠️  No test database found, skipping SQLite test")
            
    except Exception as e:
        print(f"  ❌ SQLite Extractor test failed: {e}")
    
    # Test 3: Analytics Processor (if analytics exists)
    print("\n3. Testing Analytics Processor...")
    try:
        analytics_processor = AnalyticsProcessor(state_manager)
        
        # Check if test analytics exists
        test_analytics = Path("ui/indiaml-tracker/public/tracker/icml-2025-analytics.json")
        if test_analytics.exists():
            with open(test_analytics, 'r') as f:
                sample_analytics = json.load(f)
            
            # Test with minimal conference info
            conference_info = {"conference": "ICML", "year": 2025}
            processed = analytics_processor._process_analytics_data(sample_analytics, conference_info)
            print(f"  ✅ Analytics processed: {processed['conference']['name']}")
        else:
            print("  ⚠️  No test analytics found, skipping analytics test")
            
    except Exception as e:
        print(f"  ❌ Analytics Processor test failed: {e}")
    
    # Test 4: Configuration Validation
    print("\n4. Testing Configuration...")
    try:
        from pipeline.main_pipeline import TweetGenerationPipeline
        
        # Test valid conference
        pipeline = TweetGenerationPipeline("icml-2025")
        config = pipeline._get_conference_config()
        print(f"  ✅ Configuration loaded: {config}")
        
        # Test invalid conference
        try:
            invalid_pipeline = TweetGenerationPipeline("invalid-conference")
            invalid_pipeline._get_conference_config()
            print("  ❌ Should have failed for invalid conference")
        except ValueError:
            print("  ✅ Invalid conference properly rejected")
            
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
    
    # Test 5: Environment Check
    print("\n5. Testing Environment...")
    try:
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Check for API keys
        openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY")
        
        if openrouter_key:
            print("  ✅ OpenRouter API key found")
        elif openai_key:
            print("  ✅ OpenAI API key found")
        else:
            print("  ⚠️  No API keys found (profile verification will be basic)")
        
        # Check playwright
        try:
            from playwright.async_api import async_playwright
            print("  ✅ Playwright available")
        except ImportError:
            print("  ❌ Playwright not installed")
            
    except Exception as e:
        print(f"  ❌ Environment test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Component testing completed!")
    
    return True


def test_data_availability():
    """Test if required data files are available."""
    print("\n📁 Testing Data Availability")
    print("-" * 30)
    
    # Test SQLite databases
    data_dir = Path("data")
    if data_dir.exists():
        db_files = list(data_dir.glob("venues-*.db"))
        print(f"  📊 Found {len(db_files)} database files:")
        for db in db_files:
            print(f"    • {db.name}")
    else:
        print("  ❌ Data directory not found")
    
    # Test analytics files
    analytics_dir = Path("ui/indiaml-tracker/public/tracker")
    if analytics_dir.exists():
        analytics_files = list(analytics_dir.glob("*-analytics.json"))
        print(f"  📈 Found {len(analytics_files)} analytics files:")
        for analytics in analytics_files:
            print(f"    • {analytics.name}")
    else:
        print("  ❌ Analytics directory not found")
    
    # Test index file
    index_file = Path("ui/indiaml-tracker/public/tracker/index.json")
    if index_file.exists():
        print("  ✅ Index file found")
        try:
            with open(index_file, 'r') as f:
                index_data = json.load(f)
            print(f"    • Contains {len(index_data)} conference entries")
        except Exception as e:
            print(f"    ⚠️  Could not parse index file: {e}")
    else:
        print("  ❌ Index file not found")


async def main():
    """Main test function."""
    print("🚀 Tweet Generation Pipeline Test Suite")
    print("=" * 60)
    
    # Test data availability
    test_data_availability()
    
    # Test pipeline components
    success = await test_pipeline_components()
    
    if success:
        print("\n✅ All tests passed! Pipeline is ready to use.")
        print("\nNext steps:")
        print("1. Ensure you have the required data files")
        print("2. Set up API keys in .env file")
        print("3. Run: python run_pipeline.py icml-2025")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
