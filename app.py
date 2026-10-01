from flask import Flask, render_template_string, request, jsonify, session, Response
import sqlite3
import json
import os
import csv
import io
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
DB_NAME = "ogun_east_2027_master.db"

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==========================================
# DATABASE SETUP & FORCE SUPER ADMIN SEED
# ==========================================
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Submissions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id TEXT, election_name TEXT, election_type TEXT, lga TEXT, ward TEXT,
            polling_unit TEXT, pu_code TEXT, party_votes TEXT DEFAULT '{}',
            valid_votes INTEGER DEFAULT 0, rejected_votes INTEGER DEFAULT 0,
            total_votes_cast INTEGER DEFAULT 0, image_url TEXT, submitted_by TEXT,
            assigned_to TEXT DEFAULT '', timestamp DATETIME, status TEXT DEFAULT 'PENDING',
            review_notes TEXT, is_flagged INTEGER DEFAULT 0, flag_reason TEXT DEFAULT '',
            verified_by TEXT, verified_at DATETIME
        )
    ''')

    # 2. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, username TEXT UNIQUE,
            password_hash TEXT, role TEXT, assigned_lga TEXT DEFAULT '', assigned_ward TEXT DEFAULT '',
            assigned_pu_code TEXT DEFAULT '', assigned_pu_name TEXT DEFAULT '',
            email TEXT, created_by TEXT DEFAULT 'Super Admin', created_at DATETIME
        )
    ''')
    
    # 3. Elections Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS elections (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, type TEXT,
            constituency TEXT, registered_voters INTEGER DEFAULT 1150000, is_active INTEGER DEFAULT 1
        )
    ''')

    # 4. Parties Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parties (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, acronym TEXT UNIQUE,
            inec_code TEXT, logo_url TEXT DEFAULT '', is_active INTEGER DEFAULT 1
        )
    ''')

    # 5. Candidates Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, party TEXT,
            election_name TEXT, photo_url TEXT DEFAULT '', created_at DATETIME
        )
    ''')

    # 6. Locations Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, state TEXT DEFAULT 'Ogun',
            lga TEXT, ward TEXT, polling_unit TEXT, pu_code TEXT
        )
    ''')
    
    # FORCE SEED / RESET SUPER ADMIN CREDENTIALS ON STARTUP
    super_admin_pass = generate_password_hash("rotimi1972")
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = 'rotimi' OR LOWER(full_name) = 'oladele rotimi williams'")
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("UPDATE users SET password_hash = ?, full_name = 'Oladele Rotimi Williams', username = 'rotimi', role = 'Super Admin' WHERE id = ?", (super_admin_pass, existing['id']))
    else:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO users (full_name, username, password_hash, role, email, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("Oladele Rotimi Williams", "rotimi", super_admin_pass, "Super Admin", "admin@electionwatch.ng", "System", now_str))

    # Preload Elections
    cursor.execute("SELECT COUNT(*) FROM elections")
    if cursor.fetchone()[0] == 0:
        default_elections = [
            ("Ogun East Senatorial District Election 2027", "Senatorial", "Ogun East Senatorial District", 1150000, 1),
            ("Ogun State Governorship Election 2027", "Governorship", "Ogun State", 2400000, 1),
            ("Nigeria Presidential Election 2027", "Presidential", "National", 93000000, 1),
            ("House of Representatives Election 2027", "House of Representatives", "Ogun East Federal Constituencies", 1150000, 1),
            ("State House of Assembly Election 2027", "State House of Assembly", "Ogun East State Constituencies", 1150000, 1),
            ("Local Government Chairmanship Election 2027", "LGA Chairman", "Ogun East Local Governments", 1150000, 1),
            ("Local Government Councilorship Election 2027", "LGA Councillor", "Ogun East Wards", 1150000, 1)
        ]
        cursor.executemany("INSERT INTO elections (name, type, constituency, registered_voters, is_active) VALUES (?, ?, ?, ?, ?)", default_elections)

    # Preload All 19 Political Parties
    cursor.execute("SELECT COUNT(*) FROM parties")
    if cursor.fetchone()[0] < 19:
        cursor.execute("DELETE FROM parties")
        all_inec_parties = [
            ("Accord", "A", "001", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Accord_Party_Logo.png/120px-Accord_Party_Logo.png"),
            ("Action Alliance", "AA", "002", "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Action_Alliance_Logo.png/120px-Action_Alliance_Logo.png"),
            ("Action Democratic Party", "ADP", "003", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/ADP_Nigeria_Logo.png/120px-ADP_Nigeria_Logo.png"),
            ("Action Peoples Party", "APP", "004", "https://via.placeholder.com/60?text=APP"),
            ("African Action Congress", "AAC", "005", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/AAC_Party_Logo.jpg/120px-AAC_Party_Logo.jpg"),
            ("African Democratic Congress", "ADC", "006", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/ADC_Nigeria_Logo.png/120px-ADC_Nigeria_Logo.png"),
            ("All Progressives Congress", "APC", "007", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/All_Progressives_Congress_flag.svg/120px-All_Progressives_Congress_flag.svg.png"),
            ("All Progressives Grand Alliance", "APGA", "008", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/APGA_Party_Logo.png/120px-APGA_Party_Logo.png"),
            ("Allied Peoples Movement", "APM", "009", "https://via.placeholder.com/60?text=APM"),
            ("Boot Party", "BP", "010", "https://via.placeholder.com/60?text=BP"),
            ("Labour Party", "LP", "011", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Labour_Party_Nigeria_Logo.png/120px-Labour_Party_Nigeria_Logo.png"),
            ("National Rescue Movement", "NRM", "012", "https://via.placeholder.com/60?text=NRM"),
            ("New Nigeria Peoples Party", "NNPP", "013", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/NNPP_Logo.png/120px-NNPP_Logo.png"),
            ("Peoples Democratic Party", "PDP", "014", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Peoples_Democratic_Party_logo.svg/120px-Peoples_Democratic_Party_logo.svg.png"),
            ("People's Redemption Party", "PRP", "015", "https://via.placeholder.com/60?text=PRP"),
            ("Social Democratic Party", "SDP", "016", "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/SDP_Nigeria_Logo.png/120px-SDP_Nigeria_Logo.png"),
            ("Youth Party", "YP", "017", "https://via.placeholder.com/60?text=YP"),
            ("Young Progressives Party", "YPP", "018", "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/YPP_Nigeria_Logo.png/120px-YPP_Nigeria_Logo.png"),
            ("Zenith Labour Party", "ZLP", "019", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/ZLP_Logo.png/120px-ZLP_Logo.png")
        ]
        cursor.executemany("INSERT INTO parties (name, acronym, inec_code, logo_url, is_active) VALUES (?, ?, ?, ?, 1)", all_inec_parties)

    # Preload Locations
    cursor.execute("SELECT COUNT(*) FROM locations")
    if cursor.fetchone()[0] < 50:
        cursor.execute("DELETE FROM locations")
        ogun_east_locations = [
            ("Ogun", "Ijebu East", "Ijebu Mushin I", "ODOSEGBUREN SQUARE", "27/07/01/001"),
            ("Ogun", "Ijebu East", "Ijebu Mushin I", "IDONA CENTRAL", "27/07/01/002"),
            ("Ogun", "Ijebu East", "Ijebu Mushin II", "MUSHIN MARKET SQUARE", "27/07/02/001"),
            ("Ogun", "Ijebu East", "Ijebu Ife I", "ITAKO OLUWERI SQUARE", "27/07/03/001"),
            ("Ogun", "Ijebu East", "Ogbere", "PALACE FRONTAGE OGBERE", "27/07/08/001"),
            ("Ogun", "Ijebu East", "Ajebandele", "ST. SAVIOURS SCH AJEBANDELE", "27/07/11/001"),
            ("Ogun", "Sagamu", "Makun I", "ST. PAULS PRY SCH MAKUN I", "27/18/01/001"),
            ("Ogun", "Sagamu", "Makun I", "EWUSI PALACE SQUARE", "27/18/01/002"),
            ("Ogun", "Sagamu", "Makun II", "AJEDE COMMUNITY SCH", "27/18/02/001"),
            ("Ogun", "Ijebu Ode", "Porogun I", "POROGUN CHURCH PRY SCH", "27/11/01/001"),
            ("Ogun", "Ijebu Ode", "Porogun II", "ITA OLE MARKET SQUARE", "27/11/02/001"),
            ("Ogun", "Ijebu North", "Ago Iwoye I", "METHODIST PRY SCH AGO IWOYE", "27/09/01/001"),
            ("Ogun", "Ikenne", "Iperu I", "AKESAN MARKET SQUARE IPERU", "27/12/01/001"),
            ("Ogun", "Remo North", "Isara I", "ISARA TOWN HALL", "27/17/01/001"),
            ("Ogun", "Ijebu North East", "Atan", "ATAN TOWN HALL", "27/10/01/001"),
            ("Ogun", "Ogun Waterside", "Abigi", "ABIGI TOWN HALL", "27/15/01/001"),
            ("Ogun", "Odogbolu", "Odogbolu I", "ODOGBOLU TOWN HALL", "27/14/01/001")
        ]
        cursor.executemany("INSERT INTO locations (state, lga, ward, polling_unit, pu_code) VALUES (?, ?, ?, ?, ?)", ogun_east_locations)
        
    conn.commit()
    conn.close()

init_db()

# ==========================================
# WORKFLOW ENGINE & ROUTING LOGIC
# ==========================================
def get_assigned_verifier(submission_lga, submission_ward):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE role = 'Collation Admin' AND LOWER(assigned_lga) = LOWER(?) AND LOWER(assigned_ward) = LOWER(?) LIMIT 1", (submission_lga, submission_ward))
    ward_admin = cursor.fetchone()
    if ward_admin:
        conn.close()
        return ward_admin['full_name']
        
    cursor.execute("SELECT full_name FROM users WHERE role = 'LGA Admin' AND LOWER(assigned_lga) = LOWER(?) LIMIT 1", (submission_lga,))
    lga_admin = cursor.fetchone()
    conn.close()
    if lga_admin:
        return lga_admin['full_name']
        
    return "Super Admin"

def save_pending_photo_submission(data, username):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT role, assigned_lga, assigned_ward, assigned_pu_code, assigned_pu_name FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if user and user['role'] == 'Field Officer':
        lga = user['assigned_lga']
        ward = user['assigned_ward']
        pu_code = user['assigned_pu_code']
        pu_name = user['assigned_pu_name']
    else:
        lga = data.get('lga', '')
        ward = data.get('ward', '')
        pu_code = data.get('pu_code', '')
        pu_name = data.get('polling_unit', '')

    assigned_admin = get_assigned_verifier(lga, ward)
    
    cursor.execute('''
        INSERT INTO submissions (election_id, election_name, election_type, lga, ward, polling_unit, pu_code, image_url, submitted_by, assigned_to, timestamp, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
    ''', (
        data.get('election_id', '1'),
        data.get('election_name', 'Ogun East Senatorial District Election 2027'),
        data.get('election_type', 'Senatorial'),
        lga, ward, pu_name, pu_code,
        data.get('image_url', ''),
        username, assigned_admin,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()
    return {
        "status": "success",
        "message": f"Result sheet submitted for {pu_name} ({pu_code})! Routed to [{assigned_admin}] for verification."
    }

def get_live_collation(election_id=None, filter_lga=None, election_type=None):
    conn = get_db()
    cursor = conn.cursor()

    target_election_name = None
    registered_voters = 1150000

    if election_id and str(election_id).strip() != 'all':
        cursor.execute("SELECT name, type, registered_voters FROM elections WHERE id = ? OR name = ?", (str(election_id), str(election_id)))
        e_row = cursor.fetchone()
        if e_row:
            target_election_name = e_row['name']
            registered_voters = e_row['registered_voters'] or 1150000

    cursor.execute("SELECT full_name, party, photo_url FROM candidates")
    candidates_map = {c['party']: {"name": c['full_name'], "photo": c['photo_url']} for c in cursor.fetchall()}

    cursor.execute("SELECT acronym, name, logo_url FROM parties ORDER BY acronym ASC")
    all_parties = cursor.fetchall()
    parties_logo_map = {p['acronym']: p['logo_url'] for p in all_parties}
    parties_name_map = {p['acronym']: p['name'] for p in all_parties}

    if filter_lga and filter_lga != 'all':
        cursor.execute("SELECT COUNT(*) FROM locations WHERE LOWER(lga) = LOWER(?)", (filter_lga,))
    else:
        cursor.execute("SELECT COUNT(*) FROM locations")
    total_pus_count = cursor.fetchone()[0] or 1

    query = "SELECT party_votes, valid_votes, rejected_votes, total_votes_cast FROM submissions WHERE status = 'ACCEPTED'"
    params = []
    
    if target_election_name:
        query += " AND (election_id = ? OR election_name = ?)"
        params.extend([str(election_id), target_election_name])
    elif election_type and election_type != 'all':
        query += " AND LOWER(election_type) = LOWER(?)"
        params.append(election_type)

    if filter_lga and filter_lga != 'all':
        query += " AND LOWER(lga) = LOWER(?)"
        params.append(filter_lga)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    pu_query = "SELECT COUNT(DISTINCT pu_code) FROM submissions WHERE status = 'ACCEPTED'"
    pu_params = []
    if target_election_name:
        pu_query += " AND (election_id = ? OR election_name = ?)"
        pu_params.extend([str(election_id), target_election_name])
    elif election_type and election_type != 'all':
        pu_query += " AND LOWER(election_type) = LOWER(?)"
        pu_params.append(election_type)

    if filter_lga and filter_lga != 'all':
        pu_query += " AND LOWER(lga) = LOWER(?)"
        pu_params.append(filter_lga)

    cursor.execute(pu_query, pu_params)
    verified_pus = cursor.fetchone()[0] or 0
    conn.close()
    
    party_totals = {p['acronym']: 0 for p in all_parties}
    grand_valid = 0
    grand_rejected = 0
    grand_total_cast = 0
    
    for r in rows:
        votes = json.loads(r['party_votes']) if r['party_votes'] else {}
        grand_valid += r['valid_votes']
        grand_rejected += r['rejected_votes']
        grand_total_cast += r['total_votes_cast']
        for party, count in votes.items():
            party_totals[party] = party_totals.get(party, 0) + int(count)
            
    leader = {"candidate": "Awaiting Verified Results", "party": "N/A", "votes": 0, "percentage": "0%", "photo": "", "party_logo": "", "margin": 0}
    
    if grand_valid > 0 and any(v > 0 for v in party_totals.values()):
        sorted_parties = sorted(party_totals.items(), key=lambda x: x[1], reverse=True)
        top_party, top_votes = sorted_parties[0]
        second_votes = sorted_parties[1][1] if len(sorted_parties) > 1 else 0
        margin = top_votes - second_votes
        
        top_pct = round((top_votes / grand_valid * 100), 1)
        cand_info = candidates_map.get(top_party, {"name": "Candidate Not Assigned", "photo": ""})
        leader = {
            "candidate": cand_info["name"], "party": top_party, "votes": top_votes,
            "percentage": f"{top_pct}%", "photo": cand_info["photo"], "party_logo": parties_logo_map.get(top_party, ""),
            "margin": margin
        }
        
    standings = []
    for party_acronym, count in party_totals.items():
        pct = round((count / grand_valid * 100), 1) if grand_valid > 0 else 0.0
        cand_info = candidates_map.get(party_acronym, {"name": "Candidate Not Assigned", "photo": ""})
        standings.append({
            "candidate": cand_info["name"],
            "party": party_acronym,
            "party_full_name": parties_name_map.get(party_acronym, party_acronym),
            "photo": cand_info["photo"],
            "party_logo": parties_logo_map.get(party_acronym, ""),
            "votes": count,
            "percentage": f"{pct}%",
            "percent_num": pct
        })
        
    standings.sort(key=lambda x: (-x['votes'], x['party']))
    
    return {
        "leader": leader,
        "metrics": {
            "registered": registered_voters, "votes_cast": grand_total_cast,
            "turnout": f"{round((grand_total_cast / registered_voters * 100), 1) if grand_total_cast > 0 else 0}%",
            "valid": grand_valid, "rejected": grand_rejected,
            "pus_verified": f"{verified_pus}/{total_pus_count}",
            "progress_pct": f"{round((verified_pus / total_pus_count * 100), 1) if total_pus_count > 0 else 0}%"
        },
        "standings": standings
    }

# ==========================================
# REST API ENDPOINTS
# ==========================================
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?) OR LOWER(full_name) = LOWER(?)", (username, username))
    user = cursor.fetchone()
    conn.close()

    if user and user['password_hash']:
        if check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return jsonify({
                "success": True,
                "username": user['username'],
                "full_name": user['full_name'],
                "role": user['role'],
                "assigned_lga": user['assigned_lga'] or '',
                "assigned_ward": user['assigned_ward'] or '',
                "assigned_pu_code": user['assigned_pu_code'] or '',
                "assigned_pu_name": user['assigned_pu_name'] or ''
            })
    return jsonify({"success": False, "message": "Invalid Username or Password. Use 'rotimi' and 'rotimi1972'"}), 401

@app.route('/api/upload-photo-result', methods=['POST'])
def upload_photo_result():
    if 'photo' not in request.files:
        return jsonify({"status": "error", "message": "No photograph attached"}), 400
    file = request.files['photo']
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        username = request.form.get("submitted_by", "")
        data = {
            "election_id": request.form.get("election_id", "1"),
            "election_name": request.form.get("election_name", "Ogun East Senatorial District Election 2027"),
            "election_type": request.form.get("election_type", "Senatorial"),
            "lga": request.form.get("lga", ""),
            "ward": request.form.get("ward", ""),
            "polling_unit": request.form.get("polling_unit", ""),
            "pu_code": request.form.get("pu_code", ""),
            "image_url": f"/{filepath}"
        }
        return jsonify(save_pending_photo_submission(data, username))
    return jsonify({"status": "error", "message": "Invalid file format"}), 400

@app.route('/api/review-queue', methods=['GET'])
def review_queue():
    username = request.args.get('username', '')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT role, assigned_lga, assigned_ward FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify([])

    role = user['role']
    lga = user['assigned_lga']
    ward = user['assigned_ward']

    if role == 'Super Admin':
        cursor.execute("SELECT * FROM submissions WHERE status = 'PENDING' ORDER BY id DESC")
    elif role == 'LGA Admin':
        cursor.execute("SELECT * FROM submissions WHERE status = 'PENDING' AND LOWER(lga) = LOWER(?) ORDER BY id DESC", (lga,))
    elif role == 'Collation Admin':
        cursor.execute("SELECT * FROM submissions WHERE status = 'PENDING' AND LOWER(lga) = LOWER(?) AND LOWER(ward) = LOWER(?) ORDER BY id DESC", (lga, ward))
    else:
        cursor.execute("SELECT * FROM submissions WHERE 1=0")

    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/admin-verify-collate', methods=['POST'])
def admin_verify_collate_route():
    d = request.json
    sub_id = d.get('submission_id')
    party_votes = d.get('party_votes', {})
    rejected_votes = int(d.get('rejected_votes', 0))
    status = d.get('status', 'ACCEPTED')
    notes = d.get('notes', '')
    is_flagged = 1 if d.get('is_flagged') else 0
    flag_reason = d.get('flag_reason', '')
    verified_by = d.get('verified_by', 'Admin')

    conn = get_db()
    cursor = conn.cursor()
    valid_votes = sum(int(v) for v in party_votes.values())
    total_cast = valid_votes + rejected_votes

    cursor.execute('''
        UPDATE submissions 
        SET party_votes = ?, valid_votes = ?, rejected_votes = ?, total_votes_cast = ?, status = ?, review_notes = ?, is_flagged = ?, flag_reason = ?, verified_by = ?, verified_at = ?
        WHERE id = ?
    ''', (json.dumps(party_votes), valid_votes, rejected_votes, total_cast, status, notes, is_flagged, flag_reason, verified_by, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sub_id))
    
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": f"Submission #{sub_id} processed!"})

@app.route('/api/live-results', methods=['GET'])
def live_results():
    election_id = request.args.get('election_id', 'all')
    election_type = request.args.get('election_type', 'all')
    filter_lga = request.args.get('lga', 'all')
    return jsonify(get_live_collation(election_id, filter_lga, election_type))

@app.route('/api/ward-results', methods=['GET'])
def ward_results():
    filter_lga = request.args.get('lga', 'all')
    filter_type = request.args.get('election_type', 'all')
    
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM submissions WHERE status = 'ACCEPTED'"
    params = []
    
    if filter_lga and filter_lga != 'all':
        query += " AND LOWER(lga) = LOWER(?)"
        params.append(filter_lga)
    if filter_type and filter_type != 'all':
        query += " AND LOWER(election_type) = LOWER(?)"
        params.append(filter_type)
        
    query += " ORDER BY lga, ward, polling_unit"
    
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    for r in rows:
        r['party_votes'] = json.loads(r['party_votes']) if r['party_votes'] else {}
    return jsonify(rows)

@app.route('/api/export-csv', methods=['GET'])
def export_csv():
    filter_lga = request.args.get('lga', 'all')
    conn = get_db()
    cursor = conn.cursor()
    if filter_lga and filter_lga != 'all':
        cursor.execute("SELECT * FROM submissions WHERE status = 'ACCEPTED' AND LOWER(lga) = LOWER(?)", (filter_lga,))
    else:
        cursor.execute("SELECT * FROM submissions WHERE status = 'ACCEPTED'")
    rows = cursor.fetchall()
    
    cursor.execute("SELECT acronym FROM parties ORDER BY acronym ASC")
    all_parties = [p['acronym'] for p in cursor.fetchall()]
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    
    header = ['Submission ID', 'Election Name', 'Type', 'LGA', 'Ward', 'Polling Unit', 'PU Code'] + all_parties + ['Valid Votes', 'Rejected Votes', 'Total Cast', 'Verified By', 'Timestamp']
    writer.writerow(header)

    for r in rows:
        votes = json.loads(r['party_votes']) if r['party_votes'] else {}
        party_cols = [votes.get(p, 0) for p in all_parties]
        row_data = [r['id'], r['election_name'], r['election_type'], r['lga'], r['ward'], r['polling_unit'], r['pu_code']] + party_cols + [r['valid_votes'], r['rejected_votes'], r['total_votes_cast'], r['verified_by'], r['verified_at']]
        writer.writerow(row_data)

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=Ogun_East_2027_Full_Results.csv"}
    )

@app.route('/api/admin/users', methods=['GET', 'POST'])
def handle_users():
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'POST':
        d = request.json
        creator = d.get('created_by_user', 'Super Admin')
        pass_hash = generate_password_hash(d.get('password', 'Pass1234!'))
        role = d.get('role')
        
        cursor.execute("SELECT role, assigned_lga FROM users WHERE username = ?", (creator,))
        creator_user = cursor.fetchone()
        
        if creator_user and creator_user['role'] == 'Super Admin':
            if role not in ['LGA Admin', 'Viewer']:
                conn.close()
                return jsonify({"success": False, "message": "Super Admin can ONLY create LGA Admins or Viewers!"}), 400
        elif creator_user and creator_user['role'] == 'LGA Admin':
            if role not in ['Collation Admin', 'Field Officer', 'Viewer']:
                conn.close()
                return jsonify({"success": False, "message": "LGA Admin can ONLY create Collation Admins, Field Officers, or Viewers!"}), 400

        cursor.execute("""
            INSERT INTO users (full_name, username, password_hash, role, assigned_lga, assigned_ward, assigned_pu_code, assigned_pu_name, email, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            d.get('full_name'), d.get('username'), pass_hash, role,
            d.get('assigned_lga', ''), d.get('assigned_ward', ''),
            d.get('assigned_pu_code', ''), d.get('assigned_pu_name', ''),
            d.get('email'), creator, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"User '{d.get('username')}' ({role}) created!"})
    
    requester = request.args.get('username', '')
    cursor.execute("SELECT role, assigned_lga FROM users WHERE username = ?", (requester,))
    user = cursor.fetchone()
    
    if user and user['role'] == 'LGA Admin':
        cursor.execute("SELECT id, full_name, username, role, assigned_lga, assigned_ward, assigned_pu_code, email FROM users WHERE LOWER(assigned_lga) = LOWER(?) ORDER BY id DESC", (user['assigned_lga'],))
    else:
        cursor.execute("SELECT id, full_name, username, role, assigned_lga, assigned_ward, assigned_pu_code, email FROM users ORDER BY id DESC")
        
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/admin/elections', methods=['GET', 'POST', 'PUT'])
def handle_elections():
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'POST':
        d = request.json
        cursor.execute("INSERT INTO elections (name, type, constituency, registered_voters, is_active) VALUES (?, ?, ?, ?, 1)",
                       (d.get('name'), d.get('type'), d.get('constituency'), d.get('registered_voters', 250000)))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Election Created!"})
    elif request.method == 'PUT':
        d = request.json
        cursor.execute("UPDATE elections SET is_active = ? WHERE id = ?", (d.get('is_active'), d.get('id')))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Election status updated!"})
        
    cursor.execute("SELECT * FROM elections ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/admin/parties', methods=['GET'])
def handle_parties():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM parties ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/admin/candidates', methods=['GET', 'POST'])
def handle_candidates():
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        party = request.form.get('party', '').strip()
        election_name = request.form.get('election_name', '').strip()

        photo_url = ''
        if 'photo' in request.files and request.files['photo'].filename != '':
            file = request.files['photo']
            if allowed_file(file.filename):
                filename = secure_filename(f"cand_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                photo_url = f"/{filepath}"

        cursor.execute("SELECT id FROM candidates WHERE party = ? AND election_name = ?", (party, election_name))
        existing = cursor.fetchone()
        
        if existing:
            if photo_url:
                cursor.execute("UPDATE candidates SET full_name = ?, photo_url = ?, created_at = ? WHERE id = ?",
                               (full_name, photo_url, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), existing['id']))
            else:
                cursor.execute("UPDATE candidates SET full_name = ?, created_at = ? WHERE id = ?",
                               (full_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), existing['id']))
        else:
            cursor.execute("INSERT INTO candidates (full_name, party, election_name, photo_url, created_at) VALUES (?, ?, ?, ?, ?)",
                           (full_name, party, election_name, photo_url, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"Candidate '{full_name}' ({party}) successfully updated!"})
        
    cursor.execute("SELECT * FROM candidates ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/admin/reset-system', methods=['POST'])
def reset_system():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM submissions")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='submissions'")
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "⚡ System Reset Complete!"})

@app.route('/api/locations/lgas', methods=['GET'])
def get_lgas():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT lga FROM locations ORDER BY lga ASC")
    lgas = [r['lga'] for r in cursor.fetchall()]
    conn.close()
    return jsonify(lgas)

@app.route('/api/locations/wards', methods=['GET'])
def get_wards():
    lga = request.args.get('lga', '')
    conn = get_db()
    cursor = conn.cursor()
    if lga:
        cursor.execute("SELECT DISTINCT ward FROM locations WHERE LOWER(lga) = LOWER(?) ORDER BY ward ASC", (lga,))
    else:
        cursor.execute("SELECT DISTINCT ward FROM locations ORDER BY ward ASC")
    wards = [r['ward'] for r in cursor.fetchall()]
    conn.close()
    return jsonify(wards)

@app.route('/api/locations/pus', methods=['GET'])
def get_pus():
    ward = request.args.get('ward', '')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT polling_unit, pu_code FROM locations WHERE LOWER(ward) = LOWER(?) ORDER BY id ASC", (ward,))
    pus = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(pus)

# ==========================================
# FRONTEND UI (MASTER SYSTEM ENGINE)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ogun East 2027 Election Watch</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background-color: #ffffff; color: #1a1a1a; min-height: 100vh; }
        .page { display: none; width: 100%; min-height: 100vh; }
        .page.active { display: flex; flex-direction: column; }
        
        #authPage { background-color: #ffffff; justify-content: center; align-items: center; padding: 24px 20px; }
        .auth-container { width: 100%; max-width: 420px; display: flex; flex-direction: column; align-items: center; text-align: center; }
        .auth-title { color: #0c235c; font-size: 24px; font-weight: 800; margin-top: 10px; margin-bottom: 4px; }
        .auth-subtitle { color: #2563eb; font-size: 13px; font-weight:700; margin-bottom: 25px; }
        .auth-form { width: 100%; text-align: left; }
        .input-group { margin-bottom: 16px; }
        .input-group label { display: block; font-size: 13px; font-weight: 700; color: #1a1a1a; margin-bottom: 6px; }
        .input-group input, .input-group select { width: 100%; padding: 12px 14px; font-size: 14px; border: 1.5px solid #d1d5db; border-radius: 8px; outline: none; }
        .btn-submit { width: 100%; background-color: #0c235c; color: #ffffff; border: none; padding: 14px; border-radius: 8px; font-size: 15px; font-weight: 700; cursor: pointer; }

        #dashboardPage { background-color: #ffffff; padding-bottom: 75px; }
        .app-header { background-color: #0c235c; color: #ffffff; padding: 18px 16px 12px; }
        .app-header h1 { font-size: 20px; font-weight: 900; }
        .app-header p { font-size: 12.5px; color: #cbd5e1; }
        .user-bar { background-color: #081740; color: #ffffff; padding: 10px 16px; display: flex; justify-content: space-between; align-items: center; }
        .user-info { display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; flex-wrap: wrap; }
        .role-badge { background-color: #2563eb; color: #fff; font-size: 10px; padding: 2px 6px; border-radius: 12px; text-transform: uppercase; font-weight: 800; }
        .scope-badge { background-color: #16a34a; color: #fff; font-size: 10px; padding: 2px 6px; border-radius: 12px; font-weight: 800; }
        .btn-logout { background-color: #ffffff; color: #0c235c; border: none; padding: 6px 16px; border-radius: 20px; font-size: 12px; font-weight: 700; cursor: pointer; }
        .dashboard-content { padding: 20px 16px; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .section-heading { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; color: #0c235c; }
        .info-box { background-color: #e0f2fe; border: 1px solid #bae6fd; border-radius: 10px; padding: 10px 12px; margin-bottom: 14px; font-size: 12.5px; color: #0369a1; }

        .leader-card { background-color: #0c235c; color: #ffffff; padding: 20px 16px; border-radius: 16px; text-align: center; display: flex; flex-direction: column; align-items: center; margin-bottom: 20px; }
        .avatar-circle { width: 80px; height: 80px; border-radius: 50%; background-color: #3b82f6; border: 3px solid #60a5fa; display: flex; justify-content: center; align-items: center; margin-bottom: 12px; font-size: 28px; overflow: hidden; }
        .leader-title { font-size: 20px; font-weight: 800; }
        .big-stat { font-size: 30px; font-weight: 900; }
        .percentage-stat { font-size: 18px; font-weight: 700; color: #93c5fd; }
        
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 20px; }
        .stat-card { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 4px; text-align: center; }
        .stat-value { font-size: 14px; font-weight: 900; color: #0c235c; display: block; }
        .stat-label { font-size: 9.5px; font-weight: 700; color: #64748b; }
        
        .progress-section { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px; margin-bottom: 20px; }
        .progress-track { width: 100%; height: 10px; background-color: #e2e8f0; border-radius: 6px; overflow: hidden; }
        .progress-fill { height: 100%; background-color: #0c235c; }

        .party-counter-grid { display: flex; flex-direction: column; gap: 10px; margin-top: 10px; }
        .party-card { background-color: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid #0c235c; border-radius: 10px; padding: 12px 14px; }
        .party-info { display: flex; justify-content: space-between; align-items: center; }
        .party-bar-bg { width: 100%; height: 6px; background-color: #f1f5f9; border-radius: 4px; margin-top: 8px; overflow: hidden; }
        .party-bar-fill { height: 100%; background-color: #2563eb; }

        .table-responsive { overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 10px; margin-bottom: 20px; }
        .results-table { width: 100%; border-collapse: collapse; font-size: 12px; text-align: left; }
        .results-table th, .results-table td { padding: 10px 6px; border-bottom: 1px solid #e2e8f0; white-space: nowrap; }
        .results-table th { background-color: #f1f5f9; color: #0c235c; font-weight: 800; }

        .wizard-step { display: none; }
        .wizard-step.active { display: block; }
        .btn-stack { display: flex; flex-direction: column; gap: 10px; }
        .btn-select-option { width: 100%; background-color: #0c235c; color: #ffffff; border: none; padding: 14px; border-radius: 10px; font-size: 14px; font-weight: 700; cursor: pointer; text-align: left; }
        .btn-secondary { width: 100%; background-color: #64748b; color: #ffffff; border: none; padding: 12px; border-radius: 10px; font-size: 14px; font-weight: 700; cursor: pointer; }
        .btn-action { width: 100%; background-color: #0c235c; color: #ffffff; border: none; padding: 12px; border-radius: 10px; font-weight: 700; cursor: pointer; }
        .input-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #e2e8f0; }
        .input-row input { width: 100px; padding: 6px 10px; border: 1px solid #ccc; border-radius: 6px; text-align: right; font-weight: 700; }

        .app-footer { text-align: center; margin-top: 30px; padding: 15px 0; font-size: 11.5px; color: #64748b; line-height: 1.5; border-top: 1px solid #e2e8f0; }
        .bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; height: 60px; background-color: #ffffff; border-top: 1px solid #e2e8f0; display: flex; justify-content: space-around; align-items: center; z-index: 100; }
        .nav-item { background: none; border: none; display: flex; flex-direction: column; align-items: center; color: #64748b; cursor: pointer; flex: 1; padding: 8px 0; font-weight: 600; font-size: 11px; }
        .nav-item.active { color: #0c235c; background-color: #eff6ff; font-weight: 800; }

        .modal-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; justify-content: center; align-items: center; padding: 16px; }
        .modal-overlay.active { display: flex; }
        .modal-card { background: #ffffff; border-radius: 16px; width: 100%; max-width: 440px; max-height: 90vh; overflow-y: auto; padding: 18px; }
    </style>
</head>
<body>

    <div id="authPage" class="page active">
        <div class="auth-container">
            <h1 class="auth-title">OGUN EAST 2027</h1>
            <p class="auth-subtitle">Official Election Collation Portal</p>

            <form id="loginForm" class="auth-form">
                <div class="input-group">
                    <label>Username Account ID</label>
                    <input type="text" id="username" placeholder="e.g. rotimi" required>
                </div>
                <div class="input-group">
                    <label>Password</label>
                    <input type="password" id="password" placeholder="e.g. rotimi1972" required>
                </div>
                <button type="submit" class="btn-submit">🔐 Sign In</button>
            </form>

            <footer class="app-footer">
                <p><strong>OGUN EAST 2027 ELECTION WATCH</strong></p>
                <p style="color:#2563eb; font-weight:700;">Multi-Tier Governance Architecture</p>
                <p>Designed by Willys Media World · 09018363715</p>
            </footer>
        </div>
    </div>

    <div id="dashboardPage" class="page">
        <header class="app-header">
            <h1>OGUN EAST 2027 WATCH</h1>
            <p>Real-Time Micro-Scoped Collation System</p>
        </header>

        <div class="user-bar">
            <div class="user-info">
                👤 <span id="userDisplayName">Guest</span>
                <span id="userRoleBadge" class="role-badge">Viewer</span>
                <span id="userScopeBadge" class="scope-badge" style="display:none;"></span>
            </div>
            <button id="logoutBtn" class="btn-logout">Exit</button>
        </div>

        <main class="dashboard-content">

            <!-- TAB 1: LIVE FEED & REAL-TIME PARTY COUNTER -->
            <section id="tab-live" class="tab-content active">
                <div class="section-heading"><h2>📊 Live District Collation</h2></div>

                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-bottom:12px;">
                    <div class="input-group" style="margin:0;">
                        <label>Select Election Category</label>
                        <select id="liveTypeSelect" onchange="onLiveFilterChanged()">
                            <option value="all">-- All Categories --</option>
                            <option value="Presidential">Presidential</option>
                            <option value="Senatorial">Senatorial (Ogun East)</option>
                            <option value="House of Representatives">House of Representatives</option>
                            <option value="Governorship">Governorship</option>
                            <option value="State House of Assembly">State House of Assembly</option>
                            <option value="LGA Chairman">LGA Chairman</option>
                            <option value="LGA Councillor">LGA Councillor</option>
                        </select>
                    </div>
                    <div class="input-group" style="margin:0;">
                        <label>Filter LGA</label>
                        <select id="liveLgaSelect" onchange="onLiveFilterChanged()"></select>
                    </div>
                </div>

                <div class="leader-card">
                    <h4>CURRENT VERIFIED LEADER</h4>
                    <div id="leaderAvatar" class="avatar-circle">👤</div>
                    <h3 id="leaderTitle" class="leader-title">Awaiting Verified Results</h3>
                    <p id="leaderParty" style="font-size:13px; color:#93c5fd; font-weight:700; margin-top:2px;"></p>
                    <div style="color:#64748b; margin:6px 0;">—</div>
                    <div id="leaderVotes" class="big-stat">0</div>
                    <div id="leaderPct" class="percentage-stat">0%</div>
                    <p id="leaderMargin" style="font-size:12px; color:#60a5fa; margin-top:4px; font-weight:700;"></p>
                </div>

                <div class="stats-grid">
                    <div class="stat-card"><span id="statReg" class="stat-value">1,150,000</span><span class="stat-label">REGISTERED</span></div>
                    <div class="stat-card"><span id="statCast" class="stat-value">0</span><span class="stat-label">VOTES CAST</span></div>
                    <div class="stat-card"><span id="statTurnout" class="stat-value">0.0%</span><span class="stat-label">TURNOUT</span></div>
                    <div class="stat-card"><span id="statValid" class="stat-value">0</span><span class="stat-label">VALID</span></div>
                    <div class="stat-card"><span id="statRejected" class="stat-value">0</span><span class="stat-label">REJECTED</span></div>
                    <div class="stat-card"><span id="statPUs" class="stat-value">0/0</span><span class="stat-label">PUS VERIFIED</span></div>
                </div>

                <div class="progress-section">
                    <div style="display:flex; justify-content:space-between; font-size:12.5px; font-weight:700; margin-bottom:6px;">
                        <span>Polling Units Collation Progress</span><span id="progressPctText">0.0%</span>
                    </div>
                    <div class="progress-track"><div id="progressFill" class="progress-fill" style="width: 0%;"></div></div>
                </div>

                <div class="section-heading"><h2>🗳️ All 19 Political Parties - Real-Time Counter</h2></div>
                <div id="standingsContainer" class="party-counter-grid"></div>
            </section>

            <!-- TAB 2: WARD / PU RESULTS TABLE -->
            <section id="tab-results" class="tab-content">
                <div class="section-heading">
                    <h2>📋 Ward / PU Breakdown</h2>
                    <button class="btn-submit" style="width:auto; padding:6px 12px; font-size:12px; background:#16a34a;" onclick="exportResultsCSV()">📄 Export CSV</button>
                </div>
                
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-bottom:12px;">
                    <div class="input-group" style="margin:0;">
                        <label>Filter Election Category</label>
                        <select id="resultsTypeSelect" onchange="loadWardTable()">
                            <option value="all">-- All Categories --</option>
                            <option value="Presidential">Presidential</option>
                            <option value="Senatorial">Senatorial</option>
                            <option value="House of Representatives">House of Representatives</option>
                            <option value="Governorship">Governorship</option>
                            <option value="State House of Assembly">State House of Assembly</option>
                            <option value="LGA Chairman">LGA Chairman</option>
                            <option value="LGA Councillor">LGA Councillor</option>
                        </select>
                    </div>
                    <div class="input-group" style="margin:0;">
                        <label>Filter Local Government</label>
                        <select id="resultsLgaSelect" onchange="loadWardTable()"></select>
                    </div>
                </div>

                <div class="table-responsive">
                    <table class="results-table">
                        <thead id="resultsTableHeader"></thead>
                        <tbody id="resultsTableBody">
                            <tr><td colspan="25" style="text-align:center;">No collated results found.</td></tr>
                        </tbody>
                    </table>
                </div>
            </section>

            <!-- TAB 3: UPLOAD RESULT SHEET -->
            <section id="tab-upload" class="tab-content">
                <div class="section-heading"><h2>📥 Submit Result Sheet (EC8A)</h2></div>

                <div id="uploadCollationAdminBlocked" style="display:none; background:#fef2f2; border:2px solid #fca5a5; padding:16px; border-radius:12px; text-align:center; color:#991b1b; font-weight:700;">
                    ⛔ Upload Disabled for Collation Admins. You are authorized ONLY to Review & Verify submissions.
                </div>

                <div id="uploadWizardContainer">
                    <div id="fieldOfficerLockedBox" style="display:none; background:#eff6ff; border:2px solid #2563eb; padding:16px; border-radius:12px; margin-bottom:15px;">
                        <h3 style="color:#1e40af; font-size:15px; margin-bottom:6px;">🔒 Your Pre-Assigned Polling Unit</h3>
                        <p style="font-size:13px; color:#1e3a8a;" id="fieldLockLgaWard"></p>
                        <p style="font-size:15px; font-weight:900; color:#0c235c; margin-top:4px;" id="fieldLockPuName"></p>
                        <p style="font-size:12px; font-weight:700; color:#2563eb;" id="fieldLockPuCode"></p>
                    </div>

                    <div id="uploadStep1" class="wizard-step active">
                        <h3 style="margin-bottom:12px; color:#0c235c;">1. Select Local Government Area (LGA)</h3>
                        <div class="btn-stack" id="lgasListStack"></div>
                    </div>

                    <div id="uploadStep2" class="wizard-step">
                        <h3 style="margin-bottom:12px; color:#0c235c;">2. Select Election Category</h3>
                        <div class="btn-stack" id="electionsListStack"></div>
                        <button class="btn-secondary" style="margin-top:10px;" id="btnBackToStep1" onclick="goToUploadStep(1)">← Back</button>
                    </div>

                    <div id="uploadStep3" class="wizard-step">
                        <h3 style="margin-bottom:12px; color:#0c235c;">3. Select Ward</h3>
                        <div class="btn-stack" id="wardsListStack"></div>
                        <button class="btn-secondary" style="margin-top:10px;" onclick="goToUploadStep(2)">← Back</button>
                    </div>

                    <div id="uploadStep4" class="wizard-step">
                        <h3 style="margin-bottom:12px; color:#0c235c;">4. Select Polling Unit</h3>
                        <div class="btn-stack" id="pusListStack"></div>
                        <button class="btn-secondary" style="margin-top:10px;" onclick="goToUploadStep(3)">← Back</button>
                    </div>

                    <div id="uploadStep5" class="wizard-step">
                        <h3 style="margin-bottom:12px; color:#0c235c;">5. Capture / Attach EC8A Photo</h3>
                        <div style="background:#1d3557; color:#fff; padding:14px; border-radius:10px; margin-bottom:15px;">
                            <h4 id="summaryElection">Ogun East Election</h4>
                            <p id="summaryWardPU" style="font-size:12px; color:#a8dadc; margin-top:4px;"></p>
                        </div>

                        <div style="margin-bottom:15px;">
                            <label class="btn-action" style="display:block; text-align:center; background:#2563eb; cursor:pointer;">
                                📷 Take Photo / Attach Image
                                <input type="file" id="ec8aPhoto" accept="image/*" style="display:none;" onchange="previewUploadImage(this)">
                            </label>
                        </div>

                        <div id="imagePreviewBox" style="display:none; text-align:center; margin-bottom:15px;">
                            <img id="uploadPreviewImg" src="" style="width:100%; max-height:250px; object-fit:contain; border-radius:8px; border:2px solid #0c235c;">
                        </div>

                        <button id="btnSubmitPhoto" class="btn-submit" style="display:none;" onclick="submitPhotoOnly()">📤 Upload EC8A for Verification</button>
                        <button class="btn-secondary" style="margin-top:10px;" id="btnBackFromStep5" onclick="goToUploadStep(4)">← Back</button>
                    </div>
                </div>
            </section>

            <!-- TAB 4: REVIEW & COLLATION -->
            <section id="tab-review" class="tab-content">
                <div class="section-heading"><h2 id="reviewTabTitle">🔍 Verification Queue</h2></div>
                <div class="info-box" id="reviewScopeBanner"></div>
                <div id="reviewQueueList"></div>
            </section>

            <!-- TAB 5: ADMINISTRATION -->
            <section id="tab-admin" class="tab-content">
                <div class="section-heading"><h2>⚙️ Staff & Account Administration</h2></div>
                
                <div style="margin-bottom:15px;">
                    <button class="btn-submit" style="background:#2563eb;" onclick="copyViewerLink()">📋 Copy Dedicated Viewer Access Link</button>
                </div>

                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-bottom:15px;">
                    <button class="btn-select-option" style="text-align:center;" onclick="openAdminModal('user')">👤 Create & Scope User</button>
                    <button class="btn-select-option" style="text-align:center;" onclick="openAdminModal('candidate')">👥 Candidates Management</button>
                    <button class="btn-select-option" style="text-align:center;" onclick="loadAdminData('users')">📜 View Staff Registry</button>
                    <button class="btn-select-option" style="text-align:center;" onclick="openAdminModal('election')" id="btnManageElections">📦 Elections & Ongoing Activation</button>
                </div>
                <div id="adminDataDisplay"></div>

                <div id="superAdminResetBox" style="background:#fef2f2; border:1px solid #fca5a5; padding:14px; border-radius:12px; margin-top:20px;">
                    <h4 style="color:#991b1b;">🚨 District System Reset</h4>
                    <p style="font-size:12px; color:#991b1b; margin:6px 0 10px;">Wipes all result submissions across all 9 LGAs and resets district tallies to 0.</p>
                    <button class="btn-submit" style="background:#dc2626;" onclick="triggerSystemReset()">⚡ Reset System Data</button>
                </div>
            </section>

            <footer class="app-footer">
                <p><strong>OGUN EAST 2027 ELECTION WATCH</strong></p>
                <p style="color:#2563eb; font-weight:700;">Multi-Tier Governance Architecture</p>
                <p>Designed by Willys Media World · 09018363715</p>
            </footer>
        </main>

        <nav class="bottom-nav">
            <button class="nav-item active" data-tab="live" id="navLiveBtn">Live</button>
            <button class="nav-item" data-tab="results" id="navResultsBtn">Results</button>
            <button class="nav-item" data-tab="upload" id="navUploadBtn">Upload</button>
            <button class="nav-item" data-tab="review" id="navReviewBtn">Review</button>
            <button class="nav-item" data-tab="admin" id="navAdminBtn">Admin</button>
        </nav>
    </div>

    <!-- CREATE USER & SCOPING MODAL -->
    <div id="adminUserModal" class="modal-overlay">
        <div class="modal-card">
            <h3>👤 Create & Scope User Account</h3>
            <div class="input-group"><label>Full Name</label><input type="text" id="adminUserFullName" placeholder="e.g. Chief Adebayo"></div>
            <div class="input-group"><label>Username</label><input type="text" id="adminUsername" placeholder="e.g. adebayo_makun"></div>
            <div class="input-group"><label>Account Password</label><input type="password" id="adminUserPassword" placeholder="Set Account Password"></div>
            <div class="input-group">
                <label>User Role Hierarchy Level</label>
                <select id="adminUserRole" onchange="onRoleSelectionChanged()"></select>
            </div>

            <div class="input-group" id="groupAssignLga">
                <label>Assign LGA</label>
                <select id="adminUserLga" onchange="onAdminLgaChanged()"></select>
            </div>
            <div class="input-group" id="groupAssignWard" style="display:none;">
                <label>Assign Ward</label>
                <select id="adminUserWard" onchange="onAdminWardChanged()"></select>
            </div>
            <div class="input-group" id="groupAssignPu" style="display:none;">
                <label>Assign Polling Unit</label>
                <select id="adminUserPu"></select>
            </div>

            <div class="input-group"><label>Email Address</label><input type="email" id="adminUserEmail" placeholder="user@domain.com"></div>
            <button class="btn-submit" style="background:#16a34a;" onclick="submitCreateUser()">Save Scoped Account</button>
            <button class="btn-secondary" style="margin-top:8px;" onclick="closeAdminModals()">Cancel</button>
        </div>
    </div>

    <!-- ELECTION ACTIVATION MODAL -->
    <div id="adminElectionModal" class="modal-overlay">
        <div class="modal-card">
            <h3>📦 Ongoing Elections Activation</h3>
            <div id="electionsActivationList" style="margin-bottom:15px;"></div>
            <button class="btn-secondary" onclick="closeAdminModals()">Done</button>
        </div>
    </div>

    <!-- CANDIDATE MODAL -->
    <div id="adminCandidateModal" class="modal-overlay">
        <div class="modal-card">
            <h3>👥 Add / Update Candidate</h3>
            <div class="input-group"><label>Candidate Full Name</label><input type="text" id="adminCandName" placeholder="Enter Full Name"></div>
            <div class="input-group"><label>Political Party (19 Parties)</label><select id="adminCandParty"></select></div>
            <div class="input-group"><label>Election Category</label><select id="adminCandElection"></select></div>
            <div class="input-group"><label>Candidate Photograph</label><input type="file" id="adminCandPhoto" accept="image/*"></div>
            <button class="btn-submit" style="background:#16a34a;" onclick="submitCreateCandidate()">Save Candidate Record</button>
            <button class="btn-secondary" style="margin-top:8px;" onclick="closeAdminModals()">Cancel</button>
        </div>
    </div>

    <!-- REVIEW COLLATION MODAL -->
    <div id="reviewModal" class="modal-overlay">
        <div class="modal-card">
            <h3>🔍 Verification & Collation</h3>
            <img id="modalImage" src="" style="width:100%; height:180px; object-fit:contain; background:#1e293b; border-radius:8px; margin:8px 0;">
            <div id="modalDetails" style="font-size:12px; background:#f1f5f9; padding:8px; border-radius:6px; margin-bottom:10px;"></div>
            <div id="reviewPartyInputs"></div>
            
            <div style="margin-top:10px; background:#fff1f2; padding:10px; border-radius:8px; border:1px solid #fecdd3;">
                <label style="font-size:12px; font-weight:800; color:#9f1239; display:flex; align-items:center; gap:6px;">
                    <input type="checkbox" id="reviewFlagged"> ⚠️ Flag Submission Discrepancy / Incident
                </label>
                <input type="text" id="reviewFlagReason" placeholder="Reason for flag..." style="width:100%; padding:6px; margin-top:6px; border:1px solid #fda4af; border-radius:4px; font-size:12px;">
            </div>

            <textarea id="reviewNotes" placeholder="Collation Notes..." style="width:100%; height:40px; padding:6px; margin-top:8px;"></textarea>
            <div style="display:flex; gap:8px; margin-top:10px;">
                <button class="btn-submit" style="background:#16a34a; flex:1;" onclick="submitManualCollation('ACCEPTED')">✓ Accept & Collate</button>
                <button class="btn-submit" style="background:#dc2626; flex:1;" onclick="submitManualCollation('REJECTED')">✕ Reject</button>
            </div>
            <button class="btn-secondary" style="margin-top:8px;" onclick="closeReviewModal()">Close</button>
        </div>
    </div>

    <script>
        let currentUploadData = { lga: '', election_name: '', election_id: '1', election_type: '', ward: '', polling_unit: '', pu_code: '' };
        let activeModalSubmissionId = null;
        let selectedPhotoFile = null;
        let allPartiesList = [];
        
        let currentUser = {
            username: '', full_name: '', role: 'Viewer',
            assigned_lga: '', assigned_ward: '', assigned_pu_code: '', assigned_pu_name: ''
        };

        document.addEventListener('DOMContentLoaded', () => {
            fetch('/api/admin/parties').then(r=>r.json()).then(p => { allPartiesList = p; buildResultsTableHeader(); });

            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.has('viewer')) {
                openGuestViewer();
            }

            const loginForm = document.getElementById('loginForm');
            if (loginForm) {
                loginForm.addEventListener('submit', (e) => {
                    e.preventDefault();
                    const u = document.getElementById('username')?.value || '';
                    const p = document.getElementById('password')?.value || '';
                    
                    fetch('/api/login', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ username: u, password: p })
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            currentUser = data;
                            applyRolePermissions();
                            document.getElementById('authPage').classList.remove('active');
                            document.getElementById('dashboardPage').classList.add('active');
                            initDropdowns().then(() => {
                                document.querySelector('.nav-item[data-tab="live"]').click();
                            });
                        } else {
                            alert(data.message || "Invalid Login Credentials");
                        }
                    });
                });
            }

            document.getElementById('logoutBtn').addEventListener('click', () => {
                document.getElementById('dashboardPage').classList.remove('active');
                document.getElementById('authPage').classList.add('active');
            });

            document.querySelectorAll('.nav-item').forEach(item => {
                item.addEventListener('click', () => {
                    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
                    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
                    item.classList.add('active');
                    const tab = item.getAttribute('data-tab');
                    document.getElementById('tab-' + tab).classList.add('active');
                    if (tab === 'live') loadLiveResults();
                    if (tab === 'results') loadWardTable();
                    if (tab === 'upload') loadUploadWizardData();
                    if (tab === 'review') loadReviewQueue();
                    if (tab === 'admin') loadAdminData('users');
                });
            });
        });

        function openGuestViewer() {
            currentUser = { username: 'viewer', full_name: 'Assigned Viewer', role: 'Viewer', assigned_lga: '', assigned_ward: '', assigned_pu_code: '', assigned_pu_name: '' };
            applyRolePermissions();
            document.getElementById('authPage').classList.remove('active');
            document.getElementById('dashboardPage').classList.add('active');
            initDropdowns().then(() => {
                document.querySelector('.nav-item[data-tab="live"]').click();
            });
        }

        function copyViewerLink() {
            const viewerUrl = window.location.origin + window.location.pathname + '?viewer=1';
            navigator.clipboard.writeText(viewerUrl);
            alert("📋 Dedicated Viewer Access Link copied to clipboard!\n" + viewerUrl);
        }

        function applyRolePermissions() {
            document.getElementById('userDisplayName').innerText = currentUser.full_name || currentUser.username;
            document.getElementById('userRoleBadge').innerText = currentUser.role;

            const scopeBadge = document.getElementById('userScopeBadge');
            if (currentUser.role === 'Field Officer') {
                scopeBadge.innerText = `PU: ${currentUser.assigned_pu_code}`;
                scopeBadge.style.display = 'inline-block';
            } else if (currentUser.role === 'Collation Admin') {
                scopeBadge.innerText = `Ward: ${currentUser.assigned_ward}`;
                scopeBadge.style.display = 'inline-block';
            } else if (currentUser.role === 'LGA Admin') {
                scopeBadge.innerText = `LGA: ${currentUser.assigned_lga}`;
                scopeBadge.style.display = 'inline-block';
            } else {
                scopeBadge.style.display = 'none';
            }

            const btnUpload = document.getElementById('navUploadBtn');
            const btnReview = document.getElementById('navReviewBtn');
            const btnAdmin = document.getElementById('navAdminBtn');

            btnUpload.style.display = 'none';
            btnReview.style.display = 'none';
            btnAdmin.style.display = 'none';

            if (currentUser.role === 'Super Admin') {
                btnUpload.style.display = 'flex';
                btnReview.style.display = 'flex';
                btnAdmin.style.display = 'flex';
                document.getElementById('superAdminResetBox').style.display = 'block';
                document.getElementById('btnManageElections').style.display = 'block';
            } else if (currentUser.role === 'LGA Admin') {
                btnUpload.style.display = 'flex';
                btnReview.style.display = 'flex';
                btnAdmin.style.display = 'flex';
                document.getElementById('superAdminResetBox').style.display = 'none';
                document.getElementById('btnManageElections').style.display = 'none';
            } else if (currentUser.role === 'Collation Admin') {
                btnReview.style.display = 'flex';
            } else if (currentUser.role === 'Field Officer') {
                btnUpload.style.display = 'flex';
            }
        }

        function initDropdowns() {
            return fetch('/api/locations/lgas').then(res => res.json()).then(lgas => {
                let lgaOpts = '<option value="all">-- All 9 LGAs (Ogun East) --</option>';
                lgas.forEach(l => { lgaOpts += `<option value="${l}">${l}</option>`; });
                document.getElementById('liveLgaSelect').innerHTML = lgaOpts;
                document.getElementById('resultsLgaSelect').innerHTML = lgaOpts;

                if (['LGA Admin', 'Collation Admin', 'Field Officer'].includes(currentUser.role) && currentUser.assigned_lga) {
                    document.getElementById('liveLgaSelect').value = currentUser.assigned_lga;
                    document.getElementById('resultsLgaSelect').value = currentUser.assigned_lga;
                }
            });
        }

        function onLiveFilterChanged() { loadLiveResults(); }

        function loadLiveResults() {
            const selectedType = document.getElementById('liveTypeSelect')?.value || 'all';
            const selectedLga = document.getElementById('liveLgaSelect')?.value || 'all';

            fetch(`/api/live-results?election_type=${encodeURIComponent(selectedType)}&lga=${encodeURIComponent(selectedLga)}`)
            .then(res => res.json())
            .then(data => {
                document.getElementById('leaderTitle').innerText = data.leader?.candidate || 'Awaiting Verified Results';
                document.getElementById('leaderParty').innerText = data.leader?.party !== 'N/A' ? 'Party: ' + data.leader?.party : '';
                document.getElementById('leaderVotes').innerText = (data.leader?.votes || 0).toLocaleString();
                document.getElementById('leaderPct').innerText = data.leader?.percentage || '0%';
                document.getElementById('leaderMargin').innerText = data.leader?.margin > 0 ? `Lead Gap: +${data.leader.margin.toLocaleString()} votes` : '';
                
                const avatar = document.getElementById('leaderAvatar');
                if (data.leader?.photo) avatar.innerHTML = `<img src="${data.leader.photo}" style="width:100%; height:100%; object-fit:cover;">`;
                else if (data.leader?.party_logo) avatar.innerHTML = `<img src="${data.leader.party_logo}" style="width:80%; height:80%; object-fit:contain;">`;
                else avatar.innerText = '👤';

                document.getElementById('statReg').innerText = (data.metrics?.registered || 1150000).toLocaleString();
                document.getElementById('statCast').innerText = (data.metrics?.votes_cast || 0).toLocaleString();
                document.getElementById('statTurnout').innerText = data.metrics?.turnout || '0.0%';
                document.getElementById('statValid').innerText = (data.metrics?.valid || 0).toLocaleString();
                document.getElementById('statRejected').innerText = (data.metrics?.rejected || 0).toLocaleString();
                document.getElementById('statPUs').innerText = data.metrics?.pus_verified || '0/0';
                document.getElementById('progressPctText').innerText = data.metrics?.progress_pct || '0.0%';
                document.getElementById('progressFill').style.width = data.metrics?.progress_pct || '0%';

                let html = '';
                (data.standings || []).forEach(item => {
                    html += `
                    <div class="party-card">
                        <div class="party-info">
                            <div style="display:flex; align-items:center; gap:10px;">
                                ${item.party_logo ? `<img src="${item.party_logo}" style="width:36px; height:36px; object-fit:contain;">` : '🏛️'}
                                <div>
                                    <h4 style="font-size:14.5px;">${item.party} - ${item.party_full_name}</h4>
                                    <p style="font-size:11px; color:#2563eb; font-weight:700;">Candidate: ${item.candidate}</p>
                                </div>
                            </div>
                            <div style="text-align:right;">
                                <span style="font-size:16px; font-weight:900; color:#0c235c;">${(item.votes||0).toLocaleString()}</span>
                                <br><small style="font-weight:700; color:#2563eb;">${item.percentage}</small>
                            </div>
                        </div>
                        <div class="party-bar-bg"><div class="party-bar-fill" style="width: ${item.percent_num}%;"></div></div>
                    </div>`;
                });
                document.getElementById('standingsContainer').innerHTML = html || '<p style="text-align:center; padding:10px;">No party data loaded.</p>';
            });
        }

        function buildResultsTableHeader() {
            let headerHtml = '<tr><th>LGA</th><th>Ward</th><th>Polling Unit</th><th>Category</th>';
            allPartiesList.forEach(p => { headerHtml += `<th>${p.acronym}</th>`; });
            headerHtml += '<th>Valid</th><th>Rejected</th><th>Total Cast</th></tr>';
            document.getElementById('resultsTableHeader').innerHTML = headerHtml;
        }

        function loadWardTable() {
            const selectedLga = document.getElementById('resultsLgaSelect')?.value || 'all';
            const selectedType = document.getElementById('resultsTypeSelect')?.value || 'all';

            fetch(`/api/ward-results?lga=${encodeURIComponent(selectedLga)}&election_type=${encodeURIComponent(selectedType)}`).then(res => res.json()).then(rows => {
                let html = '';
                rows.forEach(r => {
                    const v = r.party_votes || {};
                    html += `<tr><td><strong>${r.lga}</strong></td><td>${r.ward}</td><td>${r.polling_unit}<br><small>${r.pu_code}</small></td><td><span class="role-badge" style="background:#0c235c;">${r.election_type||'Senatorial'}</span></td>`;
                    allPartiesList.forEach(p => { html += `<td>${v[p.acronym]||0}</td>`; });
                    html += `<td><strong>${r.valid_votes||0}</strong></td><td>${r.rejected_votes||0}</td><td><strong>${r.total_votes_cast||0}</strong></td></tr>`;
                });
                document.getElementById('resultsTableBody').innerHTML = html || `<tr><td colspan="${allPartiesList.length + 7}" style="text-align:center;">No collated results found.</td></tr>`;
            });
        }

        function exportResultsCSV() {
            const lga = document.getElementById('resultsLgaSelect')?.value || 'all';
            window.location.href = `/api/export-csv?lga=${encodeURIComponent(lga)}`;
        }

        function loadUploadWizardData() {
            if (currentUser.role === 'Collation Admin') {
                document.getElementById('uploadCollationAdminBlocked').style.display = 'block';
                document.getElementById('uploadWizardContainer').style.display = 'none';
                return;
            } else {
                document.getElementById('uploadCollationAdminBlocked').style.display = 'none';
                document.getElementById('uploadWizardContainer').style.display = 'block';
            }

            if (currentUser.role === 'Field Officer') {
                document.getElementById('fieldOfficerLockedBox').style.display = 'block';
                document.getElementById('fieldLockLgaWard').innerText = `LGA: ${currentUser.assigned_lga} | Ward: ${currentUser.assigned_ward}`;
                document.getElementById('fieldLockPuName').innerText = currentUser.assigned_pu_name;
                document.getElementById('fieldLockPuCode').innerText = `Code: ${currentUser.assigned_pu_code}`;

                currentUploadData.lga = currentUser.assigned_lga;
                currentUploadData.ward = currentUser.assigned_ward;
                currentUploadData.polling_unit = currentUser.assigned_pu_name;
                currentUploadData.pu_code = currentUser.assigned_pu_code;

                document.getElementById('summaryElection').innerText = "Ogun East Senatorial District Election 2027";
                document.getElementById('summaryWardPU').innerText = `PU: ${currentUser.assigned_pu_name} (${currentUser.assigned_pu_code})`;

                document.getElementById('btnBackFromStep5').style.display = 'none';
                goToUploadStep(5);
            } else {
                document.getElementById('fieldOfficerLockedBox').style.display = 'none';
                document.getElementById('btnBackFromStep5').style.display = 'block';
                
                fetch('/api/locations/lgas').then(res => res.json()).then(lgas => {
                    let lgaBtns = '';
                    const availableLgas = currentUser.role === 'LGA Admin' ? [currentUser.assigned_lga] : lgas;
                    availableLgas.forEach(l => { lgaBtns += `<button class="btn-select-option" onclick="selectLga('${l}')">${l} LGA</button>`; });
                    document.getElementById('lgasListStack').innerHTML = lgaBtns;
                    goToUploadStep(1);
                });
            }
        }

        function goToUploadStep(s) {
            document.querySelectorAll('.wizard-step').forEach(step => step.classList.remove('active'));
            document.getElementById('uploadStep' + s).classList.add('active');
        }

        function selectLga(lga) {
            currentUploadData.lga = lga;
            fetch('/api/admin/elections').then(res => res.json()).then(elections => {
                let electBtns = '';
                const activeElections = elections.filter(e => e.is_active === 1);
                activeElections.forEach(e => { electBtns += `<button class="btn-select-option" onclick="selectElection('${e.id}', '${e.name}', '${e.type}')">${e.name} (${e.type})</button>`; });
                document.getElementById('electionsListStack').innerHTML = electBtns || '<p style="padding:10px;">No active elections enabled by Super Admin.</p>';
                goToUploadStep(2);
            });
        }

        function selectElection(id, name, type) {
            currentUploadData.election_id = id;
            currentUploadData.election_name = name;
            currentUploadData.election_type = type;

            fetch(`/api/locations/wards?lga=${encodeURIComponent(currentUploadData.lga)}`).then(res => res.json()).then(wards => {
                let wardBtns = '';
                wards.forEach(w => { wardBtns += `<button class="btn-select-option" onclick="selectWard('${w}')">${w}</button>`; });
                document.getElementById('wardsListStack').innerHTML = wardBtns;
                goToUploadStep(3);
            });
        }

        function selectWard(w) {
            currentUploadData.ward = w;
            fetch(`/api/locations/pus?ward=${encodeURIComponent(w)}`).then(res => res.json()).then(pus => {
                let puBtns = '';
                pus.forEach(p => { puBtns += `<button class="btn-select-option" onclick="selectPU('${p.polling_unit}', '${p.pu_code}')">${p.polling_unit} (${p.pu_code})</button>`; });
                document.getElementById('pusListStack').innerHTML = puBtns;
                goToUploadStep(4);
            });
        }

        function selectPU(pu, code) {
            currentUploadData.polling_unit = pu; currentUploadData.pu_code = code;
            document.getElementById('summaryElection').innerText = `${currentUploadData.election_name} (${currentUploadData.lga} LGA)`;
            document.getElementById('summaryWardPU').innerText = `Ward: ${currentUploadData.ward} | PU: ${pu} (${code})`;
            goToUploadStep(5);
        }

        function previewUploadImage(input) {
            if (input.files && input.files[0]) {
                selectedPhotoFile = input.files[0];
                const r = new FileReader();
                r.onload = function(e) {
                    document.getElementById('uploadPreviewImg').src = e.target.result;
                    document.getElementById('imagePreviewBox').style.display = 'block';
                    document.getElementById('btnSubmitPhoto').style.display = 'block';
                };
                r.readAsDataURL(selectedPhotoFile);
            }
        }

        function submitPhotoOnly() {
            if (!selectedPhotoFile) return alert("Please select or take a photo first.");
            const fd = new FormData();
            fd.append('photo', selectedPhotoFile);
            fd.append('election_id', currentUploadData.election_id);
            fd.append('election_name', currentUploadData.election_name);
            fd.append('election_type', currentUploadData.election_type);
            fd.append('lga', currentUploadData.lga);
            fd.append('ward', currentUploadData.ward);
            fd.append('polling_unit', currentUploadData.polling_unit);
            fd.append('pu_code', currentUploadData.pu_code);
            fd.append('submitted_by', currentUser.username);

            fetch('/api/upload-photo-result', { method: 'POST', body: fd })
            .then(res => res.json()).then(res => {
                alert(res.message);
                selectedPhotoFile = null;
                document.getElementById('imagePreviewBox').style.display = 'none';
                document.getElementById('btnSubmitPhoto').style.display = 'none';
                if (['Super Admin', 'LGA Admin', 'Collation Admin'].includes(currentUser.role)) {
                    document.querySelector('.nav-item[data-tab="review"]').click();
                } else {
                    document.querySelector('.nav-item[data-tab="live"]').click();
                }
            });
        }

        function loadReviewQueue() {
            const banner = document.getElementById('reviewScopeBanner');
            if (currentUser.role === 'Collation Admin') {
                banner.innerText = `🔒 Scoped Collation: Viewing Pending Results ONLY for ${currentUser.assigned_lga} LGA -> ${currentUser.assigned_ward} Ward`;
            } else if (currentUser.role === 'LGA Admin') {
                banner.innerText = `📍 LGA Collation: Viewing Pending Results for ${currentUser.assigned_lga} LGA`;
            } else {
                banner.innerText = `🌐 Global Collation: Super Admin Overview (All 9 LGAs)`;
            }

            fetch(`/api/review-queue?username=${encodeURIComponent(currentUser.username)}`)
            .then(res => res.json())
            .then(queue => {
                let html = '';
                queue.forEach(item => {
                    html += `
                    <div class="party-card" style="border-left-color:#d97706; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:10px; font-weight:800; background:#fef3c7; color:#92400e; padding:2px 6px; border-radius:4px;">PENDING VERIFICATION</span>
                            <span style="font-size:11px; font-weight:700; color:#2563eb;">📍 ${item.lga} | ${item.ward}</span>
                        </div>
                        <h4 style="margin-top:6px;">#${item.id} ${item.election_name}</h4>
                        <p><small>PU: <strong>${item.polling_unit} (${item.pu_code})</strong></small></p>
                        <p><small>Submitted by Field Officer: <strong>${item.submitted_by}</strong></small></p>
                        <button class="btn-action" style="margin-top:8px;" onclick="openReviewModal(${item.id}, '${item.image_url}', '${item.lga}', '${item.ward}', '${item.polling_unit}', '${item.pu_code}', '${item.election_name}')">🔍 Verify & Collate Result</button>
                    </div>`;
                });
                document.getElementById('reviewQueueList').innerHTML = html || '<p style="text-align:center; padding:15px; color:#64748b;">No pending submissions in your scope.</p>';
            });
        }

        function openReviewModal(id, img, lga, ward, pu, puCode, electName) {
            activeModalSubmissionId = id;
            document.getElementById('modalImage').src = img || '';
            document.getElementById('modalDetails').innerHTML = `<strong>${electName}</strong><br>LGA: ${lga} | Ward: ${ward} | PU: ${pu} (${puCode})`;

            fetch('/api/admin/parties').then(res => res.json()).then(parties => {
                let html = '';
                parties.forEach(p => { html += `<div class="input-row"><label>${p.name} (${p.acronym})</label><input type="number" id="review_${p.acronym}" value="0"></div>`; });
                html += `<div class="input-row"><label>Rejected Votes</label><input type="number" id="review_Rejected" value="0"></div>`;
                document.getElementById('reviewPartyInputs').innerHTML = html;
                document.getElementById('reviewModal').classList.add('active');
            });
        }

        function closeReviewModal() { document.getElementById('reviewModal').classList.remove('active'); }

        function submitManualCollation(status) {
            fetch('/api/admin/parties').then(res=>res.json()).then(parties => {
                let votes = {};
                parties.forEach(p => { votes[p.acronym] = parseInt(document.getElementById('review_' + p.acronym)?.value || 0); });
                
                fetch('/api/admin-verify-collate', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        submission_id: activeModalSubmissionId, party_votes: votes,
                        rejected_votes: parseInt(document.getElementById('review_Rejected')?.value || 0),
                        status: status, notes: document.getElementById('reviewNotes')?.value || '',
                        is_flagged: document.getElementById('reviewFlagged').checked,
                        flag_reason: document.getElementById('reviewFlagReason').value,
                        verified_by: currentUser.full_name || currentUser.username
                    })
                }).then(res => res.json()).then(res => {
                    alert(`✓ Submission #${activeModalSubmissionId} marked as ${status}!`);
                    closeReviewModal();
                    loadReviewQueue(); loadLiveResults(); loadWardTable();
                });
            });
        }

        function onRoleSelectionChanged() {
            const role = document.getElementById('adminUserRole').value;
            const gLga = document.getElementById('groupAssignLga');
            const gWard = document.getElementById('groupAssignWard');
            const gPu = document.getElementById('groupAssignPu');

            if (role === 'LGA Admin') {
                gLga.style.display = 'block'; gWard.style.display = 'none'; gPu.style.display = 'none';
            } else if (role === 'Collation Admin') {
                gLga.style.display = 'block'; gWard.style.display = 'block'; gPu.style.display = 'none';
            } else if (role === 'Field Officer') {
                gLga.style.display = 'block'; gWard.style.display = 'block'; gPu.style.display = 'block';
            } else {
                gLga.style.display = 'none'; gWard.style.display = 'none'; gPu.style.display = 'none';
            }
        }

        function onAdminLgaChanged() {
            const lga = document.getElementById('adminUserLga').value;
            fetch(`/api/locations/wards?lga=${encodeURIComponent(lga)}`).then(res => res.json()).then(wards => {
                document.getElementById('adminUserWard').innerHTML = wards.map(w => `<option value="${w}">${w}</option>`).join('');
                onAdminWardChanged();
            });
        }

        function onAdminWardChanged() {
            const ward = document.getElementById('adminUserWard').value;
            fetch(`/api/locations/pus?ward=${encodeURIComponent(ward)}`).then(res => res.json()).then(pus => {
                document.getElementById('adminUserPu').innerHTML = pus.map(p => `<option value="${p.pu_code}" data-name="${p.polling_unit}">${p.polling_unit} (${p.pu_code})</option>`).join('');
            });
        }

        function openAdminModal(type) {
            closeAdminModals();
            if (type === 'user') {
                const roleSelect = document.getElementById('adminUserRole');
                if (currentUser.role === 'Super Admin') {
                    roleSelect.innerHTML = '<option value="LGA Admin">LGA Admin (Assigned to 1 LGA)</option><option value="Viewer">Viewer (Read Only)</option>';
                } else if (currentUser.role === 'LGA Admin') {
                    roleSelect.innerHTML = '<option value="Collation Admin">Collation Admin (Assigned to 1 Ward)</option><option value="Field Officer">Field Officer (Assigned to 1 PU)</option><option value="Viewer">Viewer (Read Only)</option>';
                }

                fetch('/api/locations/lgas').then(res => res.json()).then(lgas => {
                    const lgaSel = document.getElementById('adminUserLga');
                    lgaSel.innerHTML = lgas.map(l => `<option value="${l}">${l}</option>`).join('');
                    
                    if (currentUser.role === 'LGA Admin') {
                        lgaSel.value = currentUser.assigned_lga;
                        lgaSel.disabled = true;
                    } else {
                        lgaSel.disabled = false;
                    }
                    
                    onRoleSelectionChanged();
                    onAdminLgaChanged();
                    document.getElementById('adminUserModal').classList.add('active');
                });
            }
            if (type === 'election') {
                fetch('/api/admin/elections').then(res => res.json()).then(elections => {
                    let html = '';
                    elections.forEach(e => {
                        html += `
                        <div class="party-card" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <div>
                                <strong>${e.name}</strong><br><small>${e.type}</small>
                            </div>
                            <label style="font-size:12px; font-weight:700;">
                                <input type="checkbox" ${e.is_active === 1 ? 'checked' : ''} onchange="toggleElectionActive(${e.id}, this.checked)"> Active
                            </label>
                        </div>`;
                    });
                    document.getElementById('electionsActivationList').innerHTML = html;
                    document.getElementById('adminElectionModal').classList.add('active');
                });
            }
            if (type === 'candidate') {
                fetch('/api/admin/parties').then(res=>res.json()).then(parties => {
                    let opts = '<option value="">-- Select Party --</option>';
                    parties.forEach(p => { opts += `<option value="${p.acronym}">${p.acronym} - ${p.name}</option>`; });
                    document.getElementById('adminCandParty').innerHTML = opts;
                });
                fetch('/api/admin/elections').then(res=>res.json()).then(elections => {
                    let opts = '<option value="">-- Select Election Category --</option>';
                    elections.forEach(e => { opts += `<option value="${e.name}">${e.name}</option>`; });
                    document.getElementById('adminCandElection').innerHTML = opts;
                });
                document.getElementById('adminCandidateModal').classList.add('active');
            }
        }

        function toggleElectionActive(id, isActive) {
            fetch('/api/admin/elections', {
                method: 'PUT', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ id: id, is_active: isActive ? 1 : 0 })
            }).then(res => res.json());
        }

        function closeAdminModals() { document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active')); }

        function submitCreateUser() {
            const puSelect = document.getElementById('adminUserPu');
            const selectedPuOpt = puSelect.options[puSelect.selectedIndex];
            
            fetch('/api/admin/users', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    full_name: document.getElementById('adminUserFullName').value,
                    username: document.getElementById('adminUsername').value,
                    password: document.getElementById('adminUserPassword').value,
                    role: document.getElementById('adminUserRole').value,
                    assigned_lga: document.getElementById('adminUserLga').value,
                    assigned_ward: document.getElementById('adminUserWard').value,
                    assigned_pu_code: puSelect.value,
                    assigned_pu_name: selectedPuOpt ? selectedPuOpt.getAttribute('data-name') : '',
                    email: document.getElementById('adminUserEmail').value,
                    created_by_user: currentUser.username
                })
            }).then(res => res.json()).then(res => { 
                if (res.success) {
                    alert(res.message); closeAdminModals(); loadAdminData('users');
                } else {
                    alert(res.message);
                }
            });
        }

        function submitCreateCandidate() {
            const name = document.getElementById('adminCandName').value.trim();
            const party = document.getElementById('adminCandParty').value;
            const election = document.getElementById('adminCandElection').value;

            if (!name || !party || !election) return alert("Please fill in Candidate Name and select Party and Election Category.");

            const fd = new FormData();
            fd.append('full_name', name);
            fd.append('party', party);
            fd.append('election_name', election);
            const photoInput = document.getElementById('adminCandPhoto');
            if (photoInput && photoInput.files[0]) fd.append('photo', photoInput.files[0]);

            fetch('/api/admin/candidates', { method: 'POST', body: fd })
            .then(res => res.json()).then(res => {
                alert(res.message); closeAdminModals(); loadLiveResults();
            });
        }

        function loadAdminData(type) {
            fetch(`/api/admin/${type}?username=${encodeURIComponent(currentUser.username)}`).then(res => res.json()).then(data => {
                let html = `<h4 style="color:#0c235c; margin-bottom:8px;">${type.toUpperCase()} (${data.length})</h4><div class="party-counter-grid">`;
                data.forEach(item => {
                    const img = item.photo_url || item.logo_url || '';
                    html += `
                    <div class="party-card" style="display:flex; align-items:center; gap:10px;">
                        ${img ? `<img src="${img}" style="width:36px; height:36px; object-fit:contain; border-radius:4px;">` : '👤'}
                        <div>
                            <strong>${item.full_name || item.name || item.acronym} (@${item.username||''})</strong>
                            <p><small>Role: <b>${item.role}</b> ${item.assigned_lga ? '| LGA: ' + item.assigned_lga : ''} ${item.assigned_ward ? '| Ward: ' + item.assigned_ward : ''} ${item.assigned_pu_code ? '| PU: ' + item.assigned_pu_code : ''}</small></p>
                        </div>
                    </div>`;
                });
                document.getElementById('adminDataDisplay').innerHTML = html + '</div>';
            });
        }

        function triggerSystemReset() {
            if (confirm("Reset all Ogun East collation tallies to 0?")) {
                fetch('/api/admin/reset-system', { method: 'POST' }).then(res => res.json()).then(res => {
                    alert(res.message); loadLiveResults(); loadWardTable();
                });
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"==================================================")
    print(f" OGUN EAST 2027 WATCH ACTIVE ON PORT {port}")
    print(f"==================================================")
    app.run(host='0.0.0.0', port=port, debug=True)
    