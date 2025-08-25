#!/usr/bin/env python3
"""
Unitree G1 AI Assistant - Main Entry Point

This script serves as the main entry point for the Unitree G1 AI Assistant.
It handles environment setup, argument parsing, and application initialization.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if required environment variables are set."""
    required_vars = [
        'OPENAI_API_KEY',
        'ELEVENLABS_API_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("Please create a .env file in the project root or set these variables in your environment.")
        return False
    return True

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Unitree G1 AI Assistant')
    
    # Add arguments
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--no-audio',
        action='store_true',
        help='Run without audio (for testing)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        default='assistant.log',
        help='Path to log file (default: assistant.log)'
    )
    
    return parser.parse_args()

def setup_environment():
    """Set up the Python environment and paths."""
    # Add project root to path
    project_root = str(Path(__file__).parent.absolute())
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Load environment variables from .env file if it exists
    env_path = Path(project_root) / '.env'
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path)
        logger.info("Loaded environment variables from .env file")

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Set up file logging
    file_handler = logging.FileHandler(args.log_file)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    logging.getLogger().addHandler(file_handler)
    
    # Set up environment
    setup_environment()
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    logger.info("Starting Unitree G1 AI Assistant")
    
    try:
        # Import and run the main application
        from core.cortex import process_conversation
        
        if args.no_audio:
            logger.info("Running in no-audio mode")
            # You might want to mock audio-related functionality here
        
        # Start the main conversation loop
        while True:
            try:
                process_conversation()
            except KeyboardInterrupt:
                logger.info("\nReceived keyboard interrupt. Exiting...")
                break
            except Exception as e:
                logger.error(f"An error occurred: {str(e)}", exc_info=True)
                logger.info("Restarting conversation...")
                continue
                
    except ImportError as e:
        logger.error(f"Failed to import required modules: {str(e)}")
        logger.error("Please make sure all dependencies are installed and the project structure is correct.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Unitree G1 AI Assistant has been terminated")

if __name__ == "__main__":
    main()
