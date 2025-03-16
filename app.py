from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import sys
import subprocess
import tempfile
import uuid
import requests
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# This is the main route that will be called from your NextJS app
@app.route('/process-detection', methods=['POST'])
def process_detection():
    try:
        data = request.json
        video_url = data.get('videoUrl')
        timestamp = data.get('timestamp')
        detection_id = data.get('detectionId')
        
        print(f"Received request for video: {video_url}, timestamp: {timestamp}, detectionId: {detection_id}")
        
        # Check if we need to download the video first (especially if from localhost/Supabase)
        if video_url and ('localhost' in video_url or '127.0.0.1' in video_url):
            try:
                # For development, download the video first
                temp_dir = tempfile.gettempdir()
                parsed_url = urlparse(video_url)
                filename = os.path.basename(parsed_url.path)
                local_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{filename}")
                
                print(f"Downloading video from {video_url} to {local_path}")
                
                response = requests.get(video_url, stream=True)
                response.raise_for_status()
                
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Use the local path instead of the URL
                video_url = local_path
            except Exception as e:
                print(f"Error downloading video: {str(e)}", file=sys.stderr)
                # Continue with the original URL if download fails
        
        # Call the video processor script
        result = subprocess.run([
            'python', 
            'video_processor.py',
            '--video_url', str(video_url),
            '--timestamp', str(timestamp),
            '--detection_id', str(detection_id)
        ], capture_output=True, text=True)
        
        print(f"Python script stdout: {result.stdout}")
        print(f"Python script stderr: {result.stderr}")
        
        if result.returncode != 0:
            print(f"Python processing error: {result.stderr}", file=sys.stderr)
            return jsonify({
                'success': False,
                'detection': None,
                'message': 'No detection found'
            })
        
        try:
            # Parse the JSON output from the Python script
            python_result = json.loads(result.stdout)
            return jsonify(python_result)
            
        except Exception as e:
            print(f"Invalid detection data: {e}", file=sys.stderr)
            return jsonify({
                'success': False,
                'detection': None,
                'message': f'Invalid detection data: {str(e)}'
            })
            
    except Exception as e:
        print(f"Error processing detection: {str(e)}", file=sys.stderr)
        return jsonify({
            'success': False,
            'error': str(e),
            'detection': None
        }), 500

# Add a simpler health check route
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Video processing service is running'
    })

# For backwards compatibility, also handle requests to the root path
@app.route('/', methods=['POST'])
def root_process():
    return process_detection()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)