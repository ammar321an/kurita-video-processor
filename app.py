from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import sys
import subprocess

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/process-detection', methods=['POST'])
def process_detection():
    try:
        data = request.json
        video_url = data.get('videoUrl')
        timestamp = data.get('timestamp')
        detection_id = data.get('detectionId')
        
        # Call your existing Python video_processor.py script directly
        # This mimics what your route.ts file does
        result = subprocess.run([
            'python', 
            'video_processor.py',
            '--video_url', str(video_url),
            '--timestamp', str(timestamp),
            '--detection_id', str(detection_id)
        ], capture_output=True, text=True)
        
        # Process the output exactly like your route.ts
        if result.returncode != 0:
            print(f"Python processing error: {result.stderr}", file=sys.stderr)
            return jsonify({
                'success': False,
                'detection': None,
                'message': 'No detection found'
            })
        
        try:
            # Parse the JSON exactly as you do in route.ts
            python_result = json.loads(result.stdout)
            return jsonify(python_result)
            
        except Exception as e:
            print(f"Invalid detection data: {e}", file=sys.stderr)
            return jsonify({
                'success': False,
                'detection': None,
                'message': 'Invalid detection data'
            })
            
    except Exception as e:
        print(f"Error processing detection: {str(e)}", file=sys.stderr)
        return jsonify({
            'success': False,
            'error': str(e),
            'detection': None
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)