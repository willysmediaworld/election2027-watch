from flask import Flask, render_template_string, request, jsonify
import sqlite3
import json
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
DB_NAME = "ogun_east_2027.db"

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==========================================
# DATABASE SETUP & OGUN EAST PRELOADING
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
            election_id TEXT, election_name TEXT, lga TEXT, ward TEXT,
            polling_unit TEXT, pu_code TEXT, party_votes TEXT DEFAULT '{}',
            valid_votes INTEGER DEFAULT 0, rejected_votes INTEGER DEFAULT 0,
            total_votes_cast INTEGER DEFAULT 0, image_url TEXT, submitted_by TEXT,
            assigned_to TEXT DEFAULT '', timestamp DATETIME, status TEXT DEFAULT 'PENDING',
            review_notes TEXT, verified_by TEXT, verified_at DATETIME
        )
    ''')

    # 2. Users Table (With Assigned LGA column for LGA Admins)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, username TEXT UNIQUE,
            role TEXT, assigned_lga TEXT DEFAULT '', email TEXT, created_at DATETIME
        )
    ''')
    
    # Migration check for assigned_lga column
    cursor.execute("PRAGMA table_info(users)")
    user_cols = [col[1] for col in cursor.fetchall()]
    if 'assigned_lga' not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN assigned_lga TEXT DEFAULT ''")

    # 3. Elections Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS elections (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, type TEXT,
            constituency TEXT, registered_voters INTEGER DEFAULT 250000
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

    # 6. Locations Table (Ogun East LGAs, Wards & PUs)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, state TEXT DEFAULT 'Ogun',
            lga TEXT, ward TEXT, polling_unit TEXT, pu_code TEXT
        )
    ''')
    
    # Seed Accounts for all 5 User Levels
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        default_users = [
            ("Oladele Rotimi Williams", "superadmin", "Super Admin", "", "admin@electionwatch.ng"),
            ("Sagamu LGA Officer", "sagamu_admin", "LGA Admin", "Sagamu", "sagamu@electionwatch.ng"),
            ("Ijebu Ode LGA Officer", "ijebuode_admin", "LGA Admin", "Ijebu Ode", "ijebuode@electionwatch.ng"),
            ("Collation Admin 1", "admin1", "Admin", "", "admin1@electionwatch.ng"),
            ("Ogun East Field Officer", "field", "Field Officer", "", "field@electionwatch.ng"),
            ("Public Observer", "viewer", "Viewer", "", "observer@electionwatch.ng")
        ]
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.executemany("INSERT INTO users (full_name, username, role, assigned_lga, email, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                           [(u[0], u[1], u[2], u[3], u[4], now_str) for u in default_users])

    # Preload Default Elections for Ogun East
    cursor.execute("SELECT COUNT(*) FROM elections")
    if cursor.fetchone()[0] == 0:
        default_elections = [
            ("Ogun East Senatorial District Election 2027", "Senatorial", "Ogun East", 1150000),
            ("Sagamu / Ikenne / Remo North Reps Election 2027", "House of Representatives", "Remo Federal Constituency", 380000),
            ("Ijebu Ode / Odogbolu / Ijebu North East Reps Election 2027", "House of Representatives", "Ijebu Central Constituency", 320000),
            ("Ijebu North / Ijebu East / Ogun Waterside Reps Election 2027", "House of Representatives", "Ijebu Federal Constituency", 350000),
            ("Ogun State Governorship Election 2027", "Governorship", "Ogun State", 2400000),
            ("Nigeria Presidential Election 2027", "Presidential", "National", 93000000)
        ]
        cursor.executemany("INSERT INTO elections (name, type, constituency, registered_voters) VALUES (?, ?, ?, ?)", default_elections)

    # Preload All 19 Active INEC Registered Political Parties
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

    # Preload ALL 9 LGAS of Ogun East Senatorial District with sample Wards & Polling Units
    cursor.execute("SELECT COUNT(*) FROM locations")
    if cursor.fetchone()[0] < 50:
        cursor.execute("DELETE FROM locations")
        ogun_east_locations = [
            # 1. IJEBU ODE LGA
            ("Ogun", "Ijebu Ode", "Porogun I", "POROGUN CHURCH PRY SCH", "27/11/01/001"),
            ("Ogun", "Ijebu Ode", "Porogun I", "COURT HALL POROGUN", "27/11/01/002"),
            ("Ogun", "Ijebu Ode", "Porogun II", "ITA OLE MARKET SQUARE", "27/11/02/001"),
            ("Ogun", "Ijebu Ode", "Ijasi", "IJASI TOWN HALL", "27/11/03/001"),
            ("Ogun", "Ijebu Ode", "Molipa", "MOLIPA HIGH SCHOOL", "27/11/04/001"),

            # 2. SAGAMU LGA
            ("Ogun", "Sagamu", "Makun I", "ST. PAULS PRY SCH MAKUN", "27/18/01/001"),
            ("Ogun", "Sagamu", "Makun II", "EWUSI PALACE SQUARE", "27/18/02/001"),
            ("Ogun", "Sagamu", "Offin/Sotubo", "OFFIN COMMUNITY HALL", "27/18/03/001"),
            ("Ogun", "Sagamu", "Sabo I", "SABO MARKET SQUARE", "27/18/04/001"),
            ("Ogun", "Sagamu", "Ogijo/Ikosi", "OGIJO COMMUNITY SCH", "27/18/05/001"),

            # 3. IJEBU NORTH LGA
            ("Ogun", "Ijebu North", "Ago Iwoye I", "METHODIST PRY SCH AGO IWOYE", "27/09/01/001"),
            ("Ogun", "Ijebu North", "Ago Iwoye II", "FOWOSEJE TOWN HALL", "27/09/02/001"),
            ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "ORU TOWN HALL", "27/09/03/001"),
            ("Ogun", "Ijebu North", "Oke Sopin", "OKE SOPIN MARKET", "27/09/04/001"),

            # 4. IJEBU EAST LGA
            ("Ogun", "Ijebu East", "Ijebu Mushin I", "ODOSEGBUREN", "27/07/01/001"),
            ("Ogun", "Ijebu East", "Ijebu Ife I", "ITAKO SQUARE", "27/07/03/001"),
            ("Ogun", "Ijebu East", "Ogbere", "PALACE FRONTAGE", "27/07/08/001"),
            ("Ogun", "Ijebu East", "Ajebandele", "ST. SAVIOUR’S SCH.", "27/07/11/001"),

            # 5. IKENNE LGA
            ("Ogun", "Ikenne", "Iperu I", "AKESAN MARKET SQUARE IPERU", "27/12/01/001"),
            ("Ogun", "Ikenne", "Iperu II", "CHRIST CHURCH PRY SCH IPERU", "27/12/02/001"),
            ("Ogun", "Ikenne", "Ikenne I", "OBAFEMI AWOLOWO TOWN HALL", "27/12/03/001"),
            ("Ogun", "Ikenne", "Ilisan I", "ILISAN TOWN HALL", "27/12/04/001"),

            # 6. REMO NORTH LGA
            ("Ogun", "Remo North", "Isara I", "ISARA TOWN HALL", "27/17/01/001"),
            ("Ogun", "Remo North", "Ipara", "IPARA MARKET SQUARE", "27/17/02/001"),
            ("Ogun", "Remo North", "Ode I", "ODE REMO PRY SCH", "27/17/03/001"),

            # 7. IJEBU NORTH EAST LGA
            ("Ogun", "Ijebu North East", "Atan", "ATAN TOWN HALL", "27/10/01/001"),
            ("Ogun", "Ijebu North East", "Ilese", "ILESE GRAMMAR SCH", "27/10/02/001"),
            ("Ogun", "Ijebu North East", "Itamapako", "ITAMAPAKO PRY SCH", "27/10/03/001"),

            # 8. OGUN WATERSIDE LGA
            ("Ogun", "Ogun Waterside", "Abigi", "ABIGI TOWN HALL", "27/15/01/001"),
            ("Ogun", "Ogun Waterside", "Iwopin", "IWOPIN JETTY SQUARE", "27/15/02/001"),
            ("Ogun", "Ogun Waterside", "Ibiade", "IBIADE MARKET SQUARE", "27/15/03/001"),

            # 9. ODOGBOLU LGA
            ("Ogun", "Odogbolu", "Odogbolu I", "ODOGBOLU TOWN HALL", "27/14/01/001"),
            ("Ogun", "Odogbolu", "Aiyepe", "AIYEPE CENTRAL SCH", "27/14/02/001"),
            ("Ogun", "Odogbolu", "Ososa", "OSOSA PRY SCHOOL", "27/14/03/001")
        ]
        cursor.executemany("INSERT INTO locations (state, lga, ward, polling_unit, pu_code) VALUES (?, ?, ?, ?, ?)", ogun_east_locations)
        
    conn.commit()
    conn.close()

init_db()

# ==========================================
# SYSTEM ROUTING LOGIC & LGA QUEUEING
# ==========================================
def get_next_assigned_admin(submission_lga):
    """Assigns submission to the designated LGA Admin first, or round-robins to Super/Collation Admins."""
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Check if an LGA Admin is specifically assigned to this LGA
    cursor.execute("SELECT full_name FROM users WHERE role = 'LGA Admin' AND LOWER(assigned_lga) = LOWER(?) LIMIT 1", (submission_lga,))
    lga_admin = cursor.fetchone()
    if lga_admin:
        conn.close()
        return lga_admin['full_name']
        
    # 2. Fallback round-robin among Super Admins and Admins
    cursor.execute("SELECT full_name FROM users WHERE role IN ('Super Admin', 'Admin') ORDER BY id ASC")
    reviewers = [r['full_name'] for r in cursor.fetchall()]
    
    if not reviewers:
        conn.close()
        return "Super Admin"
        
    cursor.execute("SELECT assigned_to FROM submissions WHERE assigned_to != '' ORDER BY id DESC LIMIT 1")
    last_sub = cursor.fetchone()
    conn.close()

    if not last_sub or last_sub['assigned_to'] not in reviewers:
        return reviewers[0]

    last_idx = reviewers.index(last_sub['assigned_to'])
    next_idx = (last_idx + 1) % len(reviewers)
    return reviewers[next_idx]

def save_pending_photo_submission(data):
    assigned_admin = get_next_assigned_admin(data.get('lga', ''))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO submissions (election_id, election_name, lga, ward, polling_unit, pu_code, image_url, submitted_by, assigned_to, timestamp, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
    ''', (
        data.get('election_id', '1'),
        data.get('election_name', 'Ogun East Senatorial District Election 2027'),
        data.get('lga', ''),
        data.get('ward', ''),
        data.get('polling_unit', ''),
        data.get('pu_code', ''),
        data.get('image_url', ''),
        data.get('submitted_by', 'Field Officer'),
        assigned_admin,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()
    return {
        "status": "success",
        "message": f"Result sheet submitted! Routed to [{assigned_admin}] for review."
    }

def admin_verify_and_collate(sub_id, party_votes, rejected_votes, status, notes="", verified_by="Super Admin"):
    conn = get_db()
    cursor = conn.cursor()
    valid_votes = sum(int(v) for v in party_votes.values())
    rejected = int(rejected_votes)
    total_cast = valid_votes + rejected
    
    cursor.execute('''
        UPDATE submissions 
        SET party_votes = ?, valid_votes = ?, rejected_votes = ?, total_votes_cast = ?, status = ?, review_notes = ?, verified_by = ?, verified_at = ?
        WHERE id = ?
    ''', (json.dumps(party_votes), valid_votes, rejected, total_cast, status, notes, verified_by, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sub_id))
    
    cursor.execute("SELECT election_id, lga FROM submissions WHERE id = ?", (sub_id,))
    row = cursor.fetchone()
    election_id = row['election_id'] if row else '1'
    conn.commit()
    conn.close()
    return get_live_collation(election_id)

def get_live_collation(election_id=None, filter_lga=None):
    conn = get_db()
    cursor = conn.cursor()

    target_election_name = None
    registered_voters = 1150000

    if election_id and str(election_id).strip() != 'all':
        cursor.execute("SELECT name, registered_voters FROM elections WHERE id = ? OR name = ?", (str(election_id), str(election_id)))
        e_row = cursor.fetchone()
        if e_row:
            target_election_name = e_row['name']
            registered_voters = e_row['registered_voters'] or 1150000

    # Get candidates map
    if target_election_name:
        cursor.execute("SELECT full_name, party, photo_url FROM candidates WHERE election_name = ?", (target_election_name,))
    else:
        cursor.execute("SELECT full_name, party, photo_url FROM candidates")
    candidates_map = {c['party']: {"name": c['full_name'], "photo": c['photo_url']} for c in cursor.fetchall()}

    # Get all 19 parties
    cursor.execute("SELECT acronym, name, logo_url FROM parties ORDER BY acronym ASC")
    all_parties = cursor.fetchall()
    parties_logo_map = {p['acronym']: p['logo_url'] for p in all_parties}
    parties_name_map = {p['acronym']: p['name'] for p in all_parties}

    # Total locations filter
    if filter_lga and filter_lga != 'all':
        cursor.execute("SELECT COUNT(*) FROM locations WHERE LOWER(lga) = LOWER(?)", (filter_lga,))
    else:
        cursor.execute("SELECT COUNT(*) FROM locations")
    total_pus_count = cursor.fetchone()[0] or 1

    # Fetch accepted submissions
    query = "SELECT party_votes, valid_votes, rejected_votes, total_votes_cast FROM submissions WHERE status = 'ACCEPTED'"
    params = []
    if target_election_name:
        query += " AND (election_id = ? OR election_name = ?)"
        params.extend([str(election_id), target_election_name])
    if filter_lga and filter_lga != 'all':
        query += " AND LOWER(lga) = LOWER(?)"
        params.append(filter_lga)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    # Distinct PUs verified
    pu_query = "SELECT COUNT(DISTINCT polling_unit) FROM submissions WHERE status = 'ACCEPTED'"
    pu_params = []
    if target_election_name:
        pu_query += " AND (election_id = ? OR election_name = ?)"
        pu_params.extend([str(election_id), target_election_name])
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
            
    leader = {"candidate": "Awaiting Verified Results", "party": "N/A", "votes": 0, "percentage": "0%", "photo": "", "party_logo": ""}
    
    if grand_valid > 0 and any(v > 0 for v in party_totals.values()):
        top_party = max(party_totals, key=party_totals.get)
        top_votes = party_totals[top_party]
        top_pct = round((top_votes / grand_valid * 100), 1)
        cand_info = candidates_map.get(top_party, {"name": "Candidate Not Assigned", "photo": ""})
        leader = {
            "candidate": cand_info["name"], "party": top_party, "votes": top_votes,
            "percentage": f"{top_pct}%", "photo": cand_info["photo"], "party_logo": parties_logo_map.get(top_party, "")
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
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({
            "success": True,
            "username": user['username'],
            "full_name": user['full_name'],
            "role": user['role'],
            "assigned_lga": user['assigned_lga'] or ''
        })
    else:
        role = "Viewer"
        if "super" in username.lower() or "rotimi" in username.lower():
            role = "Super Admin"
        elif "lga" in username.lower():
            role = "LGA Admin"
        elif "admin" in username.lower():
            role = "Admin"
        elif "field" in username.lower():
            role = "Field Officer"
        return jsonify({
            "success": True,
            "username": username,
            "full_name": username,
            "role": role,
            "assigned_lga": ""
        })

@app.route('/api/upload-photo-result', methods=['POST'])
def upload_photo_result():
    if 'photo' not in request.files:
        return jsonify({"status": "error", "message": "No photograph attached"}), 400
    file = request.files['photo']
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        data = {
            "election_id": request.form.get("election_id", "1"),
            "election_name": request.form.get("election_name", "Ogun East Senatorial District Election 2027"),
            "lga": request.form.get("lga", ""),
            "ward": request.form.get("ward", ""),
            "polling_unit": request.form.get("polling_unit", ""),
            "pu_code": request.form.get("pu_code", ""),
            "submitted_by": request.form.get("submitted_by", "Field Officer"),
            "image_url": f"/{filepath}"
        }
        return jsonify(save_pending_photo_submission(data))
    return jsonify({"status": "error", "message": "Invalid file extension format"}), 400

@app.route('/api/admin-verify-collate', methods=['POST'])
def admin_verify_collate_route():
    d = request.json
    return jsonify({
        "status": "success",
        "live": admin_verify_and_collate(d.get('submission_id'), d.get('party_votes', {}), d.get('rejected_votes', 0), d.get('status', 'ACCEPTED'), d.get('notes', ''), d.get('verified_by', 'Super Admin'))
    })

@app.route('/api/admin/reset-system', methods=['POST'])
def reset_system():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM submissions")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='submissions'")
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "⚡ Ogun East System reset complete!"})

