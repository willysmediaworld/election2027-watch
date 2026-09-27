from flask import Flask, render_template, request, jsonify
import database as db
import gemini_ai as ai
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db.init_db()

@app.route('/')
def index():
    return render_template('index.html')

# GEMINI AUTO COLLATION
@app.route('/api/upload-auto-collate', methods=['POST'])
def upload_auto_collate():
    if 'photo' not in request.files:
        return jsonify({"status": "error", "message": "No photograph attached"}), 400
        
    file = request.files['photo']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    
    parsed = ai.extract_ec8a_results(filepath)
    
    data = {
        "election_id": request.form.get("election_id", "ijebu_east_sha"),
        "election_name": request.form.get("election_name", "Ijebu East State House of Assembly Election 2027"),
        "lga": request.form.get("lga", "Ijebu East"),
        "ward": request.form.get("ward"),
        "polling_unit": request.form.get("polling_unit"),
        "pu_code": request.form.get("pu_code"),
        "submitted_by": request.form.get("submitted_by", "Field Officer"),
        "image_url": f"/{filepath}"
    }
    
    if parsed["success"]:
        party_votes = parsed["data"]
        rejected_votes = party_votes.pop("rejected_votes", 0)
        updated_live = db.save_and_auto_collate_submission(data, party_votes, rejected_votes)
        return jsonify({
            "status": "success",
            "mode": "auto",
            "message": "✓ EC8A parsed by Gemini AI & auto-collated live!",
            "extracted_votes": party_votes,
            "live": updated_live
        })
    else:
        db.save_pending_photo_submission(data)
        return jsonify({
            "status": "warning",
            "mode": "pending",
            "message": "⚠️ AI Parsing unavailable. Submission routed to Review Queue.",
            "error": parsed.get("error")
        })

# MANUAL PHOTO UPLOAD
@app.route('/api/upload-photo-result', methods=['POST'])
def upload_photo_result():
    if 'photo' not in request.files:
        return jsonify({"status": "error", "message": "No photograph attached"}), 400
        
    file = request.files['photo']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    
    data = {
        "election_id": request.form.get("election_id", "ijebu_east_sha"),
        "election_name": request.form.get("election_name", "Ijebu East State House of Assembly Election 2027"),
        "lga": request.form.get("lga", "Ijebu East"),
        "ward": request.form.get("ward"),
        "polling_unit": request.form.get("polling_unit"),
        "pu_code": request.form.get("pu_code"),
        "submitted_by": request.form.get("submitted_by", "Field Officer"),
        "image_url": f"/{filepath}"
    }
    
    res = db.save_pending_photo_submission(data)
    return jsonify(res)

# ADMIN MANUAL COLLATION
@app.route('/api/admin-verify-collate', methods=['POST'])
def admin_verify_collate():
    data = request.json
    sub_id = data.get('submission_id')
    party_votes = data.get('party_votes', {})
    rejected_votes = data.get('rejected_votes', 0)
    status = data.get('status', 'ACCEPTED')
    notes = data.get('notes', '')
    verified_by = data.get('verified_by', 'Super Admin')
    
    updated_live = db.admin_verify_and_collate(sub_id, party_votes, rejected_votes, status, notes, verified_by)
    return jsonify({
        "status": "success",
        "message": f"Submission #{sub_id} marked as {status} and collated!",
        "live": updated_live
    })

# SUPER ADMIN SYSTEM RESET
@app.route('/api/admin/reset-system', methods=['POST'])
def reset_system():
    res = db.reset_system_to_default()
    return jsonify(res)

# LIVE & RESULTS APIS
@app.route('/api/live-results', methods=['GET'])
def live_results():
    election_id = request.args.get('election_id', 'ijebu_east_sha')
    data = db.get_live_collation(election_id)
    return jsonify(data)

@app.route('/api/ward-results', methods=['GET'])
def ward_results():
    election_id = request.args.get('election_id', 'ijebu_east_sha')
    data = db.get_ward_results(election_id)
    return jsonify(data)

@app.route('/api/review-queue', methods=['GET'])
def review_queue():
    queue = db.get_pending_review_queue()
    return jsonify(queue)

@app.route('/api/audit-log', methods=['GET'])
def audit_log():
    logs = db.get_audit_log_archive()
    return jsonify(logs)

# ADMIN ENTITY ENDPOINTS
@app.route('/api/admin/users', methods=['GET', 'POST'])
def handle_users():
    if request.method == 'POST':
        data = request.json
        return jsonify(db.create_user(data.get('full_name'), data.get('username'), data.get('role'), data.get('email')))
    return jsonify(db.get_all_users())

@app.route('/api/admin/elections', methods=['GET', 'POST'])
def handle_elections():
    if request.method == 'POST':
        data = request.json
        return jsonify(db.create_election(data.get('name'), data.get('type'), data.get('constituency'), data.get('registered_voters', 50000)))
    return jsonify(db.get_all_elections())

@app.route('/api/admin/parties', methods=['GET', 'POST'])
def handle_parties():
    if request.method == 'POST':
        data = request.json
        return jsonify(db.create_party(data.get('name'), data.get('acronym'), data.get('inec_code'), data.get('is_active', True)))
    return jsonify(db.get_all_parties())

@app.route('/api/admin/candidates', methods=['GET', 'POST'])
def handle_candidates():
    if request.method == 'POST':
        data = request.json
        return jsonify(db.create_candidate(data.get('full_name'), data.get('party'), data.get('election_name')))
    return jsonify(db.get_all_candidates())

@app.route('/api/admin/locations', methods=['GET', 'POST'])
def handle_locations():
    if request.method == 'POST':
        data = request.json
        return jsonify(db.create_location(data.get('state'), data.get('lga'), data.get('ward'), data.get('polling_unit'), data.get('pu_code')))
    return jsonify(db.get_all_locations())

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"==================================================")
    print(f" 2027 ELECTION WATCH SERVER ACTIVE ON PORT {port}")
    print(f"==================================================")
    app.run(host='0.0.0.0', port=port, debug=True)