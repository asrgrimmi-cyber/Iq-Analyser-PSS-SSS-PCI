"""
IQ Analyzer — Spotify-themed Flask Web Application
Upload a .bin IQ file → Get full LTE PSS/SSS/PCI analysis dashboard
"""
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import uuid
import threading
import time

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max upload
app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/images', exist_ok=True)

# In-memory job store
jobs = {}


def run_analysis(job_id, bin_path):
    """Background thread for IQ analysis."""
    jobs[job_id]['status'] = 'processing'
    jobs[job_id]['message'] = 'Resampling IQ data...'
    try:
        from iq_engine import analyze_iq_file
        results = analyze_iq_file(bin_path, job_id)
        jobs[job_id]['status'] = 'complete'
        jobs[job_id]['results'] = results
        jobs[job_id]['message'] = 'Analysis complete!'
    except Exception as e:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['message'] = str(e)
        import traceback
        traceback.print_exc()
    finally:
        # Clean up uploaded file
        try:
            os.remove(bin_path)
        except OSError:
            pass


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.endswith('.bin'):
        return jsonify({'error': 'Only .bin files are supported'}), 400

    job_id = str(uuid.uuid4())[:8]
    filename = f"{job_id}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    jobs[job_id] = {
        'status': 'queued',
        'message': 'File uploaded, starting analysis...',
        'results': None,
        'created': time.time()
    }

    # Launch background processing
    thread = threading.Thread(target=run_analysis, args=(job_id, filepath), daemon=True)
    thread.start()

    return jsonify({'job_id': job_id})


@app.route('/status/<job_id>')
def status(job_id):
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    response = {
        'status': job['status'],
        'message': job['message']
    }

    if job['status'] == 'complete':
        response['results'] = job['results']

    return jsonify(response)


@app.route('/static/images/<session_id>/<filename>')
def serve_plot(session_id, filename):
    directory = os.path.join('static', 'images', session_id)
    return send_from_directory(directory, filename)


# Clean up old jobs (>1 hour)
def cleanup_jobs():
    while True:
        time.sleep(600)  # Every 10 minutes
        now = time.time()
        expired = [jid for jid, j in jobs.items() if now - j['created'] > 3600]
        for jid in expired:
            del jobs[jid]


cleanup_thread = threading.Thread(target=cleanup_jobs, daemon=True)
cleanup_thread.start()


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
