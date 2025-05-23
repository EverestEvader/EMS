#!/usr/bin/env python3
"""
Cleanup script for expired events.
This script can be run as a cron job to automatically clean up expired events.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Event, EventStatus
from utils import cleanup_expired_events
import logging

def main():
    """Main cleanup function"""
    with app.app_context():
        logging.info("Starting event cleanup process...")
        
        try:
            # Run cleanup
            count = cleanup_expired_events()
            logging.info(f"Cleanup completed. Processed {count} expired events.")
            
            # Log some statistics
            total_events = Event.query.count()
            active_events = Event.query.filter(
                Event.status.in_([EventStatus.PENDING, EventStatus.APPROVED])
            ).count()
            expired_events = Event.query.filter_by(status=EventStatus.EXPIRED).count()
            
            logging.info(f"Event statistics: Total={total_events}, Active={active_events}, Expired={expired_events}")
            
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")
            return 1
    
    return 0

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('cleanup.log'),
            logging.StreamHandler()
        ]
    )
    
    exit_code = main()
    sys.exit(exit_code)