@app.route('/api/live-results', methods=['GET'])
def live_results():
    election_id = request.args.get('election_id', '1')
    filter_lga = request.args.get('lga', '')
    return jsonify(get_live_collation(election_id, filter_lga))

@app.route('/api/ward-results', methods=['GET'])
def ward_results():
    filter_lga = request.args.get('lga', '')
    conn = get_db()
    cursor = conn.cursor()
    if filter_lga and filter_lga != 'all':
        cursor.execute("SELECT * FROM submissions WHERE status = 'ACCEPTED' AND LOWER(lga) = LOWER(?) ORDER BY ward, polling_unit", (filter_lga,))
    else:
        cursor.execute("SELECT * FROM submissions WHERE status = 'ACCEPTED' ORDER BY lga, ward, polling_unit")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    for r in rows:
        r['party_votes'] = json.loads(r['party_votes']) if r['party_votes'] else {}
    return jsonify(rows)

@app.route('/api/review-queue', methods=['GET'])
def review_queue():
    assigned_lga = request.args.get('assigned_lga', '')
    role = request.args.get('role', '')
    conn = get_db()
    cursor = conn.cursor()
    
    if role == 'LGA Admin' and assigned_lga:
        cursor.execute("SELECT * FROM submissions WHERE status = 'PENDING' AND LOWER(lga) = LOWER(?) ORDER BY id DESC", (assigned_lga,))
    else:
        cursor.execute("SELECT * FROM submissions WHERE status = 'PENDING' ORDER BY id DESC")
        
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/audit-log', methods=['GET'])
def audit_log():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM submissions WHERE status != 'PENDING' ORDER BY verified_at DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/admin/users', methods=['GET', 'POST'])
def handle_users():
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'POST':
        d = request.json
        cursor.execute("INSERT INTO users (full_name, username, role, assigned_lga, email, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                       (d.get('full_name'), d.get('username'), d.get('role'), d.get('assigned_lga', ''), d.get('email'), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "User Account Created Successfully!"})
    cursor.execute("SELECT * FROM users ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/admin/elections', methods=['GET', 'POST'])
def handle_elections():
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'POST':
        d = request.json
        cursor.execute("INSERT INTO elections (name, type, constituency, registered_voters) VALUES (?, ?, ?, ?)",
                       (d.get('name'), d.get('type'), d.get('constituency'), d.get('registered_voters', 250000)))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Election Created!"})
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

# Dynamic Geographic Endpoints
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
# FRONTEND UI (EMBEDDED HTML/CSS/JS)
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
        .auth-container { width: 100%; max-width: 440px; display: flex; flex-direction: column; align-items: center; text-align: center; }
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
        .user-info { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; flex-wrap: wrap; }
        .role-badge { background-color: #2563eb; color: #fff; font-size: 10px; padding: 2px 8px; border-radius: 12px; text-transform: uppercase; font-weight: 800; }
        .lga-badge { background-color: #16a34a; color: #fff; font-size: 10px; padding: 2px 8px; border-radius: 12px; font-weight: 800; }
        .btn-logout { background-color: #ffffff; color: #0c235c; border: none; padding: 6px 16px; border-radius: 20px; font-size: 12px; font-weight: 700; cursor: pointer; }
        .dashboard-content { padding: 20px 16px; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .section-heading { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; color: #0c235c; }
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
        .results-table { width: 100%; border-collapse: collapse; font-size: 12.5px; text-align: left; }
        .results-table th, .results-table td { padding: 10px 8px; border-bottom: 1px solid #e2e8f0; }
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
            <p class="auth-subtitle">Senatorial District Collation Portal</p>

            <form id="loginForm" class="auth-form">
                <div class="input-group">
                    <label>Username / Account ID</label>
                    <input type="text" id="username" placeholder="Enter username" required>
                </div>
                <div class="input-group">
                    <label>Password</label>
                    <input type="password" id="password" value="••••••••" required>
                </div>
                <button type="submit" class="btn-submit">🔐 Sign In</button>
            </form>

            <div style="margin-top:15px; width:100%;">
                <button type="button" class="btn-submit" style="background:#2563eb;" onclick="openGuestViewer()">🌐 Public Guest Access (Read Only)</button>
            </div>

            <footer class="app-footer">
                <p><strong>OGUN EAST 2027 ELECTION WATCH</strong></p>
                <p style="color:#2563eb; font-weight:700;">Covering All 9 Local Governments</p>
                <p>Designed by Willys Media World · 09018363715</p>
            </footer>
        </div>
    </div>

    <div id="dashboardPage" class="page">
        <header class="app-header">
            <h1>OGUN EAST 2027 WATCH</h1>
            <p>9 LGAs Real-Time Collation & Analytics</p>
        </header>

        <div class="user-bar">
            <div class="user-info">
                👤 <span id="userDisplayName">Guest Observer</span>
                <span id="userRoleBadge" class="role-badge">Viewer</span>
                <span id="userLgaBadge" class="lga-badge" style="display:none;"></span>
            </div>
            <button id="logoutBtn" class="btn-logout">Exit</button>
        </div>

        <main class="dashboard-content">

            <!-- TAB 1: LIVE FEED & REAL-TIME PARTY COUNTER -->
            <section id="tab-live" class="tab-content active">
                <div class="section-heading"><h2>📊 Live District Collation</h2></div>

                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-bottom:12px;">
                    <div class="input-group" style="margin:0;">
                        <label>Select Election</label>
                        <select id="liveElectionSelect" onchange="onLiveFilterChanged()"></select>
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
                <div class="section-heading"><h2>📋 LGA & Ward Breakdown</h2></div>
                <div class="input-group" style="margin-bottom:12px;">
                    <label>Filter by Local Government (LGA)</label>
                    <select id="resultsLgaSelect" onchange="loadWardTable()"></select>
                </div>

                <div class="table-responsive">
                    <table class="results-table">
                        <thead>
                            <tr><th>LGA</th><th>Ward</th><th>Polling Unit</th><th>APC</th><th>PDP</th><th>LP</th><th>NNPP</th><th>Valid</th></tr>
                        </thead>
                        <tbody id="resultsTableBody">
                            <tr><td colspan="8" style="text-align:center;">No collated results yet.</td></tr>
                        </tbody>
                    </table>
                </div>
            </section>

            <!-- TAB 3: UPLOAD RESULT SHEET -->
            <section id="tab-upload" class="tab-content">
                <div class="section-heading"><h2>📥 Submit Result Sheet (EC8A)</h2></div>

                <div id="uploadStep1" class="wizard-step active">
                    <h3 style="margin-bottom:12px; color:#0c235c;">1. Select Local Government Area (LGA)</h3>
                    <div class="btn-stack" id="lgasListStack"></div>
                </div>

                <div id="uploadStep2" class="wizard-step">
                    <h3 style="margin-bottom:12px; color:#0c235c;">2. Select Election Category</h3>
                    <div class="btn-stack" id="electionsListStack"></div>
                    <button class="btn-secondary" style="margin-top:10px;" onclick="goToUploadStep(1)">← Back</button>
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
                    <h3 style="margin-bottom:12px; color:#0c235c;">5. Upload EC8A Result Sheet</h3>
                    <div style="background:#1d3557; color:#fff; padding:14px; border-radius:10px; margin-bottom:15px;">
                        <h4 id="summaryElection">Ogun East Election</h4>
                        <p id="summaryWardPU" style="font-size:12px; color:#a8dadc; margin-top:4px;"></p>
                    </div>

                    <div style="margin-bottom:15px;">
                        <label class="btn-action" style="display:block; text-align:center; background:#2563eb; cursor:pointer;">
                            📷 Choose Photo / Capture Image
                            <input type="file" id="ec8aPhoto" accept="image/*" style="display:none;" onchange="previewUploadImage(this)">
                        </label>
                    </div>

                    <div id="imagePreviewBox" style="display:none; text-align:center; margin-bottom:15px;">
                        <img id="uploadPreviewImg" src="" style="width:100%; max-height:250px; object-fit:contain; border-radius:8px; border:2px solid #0c235c;">
                    </div>

                    <button id="btnSubmitPhoto" class="btn-submit" style="display:none;" onclick="submitPhotoOnly()">📤 Submit Result Sheet for Review</button>
                    <button class="btn-secondary" style="margin-top:10px;" onclick="goToUploadStep(4)">← Back</button>
                </div>
            </section>

            <!-- TAB 4: REVIEW & COLLATION -->
            <section id="tab-review" class="tab-content">
                <div class="section-heading"><h2>🔍 Verification & Audit Queue</h2></div>
                <div style="display:flex; gap:8px; margin-bottom:12px;">
                    <button id="btnViewPending" class="btn-select-option" style="flex:1; text-align:center;" onclick="switchReviewSubTab('pending')">📌 Pending Queue</button>
                    <button id="btnViewAudit" class="btn-secondary" style="flex:1; text-align:center;" onclick="switchReviewSubTab('audit')">📜 Audit Log</button>
                </div>
                <div id="subTabPending"><div id="reviewQueueList"></div></div>
                <div id="subTabAudit" style="display:none;"><div id="auditLogList"></div></div>
            </section>

            <!-- TAB 5: ADMINISTRATION -->
            <section id="tab-admin" class="tab-content">
                <div class="section-heading"><h2>⚙️ Super Administration Panel</h2></div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-bottom:15px;">
                    <button class="btn-select-option" style="text-align:center;" onclick="openAdminModal('user')">👤 User Roles & LGA Admins</button>
                    <button class="btn-select-option" style="text-align:center;" onclick="openAdminModal('election')">📦 Elections Setup</button>
                    <button class="btn-select-option" style="text-align:center;" onclick="loadAdminData('parties')">🏛️ Parties (19)</button>
                    <button class="btn-select-option" style="text-align:center;" onclick="openAdminModal('candidate')">👥 Candidates Management</button>
                </div>
                <div id="adminDataDisplay"></div>

                <div style="background:#fef2f2; border:1px solid #fca5a5; padding:14px; border-radius:12px; margin-top:20px;">
                    <h4 style="color:#991b1b;">🚨 System Reset</h4>
                    <p style="font-size:12px; color:#991b1b; margin:6px 0 10px;">Wipes all result submissions and resets district tallies to 0.</p>
                    <button class="btn-submit" style="background:#dc2626;" onclick="triggerSystemReset()">⚡ Reset System Data</button>
                </div>
            </section>

            <footer class="app-footer">
                <p><strong>OGUN EAST 2027 ELECTION WATCH</strong></p>
                <p style="color:#2563eb; font-weight:700;">Covering All 9 Local Governments</p>
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

    <!-- ADMIN USER CREATION MODAL -->
    <div id="adminUserModal" class="modal-overlay">
        <div class="modal-card">
            <h3>👤 Create User & Assign LGA</h3>
            <div class="input-group"><label>Full Name</label><input type="text" id="adminUserFullName" placeholder="e.g. Chief Adebayo"></div>
            <div class="input-group"><label>Username</label><input type="text" id="adminUsername" placeholder="e.g. adebayo_sagamu"></div>
            <div class="input-group">
                <label>User Role Level</label>
                <select id="adminUserRole" onchange="toggleLgaAssignField()">
                    <option value="Super Admin">Super Admin (All 9 LGAs Full Control)</option>
                    <option value="LGA Admin">LGA Admin (Assigned solely to 1 LGA)</option>
                    <option value="Admin">Collation Admin (General Verification)</option>
                    <option value="Field Officer">Field Officer (Submits EC8A Photos)</option>
                    <option value="Viewer">Viewer (Read Only Access)</option>
                </select>
            </div>
            <div class="input-group" id="lgaAssignGroup" style="display:none;">
                <label>Assign to Specific LGA (Ogun East)</label>
                <select id="adminUserAssignedLga"></select>
            </div>
            <div class="input-group"><label>Email Address</label><input type="email" id="adminUserEmail" placeholder="user@domain.com"></div>
            <button class="btn-submit" style="background:#16a34a;" onclick="submitCreateUser()">Save User Account</button>
            <button class="btn-secondary" style="margin-top:8px;" onclick="closeAdminModals()">Cancel</button>
        </div>
    </div>

    <!-- ELECTION MODAL -->
    <div id="adminElectionModal" class="modal-overlay">
        <div class="modal-card">
            <h3>📦 Create Election</h3>
            <div class="input-group"><label>Election Name</label><input type="text" id="adminElectName"></div>
            <div class="input-group"><label>Election Type</label><select id="adminElectType"><option>Senatorial</option><option>House of Representatives</option><option>State House of Assembly</option><option>Governorship</option><option>Presidential</option></select></div>
            <div class="input-group"><label>Constituency</label><input type="text" id="adminElectConstituency" value="Ogun East"></div>
            <div class="input-group"><label>Registered Voters</label><input type="number" id="adminElectVoters" value="250000"></div>
            <button class="btn-submit" style="background:#16a34a;" onclick="submitCreateElection()">Save Election</button>
            <button class="btn-secondary" style="margin-top:8px;" onclick="closeAdminModals()">Cancel</button>
        </div>
    </div>

    <!-- CANDIDATE ADD/UPDATE MODAL -->
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
            <textarea id="reviewNotes" placeholder="Collation Notes..." style="width:100%; height:40px; padding:6px; margin-top:8px;"></textarea>
            <div style="display:flex; gap:8px; margin-top:10px;">
                <button class="btn-submit" style="background:#16a34a; flex:1;" onclick="submitManualCollation('ACCEPTED')">✓ Accept & Collate</button>
                <button class="btn-submit" style="background:#dc2626; flex:1;" onclick="submitManualCollation('REJECTED')">✕ Reject</button>
            </div>
            <button class="btn-secondary" style="margin-top:8px;" onclick="closeReviewModal()">Close</button>
        </div>
    </div>

    <script>
        let currentUploadData = { lga: '', election_name: '', election_id: '1', ward: '', polling_unit: '', pu_code: '' };
        let activeModalSubmissionId = null;
        let selectedPhotoFile = null;
        let currentUserRole = "Super Admin";
        let currentUserAssignedLga = "";

        document.addEventListener('DOMContentLoaded', () => {
            const loginForm = document.getElementById('loginForm');
            if (loginForm) {
                loginForm.addEventListener('submit', (e) => {
                    e.preventDefault();
                    const username = document.getElementById('username')?.value || 'user';
                    
                    fetch('/api/login', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ username: username })
                    })
                    .then(res => res.json())
                    .then(data => {
                        applyRolePermissions(data.role, data.full_name || username, data.assigned_lga || '');
                        document.getElementById('authPage').classList.remove('active');
                        document.getElementById('dashboardPage').classList.add('active');
                        initDropdowns().then(() => {
                            document.querySelector('.nav-item[data-tab="live"]').click();
                        });
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
            applyRolePermissions("Viewer", "Guest Observer", "");
            document.getElementById('authPage').classList.remove('active');
            document.getElementById('dashboardPage').classList.add('active');
            initDropdowns().then(() => {
                document.querySelector('.nav-item[data-tab="live"]').click();
            });
        }

        function applyRolePermissions(role, name, assignedLga) {
            currentUserRole = role;
            currentUserAssignedLga = assignedLga;
            document.getElementById('userDisplayName').innerText = name;
            document.getElementById('userRoleBadge').innerText = role;

            const lgaBadge = document.getElementById('userLgaBadge');
            if (assignedLga) {
                lgaBadge.innerText = `LGA: ${assignedLga}`;
                lgaBadge.style.display = 'inline-block';
            } else {
                lgaBadge.style.display = 'none';
            }

            const btnUpload = document.getElementById('navUploadBtn');
            const btnReview = document.getElementById('navReviewBtn');
            const btnAdmin = document.getElementById('navAdminBtn');

            btnUpload.style.display = 'none';
            btnReview.style.display = 'none';
            btnAdmin.style.display = 'none';

            if (role === 'Super Admin') {
                btnUpload.style.display = 'flex';
                btnReview.style.display = 'flex';
                btnAdmin.style.display = 'flex';
            } else if (role === 'LGA Admin' || role === 'Admin') {
                btnUpload.style.display = 'flex';
                btnReview.style.display = 'flex';
            } else if (role === 'Field Officer') {
                btnUpload.style.display = 'flex';
            }
        }

        function initDropdowns() {
            return Promise.all([
                fetch('/api/admin/elections').then(res => res.json()),
                fetch('/api/locations/lgas').then(res => res.json())
            ]).then(([elections, lgas]) => {
                // Elections dropdown
                let electOpts = '<option value="all">-- All Elections Combined --</option>';
                elections.forEach(e => { electOpts += `<option value="${e.id}">${e.name}</option>`; });
                document.getElementById('liveElectionSelect').innerHTML = electOpts;
                if (elections.length > 0) document.getElementById('liveElectionSelect').value = elections[0].id;

                // LGAs dropdown
                let lgaOpts = '<option value="all">-- All 9 LGAs (Ogun East) --</option>';
                lgas.forEach(l => { lgaOpts += `<option value="${l}">${l}</option>`; });
                document.getElementById('liveLgaSelect').innerHTML = lgaOpts;
                document.getElementById('resultsLgaSelect').innerHTML = lgaOpts;
                document.getElementById('adminUserAssignedLga').innerHTML = lgas.map(l => `<option value="${l}">${l}</option>`).join('');

                if (currentUserRole === 'LGA Admin' && currentUserAssignedLga) {
                    document.getElementById('liveLgaSelect').value = currentUserAssignedLga;
                    document.getElementById('resultsLgaSelect').value = currentUserAssignedLga;
                }
            });
        }

        function onLiveFilterChanged() { loadLiveResults(); }

        function loadLiveResults() {
            const selectedElectionId = document.getElementById('liveElectionSelect')?.value || '1';
            const selectedLga = document.getElementById('liveLgaSelect')?.value || 'all';

            fetch(`/api/live-results?election_id=${encodeURIComponent(selectedElectionId)}&lga=${encodeURIComponent(selectedLga)}`)
            .then(res => res.json())
            .then(data => {
                document.getElementById('leaderTitle').innerText = data.leader?.candidate || 'Awaiting Verified Results';
                document.getElementById('leaderParty').innerText = data.leader?.party !== 'N/A' ? 'Party: ' + data.leader?.party : '';
                document.getElementById('leaderVotes').innerText = (data.leader?.votes || 0).toLocaleString();
                document.getElementById('leaderPct').innerText = data.leader?.percentage || '0%';
                
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

        function loadWardTable() {
            const selectedLga = document.getElementById('resultsLgaSelect')?.value || 'all';
            fetch(`/api/ward-results?lga=${encodeURIComponent(selectedLga)}`).then(res => res.json()).then(rows => {
                let html = '';
                rows.forEach(r => {
                    const v = r.party_votes || {};
                    html += `<tr><td><strong>${r.lga}</strong></td><td>${r.ward}</td><td>${r.polling_unit}<br><small>${r.pu_code}</small></td><td>${v.APC||0}</td><td>${v.PDP||0}</td><td>${v.LP||0}</td><td>${v.NNPP||0}</td><td><strong>${r.valid_votes||0}</strong></td></tr>`;
                });
                document.getElementById('resultsTableBody').innerHTML = html || '<tr><td colspan="8" style="text-align:center;">No collated results found.</td></tr>';
            });
        }

        function loadUploadWizardData() {
            fetch('/api/locations/lgas').then(res => res.json()).then(lgas => {
                let lgaBtns = '';
                lgas.forEach(l => { lgaBtns += `<button class="btn-select-option" onclick="selectLga('${l}')">${l} LGA</button>`; });
                document.getElementById('lgasListStack').innerHTML = lgaBtns;
            });
        }

        function goToUploadStep(s) {
            document.querySelectorAll('.wizard-step').forEach(step => step.classList.remove('active'));
            document.getElementById('uploadStep' + s).classList.add('active');
        }

        function selectLga(lga) {
            currentUploadData.lga = lga;
            fetch('/api/admin/elections').then(res => res.json()).then(elections => {
                let electBtns = '';
                elections.forEach(e => { electBtns += `<button class="btn-select-option" onclick="selectElection('${e.id}', '${e.name}')">${e.name}</button>`; });
                document.getElementById('electionsListStack').innerHTML = electBtns;
                goToUploadStep(2);
            });
        }

        function selectElection(id, name) {
            currentUploadData.election_id = id;
            currentUploadData.election_name = name;
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
            fd.append('lga', currentUploadData.lga);
            fd.append('ward', currentUploadData.ward);
            fd.append('polling_unit', currentUploadData.polling_unit);
            fd.append('pu_code', currentUploadData.pu_code);
            fd.append('submitted_by', document.getElementById('userDisplayName')?.innerText || 'Field Officer');

            fetch('/api/upload-photo-result', { method: 'POST', body: fd })
            .then(res => res.json()).then(res => {
                alert(res.message);
                selectedPhotoFile = null;
                document.getElementById('imagePreviewBox').style.display = 'none';
                document.getElementById('btnSubmitPhoto').style.display = 'none';
                goToUploadStep(1);
                if (['Super Admin', 'LGA Admin', 'Admin'].includes(currentUserRole)) {
                    document.querySelector('.nav-item[data-tab="review"]').click();
                } else {
                    document.querySelector('.nav-item[data-tab="live"]').click();
                }
            });
        }

        function switchReviewSubTab(t) {
            document.getElementById('subTabPending').style.display = t === 'pending' ? 'block' : 'none';
            document.getElementById('subTabAudit').style.display = t === 'audit' ? 'block' : 'none';
            if (t === 'pending') loadReviewQueue(); else loadAuditLog();
        }

        function loadReviewQueue() {
            fetch(`/api/review-queue?role=${encodeURIComponent(currentUserRole)}&assigned_lga=${encodeURIComponent(currentUserAssignedLga)}`)
            .then(res => res.json())
            .then(queue => {
                let html = '';
                queue.forEach(item => {
                    html += `
                    <div class="party-card" style="border-left-color:#d97706; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:10px; font-weight:800; background:#fef3c7; color:#92400e; padding:2px 6px; border-radius:4px;">PENDING VERIFICATION</span>
                            <span style="font-size:11px; font-weight:700; color:#2563eb;">📍 LGA: ${item.lga}</span>
                        </div>
                        <h4 style="margin-top:6px;">#${item.id} ${item.election_name}</h4>
                        <p><small>Ward: ${item.ward} | PU: ${item.polling_unit} (${item.pu_code})</small></p>
                        <p><small>Assigned Officer: <strong>${item.assigned_to||'LGA Admin'}</strong></small></p>
                        <button class="btn-action" style="margin-top:8px;" onclick="openReviewModal(${item.id}, '${item.image_url}', '${item.lga}', '${item.ward}', '${item.polling_unit}', '${item.pu_code}', '${item.election_name}')">🔍 Verify & Collate Result</button>
                    </div>`;
                });
                document.getElementById('reviewQueueList').innerHTML = html || '<p style="text-align:center; padding:15px;">No pending submissions in queue.</p>';
            });
        }

        function loadAuditLog() {
            fetch('/api/audit-log').then(res => res.json()).then(logs => {
                let html = '';
                logs.forEach(item => {
                    html += `
                    <div class="party-card" style="border-left-color:${item.status==='ACCEPTED'?'#16a34a':'#dc2626'}; margin-bottom:10px;">
                        <span style="font-size:10px; font-weight:800; background:${item.status==='ACCEPTED'?'#dcfce7':'#fee2e2'}; color:${item.status==='ACCEPTED'?'#166534':'#991b1b'}; padding:2px 6px; border-radius:4px;">${item.status}</span>
                        <h4 style="margin-top:4px;">#${item.id} ${item.election_name}</h4>
                        <p><small>LGA: ${item.lga} | Ward: ${item.ward} | PU: ${item.polling_unit}</small></p>
                        <p><small>Verified By: <strong>${item.verified_by||'Admin'}</strong></small></p>
                    </div>`;
                });
                document.getElementById('auditLogList').innerHTML = html || '<p style="text-align:center; padding:15px;">No audited items found.</p>';
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
                        verified_by: document.getElementById('userDisplayName')?.innerText || 'Super Admin'
                    })
                }).then(res => res.json()).then(res => {
                    alert(`✓ Submission #${activeModalSubmissionId} marked as ${status}!`);
                    closeReviewModal();
                    loadReviewQueue(); loadLiveResults(); loadWardTable();
                });
            });
        }

        function toggleLgaAssignField() {
            const role = document.getElementById('adminUserRole').value;
            document.getElementById('lgaAssignGroup').style.display = (role === 'LGA Admin') ? 'block' : 'none';
        }

        function openAdminModal(type) {
            closeAdminModals();
            if (type === 'user') {
                toggleLgaAssignField();
                document.getElementById('adminUserModal').classList.add('active');
            }
            if (type === 'election') document.getElementById('adminElectionModal').classList.add('active');
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

        function closeAdminModals() { document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active')); }

        function submitCreateUser() {
            const role = document.getElementById('adminUserRole').value;
            fetch('/api/admin/users', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    full_name: document.getElementById('adminUserFullName').value,
                    username: document.getElementById('adminUsername').value,
                    role: role,
                    assigned_lga: role === 'LGA Admin' ? document.getElementById('adminUserAssignedLga').value : '',
                    email: document.getElementById('adminUserEmail').value
                })
            }).then(res => res.json()).then(res => { alert(res.message); closeAdminModals(); loadAdminData('users'); });
        }

        function submitCreateElection() {
            fetch('/api/admin/elections', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: document.getElementById('adminElectName').value,
                    type: document.getElementById('adminElectType').value,
                    constituency: document.getElementById('adminElectConstituency').value,
                    registered_voters: document.getElementById('adminElectVoters').value
                })
            }).then(res => res.json()).then(res => { alert(res.message); closeAdminModals(); loadAdminData('elections'); });
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
                alert(res.message); closeAdminModals(); loadAdminData('candidates'); loadLiveResults();
            });
        }

        function loadAdminData(type) {
            fetch('/api/admin/' + type).then(res => res.json()).then(data => {
                let html = `<h4 style="color:#0c235c; margin-bottom:8px;">${type.toUpperCase()} (${data.length})</h4><div class="party-counter-grid">`;
                data.forEach(item => {
                    const img = item.photo_url || item.logo_url || '';
                    html += `
                    <div class="party-card" style="display:flex; align-items:center; gap:10px;">
                        ${img ? `<img src="${img}" style="width:36px; height:36px; object-fit:contain; border-radius:4px;">` : '👤'}
                        <div>
                            <strong>${item.full_name || item.name || item.acronym}</strong>
                            <p><small>${item.role ? 'Role: <b>' + item.role + '</b>' + (item.assigned_lga ? ' (LGA: ' + item.assigned_lga + ')' : '') : (item.acronym ? 'INEC Code: ' + item.inec_code : 'Party: <b>' + item.party + '</b>')}</small></p>
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
    print(f" OGUN EAST 2027 ELECTION WATCH RUNNING ON PORT {port}")
    print(f"==================================================")
    app.run(host='0.0.0.0', port=port, debug=True)
    