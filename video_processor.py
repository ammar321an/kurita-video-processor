import cv2
import numpy as np
import pytesseract
import re
import json
import sys
import argparse
from datetime import datetime
import os
import requests
import tempfile
import uuid
from urllib.parse import urlparse

# Pre-compile regex patterns
LAT_PATTERN = re.compile(r'Lat:\s*([\d.]+)')
LNG_PATTERN = re.compile(r'Lng:\s*([\d.]+)')
LOCATION_PATTERN = re.compile(r'Location:\s*([^:\n]+)')

def preprocess_frame(frame):
    """Optimized frame preprocessing"""
    try:
        # Convert to HSV once
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Create all color masks in one pass
        color_masks = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)
        
        # Color ranges
        color_ranges = [
            # Cyan (GLASS)
            ((np.array([85, 50, 50]), np.array([95, 255, 255]))),
            # Yellow (PLASTIC)
            ((np.array([20, 100, 100]), np.array([30, 255, 255]))),
            # Red (two ranges)
            ((np.array([0, 100, 100]), np.array([10, 255, 255]))),
            ((np.array([170, 100, 100]), np.array([180, 255, 255])))
        ]
        
        # Apply all masks at once
        for lower, upper in color_ranges:
            mask = cv2.inRange(hsv, lower, upper)
            color_masks = cv2.bitwise_or(color_masks, mask)
        
        # Convert to grayscale and combine with color mask
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        colored_text = np.zeros_like(gray)
        colored_text[color_masks > 0] = 255
        
        # Combine and threshold
        combined = cv2.bitwise_or(gray, colored_text)
        _, thresh = cv2.threshold(combined, 127, 255, cv2.THRESH_BINARY)
        
        return thresh
    except Exception as e:
        print(f"Error in preprocessing: {str(e)}", file=sys.stderr)
        return None

def process_frame(frame, timestamp):
    """Optimized frame processing"""
    try:
        # Preprocess frame
        processed = preprocess_frame(frame)
        if processed is None:
            return None
            
        # Get text in one pass
        text = pytesseract.image_to_string(processed)
        text_upper = text.upper()
        
        # Quick check for any keywords
        if not any(keyword in text_upper for keyword in ['GLASS', 'METAL', 'PLASTIC']):
            return None
            
        # Find coordinates once
        lat_match = LAT_PATTERN.search(text)
        lng_match = LNG_PATTERN.search(text)
        location_match = LOCATION_PATTERN.search(text)
        
        if not all([lat_match, lng_match, location_match]):
            return None
            
        # Find which type was detected
        detected_type = next(
            (keyword for keyword in ['GLASS', 'METAL', 'PLASTIC'] 
             if keyword in text_upper),
            None
        )
        
        if detected_type:
            return {
                'type': detected_type,
                'latitude': float(lat_match.group(1)),
                'longitude': float(lng_match.group(1)),
                'location': location_match.group(1).strip(),
                'timestamp': timestamp
            }
            
        return None
                    
    except Exception as e:
        print(f"Error processing frame: {str(e)}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--video_url', required=True)
    parser.add_argument('--timestamp', type=float, required=True)
    parser.add_argument('--detection_id', required=True)
    args = parser.parse_args()
    
    try:
        # Handle both local file paths and URLs
        video_path = args.video_url
        
        # Open video capture
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception(f"Failed to open video: {video_path}")
        
        # Seek to timestamp
        cap.set(cv2.CAP_PROP_POS_MSEC, args.timestamp * 1000)
        
        # Read frame
        ret, frame = cap.read()
        if not ret:
            raise Exception("Failed to read frame")
            
        # Process frame
        detection = process_frame(frame, args.timestamp)
        
        # Return results immediately
        print(json.dumps({
            'success': detection is not None,
            'detection': detection,
            'detectionId': args.detection_id
        }))
        
        cap.release()

    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e),
            'detection': None,
            'detectionId': args.detection_id
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()