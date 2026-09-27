import sqlite3
import json
import os
from datetime import datetime

DB_NAME = "election_2027.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id TEXT,
            election_name TEXT,
            lga TEXT,
            ward TEXT,
            polling_unit TEXT,
            pu_code TEXT,
            party_votes TEXT DEFAULT '{}',
            valid_votes INTEGER DEFAULT 0,
            rejected_votes INTEGER DEFAULT 0,
            total_votes_cast INTEGER DEFAULT 0,
            image_url TEXT,
            submitted_by TEXT,
            timestamp DATETIME,
            status TEXT DEFAULT 'PENDING',
            review_notes TEXT,
            verified_by TEXT,
            verified_at DATETIME
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            username TEXT UNIQUE,
            role TEXT,
            email TEXT,
            created_at DATETIME
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS elections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            type TEXT,
            constituency TEXT,
            registered_voters INTEGER DEFAULT 50000
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            acronym TEXT UNIQUE,
            inec_code TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            party TEXT,
            election_name TEXT,
            photo_url TEXT DEFAULT '',
            created_at DATETIME
        )
    ''')
    
    cursor.execute("PRAGMA table_info(candidates)")
    cols = [c[1] for c in cursor.fetchall()]
    if 'photo_url' not in cols:
        cursor.execute("ALTER TABLE candidates ADD COLUMN photo_url TEXT DEFAULT ''")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state TEXT,
            lga TEXT,
            ward TEXT,
            polling_unit TEXT,
            pu_code TEXT
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (full_name, username, role, email, created_at) VALUES (?, ?, ?, ?, ?)",
                       ("Oladele Rotimi Williams", "Oladele Rotimi Williams", "Super Admin", "admin@electionwatch.ng", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    cursor.execute("SELECT COUNT(*) FROM parties")
    if cursor.fetchone()[0] == 0:
        default_parties = [
            ("Accord", "A", "001"),
            ("Action Alliance", "AA", "002"),
            ("Action Democratic Party", "ADP", "003"),
            ("All Progressives Congress", "APC", "004"),
            ("All Progressives Grand Alliance", "APGA", "005"),
            ("Labour Party", "LP", "006"),
            ("New Nigeria Peoples Party", "NNPP", "007"),
            ("Peoples Democratic Party", "PDP", "008"),
            ("Social Democratic Party", "SDP", "009"),
            ("Young Progressive Party", "YPP", "010")
        ]
        cursor.executemany("INSERT INTO parties (name, acronym, inec_code) VALUES (?, ?, ?)", default_parties)

    cursor.execute("SELECT COUNT(*) FROM candidates")
    if cursor.fetchone()[0] == 0:
        default_candidates = [
            ("Hon. Foluso Oladele", "APC", "Ijebu East State House of Assembly Election 2027", ""),
            ("Hon. Segun Adebayo", "PDP", "Ijebu East State House of Assembly Election 2027", ""),
            ("Hon. Chidi Nnamdi", "LP", "Ijebu East State House of Assembly Election 2027", ""),
            ("Hon. Rabiu Olanrewaju", "NNPP", "Ijebu East State House of Assembly Election 2027", ""),
            ("Hon. Adebisi Samson", "SDP", "Ijebu East State House of Assembly Election 2027", "")
        ]
        cursor.executemany("INSERT INTO candidates (full_name, party, election_name, photo_url, created_at) VALUES (?, ?, ?, ?, ?)", 
                           [(c[0], c[1], c[2], c[3], datetime.now().strftime("%Y-%m-%d %H:%M:%S")) for c in default_candidates])
        
    conn.commit()
    conn.close()

def save_pending_photo_submission(data):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO submissions 
        (election_id, election_name, lga, ward, polling_unit, pu_code, image_url, submitted_by, timestamp, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
    ''', (
        data.get('election_id', 'ijebu_east_sha'),
        data.get('election_name', 'Ijebu East State House of Assembly Election 2027'),
        data.get('lga', 'Ijebu East'),
        data.get('ward'),
        data.get('polling_unit'),
        data.get('pu_code'),
        data.get('image_url', ''),
        data.get('submitted_by', 'Oladele Rotimi Williams'),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Photo uploaded successfully and routed to Review Queue!"}

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
    ''', (
        json.dumps(party_votes),
        valid_votes,
        rejected,
        total_cast,
        status,
        notes,
        verified_by,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        sub_id
    ))
    
    cursor.execute("SELECT election_id FROM submissions WHERE id = ?", (sub_id,))
    row = cursor.fetchone()
    election_id = row['election_id'] if row else 'ijebu_east_sha'
    
    conn.commit()
    conn.close()
    return get_live_collation(election_id)

def get_live_collation(election_id=None):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT full_name, party, photo_url FROM candidates")
    cand_rows = cursor.fetchall()
    candidates_map = {c['party']: {"name": c['full_name'], "photo": c['photo_url']} for c in cand_rows}

    if election_id and election_id != 'all':
        cursor.execute("SELECT party_votes, valid_votes, rejected_votes, total_votes_cast FROM submissions WHERE status = 'ACCEPTED' AND election_id = ?", (election_id,))
    else:
        cursor.execute("SELECT party_votes, valid_votes, rejected_votes, total_votes_cast FROM submissions WHERE status = 'ACCEPTED'")
        
    rows = cursor.fetchall()
    cursor.execute("SELECT COUNT(DISTINCT polling_unit) FROM submissions WHERE status = 'ACCEPTED'")
    verified_pus = cursor.fetchone()[0]
    conn.close()
    
    party_totals = {}
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
            
    leader = {
        "candidate": "Awaiting Verified Results",
        "party": "N/A",
        "votes": 0,
        "percentage": "0%",
        "photo": ""
    }
    
    if party_totals and grand_valid > 0:
        top_party = max(party_totals, key=party_totals.get)
        top_votes = party_totals[top_party]
        top_pct = round((top_votes / grand_valid * 100), 1)
        cand_info = candidates_map.get(top_party, {"name": f"{top_party} Candidate", "photo": ""})
        
        leader = {
            "candidate": cand_info["name"],
            "party": top_party,
            "votes": top_votes,
            "percentage": f"{top_pct}%",
            "photo": cand_info["photo"]
        }
        
    standings = []
    for party, count in party_totals.items():
        pct = round((count / grand_valid * 100), 1) if grand_valid > 0 else 0
        cand_info = candidates_map.get(party, {"name": f"{party} Candidate", "photo": ""})
        standings.append({
            "candidate": cand_info["name"],
            "party": party,
            "photo": cand_info["photo"],
            "votes": count,
            "percentage": f"{pct}%",
            "percent_num": pct
        })
    standings.sort(key=lambda x: x['votes'], reverse=True)
    
    return {
        "leader": leader,
        "metrics": {
            "registered": 50000,
            "votes_cast": grand_total_cast,
            "turnout": f"{round((grand_total_cast / 50000 * 100), 1) if grand_total_cast > 0 else 0}%",
            "valid": grand_valid,
            "rejected": grand_rejected,
            "pus_verified": f"{verified_pus}/154",
            "progress_pct": f"{round((verified_pus / 154 * 100), 1)}%"
        },
        "standings": standings
    }

def reset_system_to_default():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM submissions")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='submissions'")
    cursor.execute("DELETE FROM users")
    cursor.execute("INSERT INTO users (full_name, username, role, email, created_at) VALUES (?, ?, ?, ?, ?)",
                   ("Oladele Rotimi Williams", "Oladele Rotimi Williams", "Super Admin", "admin@electionwatch.ng", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    cursor.execute("DELETE FROM elections")
    cursor.execute("INSERT INTO elections (name, type, constituency, registered_voters) VALUES (?, ?, ?, ?)",
                   ("Ijebu East State House of Assembly Election 2027", "State House of Assembly", "Ijebu East", 50000))
    conn.commit()
    conn.close()
    
    upload_dir = 'static/uploads'
    if os.path.exists(upload_dir):
        for f in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, f)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
    return {"success": True, "message": "⚡ System successfully reset to default factory state!"}

def get_pending_review_queue():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM submissions WHERE status = 'PENDING' ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    output = []
    for r in rows:
        item = dict(r)
        item['party_votes'] = json.loads(r['party_votes']) if r['party_votes'] else {}
        output.append(item)
    return output

def get_audit_log_archive():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM submissions WHERE status != 'PENDING' ORDER BY verified_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    output = []
    for r in rows:
        item = dict(r)
        item['party_votes'] = json.loads(r['party_votes']) if r['party_votes'] else {}
        output.append(item)
    return output

def get_ward_results(election_id='ijebu_east_sha'):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM submissions WHERE status = 'ACCEPTED' AND election_id = ? ORDER BY ward, polling_unit", (election_id,))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        item = dict(r)
        item['party_votes'] = json.loads(r['party_votes']) if r['party_votes'] else {}
        results.append(item)
    return results

def get_all_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_user(full_name, username, role, email):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (full_name, username, role, email, created_at) VALUES (?, ?, ?, ?, ?)",
                       (full_name, username, role, email, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return {"success": True, "message": f"User {username} created successfully!"}
    except Exception as e:
        conn.close()
        return {"success": False, "error": str(e)}

def get_all_elections():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM elections ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_election(name, elect_type, constituency, registered_voters):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO elections (name, type, constituency, registered_voters) VALUES (?, ?, ?, ?)",
                   (name, elect_type, constituency, registered_voters))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Election '{name}' created successfully!"}

def get_all_parties():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM parties ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_party(name, acronym, inec_code, is_active):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO parties (name, acronym, inec_code, is_active) VALUES (?, ?, ?, ?)",
                       (name, acronym, inec_code, 1 if is_active else 0))
        conn.commit()
        conn.close()
        return {"success": True, "message": f"Party {acronym} saved!"}
    except Exception as e:
        conn.close()
        return {"success": False, "error": str(e)}

def get_all_candidates():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_candidate(full_name, party, election_name, photo_url=""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO candidates (full_name, party, election_name, photo_url, created_at) VALUES (?, ?, ?, ?, ?)",
                   (full_name, party, election_name, photo_url, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Candidate '{full_name}' saved successfully!"}

def get_all_locations():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM locations ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_location(state, lga, ward, polling_unit, pu_code):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO locations (state, lga, ward, polling_unit, pu_code) VALUES (?, ?, ?, ?, ?)",
                   (state, lga, ward, polling_unit, pu_code))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Location '{polling_unit} ({pu_code})' saved!"}
