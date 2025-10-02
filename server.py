from flask import Flask, request, jsonify, render_template
import os
import json
from datetime import datetime
from collections import Counter

# Import the classes from your existing scripts
from job_tracker import EnhancedJobTracker
from job_manager import JobManager

# --- Flask App Initialization ---
app = Flask(__name__, template_folder='.')
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- HTML Page Routes ---
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/add')
def add_job_page():
    return render_template('add_job.html')

# --- API Endpoints ---
@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    manager = JobManager()
    sorted_jobs = sorted(manager.jobs, key=lambda x: datetime.strptime(x['last_update'], '%m/%d/%Y'), reverse=True)
    return jsonify(sorted_jobs)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    manager = JobManager()
    jobs = manager.jobs
    status_counts = Counter(job['status'] for job in jobs)

    nodes = []
    links = []
    
    node_order = ["Applied", "Interview Scheduled", "Interviewed", "Hired", "Rejected", "Ghosted", "Withdrawn"]
    existing_nodes = {status for status in node_order if status_counts.get(status, 0) > 0}

    if not existing_nodes:
        return jsonify({
            'total_jobs': len(jobs), 'status_counts': dict(status_counts),
            'sankey_data': {'nodes': [], 'links': []}
        })

    for node_name in node_order:
        if node_name in existing_nodes:
            nodes.append({'name': node_name})

    # --- Calculate Flows ---
    interview_stage_total = status_counts.get("Interview Scheduled", 0) + status_counts.get("Interviewed", 0) + status_counts.get("Hired", 0)
    if interview_stage_total > 0 and "Applied" in existing_nodes and "Interview Scheduled" in existing_nodes:
        links.append({'source': 'Applied', 'target': 'Interview Scheduled', 'value': interview_stage_total})

    interviewed_stage_total = status_counts.get("Interviewed", 0) + status_counts.get("Hired", 0)
    if interviewed_stage_total > 0 and "Interview Scheduled" in existing_nodes and "Interviewed" in existing_nodes:
        links.append({'source': 'Interview Scheduled', 'target': 'Interviewed', 'value': interviewed_stage_total})

    hired_total = status_counts.get("Hired", 0)
    if hired_total > 0 and "Interviewed" in existing_nodes and "Hired" in existing_nodes:
        links.append({'source': 'Interviewed', 'target': 'Hired', 'value': hired_total})

    rejections_total = status_counts.get("Rejected", 0)
    if rejections_total > 0 and "Rejected" in existing_nodes:
        post_interview_rejections = 0
        if "Interviewed" in existing_nodes:
            # Simple heuristic: half of rejections happen after an interview, if interviews exist
            post_interview_rejections = min(rejections_total, int(rejections_total * 0.5))
            if post_interview_rejections > 0:
                 links.append({'source': 'Interviewed', 'target': 'Rejected', 'value': post_interview_rejections})
        
        pre_interview_rejections = rejections_total - post_interview_rejections
        if pre_interview_rejections > 0 and "Applied" in existing_nodes:
            links.append({'source': 'Applied', 'target': 'Rejected', 'value': pre_interview_rejections})

    sankey_data = {'nodes': nodes, 'links': links}
    
    return jsonify({
        'total_jobs': len(jobs),
        'status_counts': dict(status_counts),
        'sankey_data': sankey_data
    })

@app.route('/api/job/<int:job_id>', methods=['GET', 'POST'])
def handle_job_edit(job_id):
    manager = JobManager()
    if not (0 <= job_id < len(manager.jobs)):
        return jsonify({'success': False, 'error': 'Job not found'}), 404
        
    if request.method == 'POST':
        data = request.json
        job = manager.jobs[job_id]
        job['title'] = data.get('title', job['title'])
        job['company'] = data.get('company', job['company'])
        job['description'] = data.get('description', job['description'])
        if 'other_info' not in job: job['other_info'] = {}
        job['other_info']['location'] = data.get('location', job.get('other_info', {}).get('location'))
        job['other_info']['salary'] = data.get('salary', job.get('other_info', {}).get('salary'))
        job['url'] = data.get('url', job.get('url'))
        job['last_update'] = datetime.now().strftime('%m/%d/%Y')
        manager.save_jobs()
        return jsonify({'success': True, 'job': job})
    else:
        return jsonify(manager.jobs[job_id])

@app.route('/api/update_status', methods=['POST'])
def update_status():
    data = request.json
    job_id, new_status = data.get('job_id'), data.get('status')
    manager = JobManager()
    if not (job_id is not None and new_status is not None and 0 <= job_id < len(manager.jobs)):
        return jsonify({'success': False, 'error': 'Invalid request'}), 400
        
    manager.jobs[job_id]['status'] = new_status
    manager.jobs[job_id]['last_update'] = datetime.now().strftime('%m/%d/%Y')
    manager.save_jobs()
    return jsonify({'success': True})

# --- Routes for Adding Jobs ---
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return jsonify({'success': False, 'error': 'No file part'})
    file = request.files['file']
    if file.filename == '': return jsonify({'success': False, 'error': 'No selected file'})
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)
    tracker = EnhancedJobTracker()
    success = tracker.add_job_from_input(filepath)
    os.remove(filepath)
    return jsonify({'success': True, 'job': tracker.jobs[-1]}) if success else jsonify({'success': False, 'error': 'Failed to process file'})

@app.route('/api/process_url', methods=['POST'])
def process_url():
    url = request.json.get('url')
    if not url: return jsonify({'success': False, 'error': 'URL is required'})
    tracker = EnhancedJobTracker()
    success = tracker.add_job_from_url(url)
    return jsonify({'success': True, 'job': tracker.jobs[-1]}) if success else jsonify({'success': False, 'error': 'Failed to process URL'})

@app.route('/api/process_text', methods=['POST'])
def process_text():
    text = request.json.get('text')
    if not text: return jsonify({'success': False, 'error': 'Text is required'})
    tracker = EnhancedJobTracker()
    success = tracker.add_job_from_text(text)
    return jsonify({'success': True, 'job': tracker.jobs[-1]}) if success else jsonify({'success': False, 'error': 'Failed to process text'})

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True, port=5001)

