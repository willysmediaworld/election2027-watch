from flask import Flask, render_template_string, request, jsonify, session, Response, send_from_directory
import sqlite3
import json
import os
import csv
import io
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "ogun-east-2027-willys-media-world-fixed-secret-key"

# ==========================================
# ANDROID / PYROID 3 FILE PATHS
# ==========================================
ANDROID_BASE = "/storage/emulated/0/Documents/Pydroid3/ogun_election"
if not os.path.exists("/storage/emulated/0"):
    ANDROID_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ogun_election")

os.makedirs(ANDROID_BASE, exist_ok=True)
DB_NAME = os.path.join(ANDROID_BASE, "ogun_east_2027_production.db")
UPLOAD_FOLDER = os.path.join(ANDROID_BASE, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

print("=" * 60)
print(">>> ANDROID BASE FOLDER:", ANDROID_BASE)
print(">>> DATABASE PATH:", DB_NAME)
print(">>> UPLOAD FOLDER:", UPLOAD_FOLDER)
print("=" * 60)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# COMPLETE OGUN EAST LOCATIONS DATA
# 9 LGAs | 103 Wards | 1,555 Polling Units
# ==========================================
OGUN_EAST_LOCATIONS = [
    # =========================================================
    # IJEBU EAST (11 Wards, 154 PUs)
    # =========================================================
    ("Ogun", "Ijebu East", "Ijebu Mushin I", "ODOSEGBUREN", "27/08/01/001"),
    ("Ogun", "Ijebu East", "Ijebu Mushin I", "IDONA CENTRAL", "27/08/01/002"),
    ("Ogun", "Ijebu East", "Ijebu Mushin I", "ST. PETERS CLEVER PRY. SCH.", "27/08/01/003"),
    ("Ogun", "Ijebu East", "Ijebu Mushin I", "EWUREN SQUARE", "27/08/01/004"),
    ("Ogun", "Ijebu East", "Ijebu Mushin I", "LOCAL GOVT. PRY. SCHOOL", "27/08/01/005"),
    ("Ogun", "Ijebu East", "Ijebu Mushin I", "ST. ANDREWS SCH. IMUWEN I", "27/08/01/006"),
    ("Ogun", "Ijebu East", "Ijebu Mushin I", "ST. ANDREWS SCH. IMUWEN II", "27/08/01/007"),
    ("Ogun", "Ijebu East", "Ijebu Mushin I", "FEDERAL TECHNICAL ITA MOGIRI", "27/08/01/008"),
    ("Ogun", "Ijebu East", "Ijebu Mushin I", "ESURE JUNCTION", "27/08/01/009"),
    ("Ogun", "Ijebu East", "Ijebu Mushin I", "EHINADE COMM. PRY SCH. IDOMODU", "27/08/01/010"),
    ("Ogun", "Ijebu East", "Ijebu Mushin I", "OPEN SPACE AT ST ROAD SQUARE", "27/08/01/011"),
    ("Ogun", "Ijebu East", "Ijebu Mushin I", "MOSLEM PRY. SCH, ESURE", "27/08/01/012"),
    ("Ogun", "Ijebu East", "Ijebu Mushin II", "MUSHIN MARKET SQUARE", "27/08/02/001"),
    ("Ogun", "Ijebu East", "Ijebu Mushin II", "ST. MARY'S PRY OKEPO I", "27/08/02/002"),
    ("Ogun", "Ijebu East", "Ijebu Mushin II", "ST. MARY'S PRY OKEPO II", "27/08/02/003"),
    ("Ogun", "Ijebu East", "Ijebu Mushin II", "L.G. SCHOOL, KOKUNESERE", "27/08/02/004"),
    ("Ogun", "Ijebu East", "Ijebu Mushin II", "NEAR HEALTH CENTRE ILODO", "27/08/02/005"),
    ("Ogun", "Ijebu East", "Ijebu Mushin II", "AJEBO UNITED PRY. SCH. IKALA", "27/08/02/006"),
    ("Ogun", "Ijebu East", "Ijebu Mushin II", "OPEN SPACE IN FRONT OF JEJENIWA'S HOUSE", "27/08/02/007"),
    ("Ogun", "Ijebu East", "Ijebu Mushin II", "TOJORO JUNCTION", "27/08/02/008"),
    ("Ogun", "Ijebu East", "Ijebu Mushin II", "ST. MARY'S SCH. EXTENSION", "27/08/02/009"),
    ("Ogun", "Ijebu East", "Ijebu Mushin II", "IDOKUNUSI CENTRE", "27/08/02/010"),
    ("Ogun", "Ijebu East", "Ijebu Mushin II", "FRONTAGE OF ADESANYA'S HOUSE ILAGUNJO", "27/08/02/011"),
    ("Ogun", "Ijebu East", "Ijebu Mushin II", "IMUSHIN HEALTH CENTER", "27/08/02/012"),
    ("Ogun", "Ijebu East", "Ijebu Mushin II", "IDOKUNUSI TOWN HALL", "27/08/02/013"),
    ("Ogun", "Ijebu East", "Ijebu Ife I", "ITAKO SQUARE", "27/08/03/001"),
    ("Ogun", "Ijebu East", "Ijebu Ife I", "ST. LOUIS CATH. PRY. SCH. IFE", "27/08/03/002"),
    ("Ogun", "Ijebu East", "Ijebu Ife I", "ITUNMODU SQUARE", "27/08/03/003"),
    ("Ogun", "Ijebu East", "Ijebu Ife I", "ANG. PRY SCH. IJEBU-IFE", "27/08/03/004"),
    ("Ogun", "Ijebu East", "Ijebu Ife I", "BAPTIST SCHOOL II IJEBU IFE", "27/08/03/005"),
    ("Ogun", "Ijebu East", "Ijebu Ife I", "MOBORODE", "27/08/03/006"),
    ("Ogun", "Ijebu East", "Ijebu Ife I", "ITORO/ODELA SQUARE", "27/08/03/007"),
    ("Ogun", "Ijebu East", "Ijebu Ife I", "IROWO SQUARE", "27/08/03/008"),
    ("Ogun", "Ijebu East", "Ijebu Ife I", "ITORO/ODATA SQUARE", "27/08/03/009"),
    ("Ogun", "Ijebu East", "Ijebu Ife I", "IGBODU", "27/08/03/010"),
    ("Ogun", "Ijebu East", "Ijebu Ife I", "BESIDE OBADA MARKET", "27/08/03/011"),
    ("Ogun", "Ijebu East", "Ijebu Ife I", "ITAKO OLUWERI SQUARE", "27/08/03/012"),
    ("Ogun", "Ijebu East", "Ijebu Ife I", "BAPTIST SCHOOL II EXTENSION", "27/08/03/013"),
    ("Ogun", "Ijebu East", "Ijebu Ife I", "MOBORODE SQUARE", "27/08/03/014"),
    ("Ogun", "Ijebu East", "Ijebu Ife II", "TOWN HALL IJEBU IFE I", "27/08/04/001"),
    ("Ogun", "Ijebu East", "Ijebu Ife II", "TOWN HALL IJEBU IFE II", "27/08/04/002"),
    ("Ogun", "Ijebu East", "Ijebu Ife II", "COURT HALL", "27/08/04/003"),
    ("Ogun", "Ijebu East", "Ijebu Ife II", "ODUDUWA SQUARE", "27/08/04/004"),
    ("Ogun", "Ijebu East", "Ijebu Ife II", "TIMOROWO SQUARE", "27/08/04/005"),
    ("Ogun", "Ijebu East", "Ijebu Ife II", "MOSLEM SCHOOL II", "27/08/04/006"),
    ("Ogun", "Ijebu East", "Ijebu Ife II", "TIROSOGUN SQUARE", "27/08/04/007"),
    ("Ogun", "Ijebu East", "Ijebu Ife II", "ABIDAGBA VILLAGE", "27/08/04/008"),
    ("Ogun", "Ijebu East", "Ijebu Ife II", "EHINADE ILASE", "27/08/04/009"),
    ("Ogun", "Ijebu East", "Ijebu Ife II", "SQUARE NEAR MOSQUE", "27/08/04/010"),
    ("Ogun", "Ijebu East", "Ijebu Ife II", "IWAYA ROAD", "27/08/04/011"),
    ("Ogun", "Ijebu East", "Ijebu Ife II", "BAPTIST SCH. I, OKE IFE", "27/08/04/012"),
    ("Ogun", "Ijebu East", "Owu", "AGLICAN PRY. SCHOOL OWU I", "27/08/05/001"),
    ("Ogun", "Ijebu East", "Owu", "AGLICAN PRY. SCHOOL OWU II", "27/08/05/002"),
    ("Ogun", "Ijebu East", "Owu", "COMMUNITY PRY. SCH. ONIPETESI", "27/08/05/003"),
    ("Ogun", "Ijebu East", "Owu", "L.G. SCH. EGBEDA", "27/08/05/004"),
    ("Ogun", "Ijebu East", "Owu", "ABA OKONZIN JUNCTION", "27/08/05/005"),
    ("Ogun", "Ijebu East", "Owu", "ANG. PRY. SCH. II AGO OWU", "27/08/05/006"),
    ("Ogun", "Ijebu East", "Owu", "AJEPODO", "27/08/05/007"),
    ("Ogun", "Ijebu East", "Owu", "TOGUNMAGA", "27/08/05/008"),
    ("Ogun", "Ijebu East", "Owu", "GBAMUGBAMU", "27/08/05/009"),
    ("Ogun", "Ijebu East", "Owu", "ABU SORO", "27/08/05/010"),
    ("Ogun", "Ijebu East", "Owu", "TOWN HALL, ILORO", "27/08/05/011"),
    ("Ogun", "Ijebu East", "Owu", "AGBORO SQUARE", "27/08/05/012"),
    ("Ogun", "Ijebu East", "Owu", "ABA-EYO MARKET SQUARE", "27/08/05/013"),
    ("Ogun", "Ijebu East", "Owu", "ISIBA SQUARE", "27/08/05/014"),
    ("Ogun", "Ijebu East", "Owu", "ERINWONRAN MARKET SQUARE", "27/08/05/015"),
    ("Ogun", "Ijebu East", "Owu", "OLOMIKOKO SQUARE", "27/08/05/016"),
    ("Ogun", "Ijebu East", "Ikija", "ANGLICAN PRY. SCH. IKIJA", "27/08/06/001"),
    ("Ogun", "Ijebu East", "Ikija", "ISOMU SQUARE", "27/08/06/002"),
    ("Ogun", "Ijebu East", "Ikija", "L.G. SCHOOL ISIRE", "27/08/06/003"),
    ("Ogun", "Ijebu East", "Ikija", "COURT HALL, IKIJA", "27/08/06/004"),
    ("Ogun", "Ijebu East", "Ikija", "ANGLICAN PRY. SCH. IGAN IPABI", "27/08/06/005"),
    ("Ogun", "Ijebu East", "Ikija", "ODOMEFI SQUARE", "27/08/06/006"),
    ("Ogun", "Ijebu East", "Ikija", "OLOKOKO SQUARE", "27/08/06/007"),
    ("Ogun", "Ijebu East", "Ikija", "IMARERE SQUARE", "27/08/06/008"),
    ("Ogun", "Ijebu East", "Itele", "ST. JOHN'S SCH. ITELE I", "27/08/07/001"),
    ("Ogun", "Ijebu East", "Itele", "ST. JOHN'S SCH. ITELE II", "27/08/07/002"),
    ("Ogun", "Ijebu East", "Itele", "CATH. PRY. SCH. ITELE", "27/08/07/003"),
    ("Ogun", "Ijebu East", "Itele", "ITELE MOTOR PARK", "27/08/07/004"),
    ("Ogun", "Ijebu East", "Itele", "ST. JAMES SCH. ATOYO", "27/08/07/005"),
    ("Ogun", "Ijebu East", "Itele", "ST. PETERS SCH. OKO-EKO", "27/08/07/006"),
    ("Ogun", "Ijebu East", "Itele", "ST. JOHN'S SCH. LUMAFON", "27/08/07/007"),
    ("Ogun", "Ijebu East", "Itele", "COMM. PRY. SCH. IMEGUN", "27/08/07/008"),
    ("Ogun", "Ijebu East", "Itele", "OPP. HEALTH POST TIGBORI", "27/08/07/009"),
    ("Ogun", "Ijebu East", "Itele", "COMM. SQUARE AWOTUNDE", "27/08/07/010"),
    ("Ogun", "Ijebu East", "Itele", "AGERIGE", "27/08/07/011"),
    ("Ogun", "Ijebu East", "Itele", "ODOMORE ROUND ABOUT", "27/08/07/012"),
    ("Ogun", "Ijebu East", "Itele", "DAGUNJA OPEN SPACE", "27/08/07/013"),
    ("Ogun", "Ijebu East", "Itele", "ITELE TOWN HALL", "27/08/07/014"),
    ("Ogun", "Ijebu East", "Itele", "ITELE HEALTH CENTER", "27/08/07/015"),
    ("Ogun", "Ijebu East", "Itele", "ATOYO MATERNITY CENTER", "27/08/07/016"),
    ("Ogun", "Ijebu East", "Itele", "MOTOR PARK, OGBERE JUNCTION", "27/08/07/017"),
    ("Ogun", "Ijebu East", "Ogbere", "PALACE FRONTAGE", "27/08/08/001"),
    ("Ogun", "Ijebu East", "Ogbere", "NEAR MOTOR PARK OGBERE", "27/08/08/002"),
    ("Ogun", "Ijebu East", "Ogbere", "ST. MARY SCHOOL OGBERE I", "27/08/08/003"),
    ("Ogun", "Ijebu East", "Ogbere", "ST. MARY SCHOOL OGBERE II", "27/08/08/004"),
    ("Ogun", "Ijebu East", "Ogbere", "COMM. PRY. SCHOOL KAJOLA", "27/08/08/005"),
    ("Ogun", "Ijebu East", "Ogbere", "ST. PAULS SCH. URO", "27/08/08/006"),
    ("Ogun", "Ijebu East", "Ogbere", "ST. PAULS SCH. OGURU", "27/08/08/007"),
    ("Ogun", "Ijebu East", "Ogbere", "MOBORODE VILLAGE", "27/08/08/008"),
    ("Ogun", "Ijebu East", "Ogbere", "J. 3", "27/08/08/009"),
    ("Ogun", "Ijebu East", "Ogbere", "ST. JOHN'S SCH. KOREDE", "27/08/08/010"),
    ("Ogun", "Ijebu East", "Ogbere", "LOCAL GOVERNMENT SCH. IMAYAN", "27/08/08/011"),
    ("Ogun", "Ijebu East", "Ogbere", "ORITA IMOBI", "27/08/08/012"),
    ("Ogun", "Ijebu East", "Ogbere", "TRIANGA", "27/08/08/013"),
    ("Ogun", "Ijebu East", "Ogbere", "OPEN SPACE BESIDE ANGLICAN CHURCH", "27/08/08/014"),
    ("Ogun", "Ijebu East", "Ogbere", "MATERNITY CENTER OGBERE", "27/08/08/015"),
    ("Ogun", "Ijebu East", "Ogbere", "OGBERE SHOPPING COMPLEX", "27/08/08/016"),
    ("Ogun", "Ijebu East", "Ogbere", "ST. BRENDANS GRAMMAR SCH., OGBERE", "27/08/08/017"),
    ("Ogun", "Ijebu East", "Ogbere", "COMMUNITY PRY. SCH., OKEMISHA", "27/08/08/018"),
    ("Ogun", "Ijebu East", "Ogbere", "OPEN SPACE, BETWEEN", "27/08/08/019"),
    ("Ogun", "Ijebu East", "Ogbere", "COMMUNITY PRY SCH. OGUNGBO", "27/08/08/020"),
    ("Ogun", "Ijebu East", "Ogbere", "COMMUNITY PRY. SCH., AJEDE", "27/08/08/021"),
    ("Ogun", "Ijebu East", "Imobi I", "ST. MARY'S SCHOOL FOWOSEJE I", "27/08/09/001"),
    ("Ogun", "Ijebu East", "Imobi I", "ST. MARY'S SCHOOL FOWOSEJE II", "27/08/09/002"),
    ("Ogun", "Ijebu East", "Imobi I", "CATH. PRY. SCH. FOTEDO", "27/08/09/003"),
    ("Ogun", "Ijebu East", "Imobi I", "DENUREN", "27/08/09/004"),
    ("Ogun", "Ijebu East", "Imobi I", "MOSLEM PRY. SCH. ITA PAMPA", "27/08/09/005"),
    ("Ogun", "Ijebu East", "Imobi I", "MOSLEM PRY. SCH. TERELU", "27/08/09/006"),
    ("Ogun", "Ijebu East", "Imobi I", "TOLIWO OKE-IMOBI", "27/08/09/007"),
    ("Ogun", "Ijebu East", "Imobi I", "MAFOWOKU", "27/08/09/008"),
    ("Ogun", "Ijebu East", "Imobi II", "CATH. SCHOOL ITASIN", "27/08/10/001"),
    ("Ogun", "Ijebu East", "Imobi II", "CATH. SCHOOL EBUTE-IMOBI", "27/08/10/002"),
    ("Ogun", "Ijebu East", "Imobi II", "ANG. PRY. SCH. OKI-ARAROMI", "27/08/10/003"),
    ("Ogun", "Ijebu East", "Imobi II", "CATH. SCH. OKI-IGBODE I", "27/08/10/004"),
    ("Ogun", "Ijebu East", "Imobi II", "CATH. SCH. OKI-IGBODE II", "27/08/10/005"),
    ("Ogun", "Ijebu East", "Imobi II", "ST. COLUMBUS OKE-MAKUN", "27/08/10/006"),
    ("Ogun", "Ijebu East", "Imobi II", "TOGUNSELU SQUARE", "27/08/10/007"),
    ("Ogun", "Ijebu East", "Imobi II", "TOTUNBA", "27/08/10/008"),
    ("Ogun", "Ijebu East", "Ajebandele", "COMMUNITY PRY. SCHOOL ORITA J4", "27/08/11/001"),
    ("Ogun", "Ijebu East", "Ajebandele", "AJEGBENDE", "27/08/11/002"),
    ("Ogun", "Ijebu East", "Ajebandele", "ORISUMBARE", "27/08/11/003"),
    ("Ogun", "Ijebu East", "Ajebandele", "ST. SAVIOUR'S SCH. AJEBANDELE I", "27/08/11/004"),
    ("Ogun", "Ijebu East", "Ajebandele", "ST. SAVIOUR'S SCH. AJEBANDELE II", "27/08/11/005"),
    ("Ogun", "Ijebu East", "Ajebandele", "COMM. PRY. SCH. OLOJI", "27/08/11/006"),
    ("Ogun", "Ijebu East", "Ajebandele", "COMM. PRY. SCH. ABERU", "27/08/11/007"),
    ("Ogun", "Ijebu East", "Ajebandele", "ST. PETERS SCH. FOWOWA J4", "27/08/11/008"),
    ("Ogun", "Ijebu East", "Ajebandele", "OPEN SPACE AT ALAFIA CAMP", "27/08/11/009"),
    ("Ogun", "Ijebu East", "Ajebandele", "AJELANWA", "27/08/11/010"),
    ("Ogun", "Ijebu East", "Ajebandele", "MOYAFOKO TOWN HALL", "27/08/11/011"),
    ("Ogun", "Ijebu East", "Ajebandele", "AGO/SULE TOWN HALL", "27/08/11/012"),
    ("Ogun", "Ijebu East", "Ajebandele", "BASHIRU TOWN HALL", "27/08/11/013"),
    ("Ogun", "Ijebu East", "Ajebandele", "OLOKE ALLI TOWN HALL", "27/08/11/014"),
    ("Ogun", "Ijebu East", "Ajebandele", "OWODE COMMUNITY PRY. SCH", "27/08/11/015"),
    ("Ogun", "Ijebu East", "Ajebandele", "TEMIDIRE TOWN HALL", "27/08/11/016"),
    ("Ogun", "Ijebu East", "Ajebandele", "AJEBO TOWN HALL", "27/08/11/017"),
    ("Ogun", "Ijebu East", "Ajebandele", "LUKOSI COMMUNITY PRIMARY SCHOOL", "27/08/11/018"),
    ("Ogun", "Ijebu East", "Ajebandele", "LAAGAN TOWN HALL", "27/08/11/019"),
    ("Ogun", "Ijebu East", "Ajebandele", "COMMUNITY PRIMARY SCHOOL, IDI EGUN SITE", "27/08/11/020"),
    ("Ogun", "Ijebu East", "Ajebandele", "COMMUNITY PRIMARY SCHOOL, ADEMOLA IDI EGUN", "27/08/11/021"),
    ("Ogun", "Ijebu East", "Ajebandele", "AJELANWA MARKET SQUARE", "27/08/11/022"),
    ("Ogun", "Ijebu East", "Ajebandele", "ABA SADIKU TOWN HALL", "27/08/11/023"),
    ("Ogun", "Ijebu East", "Ajebandele", "AFUYE/OGBARA TOWN HALL", "27/08/11/024"),
    ("Ogun", "Ijebu East", "Ajebandele", "OLORUNPODO COMMUNITY PRY SCH.", "27/08/11/025"),

    # =========================================================
    # IJEBU NORTH (11 Wards, 268 PUs)
    # =========================================================
    ("Ogun", "Ijebu North", "Atikori", "IN FRONT OF OLOYEDE'S HOUSE", "27/09/01/001"),
    ("Ogun", "Ijebu North", "Atikori", "CHRIST DISCIPLES SCHOOL", "27/09/01/002"),
    ("Ogun", "Ijebu North", "Atikori", "NEAR BOGIJIE'S HOUSE I", "27/09/01/003"),
    ("Ogun", "Ijebu North", "Atikori", "NEAR BOGIJIE'S HOUSE II", "27/09/01/004"),
    ("Ogun", "Ijebu North", "Atikori", "HEALTH CENTRE, OKE-IFE I", "27/09/01/005"),
    ("Ogun", "Ijebu North", "Atikori", "HEALTH CENTRE, OKE-IFE II", "27/09/01/006"),
    ("Ogun", "Ijebu North", "Atikori", "ST. JAMES' SCHOOL I", "27/09/01/007"),
    ("Ogun", "Ijebu North", "Atikori", "IN FRONT OF DR. SOJOBI'S HOUSE I", "27/09/01/008"),
    ("Ogun", "Ijebu North", "Atikori", "IN FRONT OF DR. SOJOBI'S HOUSE II", "27/09/01/009"),
    ("Ogun", "Ijebu North", "Atikori", "IN FRONT OF JEBODA'S HOUSE I", "27/09/01/010"),
    ("Ogun", "Ijebu North", "Atikori", "IN FRONT OF JEBODA'S HOUSE II", "27/09/01/011"),
    ("Ogun", "Ijebu North", "Atikori", "IN FRONT OF IMAM'S HOUSE OKUMOJE I", "27/09/01/012"),
    ("Ogun", "Ijebu North", "Atikori", "IN FRONT OF IMAM'S HOUSE OKUMOJE II", "27/09/01/013"),
    ("Ogun", "Ijebu North", "Atikori", "IN FRONT OF ONIGBURE'S HOUSE", "27/09/01/014"),
    ("Ogun", "Ijebu North", "Atikori", "DAGBOLU MOTOR PARK", "27/09/01/015"),
    ("Ogun", "Ijebu North", "Atikori", "HEALTH CENTRE", "27/09/01/016"),
    ("Ogun", "Ijebu North", "Atikori", "ST. JAMES' SCHOOL II", "27/09/01/017"),
    ("Ogun", "Ijebu North", "Atikori", "OSUN MOTOR PARK", "27/09/01/018"),
    ("Ogun", "Ijebu North", "Atikori", "SHAMUSU-SUUDIL ISLAMIC PRY. SCH. ATIKORI", "27/09/01/019"),
    ("Ogun", "Ijebu North", "Atikori", "OPEN SPACE BESIDE VULCANISER HOUSE OLD ROTIMI JOBO JUNCTION", "27/09/01/020"),
    ("Ogun", "Ijebu North", "Atikori", "OPEN SPACE IN FRONT OF MAGISTRATE COURT", "27/09/01/021"),
    ("Ogun", "Ijebu North", "Atikori", "KEGBO COMPREHENSIVE HIGH SCHOOL", "27/09/01/022"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "IN FRONT OF NUBI CARPENTER'S HOUSE", "27/09/02/001"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "AT LOCAL GOVT. MARKET", "27/09/02/002"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "IN FRONT OF OLORITUN'S HOUSE", "27/09/02/003"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "ST. MATHEW SCHOOL II", "27/09/02/004"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "AT VICARAGE", "27/09/02/005"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "ST. MATHEW SCHOOL I", "27/09/02/006"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "ST. LUKE'S SCHOOL, JAPARA", "27/09/02/007"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "FRONT OF SODINA'S HOUSE", "27/09/02/008"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "FRONT OF HEALTH CENTRE, JAPARA", "27/09/02/009"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "FRONT OF AYANWALE'S HOUSE OJOWO", "27/09/02/010"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "FRONT OF ALHAJI LAWAL'S HOUSE ODORABOYEJI", "27/09/02/011"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "FRONT OF ABEGUNDE'S HOUSE ALEDO I", "27/09/02/012"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "FRONT OF ABEGUNDE'S HOUSE ALEDO II", "27/09/02/013"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "ROUNDABOUT ODOSENBADEJO", "27/09/02/014"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "ABIDUN HALL", "27/09/02/015"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "FRONT OF ADARAMAJA'S HOUSE", "27/09/02/016"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "FRONT OF S.S. BANJO'S HOUSE", "27/09/02/017"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "OPEN SPACE AT ARO ADEBISI JUNCTION", "27/09/02/018"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "IJEBU IGBO GIRL GRAMMAR SCH., OJOWO", "27/09/02/019"),
    ("Ogun", "Ijebu North", "Japara/Ojowo", "JAPARA HIGH SCHOOL, JAPARA, IJEBU NORTH", "27/09/02/020"),
    ("Ogun", "Ijebu North", "Omen", "PAPA OLOGBONI'S VILLAGE", "27/09/03/001"),
    ("Ogun", "Ijebu North", "Omen", "IPAKODO VILLAGE", "27/09/03/002"),
    ("Ogun", "Ijebu North", "Omen", "DAGBOLU LOCAL GOVT. SCH. I", "27/09/03/003"),
    ("Ogun", "Ijebu North", "Omen", "DAGBOLU LOCAL GOVT. SCH. II", "27/09/03/004"),
    ("Ogun", "Ijebu North", "Omen", "ITA EGBA ANGLICAN SCH.", "27/09/03/005"),
    ("Ogun", "Ijebu North", "Omen", "L.G. SCH. LUMOGEDE", "27/09/03/006"),
    ("Ogun", "Ijebu North", "Omen", "L.G. SCH. GANRIGAN, JAPARA", "27/09/03/007"),
    ("Ogun", "Ijebu North", "Omen", "AJEBANDELE OGUNYE VILLAGE", "27/09/03/008"),
    ("Ogun", "Ijebu North", "Omen", "OKOLIYAN VILLAGE", "27/09/03/009"),
    ("Ogun", "Ijebu North", "Omen", "ODULAJA BAALE PRY. SCHOOL", "27/09/03/010"),
    ("Ogun", "Ijebu North", "Omen", "IDIOPARUN VILLAGE I", "27/09/03/011"),
    ("Ogun", "Ijebu North", "Omen", "IDIOPARUN VILLAGE II", "27/09/03/012"),
    ("Ogun", "Ijebu North", "Omen", "ERIDU VILLAGE", "27/09/03/013"),
    ("Ogun", "Ijebu North", "Omen", "ORITA AGBADE I", "27/09/03/014"),
    ("Ogun", "Ijebu North", "Omen", "ORITA AGBADE II", "27/09/03/015"),
    ("Ogun", "Ijebu North", "Omen", "ABA TITUN VILLAGE I", "27/09/03/016"),
    ("Ogun", "Ijebu North", "Omen", "ABA TITUN VILLAGE II", "27/09/03/017"),
    ("Ogun", "Ijebu North", "Omen", "OSHUNBUDEPO I", "27/09/03/018"),
    ("Ogun", "Ijebu North", "Omen", "OSHUNBUDEPO II", "27/09/03/019"),
    ("Ogun", "Ijebu North", "Omen", "AGBALASON VILLAGE", "27/09/03/020"),
    ("Ogun", "Ijebu North", "Omen", "ODULAJA HOUSE", "27/09/03/021"),
    ("Ogun", "Ijebu North", "Omen", "IDIOPARUN VILLAGE III", "27/09/03/022"),
    ("Ogun", "Ijebu North", "Osun", "IMOPA MARKET I", "27/09/04/001"),
    ("Ogun", "Ijebu North", "Osun", "IMOPA MARKET II", "27/09/04/002"),
    ("Ogun", "Ijebu North", "Osun", "R.C.M. SCHOOL IDAGOLU", "27/09/04/003"),
    ("Ogun", "Ijebu North", "Osun", "ST. GEORGE'S SCH., APARAKI", "27/09/04/004"),
    ("Ogun", "Ijebu North", "Osun", "L.G. SCH. EGAMORO", "27/09/04/005"),
    ("Ogun", "Ijebu North", "Osun", "ODOOSUN VILLAGE", "27/09/04/006"),
    ("Ogun", "Ijebu North", "Osun", "ST. STEPHEN'S SCH. ASIGIDI", "27/09/04/007"),
    ("Ogun", "Ijebu North", "Osun", "ST. PETER'S SCH. AGUNBOYE", "27/09/04/008"),
    ("Ogun", "Ijebu North", "Osun", "ARAROMI ADEKANBI", "27/09/04/009"),
    ("Ogun", "Ijebu North", "Osun", "OLORUNMODI VILLAGE I", "27/09/04/010"),
    ("Ogun", "Ijebu North", "Osun", "OLORUNMODI VILLAGE II", "27/09/04/011"),
    ("Ogun", "Ijebu North", "Osun", "ST. GEORGE PRY. R.C.M. SCHOOL, TOGUNBERO", "27/09/04/012"),
    ("Ogun", "Ijebu North", "Osun", "L.G. OUT SCHOOL, AKINLADE, OBISESAN", "27/09/04/013"),
    ("Ogun", "Ijebu North", "Osun", "DANDOLA VILLAGE", "27/09/04/014"),
    ("Ogun", "Ijebu North", "Osun", "L.G. SCHOOL APOJE", "27/09/04/015"),
    ("Ogun", "Ijebu North", "Osun", "IDEKAN CAMP", "27/09/04/016"),
    ("Ogun", "Ijebu North", "Osun", "TISABA VILLAGE", "27/09/04/017"),
    ("Ogun", "Ijebu North", "Osun", "TIGIWA VILLAGE", "27/09/04/018"),
    ("Ogun", "Ijebu North", "Osun", "AGBORO VILLAGE", "27/09/04/019"),
    ("Ogun", "Ijebu North", "Osun", "ABEKU EAST I (ABEKU AGBA)", "27/09/04/020"),
    ("Ogun", "Ijebu North", "Osun", "ABEKU EAST II (IDI OPEPE)", "27/09/04/021"),
    ("Ogun", "Ijebu North", "Osun", "ERIGBORO VILLAGE", "27/09/04/022"),
    ("Ogun", "Ijebu North", "Osun", "TEMIDIRE VILLAGE", "27/09/04/023"),
    ("Ogun", "Ijebu North", "Osun", "ABEKU EAST III (TEMIDIRE ABA TUNTUN)", "27/09/04/024"),
    ("Ogun", "Ijebu North", "Osun", "ABEKU (TOGEDENGBE)", "27/09/04/025"),
    ("Ogun", "Ijebu North", "Osun", "LAOSE OSOKO VILLAGE", "27/09/04/026"),
    ("Ogun", "Ijebu North", "Osun", "BAOKU VILLAGE SQUARE", "27/09/04/027"),
    ("Ogun", "Ijebu North", "Osun", "OPEN SPACE AT TEMIDIRE ABA TUNTUN", "27/09/04/028"),
    ("Ogun", "Ijebu North", "Osun", "OSHOKO COMMUNITY PRY SCHOOL, OSHOKO", "27/09/04/029"),
    ("Ogun", "Ijebu North", "Oke Agbo", "OPP. OJUBANIRE'S HOUSE I", "27/09/05/001"),
    ("Ogun", "Ijebu North", "Oke Agbo", "OPP. OJUBANIRE'S HOUSE II", "27/09/05/002"),
    ("Ogun", "Ijebu North", "Oke Agbo", "FRONT OF ODEKU'S HOUSE OKEMORO I", "27/09/05/003"),
    ("Ogun", "Ijebu North", "Oke Agbo", "FRONT OF ODEKU'S HOUSE OKEMORO II", "27/09/05/004"),
    ("Ogun", "Ijebu North", "Oke Agbo", "FRONT OF EASY LIFE HOUSE I", "27/09/05/005"),
    ("Ogun", "Ijebu North", "Oke Agbo", "HOLY ANGEL'S PRY. SCH. IDOSA", "27/09/05/006"),
    ("Ogun", "Ijebu North", "Oke Agbo", "ST. PHILIPS SCHOOL II", "27/09/05/007"),
    ("Ogun", "Ijebu North", "Oke Agbo", "FRONT OF ELEYUN'S HOUSE", "27/09/05/008"),
    ("Ogun", "Ijebu North", "Oke Agbo", "ST. PHILIPS SCHOOL I", "27/09/05/009"),
    ("Ogun", "Ijebu North", "Oke Agbo", "L.G. PRY. SCHOOL ALEDO", "27/09/05/010"),
    ("Ogun", "Ijebu North", "Oke Agbo", "FRONT OF CHIEF BADEJO'S HOUSE (BABAMO) I", "27/09/05/011"),
    ("Ogun", "Ijebu North", "Oke Agbo", "FRONT OF CHIEF BADEJO'S HOUSE (BABAMO) II", "27/09/05/012"),
    ("Ogun", "Ijebu North", "Oke Agbo", "FRONT OF DACOSTAL'S HOUSE", "27/09/05/013"),
    ("Ogun", "Ijebu North", "Oke Agbo", "FRONT OF IGAMOSA", "27/09/05/014"),
    ("Ogun", "Ijebu North", "Oke Agbo", "FRONT OF ALEDO'S MOSQ.", "27/09/05/015"),
    ("Ogun", "Ijebu North", "Oke Agbo", "BESIDE IDESAN MOSQ. I", "27/09/05/016"),
    ("Ogun", "Ijebu North", "Oke Agbo", "BESIDE IDESAN MOSQ. II", "27/09/05/017"),
    ("Ogun", "Ijebu North", "Oke Agbo", "OPP. Y.K. ALASO OKE'S HOUSE I", "27/09/05/018"),
    ("Ogun", "Ijebu North", "Oke Agbo", "OPP. Y.K. ALASO OKE'S HOUSE II", "27/09/05/019"),
    ("Ogun", "Ijebu North", "Oke Agbo", "OPP. APOLE'S HOUSE", "27/09/05/020"),
    ("Ogun", "Ijebu North", "Oke Agbo", "IN FRONT OF BALA BUKOLA'S HOUSE", "27/09/05/021"),
    ("Ogun", "Ijebu North", "Oke Agbo", "KADIRI JUNCTION", "27/09/05/022"),
    ("Ogun", "Ijebu North", "Oke Agbo", "IN FRONT OF EASY LIFE HOUSE II", "27/09/05/023"),
    ("Ogun", "Ijebu North", "Oke Agbo", "FRONT OF ELEYIN'S HOUSE", "27/09/05/024"),
    ("Ogun", "Ijebu North", "Oke Agbo", "ITAALE MOTOR PARK, OKE AGBO", "27/09/05/025"),
    ("Ogun", "Ijebu North", "Oke Agbo", "SHAMSUDEEN GRAMMAR SCHOOL, OKE AGBO", "27/09/05/026"),
    ("Ogun", "Ijebu North", "Oke Sopin", "SPACE AT ODO BALOGUN'S", "27/09/06/001"),
    ("Ogun", "Ijebu North", "Oke Sopin", "FRONT OF ALH. ALUBANKUDI'S HOUSE I", "27/09/06/002"),
    ("Ogun", "Ijebu North", "Oke Sopin", "FRONT OF ALH. ALUBANKUDI'S HOUSE II", "27/09/06/003"),
    ("Ogun", "Ijebu North", "Oke Sopin", "ST. JOHN'S CATH. SCH., OKE PADI", "27/09/06/004"),
    ("Ogun", "Ijebu North", "Oke Sopin", "ST. JOHN'S CATH. SCH., OKE PADI II", "27/09/06/005"),
    ("Ogun", "Ijebu North", "Oke Sopin", "NEAR LEGUMSEN MOSQ. ITOWO", "27/09/06/006"),
    ("Ogun", "Ijebu North", "Oke Sopin", "ODOYANGUSISE JUNCTION", "27/09/06/007"),
    ("Ogun", "Ijebu North", "Oke Sopin", "SPACE AT OJOLO", "27/09/06/008"),
    ("Ogun", "Ijebu North", "Oke Sopin", "NEAR ODOBOTU'S MOSQ. I", "27/09/06/009"),
    ("Ogun", "Ijebu North", "Oke Sopin", "FRONT OF FUNWONDARA MOSQ. I", "27/09/06/010"),
    ("Ogun", "Ijebu North", "Oke Sopin", "OBADA MOTOR PARK", "27/09/06/011"),
    ("Ogun", "Ijebu North", "Oke Sopin", "IDI-ABA IGBAIRE", "27/09/06/012"),
    ("Ogun", "Ijebu North", "Oke Sopin", "MOSLEM SCHOOL IGBARE I", "27/09/06/013"),
    ("Ogun", "Ijebu North", "Oke Sopin", "MOSLEM SCHOOL IGBARE II", "27/09/06/014"),
    ("Ogun", "Ijebu North", "Oke Sopin", "FRONT OF ODORAYE'S HOUSE", "27/09/06/015"),
    ("Ogun", "Ijebu North", "Oke Sopin", "BESIDE PUBLIC LIBRARY OGUNGBO STREET I", "27/09/06/016"),
    ("Ogun", "Ijebu North", "Oke Sopin", "BESIDE PUBLIC LIBRARY OGUNGBO STREET II", "27/09/06/017"),
    ("Ogun", "Ijebu North", "Oke Sopin", "BESIDE ITOWO MOSQUE", "27/09/06/018"),
    ("Ogun", "Ijebu North", "Oke Sopin", "ST. JOHN'S SCHOOL, OKE JAGA", "27/09/06/019"),
    ("Ogun", "Ijebu North", "Oke Sopin", "BESIDE ODORAMUSEGUN MOSQUE", "27/09/06/020"),
    ("Ogun", "Ijebu North", "Oke Sopin", "A.U.D. PRY. SCHOOL OKE-SOPIN", "27/09/06/021"),
    ("Ogun", "Ijebu North", "Oke Sopin", "FRONT OF OLLY THE TAILOR I", "27/09/06/022"),
    ("Ogun", "Ijebu North", "Oke Sopin", "FRONT OF PARAMOLE'S HOUSE, OKE TAKO", "27/09/06/023"),
    ("Ogun", "Ijebu North", "Oke Sopin", "SHOKA'S JUNCTION", "27/09/06/024"),
    ("Ogun", "Ijebu North", "Oke Sopin", "FRONT OF ODORASOYIN", "27/09/06/025"),
    ("Ogun", "Ijebu North", "Oke Sopin", "BESIDE TADEN GARDEN HOTEL EGBE", "27/09/06/026"),
    ("Ogun", "Ijebu North", "Oke Sopin", "ODO-BALOGUN JUNCTION", "27/09/06/027"),
    ("Ogun", "Ijebu North", "Oke Sopin", "FRONT OF FUNWONDARA'S HOUSE II", "27/09/06/028"),
    ("Ogun", "Ijebu North", "Oke Sopin", "MOSLEM SCHOOL, IGBAIRE III", "27/09/06/029"),
    ("Ogun", "Ijebu North", "Oke Sopin", "NEAR ODOBOTU'S MOSQ. II", "27/09/06/030"),
    ("Ogun", "Ijebu North", "Oke Sopin", "FRONT OF ALUBANKUDI HOUSE III", "27/09/06/031"),
    ("Ogun", "Ijebu North", "Oke Sopin", "FRONT OLLY TAILOR II", "27/09/06/032"),
    ("Ogun", "Ijebu North", "Oke Sopin", "ST JOSEPH RCM PRY SCH SOPIN", "27/09/06/033"),
    ("Ogun", "Ijebu North", "Oke Sopin", "OPEN SPACE AT SHONUBI JUNCTION", "27/09/06/034"),
    ("Ogun", "Ijebu North", "Oke Sopin", "ST THOMAS AC PRY SCHOOL OBADA", "27/09/06/035"),
    ("Ogun", "Ijebu North", "Oke Sopin", "MOLUSI COLLEGE", "27/09/06/036"),
    ("Ogun", "Ijebu North", "Oke Sopin", "OPEN SPACE AT HOPE IMMACULATE SCH, SHOKAS", "27/09/06/037"),
    ("Ogun", "Ijebu North", "Oke Sopin", "FRONT OF ABUSI EDUMARE ACADEMY SCHOOL, IJEBU IGBO", "27/09/06/038"),
    ("Ogun", "Ijebu North", "Oke Sopin", "INFRONT OF EGBE HEALTH CENTRE, OKE SOPIN", "27/09/06/039"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "SAGUN UNITED PRY. SCH. - ORU", "27/09/07/001"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "ITALE AWA", "27/09/07/002"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "AJEBO MOSLEM SCHOOL, ORU", "27/09/07/003"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "ST. MARKS PRY SCH. FALAFOMU ORU", "27/09/07/004"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "WESLEY SCH. AWA", "27/09/07/005"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "MOSLEM SCHOOL AWA", "27/09/07/006"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "AJEGUNLE PRY. SCHOOL, AWA", "27/09/07/007"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "ST. ROSE'S CATH. SCHOOL, ORU", "27/09/07/008"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "IDOFE COMP. HIGH SCHOOL, ORU", "27/09/07/009"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "ITALE ORU I", "27/09/07/010"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "ST. MICHAEL'S ANG. SCHOOL, AREDI-AWA", "27/09/07/011"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "IN FRONT OF TIYAMIYU HOUSE, OKE-IFE ORU", "27/09/07/012"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "OKE SEWON AWA", "27/09/07/013"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "IN FRONT OF JIMOH NUSI'S HOUSE ILAPORU", "27/09/07/014"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "ST. ANDREW CATHOLIC PRY SCHOOL, AWA", "27/09/07/015"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "ITALE ORU II", "27/09/07/016"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "FRONT OF MUSI'S HOUSE", "27/09/07/017"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "OPEN SPACE METHODIST CHURCH, AWA", "27/09/07/018"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "OPEN SPACE IMOTA QUARTERS, ORU", "27/09/07/019"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "OPEN SPACE AT ODOGBE STREET, ORU", "27/09/07/020"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "OPEN SPACE AT AYEGBAMI STREET, AWA", "27/09/07/021"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "ORU TOWN HALL", "27/09/07/022"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "OPEN SPACE BESIDE NSCDC OFFICE, AWA", "27/09/07/023"),
    ("Ogun", "Ijebu North", "Oru/Awa/Ilaporu", "REFUGE PRY. SCHOOL, ORU", "27/09/07/024"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "L.G. AREA OFFICE", "27/09/08/001"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "OYINKORO JUNCTION", "27/09/08/002"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "R. ODUS'S JUNCTION", "27/09/08/003"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "NEAR OWOSENI'S HOUSE", "27/09/08/004"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "IDODE WESLEY SCHOOL", "27/09/08/005"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "IDODE JUNCTION", "27/09/08/006"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "OPP. ADESEGUN'S HOUSE", "27/09/08/007"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "LOCAL GOVT. SCHOOL, IGAN", "27/09/08/008"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "IN FRONT OF OSIYEMI'S HOUSE", "27/09/08/009"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "WESLEY PRY. SCHOOL", "27/09/08/010"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "ODOMOLASA VILLAGE", "27/09/08/011"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "IN FRONT OF OGUNMOSU'S HOUSE I", "27/09/08/012"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "MOSLEM SCHOOL, OKE-ODO", "27/09/08/013"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "IN FRONT OF BAALE'S HOUSE", "27/09/08/014"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "IN FRONT OF OGUNMOSU'S HOUSE II", "27/09/08/015"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "IN FRONT OF ODEKOMAYA'S HOUSE", "27/09/08/016"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "BOOTH OPP. FAGBAMILA'S HOUSE", "27/09/08/017"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "BOOTH NEAR ONANUGA'S HOUSE", "27/09/08/018"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "BOOTH OPP. BAALE'S MABINU'S HOUSE", "27/09/08/019"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "BOOTH OPP. DUNIYA'S HOUSE", "27/09/08/020"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "OPEN SPACE F.G COMMUNITY WATER PROJECT, ABOBI", "27/09/08/021"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "ABOBI COMPREHENSIVE HIGH SCHOOL", "27/09/08/022"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "ITA MERIN COMPREHENSIVE HIGH SCHOOL", "27/09/08/023"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "OKE ODO PRIMARY HEALTH CENTRE", "27/09/08/024"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "OPEN SPACE KOROKO AREA, AGO IWOYE", "27/09/08/025"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "OPEN SPACE AT KONIGBA JUNCTION AGO IWOYE", "27/09/08/026"),
    ("Ogun", "Ijebu North", "Ago Iwoye I", "OPEN SPACE AT LUGBEDU COMMUNITY MARKET, AGO IWOYE", "27/09/08/027"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "OMOEDUMARE MODEL PRY. SCHOOL", "27/09/09/001"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "NEAR ALH. OLOWO IGBO'S HOUSE", "27/09/09/002"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "FRONT OF ADEGBERIN'S HOUSE", "27/09/09/003"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "OKANLAWON JUNCTION", "27/09/09/004"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "AKO MOSLEM SCHOOL", "27/09/09/005"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "IN FRONT OF OSIYOKUN IMOISISI QUARTERS", "27/09/09/006"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "ODO YANGBURIN'S JUNCTION", "27/09/09/007"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "FRONT OF AKINSOLA'S HOUSE", "27/09/09/008"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "IMOSISI WESLEY SCHOOL", "27/09/09/009"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "OPEN SPACE IN FRONT OF J.M.K'S HOUSE", "27/09/09/010"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "FRONT OF OGUN SOWOBO'S HOUSE", "27/09/09/011"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "MUSLIM HIGH SCHOOL", "27/09/09/012"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "IMERE MOSLEM SCHOOL", "27/09/09/013"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "BESIDE HIGH CLASS", "27/09/09/014"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "ST. PAUL'S PRY. SCHOOL IMERE", "27/09/09/015"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "AGO IWOYE SECONDARY SCHOOL", "27/09/09/016"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "BOOTH OPP. KUNKUSIS HOUSE", "27/09/09/017"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "BOOTH OPP. GBINDIN'S HOUSE", "27/09/09/018"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "FOWOSEJE COMPREHENSIVE HIGH SCHOOL, AGO IWOYE", "27/09/09/019"),
    ("Ogun", "Ijebu North", "Ago Iwoye II", "OPEN SPACE OPP. CHIPS FILLING STATION", "27/09/09/020"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "AKO WESLEY SCHOOL", "27/09/10/001"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "IPADO VILLAGE", "27/09/10/002"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "ELEGBERE JUNCTION", "27/09/10/003"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "IDIAKALA ANG. SCHOOL", "27/09/10/004"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "L.G. SCHOOL FARM SETTLEMENT I", "27/09/10/005"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "L.G. SCHOOL FARM SETTLEMENT II", "27/09/10/006"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "OKE EGBE WESLEY SCHOOL", "27/09/10/007"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "ODOYE MOSLEM SCHOOL I", "27/09/10/008"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "ODOYE MOSLEM SCHOOL II", "27/09/10/009"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "OKE BIRITIRO JUNCTION", "27/09/10/010"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "IDAGOLU VILLAGE", "27/09/10/011"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "IPAKODO VILLAGE", "27/09/10/012"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "EREDO WESLEY SCHOOL", "27/09/10/013"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "OKE MASE VILLAGE", "27/09/10/014"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "ORIWU VILLAGE", "27/09/10/015"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "LOCAL GOVT. SCHOOL OKO-ODO", "27/09/10/016"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "ORILE IBIPE VILLAGE", "27/09/10/017"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "AHMADIYYA HIGH SCH., AGO IWOYE", "27/09/10/018"),
    ("Ogun", "Ijebu North", "Ako-Onigbagbo/Gelete", "ORIBE EYIN ODI (GELETE)", "27/09/10/019"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "ABA PANA VILLAGE", "27/09/11/001"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "WESLEY SCHOOL ERIKAMO", "27/09/11/002"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "OKE ERIGBA VILLAGE", "27/09/11/003"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "WESLEY SCHOOL EHIM ETIRI", "27/09/11/004"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "L.G. SCHOOL, AWORI, J.J.", "27/09/11/005"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "ORIGBANLA VILLAGE", "27/09/11/006"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "ELEGUNESAN PRY SCH.", "27/09/11/007"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "L.G. SCHOOL OKE-MOJO", "27/09/11/008"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "OKE AROWA VILLAGE", "27/09/11/009"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "IPAKODO VILLAGE", "27/09/11/010"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "HEALTH CENTRE MAMU I", "27/09/11/011"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "OBADA VILLAGE", "27/09/11/012"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "EREGINRIN VILLAGE", "27/09/11/013"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "IGAN ORILE", "27/09/11/014"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "HEALTH CENTRE MAMU II", "27/09/11/015"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "SEMORU OGUNOIKI", "27/09/11/016"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "HEALTH CENTRE MAMU III", "27/09/11/017"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "BOOTH AT ODO EJOGUN", "27/09/11/018"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "BOOTH AT ERIAJE", "27/09/11/019"),
    ("Ogun", "Ijebu North", "Mamu/Etiri", "METHODIST SCH. OKE-MOJO", "27/09/11/020"),

    # =========================================================
    # IJEBU NORTH EAST (10 Wards, 111 PUs)
    # =========================================================
    ("Ogun", "Ijebu North East", "Atan/Imuku", "R.C.M. PRY. SCHOOL ATAN I", "27/10/01/001"),
    ("Ogun", "Ijebu North East", "Atan/Imuku", "FRONT OF OLUMUKU PALACE", "27/10/01/002"),
    ("Ogun", "Ijebu North East", "Atan/Imuku", "ODOGOGO VILLAGE CENTRE", "27/10/01/003"),
    ("Ogun", "Ijebu North East", "Atan/Imuku", "AFRICAN CHURCH BETHEL SCH. IDONA", "27/10/01/004"),
    ("Ogun", "Ijebu North East", "Atan/Imuku", "A/C PRY. SCHOOL ODOTU", "27/10/01/005"),
    ("Ogun", "Ijebu North East", "Atan/Imuku", "FRONT OF IMAFON MOSQUE", "27/10/01/006"),
    ("Ogun", "Ijebu North East", "Atan/Imuku", "FRONT OF L.G.E.A. IMUROKO", "27/10/01/007"),
    ("Ogun", "Ijebu North East", "Atan/Imuku", "ST. PETER'S PRY. SCHOOL IWAYE", "27/10/01/008"),
    ("Ogun", "Ijebu North East", "Atan/Imuku", "L.G. PRY SCHOOL IMUKU/ISOWE", "27/10/01/009"),
    ("Ogun", "Ijebu North East", "Atan/Imuku", "IGBASA VILLAGE SQUARE", "27/10/01/010"),
    ("Ogun", "Ijebu North East", "Odosimadegun/Odosebora", "ST. JOHN'S PRY. SCH. ODOSIMADEGUN", "27/10/02/001"),
    ("Ogun", "Ijebu North East", "Odosimadegun/Odosebora", "ILODU, FRONTAGE OREKOYA'S HOUSE", "27/10/02/002"),
    ("Ogun", "Ijebu North East", "Odosimadegun/Odosebora", "CHRIST CHURCH SCH. ODOSENBORA", "27/10/02/003"),
    ("Ogun", "Ijebu North East", "Odosimadegun/Odosebora", "C.A.C. PRY SCHOOL ODOSIWONADE", "27/10/02/004"),
    ("Ogun", "Ijebu North East", "Odosimadegun/Odosebora", "ILUGUN CENTRAL ACADEMY IBIDO", "27/10/02/005"),
    ("Ogun", "Ijebu North East", "Odosimadegun/Odosebora", "EBENEZER PRY. SCH. OMUTEDO", "27/10/02/006"),
    ("Ogun", "Ijebu North East", "Odosimadegun/Odosebora", "ST. PETER'S PRY. SCH. OKE-AYE", "27/10/02/007"),
    ("Ogun", "Ijebu North East", "Odosimadegun/Odosebora", "FRONTAGE ONAKOYA'S HOUSE IWOROMOSUN", "27/10/02/008"),
    ("Ogun", "Ijebu North East", "Odosimadegun/Odosebora", "ST. PAUL'S PRY SCHOOL ORIWU", "27/10/02/009"),
    ("Ogun", "Ijebu North East", "Odosimadegun/Odosebora", "FRONTAGE BAALE'S HOUSE IDORUNWON", "27/10/02/010"),
    ("Ogun", "Ijebu North East", "Odosimadegun/Odosebora", "FRONTAGE BAALE'S HOUSE GBAWONJO", "27/10/02/011"),
    ("Ogun", "Ijebu North East", "Odosimadegun/Odosebora", "OKETI ORLANDO'S HOUSE", "27/10/02/012"),
    ("Ogun", "Ijebu North East", "Odosimadegun/Odosebora", "FRONTAGE NEW CHURCH ODOSENBORA", "27/10/02/013"),
    ("Ogun", "Ijebu North East", "Odosimadegun/Odosebora", "ST. PAUL SCH. ODOSUGBAGBAWA VILLAGE", "27/10/02/014"),
    ("Ogun", "Ijebu North East", "Odosimadegun/Odosebora", "ILUMERIN VILLAGE CENTRE", "27/10/02/015"),
    ("Ogun", "Ijebu North East", "Odosimadegun/Odosebora", "IWOROMOSUN", "27/10/02/016"),
    ("Ogun", "Ijebu North East", "Imewiro/Ododeyo/Imomo", "COMM. PRY. SCH. IMEWURO", "27/10/03/001"),
    ("Ogun", "Ijebu North East", "Imewiro/Ododeyo/Imomo", "MARKET SQUARE IDODE", "27/10/03/002"),
    ("Ogun", "Ijebu North East", "Imewiro/Ododeyo/Imomo", "CATHOLIC PRY. SCHOOL IMOMO I", "27/10/03/003"),
    ("Ogun", "Ijebu North East", "Imewiro/Ododeyo/Imomo", "ANG. CHURCH ODEDEYO", "27/10/03/004"),
    ("Ogun", "Ijebu North East", "Imewiro/Ododeyo/Imomo", "ST. JOHN'S PRY. SCH. IDODE I", "27/10/03/005"),
    ("Ogun", "Ijebu North East", "Imewiro/Ododeyo/Imomo", "FRONTAGE BAALE'S HOUSE IBADAN - IJEBU", "27/10/03/006"),
    ("Ogun", "Ijebu North East", "Imewiro/Ododeyo/Imomo", "FRONTAGE BAALE TIKEKU AKUNRUNDUN - EBUTE", "27/10/03/007"),
    ("Ogun", "Ijebu North East", "Imewiro/Ododeyo/Imomo", "FRONTAGE OWOTOMO'S HOUSE IWORO", "27/10/03/008"),
    ("Ogun", "Ijebu North East", "Imewiro/Ododeyo/Imomo", "ANG. PRY SCHOOL ORUNWA", "27/10/03/009"),
    ("Ogun", "Ijebu North East", "Imewiro/Ododeyo/Imomo", "ST. MICHAEL'S PRY. SCH. ODEDEYO", "27/10/03/010"),
    ("Ogun", "Ijebu North East", "Imewiro/Ododeyo/Imomo", "VICARAGE FRONTAGE, IMEWURO", "27/10/03/011"),
    ("Ogun", "Ijebu North East", "Imewiro/Ododeyo/Imomo", "ETI OBU JUNCTION ALEDO ODEDEYO", "27/10/03/012"),
    ("Ogun", "Ijebu North East", "Imewiro/Ododeyo/Imomo", "ALEDO ODEDEYO", "27/10/03/013"),
    ("Ogun", "Ijebu North East", "Imewiro/Ododeyo/Imomo", "ABA YUSUFF", "27/10/03/014"),
    ("Ogun", "Ijebu North East", "Imewiro/Ododeyo/Imomo", "VILLAGE SQUARE OKE EKI", "27/10/03/015"),
    ("Ogun", "Ijebu North East", "Odesenlu", "CHRIST CHURCH SCH. ODOSENLU I", "27/10/04/001"),
    ("Ogun", "Ijebu North East", "Odesenlu", "CHRIST CHURCH SCH. ODOSENLU II", "27/10/04/002"),
    ("Ogun", "Ijebu North East", "Odesenlu", "OJU ORE SQUARE GROUND", "27/10/04/003"),
    ("Ogun", "Ijebu North East", "Odesenlu", "FRONTAGE MOSQUE AT ODOREGBE I", "27/10/04/004"),
    ("Ogun", "Ijebu North East", "Odesenlu", "OKE-OLA", "27/10/04/005"),
    ("Ogun", "Ijebu North East", "Odesenlu", "OKE OLOWU", "27/10/04/006"),
    ("Ogun", "Ijebu North East", "Odesenlu", "ILONE", "27/10/04/007"),
    ("Ogun", "Ijebu North East", "Igede/Itamarun", "CATHOLIC PRY. SCHOOL IGEDE", "27/10/05/001"),
    ("Ogun", "Ijebu North East", "Igede/Itamarun", "A.C.H.S. ITAMARUN", "27/10/05/002"),
    ("Ogun", "Ijebu North East", "Igede/Itamarun", "ST. PETER'S SCHOOL ODOGBONDU", "27/10/05/003"),
    ("Ogun", "Ijebu North East", "Igede/Itamarun", "FRONTAGE OGUNKOYA'S HOUSE - OKEYEJO", "27/10/05/004"),
    ("Ogun", "Ijebu North East", "Igede/Itamarun", "FRONTAGE BOLA'S HOUSE EGBE", "27/10/05/005"),
    ("Ogun", "Ijebu North East", "Igede/Itamarun", "OKELUGBONGUN", "27/10/05/006"),
    ("Ogun", "Ijebu North East", "Oju Ona", "ST. MICHAEL'S SCH. IPARI NLA", "27/10/06/001"),
    ("Ogun", "Ijebu North East", "Oju Ona", "IWORO TOWN HALL", "27/10/06/002"),
    ("Ogun", "Ijebu North East", "Oju Ona", "TOWN HALL, OKE AGBONLE", "27/10/06/003"),
    ("Ogun", "Ijebu North East", "Oju Ona", "IPARI OKE", "27/10/06/004"),
    ("Ogun", "Ijebu North East", "Oju Ona", "ODOKALABA", "27/10/06/005"),
    ("Ogun", "Ijebu North East", "Oju Ona", "FRONTAGE BAALE'S HOUSE - ITEBU", "27/10/06/006"),
    ("Ogun", "Ijebu North East", "Oju Ona", "ODOGBE VILLAGE SQUARE", "27/10/06/007"),
    ("Ogun", "Ijebu North East", "Oju Ona", "FRONTAGE OWOTOMO'S HOUSE", "27/10/06/008"),
    ("Ogun", "Ijebu North East", "Isoyin", "EMMANUEL PRY. SCH. ISONYIN", "27/10/07/001"),
    ("Ogun", "Ijebu North East", "Isoyin", "ISON YIN GRAMMAR SCHOOL", "27/10/07/002"),
    ("Ogun", "Ijebu North East", "Isoyin", "FRONT OF BAALE'S HOUSE - ISONYIN", "27/10/07/003"),
    ("Ogun", "Ijebu North East", "Isoyin", "ODOLE JUNCTION", "27/10/07/004"),
    ("Ogun", "Ijebu North East", "Isoyin", "UNITED PRY. SCH. APUNEEIN", "27/10/07/005"),
    ("Ogun", "Ijebu North East", "Isoyin", "ARABIC PRY. SCH. ISONYIN", "27/10/07/006"),
    ("Ogun", "Ijebu North East", "Isoyin", "FRONT OF BAALE'S HOUSE AGBOWA", "27/10/07/007"),
    ("Ogun", "Ijebu North East", "Isoyin", "FRONT OF BALE ILUPA", "27/10/07/008"),
    ("Ogun", "Ijebu North East", "Isoyin", "FRONT OF ITUN OLUGBALA", "27/10/07/009"),
    ("Ogun", "Ijebu North East", "Ilese", "MOSLEM PRY. SCH. ILESE I", "27/10/08/001"),
    ("Ogun", "Ijebu North East", "Ilese", "IDOMOWO VILLAGE CENTER", "27/10/08/002"),
    ("Ogun", "Ijebu North East", "Ilese", "ARMY BARRACKS I", "27/10/08/003"),
    ("Ogun", "Ijebu North East", "Ilese", "IDOMILA VILLAGE SQUARE", "27/10/08/004"),
    ("Ogun", "Ijebu North East", "Ilese", "AKITIPA", "27/10/08/005"),
    ("Ogun", "Ijebu North East", "Ilese", "OKE LISA ILESE I", "27/10/08/006"),
    ("Ogun", "Ijebu North East", "Ilese", "ILONE", "27/10/08/007"),
    ("Ogun", "Ijebu North East", "Ilese", "ALEDO ILESE", "27/10/08/008"),
    ("Ogun", "Ijebu North East", "Ilese", "ODOMOLASA VILLAGE", "27/10/08/009"),
    ("Ogun", "Ijebu North East", "Ilese", "ARMY BARRACKS II", "27/10/08/010"),
    ("Ogun", "Ijebu North East", "Ilese", "ESEPA FRONTAGE SUARA'S HOUSE", "27/10/08/011"),
    ("Ogun", "Ijebu North East", "Ilese", "HEALTH TECH ILESE", "27/10/08/012"),
    ("Ogun", "Ijebu North East", "Ilese", "ILESE COMPREHESIVE HIGH SCHOOL", "27/10/08/013"),
    ("Ogun", "Ijebu North East", "Ilese", "IKEN TOWN HALL", "27/10/08/014"),
    ("Ogun", "Ijebu North East", "Ilese", "OPEN SPACE ISADE", "27/10/08/015"),
    ("Ogun", "Ijebu North East", "Ilese", "OPEN SPACE ESURU", "27/10/08/016"),
    ("Ogun", "Ijebu North East", "Ilese", "OPEN SPACE RASONWA", "27/10/08/017"),
    ("Ogun", "Ijebu North East", "Oke-Eri/Ogbogbo", "U.P.S. SCHOOL IMOWO", "27/10/09/001"),
    ("Ogun", "Ijebu North East", "Oke-Eri/Ogbogbo", "WESLEY PRY. SCHOOL OKE-ERI", "27/10/09/002"),
    ("Ogun", "Ijebu North East", "Oke-Eri/Ogbogbo", "BAALE'S HOUSE IREWON", "27/10/09/003"),
    ("Ogun", "Ijebu North East", "Oke-Eri/Ogbogbo", "TOWN HALL, OGBOGBO I", "27/10/09/004"),
    ("Ogun", "Ijebu North East", "Oke-Eri/Ogbogbo", "TOWN HALL, OGBOGBO II", "27/10/09/005"),
    ("Ogun", "Ijebu North East", "Oke-Eri/Ogbogbo", "FRONTAGE BAALE'S HOUSE - IJARI", "27/10/09/006"),
    ("Ogun", "Ijebu North East", "Oke-Eri/Ogbogbo", "IGOYA", "27/10/09/007"),
    ("Ogun", "Ijebu North East", "Oke-Eri/Ogbogbo", "FRONTAGE BAALE'S HOUSE IWESI", "27/10/09/008"),
    ("Ogun", "Ijebu North East", "Oke-Eri/Ogbogbo", "OPEN SPACE AT GOLDEN ESTATE", "27/10/09/009"),
    ("Ogun", "Ijebu North East", "Oke-Eri/Ogbogbo", "OPEN SPACE ALONG MOLIPA IREWON", "27/10/09/010"),
    ("Ogun", "Ijebu North East", "Oke-Eri/Ogbogbo", "OGBOGBO BAPTIST PRIMARY SCHOOL", "27/10/09/011"),
    ("Ogun", "Ijebu North East", "Oke-Eri/Ogbogbo", "OPEN SPACE OKELE OGBOGBO", "27/10/09/012"),
    ("Ogun", "Ijebu North East", "Oke-Eri/Ogbogbo", "ONIRUGBO OPEN SPACE", "27/10/09/013"),
    ("Ogun", "Ijebu North East", "Erunwon", "EPHIPHANY PRY. SCH. ERUNWON", "27/10/10/001"),
    ("Ogun", "Ijebu North East", "Erunwon", "B.A.C. ODOPOTU", "27/10/10/002"),
    ("Ogun", "Ijebu North East", "Erunwon", "FRONTAGE BAALE'S HOUSE ODO AYE", "27/10/10/003"),
    ("Ogun", "Ijebu North East", "Erunwon", "FRONTAGE, SYNDICATE HOUSE IGBEBA", "27/10/10/004"),
    ("Ogun", "Ijebu North East", "Erunwon", "ELERUNWON'S PALACE", "27/10/10/005"),
    ("Ogun", "Ijebu North East", "Erunwon", "SECRETARIAT VIA OBOGBO", "27/10/10/006"),
    ("Ogun", "Ijebu North East", "Erunwon", "OGIDI HEALTH CENTRE", "27/10/10/007"),
    ("Ogun", "Ijebu North East", "Erunwon", "ILEFON", "27/10/10/008"),
    ("Ogun", "Ijebu North East", "Erunwon", "OPEN SPACE ISAKI", "27/10/10/009"),
    ("Ogun", "Ijebu North East", "Erunwon", "IYANUWUYRA OPEN SPACE", "27/10/10/010"),

# =========================================================
# IJEBU ODE (11 Wards, 161 PUs)
# =========================================================
("Ogun", "Ijebu Ode", "Isoku/Ososa", "BESIDE CO-OP BUILDING", "27/11/01/001"),
("Ogun", "Ijebu Ode", "Isoku/Ososa", "EMMANUEL SCHOOL I ITALUPE", "27/11/01/002"),
("Ogun", "Ijebu Ode", "Isoku/Ososa", "MOSLEM SCHOOL, ISOKU", "27/11/01/003"),
("Ogun", "Ijebu Ode", "Isoku/Ososa", "FRONT OF TALABI'S HOUSE OLISA STREET I", "27/11/01/004"),
("Ogun", "Ijebu Ode", "Isoku/Ososa", "IMORU ROAD JUNCTION", "27/11/01/005"),
("Ogun", "Ijebu Ode", "Isoku/Ososa", "OKE-OLA ILORIN", "27/11/01/006"),
("Ogun", "Ijebu Ode", "Isoku/Ososa", "EMMANUEL SCHOOL II", "27/11/01/007"),
("Ogun", "Ijebu Ode", "Isoku/Ososa", "FRONT OF TALABI'S HOUSE OLISA STREET II", "27/11/01/008"),
("Ogun", "Ijebu Ode", "Isoku/Ososa", "ADJACENT A. B SUNMOLA HOUSE, IJAGUN ROAD", "27/11/01/009"),
("Ogun", "Ijebu Ode", "Isoku/Ososa", "BESIDE 3A'S HOTEL, IMORU ROAD", "27/11/01/010"),
("Ogun", "Ijebu Ode", "Isoku/Ososa", "MOSLEM SCHOOL II ONDO ROAD", "27/11/01/011"),
("Ogun", "Ijebu Ode", "Odo-Esa", "BAPTIST DAY SCHOOL EREKO", "27/11/02/001"),
("Ogun", "Ijebu Ode", "Odo-Esa", "FRONT OF OUR LADY'S SCHOOL", "27/11/02/002"),
("Ogun", "Ijebu Ode", "Odo-Esa", "FRONT OF ALHAJI KUKOYI'S HOUSE", "27/11/02/003"),
("Ogun", "Ijebu Ode", "Odo-Esa", "OPPOSITE ITAJANA MOSQUE", "27/11/02/004"),
("Ogun", "Ijebu Ode", "Odo-Esa", "STATE HOSPITAL", "27/11/02/005"),
("Ogun", "Ijebu Ode", "Odo-Esa", "DENTAL CENTRE", "27/11/02/006"),
("Ogun", "Ijebu Ode", "Odo-Esa", "BY ODO ESA PREMIER MOSQUE NEAR IDIROKO, OLISA", "27/11/02/007"),
("Ogun", "Ijebu Ode", "Odo-Esa", "SAKA ASHIRU JUNCTION VIA MAYOMAYO", "27/11/02/008"),
("Ogun", "Ijebu Ode", "Odo-Esa", "OPEN SPACE BY OLORUNGBEBE MOSQUE", "27/11/02/009"),
("Ogun", "Ijebu Ode", "Odo-Esa", "JIMILEYIN JUNCTION, ADJACENT IREPODUN MOSQUE", "27/11/02/010"),
("Ogun", "Ijebu Ode", "Odo-Esa", "OPEN SPACE AT OGUNTUGA FOUR JUNCTION", "27/11/02/011"),
("Ogun", "Ijebu Ode", "Itantebo", "MOSLEM SCHOOL ETITALE I", "27/11/03/001"),
("Ogun", "Ijebu Ode", "Itantebo", "OPP. OLORITUN'S HOUSE", "27/11/03/002"),
("Ogun", "Ijebu Ode", "Itantebo", "FRONT OF IGBOBURO MOSQUE", "27/11/03/003"),
("Ogun", "Ijebu Ode", "Itantebo", "FRONT OF BALOGUN KUKU'S HOUSE", "27/11/03/004"),
("Ogun", "Ijebu Ode", "Itantebo", "ISOKUN / ITAOGBE JUNCTION", "27/11/03/005"),
("Ogun", "Ijebu Ode", "Itantebo", "MOSELM SCHOOL ETITALE II", "27/11/03/006"),
("Ogun", "Ijebu Ode", "Itantebo", "AHMMADIAH MOVEMENT B/S, ARAROMI", "27/11/03/007"),
("Ogun", "Ijebu Ode", "Ijade/Mepe I", "OLD WASIMI SCHOOL HALL", "27/11/04/001"),
("Ogun", "Ijebu Ode", "Ijade/Mepe I", "JOKE TAIWO PRY. SCHOOL", "27/11/04/002"),
("Ogun", "Ijebu Ode", "Ijade/Mepe I", "BALOGUN KUKU ROAD", "27/11/04/003"),
("Ogun", "Ijebu Ode", "Ijade/Mepe I", "OTUBU MEMORIAL SCHOOL", "27/11/04/004"),
("Ogun", "Ijebu Ode", "Ijade/Mepe I", "IYANRO MOSQUE", "27/11/04/005"),
("Ogun", "Ijebu Ode", "Ijade/Mepe I", "OKE AJE, BACK OF AJAYI'S HOUSE", "27/11/04/006"),
("Ogun", "Ijebu Ode", "Ijade/Mepe I", "OPEN SPACE AT MOBORODE / GBELEGBUWA JUNCTION", "27/11/04/007"),
("Ogun", "Ijebu Ode", "Ijade/Mepe I", "OPEN SPACE AT ITAPAKURA / OLODE JUNCTION", "27/11/04/008"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "FRONT OF OLISA'S PALACE", "27/11/05/001"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "OLD IJADA MARKET", "27/11/05/002"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "OMOLUWABI PRY. SCHOOL IMEPE", "27/11/05/003"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "MOSLEM PRY. SCH. IMEPE", "27/11/05/004"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "U.N.A. PRY. SCH. IMEPE", "27/11/05/005"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "ORUNSE AREA", "27/11/05/006"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "IDOMOWO/IMOSE", "27/11/05/007"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "WASIMI PRY SCHOOL", "27/11/05/008"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "IDELE", "27/11/05/009"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "AYERU/AJEGUNLE", "27/11/05/010"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "IPAMUREN MOSQUE", "27/11/05/011"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "BESIDE RAMDAT HOTEL, OGUNTUGA ST I-ODE", "27/11/05/012"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "OPEN SPACE AT OYA JUNCTION BY ADELAJA STR.", "27/11/05/013"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "AJEGUNLE / IJADA STREET BY IYA ADAM FOOD CANTEEN", "27/11/05/014"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "OPEN SPACE BY SATINA HOTEL, OFF ONDO ROAD", "27/11/05/015"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "OPEN SPACE BY OLORUNOSUN / SATINA JUNCTION, ONDO ROAD", "27/11/05/016"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "OPEN SPACE AT ORUNSE - JAGINRIN JUNCTION IMEPE", "27/11/05/017"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "OPEN SPACE AT ALHAJI SODIQ STREET NEAR OLATOYE HOUSE BY CELE", "27/11/05/018"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "CELE T-JUNCTION BY KOWA HOSPITAL OFF EJINRIN ROAD", "27/11/05/019"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "OPEN SPACE FRONT OF BISHOP COURT EJINRIN ROAD", "27/11/05/020"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "CARTERPILLAR JUNCTION ADEFISAN ROAD, OFF EJINRIN ROAD", "27/11/05/021"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "AKINTONDE PLAZA BY OYINGBO JUNCTION", "27/11/05/022"),
("Ogun", "Ijebu Ode", "Ijade/Mepe II", "FRONT OF HALIDU MOSQUE, IDELE JUNCTION", "27/11/05/023"),
("Ogun", "Ijebu Ode", "Porogun I", "MUSLEM COLLEGE", "27/11/06/001"),
("Ogun", "Ijebu Ode", "Porogun I", "OPPOSITE APELOKO", "27/11/06/002"),
("Ogun", "Ijebu Ode", "Porogun I", "OPPOSITE L.G. WORKS DEPT.", "27/11/06/003"),
("Ogun", "Ijebu Ode", "Porogun I", "BESIDE ISASA MOSQUE", "27/11/06/004"),
("Ogun", "Ijebu Ode", "Porogun I", "CHRIST CHURCH SCHOOL MOLODE", "27/11/06/005"),
("Ogun", "Ijebu Ode", "Porogun I", "AYEGBAMI WASIMI JUNCTION", "27/11/06/006"),
("Ogun", "Ijebu Ode", "Porogun I", "OJOFA/ALAPO JUNCTION", "27/11/06/007"),
("Ogun", "Ijebu Ode", "Porogun I", "MOBEGELU ST. (INFRONT OLOWU'S HOUSE)", "27/11/06/008"),
("Ogun", "Ijebu Ode", "Porogun I", "ADEOLA ODUTOLA COLLEGE", "27/11/06/009"),
("Ogun", "Ijebu Ode", "Porogun I", "LOCAL GOVT. MATERNITY CENTRE", "27/11/06/010"),
("Ogun", "Ijebu Ode", "Porogun I", "FIDIPOTE ADEOLA JUNCTION", "27/11/06/011"),
("Ogun", "Ijebu Ode", "Porogun I", "OPEN SPACE AT AYEGBAMI ABASS STREET JUNCTION", "27/11/06/012"),
("Ogun", "Ijebu Ode", "Porogun I", "OPEN SPACE AT MUKEKE JUNCTION BY MOSLEM COLLEGE ROAD", "27/11/06/013"),
("Ogun", "Ijebu Ode", "Porogun I", "OPEN SPACE AT MIDDLE OF KAKA STREET, TANIMOLA JUNCTION", "27/11/06/014"),
("Ogun", "Ijebu Ode", "Porogun I", "MOSLEM PRIMARY SCHOOL, MOLODE", "27/11/06/015"),
("Ogun", "Ijebu Ode", "Porogun I", "OPEN SPACE AGBAJE JUNCTION, BY TRANSFORMER", "27/11/06/016"),
("Ogun", "Ijebu Ode", "Porogun I", "OPEN SPACE AT ALEBIOSU STREET, DUPMOS JUNCTION", "27/11/06/017"),
("Ogun", "Ijebu Ode", "Porogun II", "FRONT OF BABALOLA'S HOUSE", "27/11/07/001"),
("Ogun", "Ijebu Ode", "Porogun II", "IJEBU-ODE GRAMMAR SCHOOL", "27/11/07/002"),
("Ogun", "Ijebu Ode", "Porogun II", "CHRIST CHURCH SCH., POROGUN", "27/11/07/003"),
("Ogun", "Ijebu Ode", "Porogun II", "A.G.G.S. OBALENDE", "27/11/07/004"),
("Ogun", "Ijebu Ode", "Porogun II", "ABEOKUTA ROAD FRONT OF ALOWOLODU", "27/11/07/005"),
("Ogun", "Ijebu Ode", "Porogun II", "OGBAGBA STREET (MIDDLE FRONT OF ALOWONLE", "27/11/07/006"),
("Ogun", "Ijebu Ode", "Porogun II", "ITALAPO MOSQUE", "27/11/07/007"),
("Ogun", "Ijebu Ode", "Porogun II", "MIDDLE ALAPO STREET, (INFRONT OF MOSQUE)", "27/11/07/008"),
("Ogun", "Ijebu Ode", "Porogun II", "ABEOKUTA RD (INFRONT OF OLUFOWOBI'S HOUSE)", "27/11/07/009"),
("Ogun", "Ijebu Ode", "Porogun II", "FISIGBOYE - EHINDIN JUNCTION BY IJEBU-ODE LOCAL GOVERNMENT SECRETARIAT", "27/11/07/010"),
("Ogun", "Ijebu Ode", "Porogun II", "OPEN SPACE AT ALATISHE MOSQUE BY TOTAL FILLING STATION", "27/11/07/011"),
("Ogun", "Ijebu Ode", "Porogun II", "DEGUN JUNCTION, OBALENDE", "27/11/07/012"),
("Ogun", "Ijebu Ode", "Porogun II", "OPEN SPACE BESIDE OBALENDE POLICE STATION", "27/11/07/013"),
("Ogun", "Ijebu Ode", "Porogun II", "OPEN SPACE BY OGUNBULE JUNCTION, OLORUNSOGO", "27/11/07/014"),
("Ogun", "Ijebu Ode", "Porogun II", "OPEN SPACE LEWU JUNCTION BESIDE SEICO HOUSE", "27/11/07/015"),
("Ogun", "Ijebu Ode", "Porogun II", "OMOSANYA OLAONIPEKUN JUNCTION, OFF DEGUN", "27/11/07/016"),
("Ogun", "Ijebu Ode", "Porogun II", "FIDIPOTE JUNCTION, OFF FUSIGBOYE ROAD", "27/11/07/017"),
("Ogun", "Ijebu Ode", "Porogun II", "OPEN SPACE AT ALAFIA / JAURA CHURCH JUNCTION", "27/11/07/018"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "OUR SAVIOUR'S PRY. SCHOOL", "27/11/08/001"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "FRONT OF BATA SHOP", "27/11/08/002"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "WESLEY SCHOOL", "27/11/08/003"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "C.A.C. SCHOOL DEGUN", "27/11/08/004"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "IDEPO JUNCTION", "27/11/08/005"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "ARAROMI/ILORO JUNCTION", "27/11/08/006"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "ODUTOLA ST. (BESIDE ODUPELE STREET)", "27/11/08/007"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "MOLIPA (INFRONT OGO-OLUWA BAKERY)", "27/11/08/008"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "MOLIPA HIGH SCHOOL", "27/11/08/009"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "ODUPELE / OGUNYOKU JUNCTION", "27/11/08/010"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "OSIMORE JUNCTION", "27/11/08/011"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "OPEN SPACE BY KENNY BLOCK INDUSTRY, ILAMO AREA", "27/11/08/012"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "OPEN SPACE BY AJIROBA HOUSE", "27/11/08/013"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "OPEN SPACE AT AWOYEMI JUNCTION", "27/11/08/014"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "OPEN SPACE AT ALAIYEPE OLUGBILE JUNCTION MOLIPA", "27/11/08/015"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "OLD EPIC SCHOOL / CELE CHURCH JUNCTION BEHIND PRIME HOTEL", "27/11/08/016"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "OPEN SPACE BY FOUR NUMBER JUNCTION MOLIPA ROAD", "27/11/08/017"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "OPEN SPACE AT DEGUN JUNCTION BY ONALAJA STREET OFF FOLAGBADE ROAD", "27/11/08/018"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "OPEN SPACE BY OGUNBA-OLASUNBO JUNCTION, OFF FOLAGBADE ROAD", "27/11/08/019"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "OPEN SPACE BY ZIPEST FILLING STATION, OPPOSITE SOYE MOSQUE", "27/11/08/020"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "AYESAN MARKET GATE, AYESAN AREA", "27/11/08/021"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "AWOYELU-JOGBO HEALTH CENTRE", "27/11/08/022"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "OPEN SPACE AT LEKUTI OKE JUNCTION", "27/11/08/023"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "OPEN SPACE OPPOSITE MAHDIYAT MOSQUE IDEPO STREET", "27/11/08/024"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "OPEN SPACE FRONT OF OGUN STATE TELEVISION, IJEBU ODE", "27/11/08/025"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "OPEN SPACE AT OSIFESO/ODUTOLA STREET, IJEBU ODE", "27/11/08/026"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "C. A. C. SCHOOL, DEGUN (2)", "27/11/08/027"),
("Ogun", "Ijebu Ode", "Ijasi/Idepo", "C.A.C CHURCH BY POST OFFICE / C.M.S BOOKSHOP FOLAGBADE", "27/11/08/028"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "ST. AUGUSTINE CATHOLIC SCHOOL", "27/11/09/001"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "A.U.D. PRY. SCH. I, BONOJO", "27/11/09/002"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "A.U.D. PRY. SCH. II ONIRUGBA", "27/11/09/003"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "GOVT. TECHNICAL COLLEGE", "27/11/09/004"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "EZEKIEL AWOYELU JUNCTION", "27/11/09/005"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "BESIDE IJEBU-ODE STADIUM", "27/11/09/006"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "TAI SOLARIN COLLEGE OF EDUCATION", "27/11/09/007"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "OLD ODO EGBO MARKET", "27/11/09/008"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "AHMADIYYA MOSQUE", "27/11/09/009"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "K. MANSION", "27/11/09/010"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "IGBEBA / ELEBUTE JUNCTION", "27/11/09/011"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "BONJO / ODUTOLA STREET", "27/11/09/012"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "GRA OFF AWUJALE STREET (MIDDLE)", "27/11/09/013"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "END OF BONOJO ELERUKU", "27/11/09/014"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "OLUFOWOBI BY BONOJO FOUR JUNCTION", "27/11/09/015"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "MAHDIYAT PRIMARY SCHOOL", "27/11/09/016"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "ADEBEN PLACE HOTEL JUNCTION, IGBEBA", "27/11/09/017"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "V.I.O CENTRE, ERUWON ROAD", "27/11/09/018"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "LUBA COMPREHENSIVE SCHOOL OFF ERUNWON ROAD", "27/11/09/019"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "OPEN SPACE INFRONT OF EID PRAYING GROUND, IDOBI", "27/11/09/020"),
("Ogun", "Ijebu Ode", "Odo-Egbo/Oliworo", "OPEN SPACE AT NEW ROAD BY ALAFIA JUNCTION / AKINIGANYIN", "27/11/09/021"),
("Ogun", "Ijebu Ode", "Isiwo", "CHRIST CHURCH PRY. SCHOOL - ISIWO", "27/11/10/001"),
("Ogun", "Ijebu Ode", "Isiwo", "AYETEJU MATERNITY", "27/11/10/002"),
("Ogun", "Ijebu Ode", "Isiwo", "ODO/ASOYIN PRY. SCH.", "27/11/10/003"),
("Ogun", "Ijebu Ode", "Isiwo", "OKELISA (OPPOSITE NEW MOSQUE)", "27/11/10/004"),
("Ogun", "Ijebu Ode", "Isiwo", "ODO LOFA", "27/11/10/005"),
("Ogun", "Ijebu Ode", "Isiwo", "ST. PARTICK SCHOOL ISIWO", "27/11/10/006"),
("Ogun", "Ijebu Ode", "Isiwo", "ANSARUDEEN HIGH SCH, ISIWO", "27/11/10/007"),
("Ogun", "Ijebu Ode", "Itamapako", "ST. ALLOYSIOUS SCH. ILOTI", "27/11/11/001"),
("Ogun", "Ijebu Ode", "Itamapako", "ODOSENGOLU", "27/11/11/002"),
("Ogun", "Ijebu Ode", "Itamapako", "ODO-AREWA MARKET", "27/11/11/003"),
("Ogun", "Ijebu Ode", "Itamapako", "OKENLA TOMOBA PRY. SCH.", "27/11/11/004"),
("Ogun", "Ijebu Ode", "Itamapako", "LOCAL GOVERNMENT SCHOOL IDALE", "27/11/11/005"),
("Ogun", "Ijebu Ode", "Itamapako", "ST. JOSEPH ODONOKO", "27/11/11/006"),
("Ogun", "Ijebu Ode", "Itamapako", "ST. JOSEPH SCHOOL ODONOKO", "27/11/11/007"),
("Ogun", "Ijebu Ode", "Itamapako", "OKE-AKO", "27/11/11/008"),
("Ogun", "Ijebu Ode", "Itamapako", "ST. ANNE'S SCHOOL, IRAWO", "27/11/11/009"),
("Ogun", "Ijebu Ode", "Itamapako", "TOMOBA VILLAGE", "27/11/11/010"),

# =========================================================
# IKENNE (10 Wards, 126 PUs)
# =========================================================
("Ogun", "Ikenne", "Ikenne I", "IKENNE TOWN HALL", "27/12/01/001"),
("Ogun", "Ikenne", "Ikenne I", "WESLEY PRY. SCHOOL IKENNE", "27/12/01/002"),
("Ogun", "Ikenne", "Ikenne I", "ETI-OBU QUARTERS EGUNREGE", "27/12/01/003"),
("Ogun", "Ikenne", "Ikenne I", "ABIYI - OLOWO", "27/12/01/004"),
("Ogun", "Ikenne", "Ikenne I", "MOKO STREET", "27/12/01/005"),
("Ogun", "Ikenne", "Ikenne I", "ETI, OBU QUARTERS (AKINDOYIN)", "27/12/01/006"),
("Ogun", "Ikenne", "Ikenne I", "IDOMOLE SQUARE", "27/12/01/007"),
("Ogun", "Ikenne", "Ikenne I", "MORO STREET", "27/12/01/008"),
("Ogun", "Ikenne", "Ikenne I", "OPEN SPACE AT OPATEDO YEYE ODUDUWA STREET", "27/12/01/009"),
("Ogun", "Ikenne", "Ikenne I", "OBAFEMI AWOLOWO PRY. SCHOOL", "27/12/01/010"),
("Ogun", "Ikenne", "Ikenne I", "OPEN SPACE AT AIYEPE JUNCTION, YAWA IKENNE", "27/12/01/011"),
("Ogun", "Ikenne", "Ikenne I", "OPEN SPACE AT MUSLIM MODERN COLLEGE, IKENNE", "27/12/01/012"),
("Ogun", "Ikenne", "Ikenne I", "OPEN SPACE KEHINDE SOFOLA STR, IKENNE", "27/12/01/013"),
("Ogun", "Ikenne", "Ikenne I", "OPEN SPACE UNDER COLANUT TREE, AWOLOWO ROAD, EGUNREGE, IKENNE", "27/12/01/014"),
("Ogun", "Ikenne", "Ikenne I", "OPEN SPACE AT ITUN-KIJA STREET, ADJACENT ITUN+MORO STREET, IKENNE", "27/12/01/015"),
("Ogun", "Ikenne", "Ikenne I", "OPEN SPACE BESIDE THE TRANSFORMER, MORO STREET, IKENNE", "27/12/01/016"),
("Ogun", "Ikenne", "Ikenne I", "OPEN SPACE AT AKINDOYIN JUNCTION, OPPOSITE IKENNE MARKET", "27/12/01/017"),
("Ogun", "Ikenne", "Ikenne I", "OPEN SPACE INFRONT OF ISOLATION CENTRE, IKENNE", "27/12/01/018"),
("Ogun", "Ikenne", "Ikenne I", "OPEN SPACE AT THE JUNCTION OF DOWN TOWN OF OLAJIDE SODIPE/BEST WAY STREET, IKENNE", "27/12/01/019"),
("Ogun", "Ikenne", "Ikenne II", "CUSTOMARY COURT", "27/12/02/001"),
("Ogun", "Ikenne", "Ikenne II", "A.U.D. SCHOOL IKENNE", "27/12/02/002"),
("Ogun", "Ikenne", "Ikenne II", "ETI-OBU QUARTERS", "27/12/02/003"),
("Ogun", "Ikenne", "Ikenne II", "ABUJI-OLOWO", "27/12/02/004"),
("Ogun", "Ikenne", "Ikenne II", "REMO PLANTATION", "27/12/02/005"),
("Ogun", "Ikenne", "Ikenne II", "ETI-OBU QUARTERS MESE", "27/12/02/006"),
("Ogun", "Ikenne", "Ikenne II", "ITUN MOKO II", "27/12/02/007"),
("Ogun", "Ikenne", "Ikenne II", "OPEN SPACE FRONT OF MAYFLOWER SCHOOL, MORE STREET", "27/12/02/008"),
("Ogun", "Ikenne", "Ikenne II", "COMMUNITY HIGH SCHOOL IKENNE", "27/12/02/009"),
("Ogun", "Ikenne", "Ikenne II", "OPEN SPACE AT CHRIST APOSTOLIC CHURCH OKE-IGBALA ROAD", "27/12/02/010"),
("Ogun", "Ikenne", "Ikenne II", "OKE MAGBON JUNCTION IKENNE", "27/12/02/011"),
("Ogun", "Ikenne", "Ikenne II", "ITUN EPE IKENNE", "27/12/02/012"),
("Ogun", "Ikenne", "Ikenne II", "OPEN SPACE AT AWOKOYA MEDULE STREET OFF FAJEBE STREET, IKENNE", "27/12/02/013"),
("Ogun", "Ikenne", "Ikenne II", "INFRONT OF O AND A ACADEMY SCH, IKENNE", "27/12/02/014"),
("Ogun", "Ikenne", "Ikenne II", "OPEN SPACE AT EGAN TOWN JUNCTION ALONG ODOGBOLU/IKENNE ROAD", "27/12/02/015"),
("Ogun", "Ikenne", "Ikenne II", "OPEN SPACE AT AWOLESI JUNCTION", "27/12/02/016"),
("Ogun", "Ikenne", "Ikenne II", "UNITED HIGH SCHOOL, IKENNE", "27/12/02/017"),
("Ogun", "Ikenne", "Iperu I", "AFRICAN-BETHEL PRY. SCHOOL", "27/12/03/001"),
("Ogun", "Ikenne", "Iperu I", "ITA OSANYIN", "27/12/03/002"),
("Ogun", "Ikenne", "Iperu I", "IREGUN STREET", "27/12/03/003"),
("Ogun", "Ikenne", "Iperu I", "ITA OLOKU", "27/12/03/004"),
("Ogun", "Ikenne", "Iperu I", "AYEGBAMI STREET", "27/12/03/005"),
("Ogun", "Ikenne", "Iperu I", "IMOSAN STREET", "27/12/03/006"),
("Ogun", "Ikenne", "Iperu I", "OPEN SPACE AT ITA-AGAN STREET, IPERU", "27/12/03/007"),
("Ogun", "Ikenne", "Iperu I", "OPEN SPACE AT OLURE STREET, IPERU", "27/12/03/008"),
("Ogun", "Ikenne", "Iperu I", "OPEN SPACE AT JUNTION OF ORIGBEMIDELE/ARAROMI STREET, IPERU", "27/12/03/009"),
("Ogun", "Ikenne", "Iperu II", "ITA-TISA", "27/12/04/001"),
("Ogun", "Ikenne", "Iperu II", "SALVATION ARMY SCHOOL IPERU", "27/12/04/002"),
("Ogun", "Ikenne", "Iperu II", "JALUGBA SQUARE", "27/12/04/003"),
("Ogun", "Ikenne", "Iperu II", "IBU ROAD", "27/12/04/004"),
("Ogun", "Ikenne", "Iperu II", "KANGA STREET", "27/12/04/005"),
("Ogun", "Ikenne", "Iperu II", "AKESAN MARKET", "27/12/04/006"),
("Ogun", "Ikenne", "Iperu II", "AJAGBE HIGH SCHOOL", "27/12/04/007"),
("Ogun", "Ikenne", "Iperu II", "OPEN SPACE AT ITA-AGBON STREET", "27/12/04/008"),
("Ogun", "Ikenne", "Iperu II", "OPEN SPACE OPP POLICE COLLEGE, IPERU", "27/12/04/009"),
("Ogun", "Ikenne", "Iperu II", "OPEN SPACE AT BACK OF AKESAN MARKET, IPERU", "27/12/04/010"),
("Ogun", "Ikenne", "Iperu II", "OPEN SPACE AT MASEJURA JUNCTION JALUGBA, IPERU", "27/12/04/011"),
("Ogun", "Ikenne", "Iperu II", "OPEN SPACE AT THE JUNCTION OF OBA OGUNFOWORA/ODORU ROAD, IPERU", "27/12/04/012"),
("Ogun", "Ikenne", "Iperu III", "ST. JOHN'S CATH. PRY. SCH.", "27/12/05/001"),
("Ogun", "Ikenne", "Iperu III", "ARAROMI/MOSALASI SOKOTO", "27/12/05/002"),
("Ogun", "Ikenne", "Iperu III", "OPEN SPACE ALONG OLD IBADAN ROAD", "27/12/05/003"),
("Ogun", "Ikenne", "Iperu III", "WESLEY PRY. SCHOOL", "27/12/05/004"),
("Ogun", "Ikenne", "Iperu III", "ST. JAMES SCHOOL", "27/12/05/005"),
("Ogun", "Ikenne", "Iperu III", "A.U.D. SCHOOL", "27/12/05/006"),
("Ogun", "Ikenne", "Iperu III", "ABULE EGBA IMAJE", "27/12/05/007"),
("Ogun", "Ikenne", "Iperu III", "OPP. POLICE COLLEGE, OGERE ROAD", "27/12/05/008"),
("Ogun", "Ikenne", "Iperu III", "CHRIST APOSTOLIC COLLEGE", "27/12/05/009"),
("Ogun", "Ikenne", "Iperu III", "IDENA QUARTERS", "27/12/05/010"),
("Ogun", "Ikenne", "Iperu III", "THE SCHOOL FIELD, WESLEY PRY SCH, IPERU", "27/12/05/011"),
("Ogun", "Ikenne", "Iperu III", "OPEN SPACE AT IDARIKA SQUARE, IPERU", "27/12/05/012"),
("Ogun", "Ikenne", "Iperu III", "OPEN SPACE AT IMOSIMI STREET, IPERU", "27/12/05/013"),
("Ogun", "Ikenne", "Iperu III", "OPEN SPACE AT ERELU OLAYIWOLA STR IPERU", "27/12/05/014"),
("Ogun", "Ikenne", "Iperu III", "OPEN SPACE AT TIWA NEW TOWN ALONG LAGOS IBADAN EXPRESS WAY", "27/12/05/015"),
("Ogun", "Ikenne", "Iperu III", "OPEN SPACE AT AGBELE STREET, IPERU", "27/12/05/016"),
("Ogun", "Ikenne", "Iperu III", "AKESAN COMMUNITY GRAMMAR SCH", "27/12/05/017"),
("Ogun", "Ikenne", "Iperu III", "OPEN SPACE AT JUNCTION OF CHALLENGE STREET, AGBALA PHASEV II, IPERU", "27/12/05/018"),
("Ogun", "Ikenne", "Ogere I", "CATH. PRY. SCHOOL", "27/12/06/001"),
("Ogun", "Ikenne", "Ogere I", "ITA JIREN STREET JUNCTION", "27/12/06/002"),
("Ogun", "Ikenne", "Ogere I", "IDOMOGUN SQUARE", "27/12/06/003"),
("Ogun", "Ikenne", "Ogere I", "ITUNLA STREET", "27/12/06/004"),
("Ogun", "Ikenne", "Ogere I", "OBADORE SQUARE", "27/12/06/005"),
("Ogun", "Ikenne", "Ogere I", "OKE-OJA", "27/12/06/006"),
("Ogun", "Ikenne", "Ogere I", "OPEN SPACE AT ODUGESAN/AKURO ESTATE ROAD, OGERE", "27/12/06/007"),
("Ogun", "Ikenne", "Ogere I", "OPEN SPACE AT ITUN-IRAGBON/ANG STREET, OGERE", "27/12/06/008"),
("Ogun", "Ikenne", "Ogere II", "OPEN SPACE AT AJEGUNLE STREET", "27/12/07/001"),
("Ogun", "Ikenne", "Ogere II", "WESLEY SCHOOL", "27/12/07/002"),
("Ogun", "Ikenne", "Ogere II", "TOWN HALL", "27/12/07/003"),
("Ogun", "Ikenne", "Ogere II", "OPEN SPACE AT LISA TABORAH, STREET", "27/12/07/004"),
("Ogun", "Ikenne", "Ogere II", "COURT HALL", "27/12/07/005"),
("Ogun", "Ikenne", "Ogere II", "IDAREN SQUARE", "27/12/07/006"),
("Ogun", "Ikenne", "Ogere II", "ODE ROAD", "27/12/07/007"),
("Ogun", "Ikenne", "Ogere II", "OPEN SPACE AT SEGUN ADENIYI STREET OFF TABORAH ROAD, OGERE", "27/12/07/008"),
("Ogun", "Ikenne", "Ogere II", "OPEN SPACE ARAROMI PHASE II OGERE", "27/12/07/009"),
("Ogun", "Ikenne", "Ogere II", "OPEN SPACE ODUESO STREET, OGERE", "27/12/07/010"),
("Ogun", "Ikenne", "Ogere II", "OPEN SPACE AT JUNCTION OSILARU STREET, OGERE", "27/12/07/011"),
("Ogun", "Ikenne", "Ilisan I", "TOWN HALL", "27/12/08/001"),
("Ogun", "Ikenne", "Ilisan I", "A.U.D. SCHOOL ILISAN", "27/12/08/002"),
("Ogun", "Ikenne", "Ilisan I", "OPPOSITE POST OFFICE", "27/12/08/003"),
("Ogun", "Ikenne", "Ilisan I", "ISANBI HIGH SCHOOL", "27/12/08/004"),
("Ogun", "Ikenne", "Ilisan I", "TOWN PLANNING", "27/12/08/005"),
("Ogun", "Ikenne", "Ilisan I", "AFRICAN BETHEL SCHOOL", "27/12/08/006"),
("Ogun", "Ikenne", "Ilisan I", "OPEN SPACE AT (OLOFIN) A.U.D.", "27/12/08/007"),
("Ogun", "Ikenne", "Ilisan I", "OPEN SPACE AT IMOSAN JUNCTION BY KAJOLA STREET, ILISAN", "27/12/08/008"),
("Ogun", "Ikenne", "Ilisan I", "OPEN SPACE AT AJEGUNLE JUNCTION", "27/12/08/009"),
("Ogun", "Ikenne", "Ilisan I", "OPEN SPACE AT ONGBAJE SONOWO STR, ILISAN", "27/12/08/010"),
("Ogun", "Ikenne", "Ilisan I", "ILISAN HIGH SCHOOL, ILISAN", "27/12/08/011"),
("Ogun", "Ikenne", "Ilisan I", "OPEN SPACE AT OPC ROAD, ILISAN", "27/12/08/012"),
("Ogun", "Ikenne", "Ilisan I", "OPPOSIE ILISAN TOWN HALL UNDER THE TREE, ALONG OLOFIN ROAD, ILISAN", "27/12/08/013"),
("Ogun", "Ikenne", "Ilisan I", "OPEN SPACE AT IFELODUN STREET, ILISAN", "27/12/08/014"),
("Ogun", "Ikenne", "Ilisan I", "OPEN SPACE AT THE JUNCTION OF AWOLARU MUKAILA STREET OFF ISANBI HIGH SCH, ILISAN", "27/12/08/015"),
("Ogun", "Ikenne", "Ilisan II", "CUSTOMARY COURT", "27/12/09/001"),
("Ogun", "Ikenne", "Ilisan II", "WESLEY PRY. SCHOOL", "27/12/09/002"),
("Ogun", "Ikenne", "Ilisan II", "OPEN SPACE AT ITUNLEMO QUARTERS", "27/12/09/003"),
("Ogun", "Ikenne", "Ilisan II", "IWAYE COMPOUND", "27/12/09/004"),
("Ogun", "Ikenne", "Ilisan II", "AGO ILARA STREET", "27/12/09/005"),
("Ogun", "Ikenne", "Ilisan II", "OPEN SPACE AT ADEMO ABARA, STREET", "27/12/09/006"),
("Ogun", "Ikenne", "Ilisan II", "ASWA - TEXGARD ROAD", "27/12/09/007"),
("Ogun", "Ikenne", "Ilisan II", "OPP. BAB COCK GATE", "27/12/09/008"),
("Ogun", "Ikenne", "Ilisan II", "OPEN SPACE AT BACK OF BABCOCK TEACHING HOSPITAL, ILISAN", "27/12/09/009"),
("Ogun", "Ikenne", "Ilisan II", "OPEN SPACE ITUN ALASE, ILISAN", "27/12/09/010"),
("Ogun", "Ikenne", "Ilisan II", "OPEN SPACE AT OREFAGBABI STREET OFF ILISAN-IROLU ROAD, ILISAN", "27/12/09/011"),
("Ogun", "Ikenne", "Ilisan/Irolu", "A.U.D. PRY. SCHOOL IROLU", "27/12/10/001"),
("Ogun", "Ikenne", "Ilisan/Irolu", "WESLEY PRY. SCH. - IROLU", "27/12/10/002"),
("Ogun", "Ikenne", "Ilisan/Irolu", "ANGLICAN SCH. IROLU", "27/12/10/003"),
("Ogun", "Ikenne", "Ilisan/Irolu", "TOWN HALL", "27/12/10/004"),
("Ogun", "Ikenne", "Ilisan/Irolu", "ILISAN-IROLU ROAD", "27/12/10/005"),
("Ogun", "Ikenne", "Ilisan/Irolu", "OPEN SPACE AT JUNCTION OF ODEMO/ODULEYE STREET, IROLU", "27/12/10/006"),

# =========================================================
# ODOGBOLU (15 Wards, 178 PUs)
# =========================================================
("Ogun", "Odogbolu", "Imosan", "ST.PETERS PRIMARY SCHOOL, IMOSAN", "27/17/01/001"),
("Ogun", "Odogbolu", "Imosan", "ST. PETER SCHOOL IMOSAN", "27/17/01/002"),
("Ogun", "Odogbolu", "Imosan", "AJEREGUN ROAD, FRONT EBA TUTU HOUSE, IPERIN", "27/17/01/003"),
("Ogun", "Odogbolu", "Imosan", "ODOYANTA", "27/17/01/004"),
("Ogun", "Odogbolu", "Imosan", "IFESOWAPO COMPREHENSIVE HIGH SCHOOL, IMOSAN", "27/17/01/005"),
("Ogun", "Odogbolu", "Imosan", "ODOGBOLU L.G ORPHANAGE SCHOOL, IMOSAN", "27/17/01/006"),
("Ogun", "Odogbolu", "Imosan", "OPEN SPACE ODOLEWU SQUARE, BEHIND TAMCO, IMOSAN", "27/17/01/007"),
("Ogun", "Odogbolu", "Imosan", "COMMUNITY PRIMARY SCHOOL, IPERIN", "27/17/01/008"),
("Ogun", "Odogbolu", "Imosan", "OPEN SPACE PARAMOUNT ESTATE, ODOYANTA", "27/17/01/009"),
("Ogun", "Odogbolu", "Imodi", "RECRETATION CENTER, IMODI", "27/17/02/001"),
("Ogun", "Odogbolu", "Imodi", "ST.MATTEW PRY.SCHOOL, IMODI", "27/17/02/002"),
("Ogun", "Odogbolu", "Imodi", "OPP.IKANGBA CHURCH, IKANGBA", "27/17/02/003"),
("Ogun", "Odogbolu", "Imodi", "CHRIST ANG PRY.SCH.AGORO", "27/17/02/004"),
("Ogun", "Odogbolu", "Imodi", "OPP.ST.JOHN CHURCH,ERINLU", "27/17/02/005"),
("Ogun", "Odogbolu", "Imodi", "MARKET SQUARE,IMODI", "27/17/02/006"),
("Ogun", "Odogbolu", "Imodi", "MOSLEM PRY.SCH.IMODI", "27/17/02/007"),
("Ogun", "Odogbolu", "Imodi", "BLACK AND WHITE HOTEL, HOUSING ESTATE, IKANGBA", "27/17/02/008"),
("Ogun", "Odogbolu", "Imodi", "RECRETATION CENTER II, IMODI", "27/17/02/009"),
("Ogun", "Odogbolu", "Imodi", "OPP.IKANGBA CHURCH II, IKANGBA", "27/17/02/010"),
("Ogun", "Odogbolu", "Imodi", "OPP.ST.JOHN CHURCH II, ERINLU", "27/17/02/011"),
("Ogun", "Odogbolu", "Imodi", "OPEN SPACE ROYAL ESTATE IMODI", "27/17/02/012"),
("Ogun", "Odogbolu", "Imodi", "IKANGBA COMPREHENSIVE HIGH SCHOOL, IKANGBA", "27/17/02/013"),
("Ogun", "Odogbolu", "Imodi", "HEALTH POST AGORO", "27/17/02/014"),
("Ogun", "Odogbolu", "Imodi", "OPEN SPACE, HOUSIN ESTATE JUNCTION, IDOTUN", "27/17/02/015"),
("Ogun", "Odogbolu", "Imodi", "OPEN SPACE AYEGBAMI SQUARE, IMODI", "27/17/02/016"),
("Ogun", "Odogbolu", "Imodi", "OPEN SPACE IDI IROKO COMMUNITY ROAD & IKANGBA ESTATE, IKANGBA", "27/17/02/017"),
("Ogun", "Odogbolu", "Imodi", "OPEN SPACE AJAGBANLA UNITY ESTATE ERINLU", "27/17/02/018"),
("Ogun", "Odogbolu", "Okun-Owa", "ST PHILIP'S PRY SCH, OKUN OWA", "27/17/03/001"),
("Ogun", "Odogbolu", "Okun-Owa", "MOSLEM PRY. SCHOOL, OKUN OWA", "27/17/03/002"),
("Ogun", "Odogbolu", "Okun-Owa", "OKUN OWA TOWN HALL, OKUN OWA", "27/17/03/003"),
("Ogun", "Odogbolu", "Okun-Owa", "ST. JUDES PRY. SCHOOL, IJESHA IJEBU", "27/17/03/004"),
("Ogun", "Odogbolu", "Okun-Owa", "ST. PETER'S SCHOOL, ARAROMI AKE", "27/17/03/005"),
("Ogun", "Odogbolu", "Okun-Owa", "VIEWING CENTRE IJESHA, IJEBU", "27/17/03/006"),
("Ogun", "Odogbolu", "Okun-Owa", "ST. BANA BAS OKUN OWA", "27/17/03/007"),
("Ogun", "Odogbolu", "Okun-Owa", "BOOTH OPP OTUNBA OLUKOYA'S COMP.", "27/17/03/008"),
("Ogun", "Odogbolu", "Okun-Owa", "COMP. HIGH SCH OKUN OWA (GATE)", "27/17/03/009"),
("Ogun", "Odogbolu", "Okun-Owa", "OPEN SPACE IDI AGBON JUNCTION, OKUN OWA", "27/17/03/010"),
("Ogun", "Odogbolu", "Okun-Owa", "PRY HEALTH CENTRE, ODOLOWU", "27/17/03/011"),
("Ogun", "Odogbolu", "Odogbolu I", "ODO MARKET, ODOGBOLU", "27/17/04/001"),
("Ogun", "Odogbolu", "Odogbolu I", "ITUN ORIWU, ODOGBOLU", "27/17/04/002"),
("Ogun", "Odogbolu", "Odogbolu I", "IKOSA ROAD, FRONTAGE ADEYEMI HOUSE, ODOGBOLU", "27/17/04/003"),
("Ogun", "Odogbolu", "Odogbolu I", "ITUN AGBON STREET, ODOGBOLU", "27/17/04/004"),
("Ogun", "Odogbolu", "Odogbolu I", "IGBEPA/OPPOSITE, ST. PAUL CHURCH, ODOGBOLU", "27/17/04/005"),
("Ogun", "Odogbolu", "Odogbolu I", "ODI TAMI, ODOGBOLU", "27/17/04/006"),
("Ogun", "Odogbolu", "Odogbolu I", "SABO MARKET, ODOGBOLU", "27/17/04/007"),
("Ogun", "Odogbolu", "Odogbolu I", "ODO ALORO QUARTERS, ODOGBOLU", "27/17/04/008"),
("Ogun", "Odogbolu", "Odogbolu I", "ST. MARY PRY. SCH. OGOJI", "27/17/04/009"),
("Ogun", "Odogbolu", "Odogbolu I", "MOSLEM PRIMARY SCHOOL, ODOGBOLU", "27/17/04/010"),
("Ogun", "Odogbolu", "Odogbolu I", "IGBODILE SQUARE, ODOGBOLU", "27/17/04/011"),
("Ogun", "Odogbolu", "Odogbolu I", "ITUNWADE SQUARE, IKOSA, ODOGBOLU", "27/17/04/012"),
("Ogun", "Odogbolu", "Odogbolu II", "ITUN OKE QUARTERS, ODOGBOLU", "27/17/05/001"),
("Ogun", "Odogbolu", "Odogbolu II", "FEDERAL GOVT. COLLEGE, ODOGBOLU", "27/17/05/002"),
("Ogun", "Odogbolu", "Odogbolu II", "ITUN ISOKU (BESIDE OLORUNFUNMI HOUSE), ODOGBOLU", "27/17/05/003"),
("Ogun", "Odogbolu", "Odogbolu II", "UBU QUARTETRS, ODOGBOLU", "27/17/05/004"),
("Ogun", "Odogbolu", "Odogbolu II", "ODOGBON QUARTERS, ODOGBOLU", "27/17/05/005"),
("Ogun", "Odogbolu", "Odogbolu II", "ILODA QUARTERS, ODOGBOLU", "27/17/05/006"),
("Ogun", "Odogbolu", "Odogbolu II", "EFIYAN, (FRONTAGE 1ST CHOICE PHOTO), ODOGBOLU", "27/17/05/007"),
("Ogun", "Odogbolu", "Odogbolu II", "IDENA QUARTERS, ODOGBOLU", "27/17/05/008"),
("Ogun", "Odogbolu", "Odogbolu II", "LOCAL GOVERNMENT MODEL PRIMARY SCHOOL, ODOGBOLU", "27/17/05/009"),
("Ogun", "Odogbolu", "Odogbolu II", "OPEN SPACE ERI ODO SQUARE, ODOGBOLU", "27/17/05/010"),
("Ogun", "Odogbolu", "Odogbolu II", "OPEN SPACE ODOYANGBAN QTRS, ODOGBOLU", "27/17/05/011"),
("Ogun", "Odogbolu", "Odogbolu II", "OPEN SPACE EFIYAN, ODOGBOLU", "27/17/05/012"),
("Ogun", "Odogbolu", "Aiyepe", "OPPOSITE ABA CENTRAL, MOSQUE AIYEPE", "27/17/06/001"),
("Ogun", "Odogbolu", "Aiyepe", "IDOBIRI MARKET AIYEPE", "27/17/06/002"),
("Ogun", "Odogbolu", "Aiyepe", "HOLY TRINITY PRY SCH. AIYEPE", "27/17/06/003"),
("Ogun", "Odogbolu", "Aiyepe", "OPPOSITE MARKET ODOLOWU, MOSQUE AIYEPE", "27/17/06/004"),
("Ogun", "Odogbolu", "Aiyepe", "OPPOSITE ILAKAN MOSQUE, AIYEPE", "27/17/06/005"),
("Ogun", "Odogbolu", "Aiyepe", "ST. PAUL SCHOOL, EYINWA", "27/17/06/006"),
("Ogun", "Odogbolu", "Aiyepe", "MARKET SQUARE, ABA AIYEPE", "27/17/06/007"),
("Ogun", "Odogbolu", "Aiyepe", "FRONTAGE BADA HOUSE AGBOWA ROAD, AIYEPE", "27/17/06/008"),
("Ogun", "Odogbolu", "Aiyepe", "OPEN SPACE, ODO AYELUJA, ABA, AIYEPE", "27/17/06/009"),
("Ogun", "Odogbolu", "Aiyepe", "AIYEPE COMMUNITY GRAMMAR SCHOOL, AIYEPE", "27/17/06/010"),
("Ogun", "Odogbolu", "Aiyepe", "OPEN SPACE T-JUNCTION OLD SAGAMU / AGBOWA ROAD, AIYEPE", "27/17/06/011"),
("Ogun", "Odogbolu", "Aiyepe", "OPEN SPACE BACK OF SAWMILL, AIYEPE", "27/17/06/012"),
("Ogun", "Odogbolu", "Aiyepe", "AIYEPE COMPREHENSIVE HIGH SCHOOL, AIYEPE", "27/17/06/013"),
("Ogun", "Odogbolu", "Aiyepe", "OPEN SPACE BARUMI JUNCTION OLOWOPOROKU STREET, ABA, AIYEPE", "27/17/06/014"),
("Ogun", "Odogbolu", "Ososa", "OBALUFON IDOMOWO SQUARE, OSOSA", "27/17/07/001"),
("Ogun", "Odogbolu", "Ososa", "CATHOLIC SCH. OSOSA", "27/17/07/002"),
("Ogun", "Odogbolu", "Ososa", "OSOSA TOWN HALL, OSOSA", "27/17/07/003"),
("Ogun", "Odogbolu", "Ososa", "OSOSA MARKET/DISPENSARY, OSOSA", "27/17/07/004"),
("Ogun", "Odogbolu", "Ososa", "OPPOSITE IJOKU MOSQUE, OSOSA", "27/17/07/005"),
("Ogun", "Odogbolu", "Ososa", "ST. JOHN SCHOOL, OSOSA", "27/17/07/006"),
("Ogun", "Odogbolu", "Ososa", "SABO MARKET, OSOSA", "27/17/07/007"),
("Ogun", "Odogbolu", "Ososa", "OBU OBASA SQUARE OSOSA", "27/17/07/008"),
("Ogun", "Odogbolu", "Ososa", "MOSLEM PRIMARY SCHOOL, OSOSA", "27/17/07/009"),
("Ogun", "Odogbolu", "Ososa", "OPEN SPACE OKE ESIN SQUARE, OSOSA", "27/17/07/010"),
("Ogun", "Odogbolu", "Ososa", "OSALAKOYE SQUARE, OSOSA", "27/17/07/011"),
("Ogun", "Odogbolu", "Ososa", "POLICE STATION, OSOSA", "27/17/07/012"),
("Ogun", "Odogbolu", "Ososa", "OPEN SPACE ODOOWA SQUARE, OSOSA", "27/17/07/013"),
("Ogun", "Odogbolu", "Ososa", "OPEN SPACE OREMEJI CLOSE, OSOSA", "27/17/07/014"),
("Ogun", "Odogbolu", "Idowa", "TOWN HALL (IDOWA FRONT), IDOWA", "27/17/08/001"),
("Ogun", "Odogbolu", "Idowa", "ILOYE MATERNITY, IDOWA", "27/17/08/002"),
("Ogun", "Odogbolu", "Idowa", "TOWN HALL, IDOWA (BACK), IDOWA", "27/17/08/003"),
("Ogun", "Odogbolu", "Idowa", "OPP. CHIEF OLU ADEBANJO'S HOUSE (BOOTH), IDOWA", "27/17/08/004"),
("Ogun", "Odogbolu", "Idowa", "OPEN SPACE ADEBAYO MARKET", "27/17/08/005"),
("Ogun", "Odogbolu", "Idowa", "COMPREHENSIVE HIGH SCH. IDOWA", "27/17/08/006"),
("Ogun", "Odogbolu", "Idowa", "GENERAL HOSPITAL, IDOWA", "27/17/08/007"),
("Ogun", "Odogbolu", "Idowa", "OPEN SPACE POLICE BARRACK ILOYE, IDOWA", "27/17/08/008"),
("Ogun", "Odogbolu", "Ibefun", "ARAROMI IBEFUN WATER WORKS, IBEFUN", "27/17/09/001"),
("Ogun", "Odogbolu", "Ibefun", "OWODE QUARTERS, (FRONTAGE) OSIPITAN'S HOUSE) IBEFUN", "27/17/09/002"),
("Ogun", "Odogbolu", "Ibefun", "CATHOLIC PRY. SCH. IBEFUN", "27/17/09/003"),
("Ogun", "Odogbolu", "Ibefun", "OKETUN IBEFUN", "27/17/09/004"),
("Ogun", "Odogbolu", "Ibefun", "FRONTAGE OF MATERNITY CENTRE, (ISALE IBEFUN)", "27/17/09/005"),
("Ogun", "Odogbolu", "Ibefun", "MARKET SQUARE IBEFUN", "27/17/09/006"),
("Ogun", "Odogbolu", "Ibefun", "ANSAR-UD-DEEN PRY. SCH. IBEFUN", "27/17/09/007"),
("Ogun", "Odogbolu", "Ibefun", "POLICE POST ORETA", "27/17/09/008"),
("Ogun", "Odogbolu", "Ibefun", "MORNING MARKET SQUARE, ISALE IBEFUN", "27/17/09/009"),
("Ogun", "Odogbolu", "Ilado", "INFORNT OF ILADO SOCIAL CLUB SIBADEWA ILADO", "27/17/10/001"),
("Ogun", "Odogbolu", "Ilado", "ST. LUKE PRY. SCHOOL IMODI, IJASI", "27/17/10/002"),
("Ogun", "Odogbolu", "Ilado", "ODONSELU MARKET, ODONSELU", "27/17/10/003"),
("Ogun", "Odogbolu", "Ilado", "ABA TIWA/ABA SOOBO", "27/17/10/004"),
("Ogun", "Odogbolu", "Ilado", "AKIO", "27/17/10/005"),
("Ogun", "Odogbolu", "Ilado", "ST JOHN ANGLICAN PRY SCH", "27/17/10/006"),
("Ogun", "Odogbolu", "Ilado", "TOWN HALL IMODI-IJASI", "27/17/10/007"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "IMORU, OPPOSITE IMORU CHURCH", "27/17/11/001"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "MOBALUFON TOWN HALL", "27/17/11/002"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "ADEFISAN", "27/17/11/003"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "ATIBA, ST. JAMES PRY. SCH. ATIBA", "27/17/11/004"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "TOWN HALL, EGBE", "27/17/11/005"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "UNITED PRY. SCH. OKE OWA", "27/17/11/006"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "OPPOSITE ODO EPO CHURCH", "27/17/11/007"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "IMAGBON STATION", "27/17/11/008"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "FEDERAL HOUSING ESTATE IKOTO", "27/17/11/009"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "INFRONT OF BALE HOUSE, LATOGUN", "27/17/11/010"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "INFRONT OF OLU OF OREGU'S HOUSE ARAROMI OREGUN", "27/17/11/011"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "MARKET SQUARE, IMAKA", "27/17/11/012"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "OPPOSITE CHURCH, EMUREN", "27/17/11/013"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "LUMODAN IMAGBON", "27/17/11/014"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "O'DUA COMP. HIG SCHOOL, IMORU", "27/17/11/015"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "OPEN SPACE ISOPE SQUARE MOBALUFON", "27/17/11/016"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "OPEN SPACE MOBALUFON WEST MORAIKA", "27/17/11/017"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "ADEFISAN MARKET", "27/17/11/018"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "MOSLEM PRY SCH. ITANRIN", "27/17/11/019"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "ATIBA TOWN HALL SQUARE", "27/17/11/020"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "OPEN SPACE POWER LINE, ATIBA", "27/17/11/021"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "OPEN SPACE IBAGBA SQUARE, EGBE", "27/17/11/022"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "OPEN SPACE EYINFUN SQUARE, EGBE", "27/17/11/023"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "HOLY TRINITY HEALTH CENTRE, IKOTO", "27/17/11/024"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "OPEN SPACE OGUNLADE ESTATE JUNCTION, OKE OWA", "27/17/11/025"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "ST JOSEPH CATHOLIC PRY SCH. F.H. ESTATE, IKOTO", "27/17/11/026"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "ST JAMES PRY. SCHOOL, LATOGUN", "27/17/11/027"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo I", "OPEN SPACE T-JUNCTION OGUNYEMI STREET, OREGUN", "27/17/11/028"),
("Ogun", "Odogbolu", "Ala/Igbile", "OPPOSITE ALUKO MOSQUE, AKA", "27/17/12/001"),
("Ogun", "Odogbolu", "Ala/Igbile", "TOWN HALL ALA, FRONT", "27/17/12/002"),
("Ogun", "Odogbolu", "Ala/Igbile", "FRONTAGE MATERNITY, ILOFA/IWAYE IGBILE", "27/17/12/003"),
("Ogun", "Odogbolu", "Ala/Igbile", "SIFOLU/OWODE IGBILE", "27/17/12/004"),
("Ogun", "Odogbolu", "Ala/Igbile", "INFRONT OF OLORILU'S HOUSE OKE-ORUNDUN", "27/17/12/005"),
("Ogun", "Odogbolu", "Ala/Igbile", "ARAROMI SQUARE ALA", "27/17/12/006"),
("Ogun", "Odogbolu", "Ala/Igbile", "TOWN HALL, ALL BACK", "27/17/12/007"),
("Ogun", "Odogbolu", "Jobore/Ibido/Ikise", "ST. MICHAEL PRY. SCHOOL, JOBORE", "27/17/13/001"),
("Ogun", "Odogbolu", "Jobore/Ibido/Ikise", "OLORUNSOGO TOWN HALL, IBIDO", "27/17/13/002"),
("Ogun", "Odogbolu", "Jobore/Ibido/Ikise", "FRONTAGE JAMES HOUSE, IKISE", "27/17/13/003"),
("Ogun", "Odogbolu", "Jobore/Ibido/Ikise", "TOWN HALL, JOBORE", "27/17/13/004"),
("Ogun", "Odogbolu", "Omu", "Z.I. PRY. SCHOOL OKE, OYINBO OMU", "27/17/14/001"),
("Ogun", "Odogbolu", "Omu", "U.N.A. PRY. SCHOOL, OMU", "27/17/14/002"),
("Ogun", "Odogbolu", "Omu", "SAINT PAUL SCHOOL, OMU", "27/17/14/003"),
("Ogun", "Odogbolu", "Omu", "OPPOSITE MOTA MOSQUE, OMU", "27/17/14/004"),
("Ogun", "Odogbolu", "Omu", "FRONTAGE OLISA HOUSE, OMU", "27/17/14/005"),
("Ogun", "Odogbolu", "Omu", "OPPOSITE IRETE MOSQUE", "27/17/14/006"),
("Ogun", "Odogbolu", "Omu", "BESIDE ITA ALE MARKET, OMU", "27/17/14/007"),
("Ogun", "Odogbolu", "Omu", "FRONTAGE OGUNLANA HOUSE, DEGORUNSE", "27/17/14/008"),
("Ogun", "Odogbolu", "Omu", "IGBODILE/AYEGBAMI, OMU", "27/17/14/009"),
("Ogun", "Odogbolu", "Omu", "FRONTAGE ONANIYI'S HOUSE, OMU", "27/17/14/010"),
("Ogun", "Odogbolu", "Omu", "Z.I PRIMARY SCHOOL, OMU", "27/17/14/011"),
("Ogun", "Odogbolu", "Omu", "IFESOWAPO DAILY RETAIL MARKET", "27/17/14/012"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo II", "IMAWEJE TOWN HALL", "27/17/15/001"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo II", "OPPOSITE CHURCH, IDAGBO", "27/17/15/002"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo II", "OPPOSITE IBIDO, OGBO CHURCH", "27/17/15/003"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo II", "TASCE IJAGUN BUS-STOP", "27/17/15/004"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo II", "ISANYA OGBO MATERNITY", "27/17/15/005"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo II", "MARKET SQUARE OKELAMUREN", "27/17/15/006"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo II", "ABAPAWA", "27/17/15/007"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo II", "ARAROMI UNITED PRY. SCHOOL, IMAWEJE", "27/17/15/008"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo II", "OPEN SPACE OPP. TRANSFORMER, IMAWEJE", "27/17/15/009"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo II", "TOWN HALL, IJELE", "27/17/15/010"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo II", "TOWN HALL, ILUPEJU", "27/17/15/011"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo II", "OPEN SPACE ODO AGAMEGI", "27/17/15/012"),
("Ogun", "Odogbolu", "Ogbo/Moraika/Ita-Epo II", "TOWN HALL IKOFA", "27/17/15/013"),

# =========================================================
# OGUN WATERSIDE (10 Wards, 126 PUs)
# =========================================================
("Ogun", "Ogun Waterside", "Iwopin", "L.G. SCHOOL, IWOPIN", "27/18/01/001"),
("Ogun", "Ogun Waterside", "Iwopin", "ST. MARY'S PRY. SCHOOL, OLOJU META", "27/18/01/002"),
("Ogun", "Ogun Waterside", "Iwopin", "FISHERIES OFFICE, EHINDI", "27/18/01/003"),
("Ogun", "Ogun Waterside", "Iwopin", "L.G. SCHOOL, IMOSIRI", "27/18/01/004"),
("Ogun", "Ogun Waterside", "Iwopin", "EBUTE ILAMO SQUARE", "27/18/01/005"),
("Ogun", "Ogun Waterside", "Iwopin", "I.P.R.C. PRY. SCHOOL, IWOPIN", "27/18/01/006"),
("Ogun", "Ogun Waterside", "Iwopin", "L.G. SCHOOL, IMEKI", "27/18/01/007"),
("Ogun", "Ogun Waterside", "Iwopin", "TOWN HALL, IWOPIN", "27/18/01/008"),
("Ogun", "Ogun Waterside", "Iwopin", "ST PETER'S ANGLICAN PRY SCHOOL, IWOPIN", "27/18/01/009"),
("Ogun", "Ogun Waterside", "Iwopin", "OPEN SPACE AT KOREDE MARKET, IWOPIN", "27/18/01/010"),
("Ogun", "Ogun Waterside", "Iwopin", "COMMUNITY PRIMARY SCHOOL AIYEGBAMI", "27/18/01/011"),
("Ogun", "Ogun Waterside", "Iwopin", "ST. KIZITO HIGH SCHOOL, IWOPIN", "27/18/01/012"),
("Ogun", "Ogun Waterside", "Iwopin", "OLD L.G DISPENSARY HEALTH CENTRE", "27/18/01/013"),
("Ogun", "Ogun Waterside", "Oni", "L.G SCH, ONI I", "27/18/02/001"),
("Ogun", "Ogun Waterside", "Oni", "L.G SCH. ONI II", "27/18/02/002"),
("Ogun", "Ogun Waterside", "Oni", "ST PETER'S PRY SCH, OLOGBUN", "27/18/02/003"),
("Ogun", "Ogun Waterside", "Oni", "L.G SCH, AKILA", "27/18/02/004"),
("Ogun", "Ogun Waterside", "Oni", "ORITA OMO SQUARE", "27/18/02/005"),
("Ogun", "Ogun Waterside", "Oni", "L.G SCH, ALO", "27/18/02/006"),
("Ogun", "Ogun Waterside", "Oni", "ST PETERS PRY SCH, ORIYANRIN", "27/18/02/007"),
("Ogun", "Ogun Waterside", "Oni", "DEMOLU QUARTERS, ONI", "27/18/02/008"),
("Ogun", "Ogun Waterside", "Oni", "MATERNITY CENTRE, ONI", "27/18/02/009"),
("Ogun", "Ogun Waterside", "Oni", "OPEN SPACE OPP, BALOGUN BELLO'S HOUSE", "27/18/02/010"),
("Ogun", "Ogun Waterside", "Oni", "OPEN SPACE OPP. AWONUGA'S HOUSE", "27/18/02/011"),
("Ogun", "Ogun Waterside", "Oni", "L.G SCHOOL MALOFE, ONI", "27/18/02/012"),
("Ogun", "Ogun Waterside", "Ibiade", "TEBUWO SQUARE", "27/18/03/001"),
("Ogun", "Ogun Waterside", "Ibiade", "ST. MICH. PRY SCHOOL, IBIADE", "27/18/03/002"),
("Ogun", "Ogun Waterside", "Ibiade", "TOSO SQUARE", "27/18/03/003"),
("Ogun", "Ogun Waterside", "Ibiade", "TOGBUNRI SQUARE", "27/18/03/004"),
("Ogun", "Ogun Waterside", "Ibiade", "TAYOKU SQUARE", "27/18/03/005"),
("Ogun", "Ogun Waterside", "Ibiade", "TIPETU SQUARE", "27/18/03/006"),
("Ogun", "Ogun Waterside", "Ibiade", "L.G. SCHOOL, IBIADE I", "27/18/03/007"),
("Ogun", "Ogun Waterside", "Ibiade", "L.G. SCHOOL, IBIADE II", "27/18/03/008"),
("Ogun", "Ogun Waterside", "Ibiade", "ARAROMI QUARTERS", "27/18/03/009"),
("Ogun", "Ogun Waterside", "Ibiade", "L.G. SCHOOL FARM SETTLEMENT", "27/18/03/010"),
("Ogun", "Ogun Waterside", "Ibiade", "(OPEN SPACE) ZION IBIADE", "27/18/03/011"),
("Ogun", "Ogun Waterside", "Ibiade", "OPEN SPACE OPP. ODULAJA'S HOUSE", "27/18/03/012"),
("Ogun", "Ogun Waterside", "Ibiade", "HEALTH CENTRE, IBIADE (GEN. HOSPITAL ROAD)", "27/18/03/013"),
("Ogun", "Ogun Waterside", "Lukogbe/Ilusin", "L.G. SCHOOL LUKOGBE I", "27/18/04/001"),
("Ogun", "Ogun Waterside", "Lukogbe/Ilusin", "L.G. SCHOOL LUKOGBE II", "27/18/04/002"),
("Ogun", "Ogun Waterside", "Lukogbe/Ilusin", "ITUN MELEKUN LOKULA", "27/18/04/003"),
("Ogun", "Ogun Waterside", "Lukogbe/Ilusin", "L.G. SCHOOL ILUSIN I", "27/18/04/004"),
("Ogun", "Ogun Waterside", "Lukogbe/Ilusin", "L.G. SCHOOL ILUSIN II", "27/18/04/005"),
("Ogun", "Ogun Waterside", "Lukogbe/Ilusin", "ILUSIN ZION", "27/18/04/006"),
("Ogun", "Ogun Waterside", "Lukogbe/Ilusin", "F.S.P. MARKET AGBURE", "27/18/04/007"),
("Ogun", "Ogun Waterside", "Lukogbe/Ilusin", "L.G. SCHOOL ARAFIN", "27/18/04/008"),
("Ogun", "Ogun Waterside", "Lukogbe/Ilusin", "LABOUR CAMP", "27/18/04/009"),
("Ogun", "Ogun Waterside", "Lukogbe/Ilusin", "ST. JOHN'S PRY. SCH. AGODO", "27/18/04/010"),
("Ogun", "Ogun Waterside", "Lukogbe/Ilusin", "LABOUR CAMP I", "27/18/04/011"),
("Ogun", "Ogun Waterside", "Lukogbe/Ilusin", "LABOUR CAMP II", "27/18/04/012"),
("Ogun", "Ogun Waterside", "Lukogbe/Ilusin", "LABOUR CAMP III", "27/18/04/013"),
("Ogun", "Ogun Waterside", "Lukogbe/Ilusin", "APATAL ODUNI JUNCTION", "27/18/04/014"),
("Ogun", "Ogun Waterside", "Lukogbe/Ilusin", "BAGBE CAMP", "27/18/04/015"),
("Ogun", "Ogun Waterside", "Lukogbe/Ilusin", "HEALTH CENTRE, AGBURE", "27/18/04/016"),
("Ogun", "Ogun Waterside", "Abigi", "MOSLEM PAY SCHOOL ABIGI I", "27/18/05/001"),
("Ogun", "Ogun Waterside", "Abigi", "MOSLEM PAY SCHOOL ABIGI II", "27/18/05/002"),
("Ogun", "Ogun Waterside", "Abigi", "ST. THOMAS PRY. SCHOOL I ABIGI", "27/18/05/003"),
("Ogun", "Ogun Waterside", "Abigi", "ST. THOMAS PRY. SCHOOL II ABIGI", "27/18/05/004"),
("Ogun", "Ogun Waterside", "Abigi", "MARKET SQUARE SQUARE ABIGI I", "27/18/05/005"),
("Ogun", "Ogun Waterside", "Abigi", "MARKET SQUARE ABIGI II", "27/18/05/006"),
("Ogun", "Ogun Waterside", "Abigi", "L.G. SCHOOL ITA-OGUN", "27/18/05/007"),
("Ogun", "Ogun Waterside", "Abigi", "ITATIKELI JUNCTION", "27/18/05/008"),
("Ogun", "Ogun Waterside", "Abigi", "L.G. SCHOOL, ITA-OUT", "27/18/05/009"),
("Ogun", "Ogun Waterside", "Abigi", "IGBAFO I", "27/18/05/010"),
("Ogun", "Ogun Waterside", "Abigi", "IGBAFO II", "27/18/05/011"),
("Ogun", "Ogun Waterside", "Abigi", "NPC OFFICE ABIGI", "27/18/05/012"),
("Ogun", "Ogun Waterside", "Abigi", "AYEGBAMI QUARTERS", "27/18/05/013"),
("Ogun", "Ogun Waterside", "Abigi", "PELEBE AT OKO-IGBO", "27/18/05/014"),
("Ogun", "Ogun Waterside", "Abigi", "L.G SCHOOL (II),ITA OGUN", "27/18/05/015"),
("Ogun", "Ogun Waterside", "Efire", "ILE-ONA NEAR OLD CENTRAL MOSQUE", "27/18/06/001"),
("Ogun", "Ogun Waterside", "Efire", "IFELO DUN UNITED PRY. SCHOOL", "27/18/06/002"),
("Ogun", "Ogun Waterside", "Efire", "ONA ERI QUARTER'S", "27/18/06/003"),
("Ogun", "Ogun Waterside", "Efire", "UBIKU CAMP", "27/18/06/004"),
("Ogun", "Ogun Waterside", "Efire", "L.G. SCHOOL BOLOUNDURO", "27/18/06/005"),
("Ogun", "Ogun Waterside", "Efire", "CALABAR CAMP I", "27/18/06/006"),
("Ogun", "Ogun Waterside", "Efire", "CALABAR CAMP II", "27/18/06/007"),
("Ogun", "Ogun Waterside", "Efire", "AJE BAMIDELE", "27/18/06/008"),
("Ogun", "Ogun Waterside", "Efire", "ONADA SQUARE", "27/18/06/009"),
("Ogun", "Ogun Waterside", "Efire", "LEREN CAMP", "27/18/06/010"),
("Ogun", "Ogun Waterside", "Efire", "SUNBARE'S CAMP [JEREMIAH]", "27/18/06/011"),
("Ogun", "Ogun Waterside", "Ayede/Lomiro", "R.C.M. SCHOOL, AYEDE", "27/18/07/001"),
("Ogun", "Ogun Waterside", "Ayede/Lomiro", "ST. LUKE'S SCHOOL, LUWODO", "27/18/07/002"),
("Ogun", "Ogun Waterside", "Ayede/Lomiro", "ST. PAUL'S SCHOOL, IYODAN", "27/18/07/003"),
("Ogun", "Ogun Waterside", "Ayede/Lomiro", "ST. JOHN'S SCHOOL, AJEGUNLE", "27/18/07/004"),
("Ogun", "Ogun Waterside", "Ayede/Lomiro", "C.M.S SCHOOL, LOMIRO", "27/18/07/005"),
("Ogun", "Ogun Waterside", "Ayede/Lomiro", "HEALTH CENTRE, LOFOLUWA", "27/18/07/006"),
("Ogun", "Ogun Waterside", "Ayede/Lomiro", "L.G. SCHOOL, IDOBILAYO", "27/18/07/007"),
("Ogun", "Ogun Waterside", "Ayede/Lomiro", "L.G. SCHOOL, IPAI KEMORE", "27/18/07/008"),
("Ogun", "Ogun Waterside", "Ayede/Lomiro", "OLOLA CAMP", "27/18/07/009"),
("Ogun", "Ogun Waterside", "Ayede/Lomiro", "ST. MICH. PRY SCHOOL, LIGUN", "27/18/07/010"),
("Ogun", "Ogun Waterside", "Ayede/Lomiro", "LAPETI BAALE'S QUARTERS", "27/18/07/011"),
("Ogun", "Ogun Waterside", "Ayede/Lomiro", "ST. ANDREW'S ANGLICAN PRIMARY SCHOOL, AYEDE", "27/18/07/012"),
("Ogun", "Ogun Waterside", "Ayede/Lomiro", "LOMIRO TOWN HALL, LOMIRO", "27/18/07/013"),
("Ogun", "Ogun Waterside", "Ayede/Lomiro", "C.M.S SCHOOL (II), LOMIRO", "27/18/07/014"),
("Ogun", "Ogun Waterside", "Ayila/Itebu", "ST. PHILLIP'S PRY. SCHOOL", "27/18/08/001"),
("Ogun", "Ogun Waterside", "Ayila/Itebu", "ST. JOHN'S PRY. SCHOOL, AYILA I", "27/18/08/002"),
("Ogun", "Ogun Waterside", "Ayila/Itebu", "ST. JOHN'S PRY SCH, AYILA II", "27/18/08/003"),
("Ogun", "Ogun Waterside", "Ayila/Itebu", "ST. JOSEPH R.C.M. SCHOOL, AYILA", "27/18/08/004"),
("Ogun", "Ogun Waterside", "Ayila/Itebu", "ST. JOSEPH R.C.M. SCHOOL, AYILA", "27/18/08/005"),
("Ogun", "Ogun Waterside", "Ayila/Itebu", "ST. DAVID PRY. SCHOOL, AYE TUMARE", "27/18/08/006"),
("Ogun", "Ogun Waterside", "Ayila/Itebu", "ST. MARKS SCHOOL, ITEBU", "27/18/08/007"),
("Ogun", "Ogun Waterside", "Ayila/Itebu", "DOLUKE QUARTERS", "27/18/08/008"),
("Ogun", "Ogun Waterside", "Ayila/Itebu", "AGO-AJAYE QUARTERS", "27/18/08/009"),
("Ogun", "Ogun Waterside", "Makun/Irokun", "L.G. SCHOOL, MAKUN OMI", "27/18/09/001"),
("Ogun", "Ogun Waterside", "Makun/Irokun", "MOHA VILLAGE SQUARE", "27/18/09/002"),
("Ogun", "Ogun Waterside", "Makun/Irokun", "L.G. SCHOOL, EBA", "27/18/09/003"),
("Ogun", "Ogun Waterside", "Makun/Irokun", "L.G. SCHOOL, IROKUN", "27/18/09/004"),
("Ogun", "Ogun Waterside", "Makun/Irokun", "L.G. SCHOOL, IGBO-EDU", "27/18/09/005"),
("Ogun", "Ogun Waterside", "Makun/Irokun", "L.G. SCHOOL, IROKUN", "27/18/09/006"),
("Ogun", "Ogun Waterside", "Makun/Irokun", "MATERNITY CENTRE, MAKUN-OMI", "27/18/09/007"),
("Ogun", "Ogun Waterside", "Makun/Irokun", "ARIYAN VILLAGE SQUARE", "27/18/09/008"),
("Ogun", "Ogun Waterside", "Makun/Irokun", "ASEPH CAMP IGBO-EDU I", "27/18/09/009"),
("Ogun", "Ogun Waterside", "Makun/Irokun", "ASEPH CAMP IGBO-EDU II", "27/18/09/010"),
("Ogun", "Ogun Waterside", "Makun/Irokun", "NEAR CHIEF TAYO AJAYI'S HOUSE, MAKUN", "27/18/09/011"),
("Ogun", "Ogun Waterside", "Makun/Irokun", "TOWN HALL, IMAKUN", "27/18/09/012"),
("Ogun", "Ogun Waterside", "Ode-Omi", "L.G. SCHOOL, ODE-OMI I", "27/18/10/001"),
("Ogun", "Ogun Waterside", "Ode-Omi", "L.G. SCHOOL, IGBOSERE", "27/18/10/002"),
("Ogun", "Ogun Waterside", "Ode-Omi", "L.G. SCHOOL, AWODIKORA", "27/18/10/003"),
("Ogun", "Ogun Waterside", "Ode-Omi", "L.G. SCHOOL, OKUN ILETE", "27/18/10/004"),
("Ogun", "Ogun Waterside", "Ode-Omi", "L.G. SCHOOL OKUN ALEFON", "27/18/10/005"),
("Ogun", "Ogun Waterside", "Ode-Omi", "RICE MILL, BARIKEN", "27/18/10/006"),
("Ogun", "Ogun Waterside", "Ode-Omi", "OKUN ISEKUN", "27/18/10/007"),
("Ogun", "Ogun Waterside", "Ode-Omi", "OPEN SPACE AT ILETE", "27/18/10/008"),
("Ogun", "Ogun Waterside", "Ode-Omi", "OPEN SPACE AT IGBESERE", "27/18/10/009"),
("Ogun", "Ogun Waterside", "Ode-Omi", "HEALTH CENTRE, ODE-OMI", "27/18/10/010"),
("Ogun", "Ogun Waterside", "Ode-Omi", "TOWN HALL, ODE - OMI", "27/18/10/011"),

# =========================================================
# REMO NORTH (10 Wards, 132 PUs)
# =========================================================
("Ogun", "Remo North", "Ayegbami", "OPEN SPACE AT AGO ARO JUNCTION I", "27/19/01/001"),
("Ogun", "Remo North", "Ayegbami", "OPEN SPACE AT AGO ARO JUNCTION II", "27/19/01/002"),
("Ogun", "Remo North", "Ayegbami", "OPEN SPACE AT IDI-ABA", "27/19/01/003"),
("Ogun", "Remo North", "Ayegbami", "ST. PETERS SCHOOL, AYEGBAMI ISARA", "27/19/01/004"),
("Ogun", "Remo North", "Ayegbami", "OPEN SPACE AT ALL WELL (AT OMO OLOWO) I", "27/19/01/005"),
("Ogun", "Remo North", "Ayegbami", "OPEN SPACE AT ALL WELL (AT OMO OLOWO) II", "27/19/01/006"),
("Ogun", "Remo North", "Ayegbami", "OPEN SPACE AT ARAROMI MIDWAY I", "27/19/01/007"),
("Ogun", "Remo North", "Ayegbami", "OPEN SPACE AT ARAROMI MIDWAY II", "27/19/01/008"),
("Ogun", "Remo North", "Ayegbami", "OPEN SPACE ATLEMO (AT ITALE)", "27/19/01/009"),
("Ogun", "Remo North", "Ayegbami", "OPEN SPACE AT ALAGOMEJI", "27/19/01/010"),
("Ogun", "Remo North", "Ayegbami", "OPEN SPACE AT IFEPE MID-WAY", "27/19/01/011"),
("Ogun", "Remo North", "Ayegbami", "OPEN SPACE AT AYEGBAMI (TOKOTAYA), ISARA", "27/19/01/012"),
("Ogun", "Remo North", "Ayegbami", "OPEN SPACE AT OLOPOMEWA, ISARA", "27/19/01/013"),
("Ogun", "Remo North", "Ayegbami", "OPEN SPACE AT MOTOYE, ISARA", "27/19/01/014"),
("Ogun", "Remo North", "Ayegbami", "OPEN SPACE AT EREDO", "27/19/01/015"),
("Ogun", "Remo North", "Ayegbami", "OPEN SPACE AT SAREPAWO", "27/19/01/016"),
("Ogun", "Remo North", "Ayegbami", "OPEN SPACE FRONT OF MATERNITY CENTRE, MADA", "27/19/01/017"),
("Ogun", "Remo North", "Igan/Ajina", "OPEN SPACE AT OLIWO JUNCTION I", "27/19/02/001"),
("Ogun", "Remo North", "Igan/Ajina", "OPEN SPACE ATOLIWO JUNCTION II", "27/19/02/002"),
("Ogun", "Remo North", "Igan/Ajina", "AJINA SQUARE I, ISARA", "27/19/02/003"),
("Ogun", "Remo North", "Igan/Ajina", "AJINA SQUARE II, ISARA", "27/19/02/004"),
("Ogun", "Remo North", "Igan/Ajina", "OPEN SPACE AT JABATA I", "27/19/02/005"),
("Ogun", "Remo North", "Igan/Ajina", "OPEN SPACE AT JABATA II", "27/19/02/006"),
("Ogun", "Remo North", "Igan/Ajina", "OPEN SPACE AT JABATA III", "27/19/02/007"),
("Ogun", "Remo North", "Igan/Ajina", "OPEN SPACE AT ITA POKE", "27/19/02/008"),
("Ogun", "Remo North", "Igan/Ajina", "OPEN SPACE ATAGO ARO", "27/19/02/009"),
("Ogun", "Remo North", "Igan/Ajina", "OPEN SPACE AT MAJAAGO", "27/19/02/010"),
("Ogun", "Remo North", "Igan/Ajina", "OPEN SPACE FRONT OF MAJAAGO'S PALACE", "27/19/02/011"),
("Ogun", "Remo North", "Igan/Ajina", "OPEN SPACE AT ILE AWO, OPP. GEN. HOSPITAL", "27/19/02/012"),
("Ogun", "Remo North", "Igan/Ajina", "OPEN SPACE AT ITA OLIMO", "27/19/02/013"),
("Ogun", "Remo North", "Igan/Ajina", "OPEN SPACE AT ERINLA MIDWAY", "27/19/02/014"),
("Ogun", "Remo North", "Igan/Ajina", "OPEN SPACE AT POKE", "27/19/02/015"),
("Ogun", "Remo North", "Igan/Ajina", "OPEN SPACE AT MADOGA, STREET", "27/19/02/016"),
("Ogun", "Remo North", "Moborode/Oke-Ola", "OPEN SPACE AT OKE OLA, MID WAY I", "27/19/03/001"),
("Ogun", "Remo North", "Moborode/Oke-Ola", "OPEN SPACE AT OKE OLA, MID WAY II", "27/19/03/002"),
("Ogun", "Remo North", "Moborode/Oke-Ola", "A.U.D. SCHOOL, ISARA I", "27/19/03/003"),
("Ogun", "Remo North", "Moborode/Oke-Ola", "A.U.D. SCHOOL, ISARA II", "27/19/03/004"),
("Ogun", "Remo North", "Moborode/Oke-Ola", "WESLEY SCHOOL, ISARA I", "27/19/03/005"),
("Ogun", "Remo North", "Moborode/Oke-Ola", "WESLEY SCHOOL, ISARA II", "27/19/03/006"),
("Ogun", "Remo North", "Moborode/Oke-Ola", "OPEN SPACE AT OBALENDE JUNCTION", "27/19/03/007"),
("Ogun", "Remo North", "Moborode/Oke-Ola", "OPEN SPACE AT IDI-OBI, OBALENDE", "27/19/03/008"),
("Ogun", "Remo North", "Moborode/Oke-Ola", "OPEN SPACE AT IMORISA MID-WAY", "27/19/03/009"),
("Ogun", "Remo North", "Moborode/Oke-Ola", "L.G SCHOOL AGETA", "27/19/03/010"),
("Ogun", "Remo North", "Odofin/Imagbo/Petekun/Dawara", "L.G. SCHOOL ODO I", "27/19/04/001"),
("Ogun", "Remo North", "Odofin/Imagbo/Petekun/Dawara", "L.G. SCHOOL ODO II", "27/19/04/002"),
("Ogun", "Remo North", "Odofin/Imagbo/Petekun/Dawara", "L.G. SCHOOL JOWOJE", "27/19/04/003"),
("Ogun", "Remo North", "Odofin/Imagbo/Petekun/Dawara", "L.G. SCHOOL GBASEMO", "27/19/04/004"),
("Ogun", "Remo North", "Odofin/Imagbo/Petekun/Dawara", "L.G. SCHOOL IMAGBON", "27/19/04/005"),
("Ogun", "Remo North", "Odofin/Imagbo/Petekun/Dawara", "L.G. SCHOOL, ELUJU", "27/19/04/006"),
("Ogun", "Remo North", "Odofin/Imagbo/Petekun/Dawara", "OLOPARUN VILLAGE SQUARE", "27/19/04/007"),
("Ogun", "Remo North", "Odofin/Imagbo/Petekun/Dawara", "EGUNFOYE VILLAGE SQUARE I", "27/19/04/008"),
("Ogun", "Remo North", "Odofin/Imagbo/Petekun/Dawara", "EGUNFOYE VILLAGE SQUARE II", "27/19/04/009"),
("Ogun", "Remo North", "Odofin/Imagbo/Petekun/Dawara", "LAGBAN PRY. SCHOOL", "27/19/04/010"),
("Ogun", "Remo North", "Odofin/Imagbo/Petekun/Dawara", "OPEN SPACE AT IRESI VILLAGE", "27/19/04/011"),
("Ogun", "Remo North", "Odofin/Imagbo/Petekun/Dawara", "OPEN SPACE AT PETEKU LISA VILLAGE I", "27/19/04/012"),
("Ogun", "Remo North", "Odofin/Imagbo/Petekun/Dawara", "OPEN SPACE AT PETEKU LISA VILLAGE II", "27/19/04/013"),
("Ogun", "Remo North", "Odofin/Imagbo/Petekun/Dawara", "DEYORUWA", "27/19/04/014"),
("Ogun", "Remo North", "Odofin/Imagbo/Petekun/Dawara", "OPEN SPACE AT DAWARA", "27/19/04/015"),
("Ogun", "Remo North", "Odofin/Imagbo/Petekun/Dawara", "OPEN SPACE AT OPEKERE", "27/19/04/016"),
("Ogun", "Remo North", "Odofin/Imagbo/Petekun/Dawara", "OPEN SPACE AT ALAGBE", "27/19/04/017"),
("Ogun", "Remo North", "Odofin/Imagbo/Petekun/Dawara", "OPEN SPACE AT OLIWO", "27/19/04/018"),
("Ogun", "Remo North", "Ilara", "UNITED SCHOOL, ILARA I", "27/19/05/001"),
("Ogun", "Remo North", "Ilara", "UNITED SCHOOL, ILARA II", "27/19/05/002"),
("Ogun", "Remo North", "Ilara", "OPEN SPACE AT AYEGBAMI ST. MIDDLE I, ILARA", "27/19/05/003"),
("Ogun", "Remo North", "Ilara", "OPEN SPACE AT AYEGBAMI ST. MIDDLE II, ILARA", "27/19/05/004"),
("Ogun", "Remo North", "Ilara", "OPEN SPACE AT J. JUNCTION ILARA I", "27/19/05/005"),
("Ogun", "Remo North", "Ilara", "OPEN SPACE AT J. JUNCTION ILARA II", "27/19/05/006"),
("Ogun", "Remo North", "Ilara", "OPEN SPACE FRONT OF MTN MAST, ILARA", "27/19/05/007"),
("Ogun", "Remo North", "Ilara", "OPEN SPACE AT ARAROMI, ILARA", "27/19/05/008"),
("Ogun", "Remo North", "Ilara", "OPEN SPACE AT OBAOLUAYE, ILARA", "27/19/05/009"),
("Ogun", "Remo North", "Akaka", "UNITED SCHOOL, AKAKA I", "27/19/06/001"),
("Ogun", "Remo North", "Akaka", "UNITED SCHOOL, AKAKA II", "27/19/06/002"),
("Ogun", "Remo North", "Akaka", "AFONLADE VILLAGE SQUARE I", "27/19/06/003"),
("Ogun", "Remo North", "Akaka", "AFONLADE VILLAGE SQUARE II", "27/19/06/004"),
("Ogun", "Remo North", "Akaka", "SALU VILLAGE SQUARE", "27/19/06/005"),
("Ogun", "Remo North", "Akaka", "UNITED SCHOOL, AKE AMURE", "27/19/06/006"),
("Ogun", "Remo North", "Akaka", "OPEN SPACE FRONT MATERNITY CENTRE AKAKA", "27/19/06/007"),
("Ogun", "Remo North", "Akaka", "OPEN SPACE AT AGORIGO", "27/19/06/008"),
("Ogun", "Remo North", "Akaka", "OPEN SPACE AT ABORO", "27/19/06/009"),
("Ogun", "Remo North", "Akaka", "OPEN SPACE AT ABEAYIKA", "27/19/06/010"),
("Ogun", "Remo North", "Akaka", "ABULE BALOGUN, VILLAGE SQUARE", "27/19/06/011"),
("Ogun", "Remo North", "Ipara", "MARKET SQUARE IPARA I", "27/19/07/001"),
("Ogun", "Remo North", "Ipara", "MARKET SQUARE IPARA II", "27/19/07/002"),
("Ogun", "Remo North", "Ipara", "LOCAL GOVT. SCH. IPARA I", "27/19/07/003"),
("Ogun", "Remo North", "Ipara", "LOCAL GOVT. SCH. IPARA II", "27/19/07/004"),
("Ogun", "Remo North", "Ipara", "UNITED SCH. IPARA I", "27/19/07/005"),
("Ogun", "Remo North", "Ipara", "UNITED SCH. IPARA II", "27/19/07/006"),
("Ogun", "Remo North", "Ipara", "OPEN SPACE AT ABULE SONOYI", "27/19/07/007"),
("Ogun", "Remo North", "Ipara", "OPEN SPACE AT AYEGBAMI-IPARA I", "27/19/07/008"),
("Ogun", "Remo North", "Ipara", "OPEN SPACE AT AYEGBAMI-IPARA II", "27/19/07/009"),
("Ogun", "Remo North", "Ipara", "COMMUNITY HIGH SCHOOL IPARA", "27/19/07/010"),
("Ogun", "Remo North", "Orile-Oko", "ANGLICAN SCHOOL, ISAN", "27/19/08/001"),
("Ogun", "Remo North", "Orile-Oko", "L.G. SCHOOL, OKODELOKUN", "27/19/08/002"),
("Ogun", "Remo North", "Orile-Oko", "L.G. SCHOOL, ATOBA", "27/19/08/003"),
("Ogun", "Remo North", "Orile-Oko", "UNITED HALL AZANA", "27/19/08/004"),
("Ogun", "Remo North", "Orile-Oko", "AJEGUNLE VILLAGE SQUARE", "27/19/08/005"),
("Ogun", "Remo North", "Orile-Oko", "ARAROMI MARKET SQUARE", "27/19/08/006"),
("Ogun", "Remo North", "Orile-Oko", "OPEN SPACE AT OGUNMUYIWA VILLAGE", "27/19/08/007"),
("Ogun", "Remo North", "Orile-Oko", "KAJOLA VILLAGE SQUARE", "27/19/08/008"),
("Ogun", "Remo North", "Orile-Oko", "OLIWO VILLAGE SQUARE", "27/19/08/009"),
("Ogun", "Remo North", "Ode I", "XT. CHURCH SCHOOL, ODO I", "27/19/09/001"),
("Ogun", "Remo North", "Ode I", "XT. CHURCH SCHOOL, ODO II", "27/19/09/002"),
("Ogun", "Remo North", "Ode I", "ODE REMO TOWN HALL I", "27/19/09/003"),
("Ogun", "Remo North", "Ode I", "ODE REMO TOWN HALL II", "27/19/09/004"),
("Ogun", "Remo North", "Ode I", "NLOKU MARKET SQURAE I", "27/19/09/005"),
("Ogun", "Remo North", "Ode I", "NLOKU MARKET SQURAE II", "27/19/09/006"),
("Ogun", "Remo North", "Ode I", "OPEN SPACE FRONT OF MATERNITY CENTRE I", "27/19/09/007"),
("Ogun", "Remo North", "Ode I", "OPEN SPACE FRONT OF MATERNITY CENTRE II", "27/19/09/008"),
("Ogun", "Remo North", "Ode I", "ODE REMO HIGH SCH. I", "27/19/09/009"),
("Ogun", "Remo North", "Ode I", "ODE REMO HIGH SCH. II", "27/19/09/010"),
("Ogun", "Remo North", "Ode I", "AJINA SQUARE I", "27/19/09/011"),
("Ogun", "Remo North", "Ode I", "AJINA SQUARE II", "27/19/09/012"),
("Ogun", "Remo North", "Ode I", "OPEN SPACE AT ITAMARO I", "27/19/09/013"),
("Ogun", "Remo North", "Ode I", "OPEN SPACE AT ITAMARO II", "27/19/09/014"),
("Ogun", "Remo North", "Ode I", "AJINA SQUARE", "27/19/09/015"),
("Ogun", "Remo North", "Ode II", "A.U.D. SCHOOL, ODE I", "27/19/10/001"),
("Ogun", "Remo North", "Ode II", "A.U.D. SCHOOL, ODE II", "27/19/10/002"),
("Ogun", "Remo North", "Ode II", "WESLEY SCHOOL, ODE I", "27/19/10/003"),
("Ogun", "Remo North", "Ode II", "WESLEY SCHOOL, ODE II", "27/19/10/004"),
("Ogun", "Remo North", "Ode II", "OPEN SPACE AT ITUN-ODE/IGODO NEAR ASIRU'S MOSQUE", "27/19/10/005"),
("Ogun", "Remo North", "Ode II", "AGBERO MARKET SQUARE I", "27/19/10/006"),
("Ogun", "Remo North", "Ode II", "AGBERO MARKET SQUARE II", "27/19/10/007"),
("Ogun", "Remo North", "Ode II", "OKE-OLA (NEAR ADERANGA'S HOUSE) I", "27/19/10/008"),
("Ogun", "Remo North", "Ode II", "OKE-OLA (NEAR ADERANGA'S HOUSE) II", "27/19/10/009"),
("Ogun", "Remo North", "Ode II", "OPEN SPACE AT MARIDAN STREET ADEBONYI I", "27/19/10/010"),
("Ogun", "Remo North", "Ode II", "OPEN SPACE AT MARIDAN STREET ADEBONYI II", "27/19/10/011"),
("Ogun", "Remo North", "Ode II", "OPEN SPACE AT MARIDAN STREET ADEBONYI III", "27/19/10/012"),
("Ogun", "Remo North", "Ode II", "OPEN SPACE AT ITA OLISA NEAR BALOGUN'S MOSQUE", "27/19/10/013"),
("Ogun", "Remo North", "Ode II", "OPEN SPACE AT ITA OLISA", "27/19/10/014"),
("Ogun", "Remo North", "Ode II", "AGBERO MARKET SQUARE III", "27/19/10/015"),
("Ogun", "Remo North", "Ode II", "OPEN SPACE AT OKE-OLA III", "27/19/10/016"),
("Ogun", "Remo North", "Ode II", "MUSLIM PRY.SCH.OLOMOWEWE ODE", "27/19/10/017"),

# =========================================================
# SAGAMU (15 Wards, 299 PUs)
# =========================================================
("Ogun", "Sagamu", "Oko/Epe/Itula I", "OPEN SPACE AT SAGAMU ROUND ABOUT", "27/20/01/001"),
("Ogun", "Sagamu", "Oko/Epe/Itula I", "WESLEY SCHOOL, OKO I", "27/20/01/002"),
("Ogun", "Sagamu", "Oko/Epe/Itula I", "WESLEY SCHOOL, OKO II", "27/20/01/003"),
("Ogun", "Sagamu", "Oko/Epe/Itula I", "OPEN SPACE AT OLD OJA ALE EPE I", "27/20/01/004"),
("Ogun", "Sagamu", "Oko/Epe/Itula I", "OPEN SPACE NEAR NURSERY SCHOOL EJIIRO I", "27/20/01/005"),
("Ogun", "Sagamu", "Oko/Epe/Itula I", "SOYINDO WESLEY SCHOOL I", "27/20/01/006"),
("Ogun", "Sagamu", "Oko/Epe/Itula I", "A.U.D. SCHOOL OKO I", "27/20/01/007"),
("Ogun", "Sagamu", "Oko/Epe/Itula I", "OPEN SPACE @ ARAROMI JUNCTION PHASE 1, ALONG SAGAMU-IKENNE ROAD", "27/20/01/008"),
("Ogun", "Sagamu", "Oko/Epe/Itula I", "OPEN SPACE @ ORIJE JUNCTION, HARMONY JOINT COMMUNITY", "27/20/01/009"),
("Ogun", "Sagamu", "Oko/Epe/Itula I", "REMO SECONDARY SCHOOL", "27/20/01/010"),
("Ogun", "Sagamu", "Oko/Epe/Itula I", "OPEN SPACE @ARAROMI PHASE II ORION ACADEMY", "27/20/01/011"),
("Ogun", "Sagamu", "Oko/Epe/Itula II", "OPEN SPACE NEAR ALADO PALACE", "27/20/02/001"),
("Ogun", "Sagamu", "Oko/Epe/Itula II", "OWONIFARI'S HOUSE OPPOSITE I", "27/20/02/002"),
("Ogun", "Sagamu", "Oko/Epe/Itula II", "ST. COLLUMCILE SCHOOL I", "27/20/02/003"),
("Ogun", "Sagamu", "Oko/Epe/Itula II", "OPEN SPACE BESIDE K & S CHURCH OROKUTA", "27/20/02/004"),
("Ogun", "Sagamu", "Oko/Epe/Itula II", "OPEN SPACE AT DEGORUNSEN JUNCTION I", "27/20/02/005"),
("Ogun", "Sagamu", "Oko/Epe/Itula II", "OPEN SPACE AT DEGORUNSEN UPPER", "27/20/02/006"),
("Ogun", "Sagamu", "Oko/Epe/Itula II", "OPEN SPACE AT IGA LOSI/AKARIGBO", "27/20/02/007"),
("Ogun", "Sagamu", "Oko/Epe/Itula II", "OPEN SPACE AT AJINA/ISOKUN ST. JUNCTION", "27/20/02/008"),
("Ogun", "Sagamu", "Oko/Epe/Itula II", "OPEN SPACE NEAR K & S CHURCH, AINA OJOKUN", "27/20/02/009"),
("Ogun", "Sagamu", "Oko/Epe/Itula II", "OPEN SPACE OPP. LOWA IBU'S PALACE", "27/20/02/010"),
("Ogun", "Sagamu", "Oko/Epe/Itula II", "OPEN SPACE OPPOSITE IPOJI PALACE", "27/20/02/011"),
("Ogun", "Sagamu", "Oko/Epe/Itula II", "OPEN SPACE AT MABADEJE JUNCTION I", "27/20/02/012"),
("Ogun", "Sagamu", "Oko/Epe/Itula II", "OPEN SPACE AT ADIEWOCAOT-BAKARE JUNCTION", "27/20/02/013"),
("Ogun", "Sagamu", "Oko/Epe/Itula II", "OPEN SPACE BESIDE AIYEPE POLICE STATION, SHAKURA", "27/20/02/014"),
("Ogun", "Sagamu", "Oko/Epe/Itula II", "OPEN SPACE AT SOLA SOBOWALE JUNCTION BESIDE TRANSFORMER", "27/20/02/015"),
("Ogun", "Sagamu", "Oko/Epe/Itula II", "OPEN SPACE BESIDE SAKURA PALACE BY THE TRANSFORMER, SAKURA", "27/20/02/016"),
("Ogun", "Sagamu", "Oko/Epe/Itula II", "OPEN SPACE AIYEPE JUNCTION", "27/20/02/017"),
("Ogun", "Sagamu", "Ayegbami/Ijokun", "OPEN SPACE BESIDE ODEKUN", "27/20/03/001"),
("Ogun", "Sagamu", "Ayegbami/Ijokun", "OPEN SPACE FRONTAGE OF JEBE'S", "27/20/03/002"),
("Ogun", "Sagamu", "Ayegbami/Ijokun", "OPEN SPACE NEAR OLOKO'S", "27/20/03/003"),
("Ogun", "Sagamu", "Ayegbami/Ijokun", "OPEN SPACE AT KAMIYO STREET (MIDWAY)", "27/20/03/004"),
("Ogun", "Sagamu", "Ayegbami/Ijokun", "OPEN SPACE AT SODE", "27/20/03/005"),
("Ogun", "Sagamu", "Ayegbami/Ijokun", "OPEN SPACE NEAR AWOSANYA", "27/20/03/006"),
("Ogun", "Sagamu", "Ayegbami/Ijokun", "ST. PAUL'S SCHOOL IJOKUN", "27/20/03/007"),
("Ogun", "Sagamu", "Ayegbami/Ijokun", "OPEN SPACE NEAR OLD GARAGE IJOKUN", "27/20/03/008"),
("Ogun", "Sagamu", "Ayegbami/Ijokun", "OPEN SPACE AT MASUNKUNMO JUNCTION BY THE COMMUNICATION MAST", "27/20/03/009"),
("Ogun", "Sagamu", "Ayegbami/Ijokun", "OPEN SPACE JEBE STREET END", "27/20/03/010"),
("Ogun", "Sagamu", "Ayegbami/Ijokun", "OPEN SPACE BESIDE AKEREDOLU YOUTH WATER PROJECT", "27/20/03/011"),
("Ogun", "Sagamu", "Ayegbami/Ijokun", "OPEN SPACE BY RAINBOW/OGUNSOLA STREET JUNCTION, EHINGBETI", "27/20/03/012"),
("Ogun", "Sagamu", "Ayegbami/Ijokun", "AFRICAN CHURCH PRY SCH, APELOGUN SAGAMU", "27/20/03/013"),
("Ogun", "Sagamu", "Ayegbami/Ijokun", "ST PAUL SCHOOL AIYEPE", "27/20/03/014"),
("Ogun", "Sagamu", "Ayegbami/Ijokun", "OPEN SPACE AT END BABATUNDE AWOSANYA STREET", "27/20/03/015"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE AT JOHNSON OGUNSOLA CAR WASH", "27/20/04/001"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE AT DAN-TAJIRA I", "27/20/04/002"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE AT DAN-TAJIRA UPPER", "27/20/04/003"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE OPPOSITE OLORI ILU PALACE", "27/20/04/004"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE BESIDE OLUWAKEMI'S MOSQUE", "27/20/04/005"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE AT GBASEMO STREET, MIDWAY", "27/20/04/006"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE AT BURAIMO STREET, MIDWAY", "27/20/04/007"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE OPPOSITE MERCY HOSPITAL", "27/20/04/008"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE NEAR G.R.A. BEGINNING I", "27/20/04/009"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE AT MOSINMI", "27/20/04/010"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE AT OKULAJA STREET, MIDWAY", "27/20/04/011"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE NEAR MRS OKUBOTE HOUSE", "27/20/04/012"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE NEAR JUBRIL BALOGUN STREET", "27/20/04/013"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE AT KAARA TRAILER PARK I", "27/20/04/014"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE AT FAKOYA STREET MIDWAY", "27/20/04/015"),
("Ogun", "Sagamu", "Sabo I", "OPPOSITE STAR-LIGHT", "27/20/04/016"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE @ KAWEFUNMI JUNCTION, GRA QUARTERS", "27/20/04/017"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE @ BOSS JUNCTION, GRA ROAD SABO", "27/20/04/018"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE @ SABO GRA HEALTH CENTRE", "27/20/04/019"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE AT OLODO JUNCTION SABO", "27/20/04/020"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE @ ADEMOSU STREET, BESIDE COMMUNICATION MAST, SABO", "27/20/04/021"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE @ KOLAWOLE JUNCTION, OPPOSITE AA RANO PETROL STATION, AKARIGBO ROAD, SABO", "27/20/04/022"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE @ KAARA TRAILER PARK II, AKARIGBO ROAD", "27/20/04/023"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE @ BISUGA JUNCTION BESIDE TRANSFORMER", "27/20/04/024"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE @ NELSON OGUNLESI", "27/20/04/025"),
("Ogun", "Sagamu", "Sabo I", "INFRONT OF WAPCO SECOND GATE, POWERLINE", "27/20/04/026"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE @ SABITU JUNCTION, SABO", "27/20/04/027"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE @ ADENUSI STREET SABO", "27/20/04/028"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE AT AWOFALA STREET OKE ODO SABO", "27/20/04/029"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE OPPOSITE GRA QUARTERS", "27/20/04/030"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE ALAUSA JUNCTION ISOSO GRA PHASE I", "27/20/04/031"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE OBAFEMI AWOLOWO AV, GRA PHASE I", "27/20/04/032"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE @AWOFELA STR, SABO", "27/20/04/033"),
("Ogun", "Sagamu", "Sabo I", "OPEN SPACE @OLODO ROUNDABOUT SABO END", "27/20/04/034"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE OPPOSITE KINGS CROWN HOTEL", "27/20/05/001"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE NEAR SERIKI", "27/20/05/002"),
("Ogun", "Sagamu", "Sabo II", "L.G SCHOOL I SABO I", "27/20/05/003"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE NEAR AGURA ROAD UPPER", "27/20/05/004"),
("Ogun", "Sagamu", "Sabo II", "MARKET SQUARE ODE-LEMO ROAD I", "27/20/05/005"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE NEAR AGURA ROAD END", "27/20/05/006"),
("Ogun", "Sagamu", "Sabo II", "OPP. NURSERY SCHOOL ODUJOKO I", "27/20/05/007"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE AT SODE LANE UPPER", "27/20/05/008"),
("Ogun", "Sagamu", "Sabo II", "MUSLIM HIGH SCHOOL I", "27/20/05/009"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE NEAR TEMIDIRE SCHOOL, SABO", "27/20/05/010"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE AT ODI OLOWO / AKARIGBO STREET", "27/20/05/011"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE AT ONIGBALE STREET", "27/20/05/012"),
("Ogun", "Sagamu", "Sabo II", "REMO DIVISIONAL HIGH SCHOOL I", "27/20/05/013"),
("Ogun", "Sagamu", "Sabo II", "BUCKNORS HOUSE BY NEPA I", "27/20/05/014"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE AT TAIWO GORIOLA", "27/20/05/015"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE NEAR AGURA ROAD MIDDLE, (IGBELEFUN)", "27/20/05/016"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE AT LAGA JUNCTION", "27/20/05/017"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE AT OKO IGBO JUNCTION, ABIJAWUTA, ATOYO BESIDE TRANSFORMER", "27/20/05/018"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE AT ONIKOYI ROUND ABOUT", "27/20/05/019"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE HAPPY DAY JUNCTION", "27/20/05/020"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE AT COMMUNITY CENTER, LISOKU ROAD, IBELEFU", "27/20/05/021"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE ITA MERIN COMMUNITY HALL", "27/20/05/022"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE AT AYODELE JUNCTION OPP TRANSFORMER, IBELEFU ADEBOKU", "27/20/05/023"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE @ HEALTH CENTRE JUNCTION, POWERLINE ARUBA", "27/20/05/024"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE @ CEMENTRY JUNCTION, ATOYO", "27/20/05/025"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE @OGINNI COMMUNITY (PROPOSED HEALTH CENTRE)", "27/20/05/026"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE @ ATOYO EGBE - ISOPO BESIDE TRANSFORMER", "27/20/05/027"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE @ MARKET SQUARE, IBELEFUN SIMPATA, ALONG ODE - LEMO ROAD", "27/20/05/028"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE AT ELEYOWO MARKET, ELEYOWO", "27/20/05/029"),
("Ogun", "Sagamu", "Sabo II", "OPEN SPACE AT ONIGBALE END", "27/20/05/030"),
("Ogun", "Sagamu", "Isokun/Oyebado", "OPEN SPACE NEAR AGOLO, CENTRAL MOSQUE", "27/20/06/001"),
("Ogun", "Sagamu", "Isokun/Oyebado", "ST. PAUL'S SCHOOL ALAGBE", "27/20/06/002"),
("Ogun", "Sagamu", "Isokun/Oyebado", "OPEN SPACE AT ALAGBONMEFA I", "27/20/06/003"),
("Ogun", "Sagamu", "Isokun/Oyebado", "RANIKAN QUARTERS I", "27/20/06/004"),
("Ogun", "Sagamu", "Isokun/Oyebado", "OPEN SPACE AT IRAYE STREET", "27/20/06/005"),
("Ogun", "Sagamu", "Isokun/Oyebado", "METHODIST COLLEGE I", "27/20/06/006"),
("Ogun", "Sagamu", "Isokun/Oyebado", "OPEN SPACE AT OGUNLANA ARAROMI JUNCTION I", "27/20/06/007"),
("Ogun", "Sagamu", "Isokun/Oyebado", "AJEGUNLE / AKARINGBO STREET", "27/20/06/008"),
("Ogun", "Sagamu", "Isokun/Oyebado", "OPEN SPACE @ SABINTU/AJEGUNLE JUNCTION", "27/20/06/009"),
("Ogun", "Sagamu", "Isokun/Oyebado", "METHODIST COMPHRENSIVE COLLEGE SECOND GATE", "27/20/06/010"),
("Ogun", "Sagamu", "Isokun/Oyebado", "OPEN SPACE @OYEBAJO/BARUWA JUNCTION", "27/20/06/011"),
("Ogun", "Sagamu", "Isokun/Oyebado", "OPEN SPACE @ OYEBAJO MIDWAY BY ONIMALE LANE", "27/20/06/012"),
("Ogun", "Sagamu", "Isokun/Oyebado", "OPEN SPACE @OWOLEWA JUNCTION", "27/20/06/013"),
("Ogun", "Sagamu", "Isokun/Oyebado", "OPEN SPACE AT ITUNOKE ROUNDABOUT", "27/20/06/014"),
("Ogun", "Sagamu", "Ijagba", "L.G. SCHOOL I", "27/20/07/001"),
("Ogun", "Sagamu", "Ijagba", "L.G. SCHOOL II", "27/20/07/002"),
("Ogun", "Sagamu", "Ijagba", "OPEN SPACE OPPOSITE OF ILE-IFA", "27/20/07/003"),
("Ogun", "Sagamu", "Ijagba", "OPEN SPACE NEAR AFINJU BABALAWO STREET", "27/20/07/004"),
("Ogun", "Sagamu", "Ijagba", "OPEN SPACE NEAR LEGUNSEN PALACE", "27/20/07/005"),
("Ogun", "Sagamu", "Ijagba", "ONIJAGBAS PALACE", "27/20/07/006"),
("Ogun", "Sagamu", "Ijagba", "OPEN SPACE AT ITA IJAGBA JUNCTION", "27/20/07/007"),
("Ogun", "Sagamu", "Ijagba", "ONIRERE OPPOSITE NO. 30", "27/20/07/008"),
("Ogun", "Sagamu", "Ijagba", "L.G SCHOOL II, IJAGBA", "27/20/07/009"),
("Ogun", "Sagamu", "Latawa", "OPEN SPACE AT LATAWA PALACE I", "27/20/08/001"),
("Ogun", "Sagamu", "Latawa", "OPEN SPACE NEAR OGUNMEKUN STREET", "27/20/08/002"),
("Ogun", "Sagamu", "Latawa", "OPEN SPACE AT LATAWA SQUARE I", "27/20/08/003"),
("Ogun", "Sagamu", "Latawa", "OPEN SPACE NEAR ARAROMI BAKERY", "27/20/08/004"),
("Ogun", "Sagamu", "Latawa", "OPEN SPACE NEAR MECHANIC SITE /KAJOLA", "27/20/08/005"),
("Ogun", "Sagamu", "Latawa", "U.A.M.C. ELEJA I", "27/20/08/006"),
("Ogun", "Sagamu", "Latawa", "U.A.M.C. ELEJA II", "27/20/08/007"),
("Ogun", "Sagamu", "Latawa", "OPEN SPACE AT BOLAJI STREET AJEGUNLE", "27/20/08/008"),
("Ogun", "Sagamu", "Ode-Lemo", "ST. JOHN'S PRY. SCHOOL ODE - LEMO", "27/20/09/001"),
("Ogun", "Sagamu", "Ode-Lemo", "OPEN SPACE NEAR LEMO", "27/20/09/002"),
("Ogun", "Sagamu", "Ode-Lemo", "OPEN SPACE NEAR BABA IJO", "27/20/09/003"),
("Ogun", "Sagamu", "Ode-Lemo", "A.U.D. SCHOOL ODE - LEMO I", "27/20/09/004"),
("Ogun", "Sagamu", "Ode-Lemo", "A.U.D. SCHOOL ODE - LEMO II", "27/20/09/005"),
("Ogun", "Sagamu", "Ode-Lemo", "OPEN SPACE AT ILE - AJE MARKET ODE", "27/20/09/006"),
("Ogun", "Sagamu", "Ode-Lemo", "OPEN SPACE ITA MERIN SQUARE", "27/20/09/007"),
("Ogun", "Sagamu", "Ode-Lemo", "ST. PAUL'S SCHOOL IGBOLOLO", "27/20/09/008"),
("Ogun", "Sagamu", "Ode-Lemo", "ST. PAUL'S SCHOOL EMUREN I", "27/20/09/009"),
("Ogun", "Sagamu", "Ode-Lemo", "ITUN ELEMUREN STREET I", "27/20/09/010"),
("Ogun", "Sagamu", "Ode-Lemo", "OPEN SPACE AT MARKET SQUARE I", "27/20/09/011"),
("Ogun", "Sagamu", "Ode-Lemo", "OPEN SPACE AT EMUREN MARKET SQUARE II", "27/20/09/012"),
("Ogun", "Sagamu", "Ode-Lemo", "OPEN SPACE AT OKE-AYO JUNCTION BY WATERBOHOLE", "27/20/09/013"),
("Ogun", "Sagamu", "Ode-Lemo", "OPEN SPACE AT OKESELU BY COMMUNITY WATER BOREHOLE", "27/20/09/014"),
("Ogun", "Sagamu", "Ode-Lemo", "OPEN SPACE AT OKE-AROBI JUNCTION BY TRANSFORMER", "27/20/09/015"),
("Ogun", "Sagamu", "Ode-Lemo", "OPEN SPACE AT IGANKE JUNCTION EMUREN BY ADRON HOMES", "27/20/09/016"),
("Ogun", "Sagamu", "Ogijo/Likosi", "ST. PAUL'S SCHOOL IGBODE", "27/20/10/001"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE AT OSIGBOYEDE VILLAGE I", "27/20/10/002"),
("Ogun", "Sagamu", "Ogijo/Likosi", "ST. MICHAEL R.C.M. FAKALE", "27/20/10/003"),
("Ogun", "Sagamu", "Ogijo/Likosi", "U.A.M.C. SCHOOL IRAYE", "27/20/10/004"),
("Ogun", "Sagamu", "Ogijo/Likosi", "ST. FRANCIS SCHOOL IGBOSORO", "27/20/10/005"),
("Ogun", "Sagamu", "Ogijo/Likosi", "ST. JOHN SCHOOL OGIJO I", "27/20/10/006"),
("Ogun", "Sagamu", "Ogijo/Likosi", "ST. JOHN SCHOOL OGIJO II", "27/20/10/007"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE FRONT LISA'S HOUSE", "27/20/10/008"),
("Ogun", "Sagamu", "Ogijo/Likosi", "WESLEY SCHOOL EREFUN", "27/20/10/009"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE OPPOSITE CATHOLIC ABAFON", "27/20/10/010"),
("Ogun", "Sagamu", "Ogijo/Likosi", "L.G SCHOOL IGBAGA", "27/20/10/011"),
("Ogun", "Sagamu", "Ogijo/Likosi", "MOSIMI VILLAGE", "27/20/10/012"),
("Ogun", "Sagamu", "Ogijo/Likosi", "L.G. SCHOOL ITA - MERIN", "27/20/10/013"),
("Ogun", "Sagamu", "Ogijo/Likosi", "A.U.D. SCHOOL IMUSHIN - OGIJO", "27/20/10/014"),
("Ogun", "Sagamu", "Ogijo/Likosi", "EYIN EGBE VILLAGE", "27/20/10/015"),
("Ogun", "Sagamu", "Ogijo/Likosi", "WESLEY SCHOOL SOTUNBO", "27/20/10/016"),
("Ogun", "Sagamu", "Ogijo/Likosi", "C.A.C. SCHOOL OGIJO I", "27/20/10/017"),
("Ogun", "Sagamu", "Ogijo/Likosi", "EWU OLOJA PRIMARY SCHOOL", "27/20/10/018"),
("Ogun", "Sagamu", "Ogijo/Likosi", "L.G SCHOOL AJAREGUN I", "27/20/10/019"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE BESIDE TRANSFORMER, ASSOCIATION AVENUE AGODO", "27/20/10/020"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE AT ONIBURUKU JUNCTION OPP CDA ELECTRIFICATION PROJECT", "27/20/10/021"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE @ GASLINE EYITA", "27/20/10/022"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE @ROUND ABOUT ONIJAGUN, OGIJO", "27/20/10/023"),
("Ogun", "Sagamu", "Ogijo/Likosi", "IDIAGBALUMO OGEDE", "27/20/10/024"),
("Ogun", "Sagamu", "Ogijo/Likosi", "BESIDE ORIOKUTA PALACE", "27/20/10/025"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE AT IGBO OGIJO", "27/20/10/026"),
("Ogun", "Sagamu", "Ogijo/Likosi", "IMORO OGIJO COMMUNITY PRY SCHOOL, OGIJO", "27/20/10/027"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE @ OKADA PARK OSHODI - OKE", "27/20/10/028"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE BESIDE PZ ESTATE TRANSFORMER", "27/20/10/029"),
("Ogun", "Sagamu", "Ogijo/Likosi", "AROGUNRE-MELUFEN JUNCTION BESIDE TRANSFORMER, MELUFEN", "27/20/10/030"),
("Ogun", "Sagamu", "Ogijo/Likosi", "IDOMOGUN TOWN HALL OGIJO", "27/20/10/031"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OGIJO COMMUNITY HIGH SCHOOL, OGIJO", "27/20/10/032"),
("Ogun", "Sagamu", "Ogijo/Likosi", "HALEN JUNCTION NASFAT OGIJO", "27/20/10/033"),
("Ogun", "Sagamu", "Ogijo/Likosi", "ONAFOWOKAN ESTATE ITAOLIWO (OGIJO)", "27/20/10/034"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE INFRONT OF AGBOWA COMMUNITY MARKET, AGBOWA EREFUN", "27/20/10/035"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE AT MIRACLE JUNCTION OPP COMMUNICATION MAST", "27/20/10/036"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE OKE OKO GAS LINE", "27/20/10/037"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE @ POWERLINE JUNCTION PHONIX, OGIJO", "27/20/10/038"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE @ ITA - SANNI BUS STOP, OGIJO", "27/20/10/039"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OLOORODE MARKET, ERIYO-AGA OPP NNPC GASLINE", "27/20/10/040"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE AT ORI OKE JUNCTION, BESIDE TRANSFORMER, ERIYO", "27/20/10/041"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE @ ARIGBABU JUNCTION, MOSINMI", "27/20/10/042"),
("Ogun", "Sagamu", "Ogijo/Likosi", "MAGBON ELEPETE JUNCTION", "27/20/10/043"),
("Ogun", "Sagamu", "Ogijo/Likosi", "EREKO JUNCTION OGIJO", "27/20/10/044"),
("Ogun", "Sagamu", "Ogijo/Likosi", "IJAGBA COMMUNITY HIGH SCHOOL, SOTUNBO", "27/20/10/045"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE @ OLUWASEYI SQUARE, POWERLINE EYITA-MORO ODO KEKERE", "27/20/10/046"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE @ MALATORI JUNCTION, OGIJO", "27/20/10/047"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE AT MOSHOOD ODUNSI-ALH IMAM YUNUS JUNCTION, ALASE", "27/20/10/048"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE AT DELORD, BESIDE TRANSFORMER, OKE IBU", "27/20/10/049"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE @ LIKOSI MARKET", "27/20/10/050"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE @ IYANA TIPPER JUNCTION, EWU-OLOJA", "27/20/10/051"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE @ LIKOSI OLD SOLDIER BUS STOP, GOD PASS THEM DEJUWOGBO, POWERLINE", "27/20/10/052"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE @ ILARA JUNCTION, OGIJO", "27/20/10/053"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE @ OKE - OKO/OGEDE SQUARE, BESIDE TRANSFORMER, OGIJO", "27/20/10/054"),
("Ogun", "Sagamu", "Ogijo/Likosi", "ESCOBAR BUS STOP JUNCTION (OGIJO)", "27/20/10/055"),
("Ogun", "Sagamu", "Ogijo/Likosi", "OPEN SPACE AT ALH TEMIASUNWO NITOSI ILE OLOWO JUNCTION", "27/20/10/056"),
("Ogun", "Sagamu", "Surulere", "WESLEY SCHOOL MAKUN I", "27/20/11/001"),
("Ogun", "Sagamu", "Surulere", "Z. I. SCHOOL MAKUN I", "27/20/11/002"),
("Ogun", "Sagamu", "Surulere", "OPEN SPACE AT AKOREDE MIDWAY", "27/20/11/003"),
("Ogun", "Sagamu", "Surulere", "OPEN SPACE AT AKOREDE UPPER", "27/20/11/004"),
("Ogun", "Sagamu", "Surulere", "A.U.D. SCHOOL MAKUN", "27/20/11/005"),
("Ogun", "Sagamu", "Surulere", "SOKOYA MEMORIAL SCHOOL I", "27/20/11/006"),
("Ogun", "Sagamu", "Surulere", "OPEN SPACE AT AKOREDE LOWER", "27/20/11/007"),
("Ogun", "Sagamu", "Surulere", "AKOREDE JUNCTION", "27/20/11/008"),
("Ogun", "Sagamu", "Surulere", "OPEN SPACE @ OSOTUNSEN/AKOGUN OKEOWO SQUARE, EWUGA", "27/20/11/009"),
("Ogun", "Sagamu", "Surulere", "MAKUN HIGH SCHOOL SNR SECTION", "27/20/11/010"),
("Ogun", "Sagamu", "Surulere", "A.U.D SCHOOL MAKUN", "27/20/11/011"),
("Ogun", "Sagamu", "Surulere", "WESLEY SCHOOL MAKUN II", "27/20/11/012"),
("Ogun", "Sagamu", "Surulere", "Z.I SCHOOL MAKUN II", "27/20/11/013"),
("Ogun", "Sagamu", "Surulere", "OPEN SPACE AT APENA SOKOYA", "27/20/11/014"),
("Ogun", "Sagamu", "Surulere", "OPEN SPACE @ MEDITOP HOSPITAL JUNCTION, ISALE OJUMELE", "27/20/11/015"),
("Ogun", "Sagamu", "Surulere", "OPEN SPACE AKOREDE MIDWAY II", "27/20/11/016"),
("Ogun", "Sagamu", "Surulere", "OPEN SPACE AT AKOREDE PHASE II", "27/20/11/017"),
("Ogun", "Sagamu", "Surulere", "OPEN SPACE AT IWERA", "27/20/11/018"),
("Ogun", "Sagamu", "Isote", "OPEN SPACE OPP DAODU'S HOUSE I", "27/20/12/001"),
("Ogun", "Sagamu", "Isote", "OPEN SPACE OPP. AGBON OLUWOTEDO, STREET", "27/20/12/002"),
("Ogun", "Sagamu", "Isote", "OPEN SPACE AT RADELU ISOTE JUNCTION", "27/20/12/003"),
("Ogun", "Sagamu", "Isote", "OPEN SPACE AT EWUSI HOUSE", "27/20/12/004"),
("Ogun", "Sagamu", "Isote", "OPEN SPACE AT ISOTE STREET MIDWAY", "27/20/12/005"),
("Ogun", "Sagamu", "Isote", "OPEN SPACE AT OYEKAN HOUSE", "27/20/12/006"),
("Ogun", "Sagamu", "Isote", "OPEN SPACE AT ODIOLOWO/OLUKOKUN", "27/20/12/007"),
("Ogun", "Sagamu", "Isote", "OPEN SPACE AT OSISANYA ST. MIDWAY", "27/20/12/008"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "ST. PAUL'S SCHOOL SIMAWE", "27/20/13/001"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "OPEN SPACE AT EWU BOUN", "27/20/13/002"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "OPEN SPACE AT ALAWUIN VILLAGE", "27/20/13/003"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "ST PAUL'S SCHOOL IWELEPE", "27/20/13/004"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "OPEN SPACE AT OYELEKE SETTLEMENT", "27/20/13/005"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "L.G. SCHOOL KAMIYI", "27/20/13/006"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "ST. PAUL'S SCHOOL AYETORO", "27/20/13/007"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "ST. PAUL'S SCHOOL OKE-ATE", "27/20/13/008"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "OPEN SPACE AT EWU OSI", "27/20/13/009"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "L.G. AGUNFOYE", "27/20/13/010"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "OPEN SPACE AT EWU DODO", "27/20/13/011"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "OPEN SPACE AT EGBEJODA/ARAROMI JUNCTION", "27/20/13/012"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "OPEN SPACE AT ASUNORA", "27/20/13/013"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "OPEN SPACE AT EWU BALE", "27/20/13/014"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "OPEN SPACE AT MECHANIC VILLAGE", "27/20/13/015"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "OPEN SPACE AT EWU BOUN II", "27/20/13/016"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "OPEN SPACE AT OBADORE MARKET SIMAWA", "27/20/13/017"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "COMMUNITY SQUARE IGBO-IWAJU VILLAGE SIMAWA", "27/20/13/018"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "OPEN SPACE AT COMMUNITY HALL IGBEPA", "27/20/13/019"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "OPEN SPACE @ OLOGBUN-WONPORI MARKET SIMAWA", "27/20/13/020"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "OPEN SPACE EWU OLOJA JUNCTION SIMAWA", "27/20/13/021"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "OPEN SPACE IPA/SOSO JUNCTION SIMAWA", "27/20/13/022"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "OPEN SPACE@APPLE TEE JUNCTION APELE MAKUN SAGAMU", "27/20/13/023"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "OPEN SPACE AT OJU ODUWA IGE COMMUNITY JUNCTION SAGAMU", "27/20/13/024"),
("Ogun", "Sagamu", "Simawa/Iwelepe", "OPEN SPACE AREKE COMMUNITY", "27/20/13/025"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE AT WANPONRIN COURT", "27/20/14/001"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE AT RASUSI COMPOUND", "27/20/14/002"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE AT OKE-AGBAWO NEAR AWOYEMI", "27/20/14/003"),
("Ogun", "Sagamu", "Agbowa", "ST. PAUL'S SCHOOL MAKUN", "27/20/14/004"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE AT OGURO ST. MIDWAY", "27/20/14/005"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE AT KAJOLA ST. UPPER", "27/20/14/006"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE AT AJEBO LANE", "27/20/14/007"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE AT OUR MOTHER'S PLACE", "27/20/14/008"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE IN FRONT OF SHEU TIJANI", "27/20/14/009"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE AT TIPPER'S GARAGE", "27/20/14/010"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE NEAR SAGAMU MODEL SCHOOL", "27/20/14/011"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE AT BESIDE DALOF HOTEL", "27/20/14/012"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE AT ARAROMI STREET MAKUN", "27/20/14/013"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE BEHIND SOPOIKI'S HOUSE", "27/20/14/014"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE NEAR AWOLOWO MARKET", "27/20/14/015"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE @ AJAKA SECOND ROUND ABOUT", "27/20/14/016"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE @ ODIJA SQUARE BEHIND NEPA OFFICE MAKUN, SAGAMU", "27/20/14/017"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE @IJEBU ODE MOTOR PARK, EXPRESS JUNCTION SAGAMU", "27/20/14/018"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE @ REMO POLY JUNCTION, EWU-OLIWO SAGAMU", "27/20/14/019"),
("Ogun", "Sagamu", "Agbowa", "ST PAUL SCHOOL ANGLICAN SCHOOL II MAKUN", "27/20/14/020"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE AT MULERUWA/KEKEREIFA JUNCTION AGBOWA SAGAMU", "27/20/14/021"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE @ KAJOLA JUNCTION", "27/20/14/022"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE @ ADENIJI STREET NEAR COMMUNICATION MAST", "27/20/14/023"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE AT OMOBOWALE ELESHI END POWERLINE AJAKA", "27/20/14/024"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE AT DAVID SHOMEFUN GENESIS JUNCTION EWU OLIWO", "27/20/14/025"),
("Ogun", "Sagamu", "Agbowa", "OTUNBA GBENGA DANIEL MODEL SCHOOL", "27/20/14/026"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE AT ORI-APATA EWU OLIWO", "27/20/14/027"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE EWU OLIWO WHITE HOUSE JUNCTION", "27/20/14/028"),
("Ogun", "Sagamu", "Agbowa", "OPEN SPACE END ORI APATA EWO OLIWO", "27/20/14/029"),
("Ogun", "Sagamu", "Ibido/Ituwa/Alara", "TOWN HALL I", "27/20/15/001"),
("Ogun", "Sagamu", "Ibido/Ituwa/Alara", "OPEN SPACE AT OSORIBIYA COURT", "27/20/15/002"),
("Ogun", "Sagamu", "Ibido/Ituwa/Alara", "OPEN SPACE AT AGBOWA", "27/20/15/003"),
("Ogun", "Sagamu", "Ibido/Ituwa/Alara", "OPEN SPACE AT IRAYE UPPER", "27/20/15/004"),
("Ogun", "Sagamu", "Ibido/Ituwa/Alara", "OPEN SPACE AT IRAYE LOWER", "27/20/15/005"),
("Ogun", "Sagamu", "Ibido/Ituwa/Alara", "OPEN SPACE AT ITUN ALARA", "27/20/15/006"),
("Ogun", "Sagamu", "Ibido/Ituwa/Alara", "OPEN SPACE AT IBIDO SQUARE", "27/20/15/007"),
("Ogun", "Sagamu", "Ibido/Ituwa/Alara", "TOWN HALL II", "27/20/15/008"),
("Ogun", "Sagamu", "Ibido/Ituwa/Alara", "OPEN SPACE @ ITUN-MODE JUNCTION IBIDO, SAGAMU", "27/20/15/009"),
]

# ==========================================
# DATABASE INITIALIZATION
# ==========================================
def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                election_id TEXT, election_name TEXT, lga TEXT, ward TEXT,
                polling_unit TEXT, pu_code TEXT, party_votes TEXT DEFAULT '{}',
                valid_votes INTEGER DEFAULT 0, rejected_votes INTEGER DEFAULT 0,
                total_votes_cast INTEGER DEFAULT 0, image_url TEXT,
                submitted_by TEXT, assigned_to TEXT DEFAULT '',
                timestamp DATETIME, status TEXT DEFAULT 'PENDING',
                review_notes TEXT, is_flagged INTEGER DEFAULT 0,
                flag_reason TEXT DEFAULT '', verified_by TEXT, verified_at DATETIME
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT, username TEXT UNIQUE, password_hash TEXT,
                role TEXT, assigned_lga TEXT DEFAULT '', assigned_ward TEXT DEFAULT '',
                assigned_pu_code TEXT DEFAULT '', assigned_pu_name TEXT DEFAULT '',
                email TEXT, created_by TEXT DEFAULT 'Super Admin', created_at DATETIME
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS elections (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, type TEXT,
                constituency TEXT, registered_voters INTEGER DEFAULT 1150000,
                is_active INTEGER DEFAULT 1
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parties (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, acronym TEXT UNIQUE,
                inec_code TEXT, logo_url TEXT DEFAULT '', is_active INTEGER DEFAULT 1
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT, party TEXT,
                election_name TEXT, photo_url TEXT DEFAULT '', created_at DATETIME
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                state TEXT DEFAULT 'Ogun', lga TEXT, ward TEXT,
                polling_unit TEXT, pu_code TEXT
            )
        ''')

        # Super Admin sync
        super_admin_pass = generate_password_hash("Rotimi1972")
        cursor.execute("SELECT id FROM users WHERE LOWER(username) = 'willysmediaworld'")
        existing = cursor.fetchone()
        if existing:
            cursor.execute("UPDATE users SET password_hash = ?, username = 'Willysmediaworld', role = 'Super Admin' WHERE id = ?",
                           (super_admin_pass, existing['id']))
        else:
            cursor.execute("DELETE FROM users WHERE LOWER(username) = 'superadmin'")
            cursor.execute("""INSERT INTO users (full_name, username, password_hash, role, email, created_by, created_at)
                              VALUES (?, ?, ?, ?, ?, ?, ?)""",
                           ("Oladele Rotimi Williams", "Willysmediaworld", super_admin_pass,
                            "Super Admin", "admin@electionwatch.ng", "System",
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        # Elections
        cursor.execute("SELECT COUNT(*) FROM elections")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("INSERT INTO elections (name, type, constituency, registered_voters, is_active) VALUES (?, ?, ?, ?, ?)", [
                ("Ogun East Senatorial District Election 2027", "Senatorial", "Ogun East Senatorial District", 1150000, 1),
                ("Ogun State Governorship Election 2027", "Governorship", "Ogun State", 2400000, 1),
                ("Nigeria Presidential Election 2027", "Presidential", "National", 93000000, 1),
                ("House of Representatives Election 2027", "House of Representatives", "Federal Constituency", 380000, 1),
                ("State House of Assembly Election 2027", "State House of Assembly", "State Constituency", 110000, 1),
                ("Local Government Chairmanship Election 2027", "LGA Chairman", "Ogun East LGAs", 1150000, 1),
                ("Local Government Councillorship Election 2027", "LGA Councillor", "Ogun East Wards", 1150000, 1),
            ])

        # Parties
        cursor.execute("SELECT COUNT(*) FROM parties")
        if cursor.fetchone()[0] < 19:
            cursor.execute("DELETE FROM parties")
            cursor.executemany("INSERT INTO parties (name, acronym, inec_code, logo_url, is_active) VALUES (?, ?, ?, ?, 1)", [
                ("Accord", "A", "001", ""), ("Action Alliance", "AA", "002", ""),
                ("Action Democratic Party", "ADP", "003", ""), ("Action Peoples Party", "APP", "004", ""),
                ("African Action Congress", "AAC", "005", ""), ("African Democratic Congress", "ADC", "006", ""),
                ("All Progressives Congress", "APC", "007", ""), ("All Progressives Grand Alliance", "APGA", "008", ""),
                ("Allied Peoples Movement", "APM", "009", ""), ("Boot Party", "BP", "010", ""),
                ("Labour Party", "LP", "011", ""), ("National Rescue Movement", "NRM", "012", ""),
                ("New Nigeria Peoples Party", "NNPP", "013", ""), ("Peoples Democratic Party", "PDP", "014", ""),
                ("People's Redemption Party", "PRP", "015", ""), ("Social Democratic Party", "SDP", "016", ""),
                ("Youth Party", "YP", "017", ""), ("Young Progressives Party", "YPP", "018", ""),
                ("Zenith Labour Party", "ZLP", "019", ""),
            ])

        # Locations — load only if empty or count mismatched
        cursor.execute("SELECT COUNT(*) FROM locations")
        current_count = cursor.fetchone()[0]
        if current_count != len(OGUN_EAST_LOCATIONS):
            cursor.execute("DELETE FROM locations")
            cursor.executemany("INSERT INTO locations (state, lga, ward, polling_unit, pu_code) VALUES (?, ?, ?, ?, ?)",
                               OGUN_EAST_LOCATIONS)
            print(f">>> Locations loaded: {len(OGUN_EAST_LOCATIONS)} rows")
        else:
            print(f">>> Locations already loaded: {current_count} rows")

        conn.commit()
        conn.close()
        print(">>> DATABASE INITIALIZED SUCCESSFULLY")
        print(">>> DB FILE EXISTS:", os.path.exists(DB_NAME))
    except Exception as e:
        import traceback
        print(">>> !!! DATABASE INIT FAILED !!!")
        traceback.print_exc()
        raise


init_db()


# ==========================================
# WORKFLOW HELPERS
# ==========================================
def get_assigned_verifier(submission_lga, submission_ward):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE role='Collation Admin' AND LOWER(assigned_lga)=LOWER(?) AND LOWER(assigned_ward)=LOWER(?) LIMIT 1",
                   (submission_lga, submission_ward))
    ward_admin = cursor.fetchone()
    if ward_admin:
        conn.close()
        return ward_admin['full_name']
    cursor.execute("SELECT full_name FROM users WHERE role='LGA Admin' AND LOWER(assigned_lga)=LOWER(?) LIMIT 1",
                   (submission_lga,))
    lga_admin = cursor.fetchone()
    conn.close()
    return lga_admin['full_name'] if lga_admin else "Super Admin"


def save_pending_photo_submission(data, username):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT role, assigned_lga, assigned_ward, assigned_pu_code, assigned_pu_name FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user and user['role'] == 'Field Officer':
        lga, ward = user['assigned_lga'], user['assigned_ward']
        pu_code, pu_name = user['assigned_pu_code'], user['assigned_pu_name']
    else:
        lga = data.get('lga', ''); ward = data.get('ward', '')
        pu_code = data.get('pu_code', ''); pu_name = data.get('polling_unit', '')
    assigned_admin = get_assigned_verifier(lga, ward)
    cursor.execute('''INSERT INTO submissions (election_id, election_name, lga, ward, polling_unit, pu_code,
                      image_url, submitted_by, assigned_to, timestamp, status)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')''',
                   (data.get('election_id', '1'), data.get('election_name', 'Ogun East Senatorial District Election 2027'),
                    lga, ward, pu_name, pu_code, data.get('image_url', ''), username, assigned_admin,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"EC8A Result Sheet submitted for {pu_name} ({pu_code})! Routed to [{assigned_admin}] for verification."}


def get_live_collation(election_id=None, election_type=None, filter_lga=None):
    conn = get_db()
    cursor = conn.cursor()
    registered_voters = 1150000
    if election_id and str(election_id).strip() != 'all':
        cursor.execute("SELECT name, registered_voters FROM elections WHERE id = ? OR name = ?",
                       (str(election_id), str(election_id)))
        e_row = cursor.fetchone()
        if e_row: registered_voters = e_row['registered_voters'] or 1150000
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
    if election_id and str(election_id).strip() != 'all':
        query += " AND (election_id = ? OR election_name = ?)"
        params.extend([str(election_id), str(election_id)])
    if election_type and str(election_type).strip() != 'all':
        cursor.execute("SELECT name FROM elections WHERE type = ?", (election_type,))
        matched = [r['name'] for r in cursor.fetchall()]
        if matched:
            ph = ','.join(['?'] * len(matched))
            query += f" AND election_name IN ({ph})"
            params.extend(matched)
    if filter_lga and filter_lga != 'all':
        query += " AND LOWER(lga) = LOWER(?)"
        params.append(filter_lga)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    pu_query = "SELECT COUNT(DISTINCT pu_code) FROM submissions WHERE status = 'ACCEPTED'"
    pu_params = []
    if election_id and str(election_id).strip() != 'all':
        pu_query += " AND (election_id = ? OR election_name = ?)"
        pu_params.extend([str(election_id), str(election_id)])
    if filter_lga and filter_lga != 'all':
        pu_query += " AND LOWER(lga) = LOWER(?)"
        pu_params.append(filter_lga)
    cursor.execute(pu_query, pu_params)
    verified_pus = cursor.fetchone()[0] or 0
    conn.close()
    party_totals = {p['acronym']: 0 for p in all_parties}
    grand_valid = grand_rejected = grand_total_cast = 0
    for r in rows:
        votes = json.loads(r['party_votes']) if r['party_votes'] else {}
        grand_valid += r['valid_votes']; grand_rejected += r['rejected_votes']; grand_total_cast += r['total_votes_cast']
        for party, count in votes.items():
            party_totals[party] = party_totals.get(party, 0) + int(count)
    leader = {"candidate": "Awaiting Verified Results", "party": "N/A", "votes": 0, "percentage": "0%", "photo": "", "party_logo": ""}
    if grand_valid > 0 and any(v > 0 for v in party_totals.values()):
        top_party = max(party_totals, key=party_totals.get)
        top_votes = party_totals[top_party]
        top_pct = round((top_votes / grand_valid * 100), 1)
        cand_info = candidates_map.get(top_party, {"name": "Candidate Not Assigned", "photo": ""})
        leader = {"candidate": cand_info["name"], "party": top_party, "votes": top_votes,
                  "percentage": f"{top_pct}%", "photo": cand_info["photo"],
                  "party_logo": parties_logo_map.get(top_party, "")}
    standings = []
    for party_acronym, count in party_totals.items():
        pct = round((count / grand_valid * 100), 1) if grand_valid > 0 else 0.0
        cand_info = candidates_map.get(party_acronym, {"name": "Candidate Not Assigned", "photo": ""})
        standings.append({"candidate": cand_info["name"], "party": party_acronym,
                          "party_full_name": parties_name_map.get(party_acronym, party_acronym),
                          "photo": cand_info["photo"], "party_logo": parties_logo_map.get(party_acronym, ""),
                          "votes": count, "percentage": f"{pct}%", "percent_num": pct})
    standings.sort(key=lambda x: (-x['votes'], x['party']))
    return {"leader": leader,
            "metrics": {"registered": registered_voters, "votes_cast": grand_total_cast,
                        "turnout": f"{round((grand_total_cast / registered_voters * 100), 1) if grand_total_cast > 0 else 0}%",
                        "valid": grand_valid, "rejected": grand_rejected,
                        "pus_verified": f"{verified_pus}/{total_pus_count}",
                        "progress_pct": f"{round((verified_pus / total_pus_count * 100), 1) if total_pus_count > 0 else 0}%"},
            "standings": standings}


# ==========================================
# ROUTES — STATIC + AUTH + APIs
# ==========================================
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required"}), 400
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username,))
    user = cursor.fetchone(); conn.close()
    if not user:
        return jsonify({"success": False, "message": f"User '{username}' not found"}), 401
    if not user['password_hash']:
        return jsonify({"success": False, "message": "Account has no password set"}), 401
    if not check_password_hash(user['password_hash'], password):
        return jsonify({"success": False, "message": "Incorrect password"}), 401
    session['user_id'] = user['id']; session['username'] = user['username']; session.permanent = True
    return jsonify({"success": True, "username": user['username'], "full_name": user['full_name'],
                    "role": user['role'], "assigned_lga": user['assigned_lga'] or '',
                    "assigned_ward": user['assigned_ward'] or '',
                    "assigned_pu_code": user['assigned_pu_code'] or '',
                    "assigned_pu_name": user['assigned_pu_name'] or ''})


@app.route('/api/upload-photo-result', methods=['POST'])
def upload_photo_result():
    submitted_by = request.form.get("submitted_by", "")
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username = ?", (submitted_by,))
    user = cursor.fetchone(); conn.close()
    if user and user['role'] == 'Collation Admin':
        return jsonify({"status": "error", "message": "Collation Admins are restricted to verification only."}), 403
    if 'photo' not in request.files:
        return jsonify({"status": "error", "message": "No photograph attached"}), 400
    file = request.files['photo']
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        data = {"election_id": request.form.get("election_id", "1"),
                "election_name": request.form.get("election_name", "Ogun East Senatorial District Election 2027"),
                "lga": request.form.get("lga", ""), "ward": request.form.get("ward", ""),
                "polling_unit": request.form.get("polling_unit", ""), "pu_code": request.form.get("pu_code", ""),
                "image_url": f"/uploads/{filename}"}
        return jsonify(save_pending_photo_submission(data, submitted_by))
    return jsonify({"status": "error", "message": "Invalid file format"}), 400


@app.route('/api/review-queue', methods=['GET'])
def review_queue():
    username = request.args.get('username', '')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT role, assigned_lga, assigned_ward FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if not user: conn.close(); return jsonify([])
    role, lga, ward = user['role'], user['assigned_lga'], user['assigned_ward']
    if role == 'Super Admin':
        cursor.execute("SELECT * FROM submissions WHERE status = 'PENDING' ORDER BY id DESC")
    elif role == 'LGA Admin':
        cursor.execute("SELECT * FROM submissions WHERE status = 'PENDING' AND LOWER(lga) = LOWER(?) ORDER BY id DESC", (lga,))
    elif role == 'Collation Admin':
        cursor.execute("SELECT * FROM submissions WHERE status = 'PENDING' AND LOWER(lga) = LOWER(?) AND LOWER(ward) = LOWER(?) ORDER BY id DESC", (lga, ward))
    else:
        cursor.execute("SELECT * FROM submissions WHERE 1=0")
    rows = [dict(r) for r in cursor.fetchall()]; conn.close()
    return jsonify(rows)


@app.route('/api/admin-verify-collate', methods=['POST'])
def admin_verify_collate_route():
    d = request.json
    conn = get_db(); cursor = conn.cursor()
    valid = sum(int(v) for v in d.get('party_votes', {}).values())
    total = valid + int(d.get('rejected_votes', 0))
    cursor.execute('''UPDATE submissions SET party_votes=?, valid_votes=?, rejected_votes=?, total_votes_cast=?,
                      status=?, review_notes=?, is_flagged=?, flag_reason=?, verified_by=?, verified_at=? WHERE id=?''',
                   (json.dumps(d.get('party_votes', {})), valid, int(d.get('rejected_votes', 0)), total,
                    d.get('status', 'ACCEPTED'), d.get('notes', ''), 1 if d.get('is_flagged') else 0,
                    d.get('flag_reason', ''), d.get('verified_by', 'Admin'),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"), d.get('submission_id')))
    conn.commit(); conn.close()
    return jsonify({"status": "success", "message": f"Submission #{d.get('submission_id')} processed!"})


@app.route('/api/live-results', methods=['GET'])
def live_results():
    return jsonify(get_live_collation(request.args.get('election_id', 'all'),
                                      request.args.get('election_type', 'all'),
                                      request.args.get('lga', '')))


@app.route('/api/ward-results', methods=['GET'])
def ward_results():
    filter_lga = request.args.get('lga', '')
    election_type = request.args.get('election_type', '')
    conn = get_db(); cursor = conn.cursor()
    query = "SELECT * FROM submissions WHERE status = 'ACCEPTED'"
    params = []
    if filter_lga and filter_lga != 'all':
        query += " AND LOWER(lga) = LOWER(?)"; params.append(filter_lga)
    if election_type and election_type != 'all':
        cursor.execute("SELECT name FROM elections WHERE type = ?", (election_type,))
        matched = [r['name'] for r in cursor.fetchall()]
        if matched:
            ph = ','.join(['?'] * len(matched))
            query += f" AND election_name IN ({ph})"; params.extend(matched)
    query += " ORDER BY lga, ward, polling_unit"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT acronym FROM parties ORDER BY acronym ASC")
    all_parties = [p['acronym'] for p in cursor.fetchall()]; conn.close()
    for r in rows:
        r['party_votes'] = json.loads(r['party_votes']) if r['party_votes'] else {}
    return jsonify({"rows": rows, "parties": all_parties})


@app.route('/api/export-csv', methods=['GET'])
def export_csv():
    filter_lga = request.args.get('lga', '')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT acronym FROM parties ORDER BY acronym ASC")
    all_parties = [p['acronym'] for p in cursor.fetchall()]
    if filter_lga and filter_lga != 'all':
        cursor.execute("SELECT * FROM submissions WHERE status='ACCEPTED' AND LOWER(lga)=LOWER(?)", (filter_lga,))
    else:
        cursor.execute("SELECT * FROM submissions WHERE status='ACCEPTED'")
    rows = cursor.fetchall(); conn.close()
    output = io.StringIO(); writer = csv.writer(output)
    writer.writerow(['Submission ID', 'Election Name', 'LGA', 'Ward', 'Polling Unit', 'PU Code'] + all_parties + ['Valid Votes', 'Rejected Votes', 'Total Cast', 'Verified By', 'Timestamp'])
    for r in rows:
        pv = json.loads(r['party_votes']) if r['party_votes'] else {}
        writer.writerow([r['id'], r['election_name'], r['lga'], r['ward'], r['polling_unit'], r['pu_code']] +
                        [pv.get(p, 0) for p in all_parties] +
                        [r['valid_votes'], r['rejected_votes'], r['total_votes_cast'], r['verified_by'], r['verified_at']])
    output.seek(0)
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-disposition": "attachment; filename=Ogun_East_2027_Full_Results.csv"})


@app.route('/api/admin/users', methods=['GET', 'POST'])
def handle_users():
    conn = get_db(); cursor = conn.cursor()
    if request.method == 'POST':
        d = request.json
        creator = d.get('created_by_user', 'Super Admin')
        role = d.get('role')
        cursor.execute("SELECT role FROM users WHERE username = ?", (creator,))
        cu = cursor.fetchone()
        if cu:
            if cu['role'] == 'Super Admin' and role not in ['LGA Admin', 'Viewer']:
                conn.close(); return jsonify({"success": False, "message": "Super Admin can only create LGA Admin or Viewer."}), 403
            elif cu['role'] == 'LGA Admin' and role not in ['Collation Admin', 'Field Officer', 'Viewer']:
                conn.close(); return jsonify({"success": False, "message": "LGA Admin can only create Collation Admin, Field Officer, or Viewer."}), 403
        try:
            cursor.execute("""INSERT INTO users (full_name, username, password_hash, role, assigned_lga, assigned_ward,
                              assigned_pu_code, assigned_pu_name, email, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                           (d.get('full_name'), d.get('username'), generate_password_hash(d.get('password', 'Pass1234!')),
                            role, d.get('assigned_lga', ''), d.get('assigned_ward', ''),
                            d.get('assigned_pu_code', ''), d.get('assigned_pu_name', ''),
                            d.get('email'), creator, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit(); conn.close()
            return jsonify({"success": True, "message": f"Account '{d.get('username')}' ({role}) created successfully!"})
        except sqlite3.IntegrityError:
            conn.close(); return jsonify({"success": False, "message": f"Username '{d.get('username')}' already exists."}), 400
    requester = request.args.get('username', '')
    cursor.execute("SELECT role, assigned_lga FROM users WHERE username = ?", (requester,))
    user = cursor.fetchone()
    if user and user['role'] == 'LGA Admin':
        cursor.execute("SELECT id, full_name, username, role, assigned_lga, assigned_ward, assigned_pu_code, email FROM users WHERE LOWER(assigned_lga)=LOWER(?) ORDER BY id DESC", (user['assigned_lga'],))
    else:
        cursor.execute("SELECT id, full_name, username, role, assigned_lga, assigned_ward, assigned_pu_code, email FROM users ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]; conn.close()
    return jsonify(rows)


@app.route('/api/admin/elections', methods=['GET', 'POST'])
def handle_elections():
    conn = get_db(); cursor = conn.cursor()
    if request.method == 'POST':
        d = request.json
        cursor.execute("INSERT INTO elections (name, type, constituency, registered_voters, is_active) VALUES (?, ?, ?, ?, 1)",
                       (d.get('name'), d.get('type'), d.get('constituency'), d.get('registered_voters', 1150000)))
        conn.commit(); conn.close()
        return jsonify({"success": True, "message": "Election Created!"})
    only_active = request.args.get('active_only', '0')
    if only_active == '1':
        cursor.execute("SELECT * FROM elections WHERE is_active=1 ORDER BY id ASC")
    else:
        cursor.execute("SELECT * FROM elections ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]; conn.close()
    return jsonify(rows)


@app.route('/api/admin/toggle-election', methods=['POST'])
def toggle_election():
    d = request.json
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("UPDATE elections SET is_active=? WHERE id=?", (d.get('is_active', 1), d.get('id')))
    conn.commit(); conn.close()
    return jsonify({"success": True, "message": "Election status updated!"})


@app.route('/api/admin/parties', methods=['GET'])
def handle_parties():
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM parties ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]; conn.close()
    return jsonify(rows)


@app.route('/api/admin/candidates', methods=['GET', 'POST'])
def handle_candidates():
    conn = get_db(); cursor = conn.cursor()
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        party = request.form.get('party', '').strip()
        election_name = request.form.get('election_name', '').strip()
        photo_url = ''
        if 'photo' in request.files and request.files['photo'].filename != '':
            file = request.files['photo']
            if allowed_file(file.filename):
                filename = secure_filename(f"cand_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath); photo_url = f"/uploads/{filename}"
        cursor.execute("SELECT id FROM candidates WHERE party=? AND election_name=?", (party, election_name))
        existing = cursor.fetchone()
        if existing:
            if photo_url:
                cursor.execute("UPDATE candidates SET full_name=?, photo_url=?, created_at=? WHERE id=?",
                               (full_name, photo_url, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), existing['id']))
            else:
                cursor.execute("UPDATE candidates SET full_name=?, created_at=? WHERE id=?",
                               (full_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), existing['id']))
        else:
            cursor.execute("INSERT INTO candidates (full_name, party, election_name, photo_url, created_at) VALUES (?, ?, ?, ?, ?)",
                           (full_name, party, election_name, photo_url, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit(); conn.close()
        return jsonify({"success": True, "message": f"Candidate '{full_name}' ({party}) updated!"})
    cursor.execute("SELECT * FROM candidates ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]; conn.close()
    return jsonify(rows)


@app.route('/api/admin/reset-system', methods=['POST'])
def reset_system():
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("DELETE FROM submissions")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='submissions'")
    conn.commit(); conn.close()
    return jsonify({"success": True, "message": "System Reset Complete!"})


# ==========================================
# WARD/PU EDITOR APIs (Super Admin Only)
# ==========================================
@app.route('/api/admin/locations/tree', methods=['GET'])
def locations_tree():
    """Returns full LGA → Ward → PU tree for the editor."""
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT id, lga, ward, polling_unit, pu_code FROM locations ORDER BY lga, ward, id")
    rows = cursor.fetchall(); conn.close()
    tree = {}
    for r in rows:
        lga = r['lga']; ward = r['ward']
        if lga not in tree: tree[lga] = {}
        if ward not in tree[lga]: tree[lga][ward] = []
        tree[lga][ward].append({"id": r['id'], "polling_unit": r['polling_unit'], "pu_code": r['pu_code']})
    return jsonify(tree)


@app.route('/api/admin/locations/update-pu', methods=['POST'])
def update_pu():
    d = request.json
    pu_id = d.get('id')
    new_name = d.get('polling_unit', '').strip()
    new_code = d.get('pu_code', '').strip()
    if not pu_id or not new_name or not new_code:
        return jsonify({"success": False, "message": "ID, name, and code are required."}), 400
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("UPDATE locations SET polling_unit=?, pu_code=? WHERE id=?", (new_name, new_code, pu_id))
    conn.commit(); conn.close()
    return jsonify({"success": True, "message": f"Polling Unit updated successfully."})


@app.route('/api/admin/locations/delete-pu', methods=['POST'])
def delete_pu():
    d = request.json
    pu_id = d.get('id')
    if not pu_id:
        return jsonify({"success": False, "message": "ID required."}), 400
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("DELETE FROM locations WHERE id=?", (pu_id,))
    conn.commit(); conn.close()
    return jsonify({"success": True, "message": f"Polling Unit deleted."})


@app.route('/api/admin/locations/rename-ward', methods=['POST'])
def rename_ward():
    d = request.json
    lga = d.get('lga', '').strip()
    old_ward = d.get('old_ward', '').strip()
    new_ward = d.get('new_ward', '').strip()
    if not (lga and old_ward and new_ward):
        return jsonify({"success": False, "message": "LGA, old ward, and new ward are required."}), 400
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("UPDATE locations SET ward=? WHERE LOWER(lga)=LOWER(?) AND LOWER(ward)=LOWER(?)",
                   (new_ward, lga, old_ward))
    affected = cursor.rowcount
    conn.commit(); conn.close()
    return jsonify({"success": True, "message": f"Ward renamed. {affected} polling units updated."})


@app.route('/api/admin/locations/delete-ward', methods=['POST'])
def delete_ward():
    d = request.json
    lga = d.get('lga', '').strip()
    ward = d.get('ward', '').strip()
    if not (lga and ward):
        return jsonify({"success": False, "message": "LGA and ward required."}), 400
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM locations WHERE LOWER(lga)=LOWER(?) AND LOWER(ward)=LOWER(?)",
                   (lga, ward))
    count = cursor.fetchone()[0]
    cursor.execute("DELETE FROM locations WHERE LOWER(lga)=LOWER(?) AND LOWER(ward)=LOWER(?)", (lga, ward))
    conn.commit(); conn.close()
    return jsonify({"success": True, "message": f"Ward '{ward}' deleted with {count} polling units."})


@app.route('/api/admin/locations/add-pu', methods=['POST'])
def add_pu():
    d = request.json
    lga = d.get('lga', '').strip()
    ward = d.get('ward', '').strip()
    pu_name = d.get('polling_unit', '').strip()
    pu_code = d.get('pu_code', '').strip()
    if not (lga and ward and pu_name and pu_code):
        return jsonify({"success": False, "message": "All fields required."}), 400
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT id FROM locations WHERE pu_code=?", (pu_code,))
    if cursor.fetchone():
        conn.close(); return jsonify({"success": False, "message": f"PU code '{pu_code}' already exists."}), 400
    cursor.execute("INSERT INTO locations (state, lga, ward, polling_unit, pu_code) VALUES ('Ogun', ?, ?, ?, ?)",
                   (lga, ward, pu_name, pu_code))
    conn.commit(); conn.close()
    return jsonify({"success": True, "message": f"New Polling Unit added to {ward}."})


@app.route('/api/locations/lgas', methods=['GET'])
def get_lgas():
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT lga FROM locations ORDER BY lga ASC")
    lgas = [r['lga'] for r in cursor.fetchall()]; conn.close()
    return jsonify(lgas)


@app.route('/api/locations/wards', methods=['GET'])
def get_wards():
    lga = request.args.get('lga', '')
    conn = get_db(); cursor = conn.cursor()
    if lga:
        cursor.execute("SELECT DISTINCT ward FROM locations WHERE LOWER(lga)=LOWER(?) ORDER BY ward ASC", (lga,))
    else:
        cursor.execute("SELECT DISTINCT ward FROM locations ORDER BY ward ASC")
    wards = [r['ward'] for r in cursor.fetchall()]; conn.close()
    return jsonify(wards)


@app.route('/api/locations/pus', methods=['GET'])
def get_pus():
    ward = request.args.get('ward', '')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT id, polling_unit, pu_code FROM locations WHERE LOWER(ward)=LOWER(?) ORDER BY id ASC", (ward,))
    pus = [dict(r) for r in cursor.fetchall()]; conn.close()
    return jsonify(pus)


# ==========================================
HTML_TEMPLATE = r"""
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
.auth-subtitle { color: #2563eb; font-size: 13px; font-weight: 700; margin-bottom: 25px; }
.auth-form { width: 100%; text-align: left; }
.input-group { margin-bottom: 16px; }
.input-group label { display: block; font-size: 13px; font-weight: 700; color: #1a1a1a; margin-bottom: 6px; }
.input-group input, .input-group select { width: 100%; padding: 12px 14px; font-size: 14px; border: 1.5px solid #d1d5db; border-radius: 8px; outline: none; background: #fff; }
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
.section-heading { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; color: #0c235c; flex-wrap: wrap; gap: 8px; }
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
.progress-fill { height: 100%; background-color: #0c235c; transition: width 0.3s; }
.party-counter-grid { display: flex; flex-direction: column; gap: 10px; margin-top: 10px; }
.party-card { background-color: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid #0c235c; border-radius: 10px; padding: 12px 14px; }
.party-info { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.party-bar-bg { width: 100%; height: 6px; background-color: #f1f5f9; border-radius: 4px; margin-top: 8px; overflow: hidden; }
.party-bar-fill { height: 100%; background-color: #2563eb; transition: width 0.3s; }
.table-responsive { overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 10px; margin-bottom: 20px; }
.results-table { width: 100%; border-collapse: collapse; font-size: 11.5px; text-align: left; }
.results-table th, .results-table td { padding: 8px 6px; border-bottom: 1px solid #e2e8f0; white-space: nowrap; }
.results-table th { background-color: #0c235c; color: #ffffff; font-weight: 800; text-align: center; }
.results-table td { text-align: center; }
.wizard-step { display: none; }
.wizard-step.active { display: block; }
.btn-stack { display: flex; flex-direction: column; gap: 10px; }
.btn-select-option { width: 100%; background-color: #0c235c; color: #ffffff; border: none; padding: 14px; border-radius: 10px; font-size: 14px; font-weight: 700; cursor: pointer; text-align: left; }
.btn-secondary { width: 100%; background-color: #64748b; color: #ffffff; border: none; padding: 12px; border-radius: 10px; font-size: 14px; font-weight: 700; cursor: pointer; }
.btn-action { width: 100%; background-color: #0c235c; color: #ffffff; border: none; padding: 12px; border-radius: 10px; font-weight: 700; cursor: pointer; }
.btn-danger { background-color: #dc2626 !important; }
.btn-success { background-color: #16a34a !important; }
.input-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #e2e8f0; }
.input-row input { width: 100px; padding: 6px 10px; border: 1px solid #ccc; border-radius: 6px; text-align: right; font-weight: 700; }
.app-footer { text-align: center; margin-top: 30px; padding: 15px 0; font-size: 11.5px; color: #64748b; line-height: 1.5; border-top: 1px solid #e2e8f0; }
.bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; height: 60px; background-color: #ffffff; border-top: 1px solid #e2e8f0; display: flex; justify-content: space-around; align-items: center; z-index: 100; }
.nav-item { background: none; border: none; display: flex; flex-direction: column; align-items: center; color: #64748b; cursor: pointer; flex: 1; padding: 8px 0; font-weight: 600; font-size: 11px; }
.nav-item.active { color: #0c235c; background-color: #eff6ff; font-weight: 800; }
.modal-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; justify-content: center; align-items: center; padding: 16px; overflow-y: auto; }
.modal-overlay.active { display: flex; }
.modal-card { background: #ffffff; border-radius: 16px; width: 100%; max-width: 460px; max-height: 90vh; overflow-y: auto; padding: 18px; }
.modal-card h3 { margin-bottom: 12px; color: #0c235c; }
.tree-lga { background: #0c235c; color: #fff; padding: 10px 12px; border-radius: 8px; margin-top: 10px; font-weight: 800; font-size: 13px; cursor: pointer; display: flex; justify-content: space-between; }
.tree-ward { background: #eff6ff; color: #0c235c; padding: 8px 12px; border-radius: 6px; margin: 6px 0 0 12px; font-weight: 700; font-size: 12.5px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; border-left: 3px solid #2563eb; }
.tree-pu { background: #f8fafc; padding: 8px 12px; margin: 4px 0 0 24px; border-radius: 6px; font-size: 11.5px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #e2e8f0; }
.tree-pu-code { color: #2563eb; font-weight: 700; font-size: 10.5px; }
.tree-actions { display: flex; gap: 6px; }
.mini-btn { padding: 4px 8px; font-size: 10.5px; border-radius: 5px; border: none; cursor: pointer; font-weight: 700; }
.mini-btn-edit { background: #2563eb; color: #fff; }
.mini-btn-del { background: #dc2626; color: #fff; }
.mini-btn-add { background: #16a34a; color: #fff; }
.count-badge { background: rgba(255,255,255,0.25); padding: 2px 6px; border-radius: 10px; font-size: 10px; }
</style>
</head>
<body>

<!-- ========== AUTH PAGE (PUBLIC ACCESS REMOVED) ========== -->
<div id="authPage" class="page active">
  <div class="auth-container">
    <h1 class="auth-title">OGUN EAST 2027</h1>
    <p class="auth-subtitle">Official Election Collation Portal</p>
    <form id="loginForm" class="auth-form">
      <div class="input-group">
        <label>Username Account ID</label>
        <input type="text" id="username" placeholder="Enter Account Username" required autocomplete="username">
      </div>
      <div class="input-group">
        <label>Password</label>
        <input type="password" id="password" placeholder="Enter Password" required autocomplete="current-password">
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

<!-- ========== DASHBOARD ========== -->
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
    <!-- TAB LIVE -->
    <section id="tab-live" class="tab-content active">
      <div class="section-heading"><h2>📊 Live District Collation</h2></div>
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-bottom:12px;">
        <div class="input-group" style="margin:0;">
          <label>Election Category</label>
          <select id="liveTypeSelect" onchange="onLiveFilterChanged()">
            <option value="all">-- All Categories --</option>
            <option value="Presidential">Presidential</option>
            <option value="Senatorial">Senatorial</option>
            <option value="House of Representatives">House of Reps</option>
            <option value="Governorship">Governorship</option>
            <option value="State House of Assembly">State Assembly</option>
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

    <!-- TAB RESULTS -->
    <section id="tab-results" class="tab-content">
      <div class="section-heading">
        <h2>📋 Ward Breakdown & Full Table</h2>
        <button class="btn-submit" style="width:auto; padding:6px 12px; font-size:12px; background:#16a34a;" onclick="exportResultsCSV()">📄 Export CSV</button>
      </div>
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-bottom:12px;">
        <div class="input-group" style="margin:0;">
          <label>Election Category</label>
          <select id="resultsTypeSelect" onchange="loadWardTable()">
            <option value="all">-- All Categories --</option>
            <option value="Presidential">Presidential</option>
            <option value="Senatorial">Senatorial</option>
            <option value="House of Representatives">House of Reps</option>
            <option value="Governorship">Governorship</option>
            <option value="State House of Assembly">State Assembly</option>
            <option value="LGA Chairman">LGA Chairman</option>
            <option value="LGA Councillor">LGA Councillor</option>
          </select>
        </div>
        <div class="input-group" style="margin:0;">
          <label>Local Government (LGA)</label>
          <select id="resultsLgaSelect" onchange="loadWardTable()"></select>
        </div>
      </div>
      <div class="table-responsive">
        <table class="results-table">
          <thead id="resultsTableHead"></thead>
          <tbody id="resultsTableBody">
            <tr><td colspan="25" style="text-align:center;">No collated results yet.</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- TAB UPLOAD -->
    <section id="tab-upload" class="tab-content">
      <div class="section-heading"><h2>📥 Submit Result Sheet (EC8A)</h2></div>
      <div id="collationAdminDisabledBox" style="display:none; background:#fef2f2; border:2px solid #ef4444; padding:16px; border-radius:12px; margin-bottom:15px; text-align:center;">
        <h3 style="color:#991b1b; font-size:15px;">🚫 Upload Restricted</h3>
        <p style="font-size:13px; color:#7f1d1d; margin-top:4px;">As a Collation Admin, your role is strictly for reviewing and collating incoming results. Switch to the <strong>Review Tab</strong> to process submitted result sheets.</p>
      </div>
      <div id="fieldOfficerLockedBox" style="display:none; background:#eff6ff; border:2px solid #2563eb; padding:16px; border-radius:12px; margin-bottom:15px;">
        <h3 style="color:#1e40af; font-size:15px; margin-bottom:6px;">🔒 Your Pre-Assigned Polling Unit</h3>
        <p style="font-size:13px; color:#1e3a8a;" id="fieldLockLgaWard"></p>
        <p style="font-size:15px; font-weight:900; color:#0c235c; margin-top:4px;" id="fieldLockPuName"></p>
        <p style="font-size:12px; font-weight:700; color:#2563eb;" id="fieldLockPuCode"></p>
      </div>
      <div id="uploadWizardContainer">
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
          <h3 style="margin-bottom:12px; color:#0c235c;">4. Select Polling Unit / Booth</h3>
          <div class="btn-stack" id="pusListStack"></div>
          <button class="btn-secondary" style="margin-top:10px;" onclick="goToUploadStep(3)">← Back</button>
        </div>
        <div id="uploadStep5" class="wizard-step">
          <h3 style="margin-bottom:12px; color:#0c235c;">5. Capture / Attach EC8A Photo</h3>
          <div style="background:#1d3557; color:#fff; padding:14px; border-radius:10px; margin-bottom:15px;">
            <h4 id="summaryElection">Ogun East Senatorial Election</h4>
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

    <!-- TAB REVIEW -->
    <section id="tab-review" class="tab-content">
      <div class="section-heading"><h2 id="reviewTabTitle">🔍 Verification Queue</h2></div>
      <div class="info-box" id="reviewScopeBanner"></div>
      <div id="reviewQueueList"></div>
    </section>

    <!-- TAB ADMIN -->
    <section id="tab-admin" class="tab-content">
      <div class="section-heading"><h2>⚙️ Staff & Account Administration</h2></div>

      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:8px; margin-bottom:15px;">
        <button class="btn-select-option" style="text-align:center;" onclick="openAdminModal('user')">👤 Create Account</button>
        <button class="btn-select-option" style="text-align:center; background:#16a34a;" onclick="copyViewerPortalLink()">📋 Copy Portal Link</button>
        <button class="btn-select-option" style="text-align:center;" onclick="openAdminModal('candidate')">👥 Candidates Setup</button>
        <button class="btn-select-option" style="text-align:center;" onclick="loadAdminData('users')">📜 Staff Registry</button>
        <button class="btn-select-option" id="wardPuEditorBtn" style="text-align:center; background:#7c3aed;" onclick="openWardPUEditor()">🗂️ Ward/PU Editor</button>
        <button class="btn-select-option" style="text-align:center; background:#0891b2;" onclick="openAddPuModal()">➕ Add Polling Unit</button>
      </div>

      <div id="superAdminElectionsBox" style="margin-bottom:15px;">
        <h3 style="color:#0c235c; margin-bottom:8px;">📦 Active Elections Control</h3>
        <div id="electionsToggleList" class="party-counter-grid"></div>
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

<!-- ========== MODALS ========== -->

<!-- User Modal -->
<div id="adminUserModal" class="modal-overlay">
  <div class="modal-card">
    <h3>👤 Create Account</h3>
    <div class="input-group"><label>Full Name</label><input type="text" id="adminUserFullName" placeholder="e.g. Chief Adebayo"></div>
    <div class="input-group"><label>Username Account ID</label><input type="text" id="adminUsername" placeholder="e.g. adebayo_ijebu"></div>
    <div class="input-group"><label>Account Password</label><input type="password" id="adminUserPassword" placeholder="Set Password"></div>
    <div class="input-group">
      <label>User Role</label>
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
      <label>Assign Polling Unit / Booth</label>
      <select id="adminUserPu"></select>
    </div>
    <div class="input-group"><label>Email Address</label><input type="email" id="adminUserEmail" placeholder="user@domain.com"></div>
    <button class="btn-submit btn-success" onclick="submitCreateUser()">Save Scoped Account</button>
    <button class="btn-secondary" style="margin-top:8px;" onclick="closeAdminModals()">Cancel</button>
  </div>
</div>

<!-- Candidate Modal -->
<div id="adminCandidateModal" class="modal-overlay">
  <div class="modal-card">
    <h3>👥 Add / Update Candidate</h3>
    <div class="input-group"><label>Candidate Full Name</label><input type="text" id="adminCandName" placeholder="Enter Full Name"></div>
    <div class="input-group"><label>Political Party</label><select id="adminCandParty"></select></div>
    <div class="input-group"><label>Election Category</label><select id="adminCandElection"></select></div>
    <div class="input-group"><label>Candidate Photograph</label><input type="file" id="adminCandPhoto" accept="image/*"></div>
    <button class="btn-submit btn-success" onclick="submitCreateCandidate()">Save Candidate Record</button>
    <button class="btn-secondary" style="margin-top:8px;" onclick="closeAdminModals()">Cancel</button>
  </div>
</div>

<!-- Review Modal -->
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
      <button class="btn-submit btn-success" style="flex:1;" onclick="submitManualCollation('ACCEPTED')">✓ Accept & Collate</button>
      <button class="btn-submit btn-danger" style="flex:1;" onclick="submitManualCollation('REJECTED')">✕ Reject</button>
    </div>
    <button class="btn-secondary" style="margin-top:8px;" onclick="closeReviewModal()">Close</button>
  </div>
</div>

<!-- WARD/PU EDITOR MODAL -->
<div id="wardPUEditorModal" class="modal-overlay">
  <div class="modal-card" style="max-width: 520px;">
    <h3>🗂️ Ward & Polling Unit Editor</h3>
    <div class="info-box" style="margin-top:0;">
      🌐 Super Admin only. Tap any LGA to expand, then tap a Ward to see its Polling Units. Use <b>Edit</b> to rename a PU/code, <b>Delete</b> to remove, or <b>Rename</b> on a Ward to change its name.
    </div>
    <div style="display:flex; gap:6px; margin-bottom:10px;">
      <input type="text" id="puSearchBox" placeholder="🔍 Search PU name or code..." style="flex:1; padding:10px; border:1.5px solid #d1d5db; border-radius:8px; font-size:13px;" oninput="filterWardPUTree()">
      <button class="mini-btn mini-btn-add" style="padding:10px 14px;" onclick="refreshWardPUTree()">↻</button>
    </div>
    <div id="wardPUTreeContainer" style="max-height: 60vh; overflow-y: auto;"></div>
    <button class="btn-secondary" style="margin-top:12px;" onclick="closeWardPUEditor()">Close</button>
  </div>
</div>

<!-- EDIT PU MODAL -->
<div id="editPuModal" class="modal-overlay">
  <div class="modal-card" style="max-width:420px;">
    <h3>✏️ Edit Polling Unit</h3>
    <input type="hidden" id="editPuId">
    <div class="input-group"><label>Polling Unit Name</label><input type="text" id="editPuName"></div>
    <div class="input-group"><label>PU Code</label><input type="text" id="editPuCode"></div>
    <div style="background:#fef3c7; padding:8px; border-radius:6px; margin-bottom:10px; font-size:11.5px; color:#92400e;">
      ⚠️ Changing the PU code will not affect existing submissions — they keep their original code.
    </div>
    <button class="btn-submit btn-success" onclick="savePuEdit()">Save Changes</button>
    <button class="btn-secondary" style="margin-top:8px;" onclick="document.getElementById('editPuModal').classList.remove('active')">Cancel</button>
  </div>
</div>

<!-- RENAME WARD MODAL -->
<div id="renameWardModal" class="modal-overlay">
  <div class="modal-card" style="max-width:420px;">
    <h3>✏️ Rename Ward</h3>
    <input type="hidden" id="renameWardLga">
    <input type="hidden" id="renameWardOld">
    <div class="input-group"><label>LGA</label><input type="text" id="renameWardLgaDisplay" disabled></div>
    <div class="input-group"><label>Current Ward Name</label><input type="text" id="renameWardOldDisplay" disabled></div>
    <div class="input-group"><label>New Ward Name</label><input type="text" id="renameWardNew" placeholder="Enter new ward name"></div>
    <button class="btn-submit btn-success" onclick="saveWardRename()">Save Rename</button>
    <button class="btn-submit btn-danger" style="margin-top:8px;" onclick="confirmDeleteWard()">🗑️ Delete Whole Ward</button>
    <button class="btn-secondary" style="margin-top:8px;" onclick="document.getElementById('renameWardModal').classList.remove('active')">Cancel</button>
  </div>
</div>

<!-- ADD PU MODAL -->
<div id="addPuModal" class="modal-overlay">
  <div class="modal-card" style="max-width:420px;">
    <h3>➕ Add New Polling Unit</h3>
    <div class="input-group">
      <label>LGA</label>
      <select id="addPuLga" onchange="onAddPuLgaChanged()"></select>
    </div>
    <div class="input-group">
      <label>Ward</label>
      <select id="addPuWard"></select>
    </div>
    <div class="input-group"><label>Polling Unit Name</label><input type="text" id="addPuName" placeholder="e.g. ST. MARY PRY SCHOOL"></div>
    <div class="input-group"><label>PU Code</label><input type="text" id="addPuCode" placeholder="e.g. 27/08/01/013"></div>
    <button class="btn-submit btn-success" onclick="saveNewPu()">Save New Polling Unit</button>
    <button class="btn-secondary" style="margin-top:8px;" onclick="document.getElementById('addPuModal').classList.remove('active')">Cancel</button>
  </div>
</div>

<script>

let currentUploadData = { lga: '', election_name: '', election_id: '1', ward: '', polling_unit: '', pu_code: '' };
let activeModalSubmissionId = null;
let selectedPhotoFile = null;
let currentUser = { username: '', full_name: '', role: 'Viewer', assigned_lga: '', assigned_ward: '', assigned_pu_code: '', assigned_pu_name: '' };
let wardPUTreeCache = null;

document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const u = document.getElementById('username').value.trim();
      const p = document.getElementById('password').value;
      if (!u || !p) { alert("Please enter username and password."); return; }
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
      })
      .catch(err => alert("Network error: " + err));
    });
  }

  document.getElementById('logoutBtn').addEventListener('click', () => {
    currentUser = { username: '', full_name: '', role: 'Viewer', assigned_lga: '', assigned_ward: '', assigned_pu_code: '', assigned_pu_name: '' };
    document.getElementById('dashboardPage').classList.remove('active');
    document.getElementById('authPage').classList.add('active');
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
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
      if (tab === 'admin') loadAdminTabContent();
    });
  });
});

/* =============================================
   ROLE PERMISSIONS
   ============================================= */
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
  const btnWardPU = document.getElementById('wardPuEditorBtn');
  const btnAddPu = document.querySelector('button[onclick="openAddPuModal()"]');

  btnUpload.style.display = 'none';
  btnReview.style.display = 'none';
  btnAdmin.style.display = 'none';

  if (currentUser.role === 'Super Admin') {
    btnUpload.style.display = 'flex';
    btnReview.style.display = 'flex';
    btnAdmin.style.display = 'flex';
    document.getElementById('superAdminResetBox').style.display = 'block';
    document.getElementById('superAdminElectionsBox').style.display = 'block';
    if (btnWardPU) btnWardPU.style.display = 'block';
    if (btnAddPu) btnAddPu.style.display = 'block';
  } else if (currentUser.role === 'LGA Admin') {
    btnUpload.style.display = 'flex';
    btnReview.style.display = 'flex';
    btnAdmin.style.display = 'flex';
    document.getElementById('superAdminResetBox').style.display = 'none';
    document.getElementById('superAdminElectionsBox').style.display = 'none';
    if (btnWardPU) btnWardPU.style.display = 'none';
    if (btnAddPu) btnAddPu.style.display = 'none';
  } else if (currentUser.role === 'Collation Admin') {
    btnReview.style.display = 'flex';
  } else if (currentUser.role === 'Field Officer') {
    btnUpload.style.display = 'flex';
  }
}

/* =============================================
   DROPDOWNS
   ============================================= */
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

function copyViewerPortalLink() {
  const link = window.location.origin;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(link).then(() => alert("📋 Portal link copied:\n" + link))
      .catch(() => alert("Portal link: " + link));
  } else {
    alert("Portal link: " + link);
  }
}

/* =============================================
   LIVE RESULTS
   ============================================= */
function onLiveFilterChanged() { loadLiveResults(); }

function loadLiveResults() {
  const selectedType = document.getElementById('liveTypeSelect').value || 'all';
  const selectedLga = document.getElementById('liveLgaSelect').value || 'all';
  fetch(`/api/live-results?election_type=${encodeURIComponent(selectedType)}&lga=${encodeURIComponent(selectedLga)}`)
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
    })
    .catch(err => console.error("Live results error:", err));
}

/* =============================================
   WARD TABLE
   ============================================= */
function loadWardTable() {
  const selectedLga = document.getElementById('resultsLgaSelect').value || 'all';
  const selectedType = document.getElementById('resultsTypeSelect').value || 'all';
  fetch(`/api/ward-results?lga=${encodeURIComponent(selectedLga)}&election_type=${encodeURIComponent(selectedType)}`)
    .then(res => res.json())
    .then(res => {
      const parties = res.parties || [];
      const rows = res.rows || [];
      let headHtml = '<tr><th>LGA</th><th>Ward</th><th>Polling Unit</th><th>Election</th>';
      parties.forEach(p => { headHtml += `<th>${p}</th>`; });
      headHtml += '<th>Valid</th><th>Rejected</th><th>Total</th></tr>';
      document.getElementById('resultsTableHead').innerHTML = headHtml;

      let html = '';
      rows.forEach(r => {
        const v = r.party_votes || {};
        html += `<tr>
          <td><strong>${r.lga}</strong></td>
          <td>${r.ward}</td>
          <td>${r.polling_unit}<br><small style="color:#2563eb;">${r.pu_code}</small></td>
          <td><small>${r.election_name}</small></td>`;
        parties.forEach(p => { html += `<td>${v[p] || 0}</td>`; });
        html += `<td><strong>${r.valid_votes||0}</strong></td>
          <td style="color:#dc2626;">${r.rejected_votes||0}</td>
          <td><strong>${r.total_votes_cast||0}</strong></td>
        </tr>`;
      });
      document.getElementById('resultsTableBody').innerHTML = html ||
        `<tr><td colspan="${parties.length + 7}" style="text-align:center; padding:15px;">No collated results found.</td></tr>`;
    });
}

function exportResultsCSV() {
  const lga = document.getElementById('resultsLgaSelect').value || 'all';
  window.location.href = `/api/export-csv?lga=${encodeURIComponent(lga)}`;
}

/* =============================================
   UPLOAD WIZARD
   ============================================= */
function loadUploadWizardData() {
  if (currentUser.role === 'Collation Admin') {
    document.getElementById('collationAdminDisabledBox').style.display = 'block';
    document.getElementById('fieldOfficerLockedBox').style.display = 'none';
    document.getElementById('uploadWizardContainer').style.display = 'none';
    return;
  }
  document.getElementById('collationAdminDisabledBox').style.display = 'none';
  document.getElementById('uploadWizardContainer').style.display = 'block';

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
    if (currentUser.role === 'LGA Admin' && currentUser.assigned_lga) {
      selectLga(currentUser.assigned_lga);
    } else {
      fetch('/api/locations/lgas').then(res => res.json()).then(lgas => {
        let lgaBtns = '';
        lgas.forEach(l => { lgaBtns += `<button class="btn-select-option" onclick="selectLga('${l.replace(/'/g,"\\'")}')">📍 ${l} LGA</button>`; });
        document.getElementById('lgasListStack').innerHTML = lgaBtns;
        goToUploadStep(1);
      });
    }
  }
}

function goToUploadStep(s) {
  document.querySelectorAll('.wizard-step').forEach(step => step.classList.remove('active'));
  document.getElementById('uploadStep' + s).classList.add('active');
}

function selectLga(lga) {
  currentUploadData.lga = lga;
  fetch('/api/admin/elections?active_only=1').then(res => res.json()).then(elections => {
    let electBtns = '';
    elections.forEach(e => {
      electBtns += `<button class="btn-select-option" onclick="selectElection('${e.id}', '${e.name.replace(/'/g,"\\'")}')">🗳️ ${e.name} (${e.type})</button>`;
    });
    document.getElementById('electionsListStack').innerHTML = electBtns || '<p>No active elections available.</p>';
    goToUploadStep(2);
  });
}

function selectElection(id, name) {
  currentUploadData.election_id = id;
  currentUploadData.election_name = name;
  fetch(`/api/locations/wards?lga=${encodeURIComponent(currentUploadData.lga)}`).then(res => res.json()).then(wards => {
    let wardBtns = '';
    wards.forEach(w => { wardBtns += `<button class="btn-select-option" onclick="selectWard('${w.replace(/'/g,"\\'")}')">🏛️ ${w} Ward</button>`; });
    document.getElementById('wardsListStack').innerHTML = wardBtns;
    goToUploadStep(3);
  });
}

function selectWard(w) {
  currentUploadData.ward = w;
  fetch(`/api/locations/pus?ward=${encodeURIComponent(w)}`).then(res => res.json()).then(pus => {
    let puBtns = '';
    pus.forEach(p => {
      puBtns += `<button class="btn-select-option" onclick="selectPU('${p.polling_unit.replace(/'/g,"\\'")}', '${p.pu_code}')">📍 ${p.polling_unit} (${p.pu_code})</button>`;
    });
    document.getElementById('pusListStack').innerHTML = puBtns;
    goToUploadStep(4);
  });
}

function selectPU(pu, code) {
  currentUploadData.polling_unit = pu;
  currentUploadData.pu_code = code;
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
  fd.append('submitted_by', currentUser.username);
  fetch('/api/upload-photo-result', { method: 'POST', body: fd })
    .then(res => res.json())
    .then(res => {
      alert(res.message || res.status);
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

/* =============================================
   REVIEW QUEUE
   ============================================= */
function loadReviewQueue() {
  const banner = document.getElementById('reviewScopeBanner');
  if (currentUser.role === 'Collation Admin') {
    banner.innerText = `🔒 Scoped Collation: Pending Results for ${currentUser.assigned_lga} LGA → ${currentUser.assigned_ward} Ward`;
  } else if (currentUser.role === 'LGA Admin') {
    banner.innerText = `📍 LGA Collation: Pending Results for ${currentUser.assigned_lga} LGA`;
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
            <p><small>Submitted by: <strong>${item.submitted_by}</strong></small></p>
            <button class="btn-action" style="margin-top:8px;" onclick="openReviewModal(${item.id}, '${item.image_url}', '${item.lga.replace(/'/g,"\\'")}', '${item.ward.replace(/'/g,"\\'")}', '${item.polling_unit.replace(/'/g,"\\'")}', '${item.pu_code}', '${item.election_name.replace(/'/g,"\\'")}')">🔍 Verify & Collate Result</button>
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
    parties.forEach(p => {
      html += `<div class="input-row"><label>${p.name} (${p.acronym})</label><input type="number" id="review_${p.acronym}" value="0"></div>`;
    });
    html += `<div class="input-row"><label>Rejected Votes</label><input type="number" id="review_Rejected" value="0"></div>`;
    document.getElementById('reviewPartyInputs').innerHTML = html;
    document.getElementById('reviewModal').classList.add('active');
  });
}

function closeReviewModal() {
  document.getElementById('reviewModal').classList.remove('active');
}

function submitManualCollation(status) {
  fetch('/api/admin/parties').then(res=>res.json()).then(parties => {
    let votes = {};
    parties.forEach(p => {
      votes[p.acronym] = parseInt(document.getElementById('review_' + p.acronym)?.value || 0);
    });
    fetch('/api/admin-verify-collate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        submission_id: activeModalSubmissionId,
        party_votes: votes,
        rejected_votes: parseInt(document.getElementById('review_Rejected')?.value || 0),
        status: status,
        notes: document.getElementById('reviewNotes')?.value || '',
        is_flagged: document.getElementById('reviewFlagged').checked,
        flag_reason: document.getElementById('reviewFlagReason').value,
        verified_by: currentUser.full_name || currentUser.username
      })
    }).then(res => res.json()).then(res => {
      alert(`✓ Submission #${activeModalSubmissionId} marked as ${status}!`);
      closeReviewModal();
      loadReviewQueue();
      loadLiveResults();
      loadWardTable();
    });
  });
}

/* =============================================
   ADMIN TAB
   ============================================= */
function loadAdminTabContent() {
  loadAdminData('users');
  if (currentUser.role === 'Super Admin') {
    fetch('/api/admin/elections').then(res => res.json()).then(elections => {
      let html = '';
      elections.forEach(e => {
        html += `
          <div class="party-card" style="display:flex; justify-content:space-between; align-items:center;">
            <div>
              <strong>${e.name}</strong>
              <p><small>Type: ${e.type} | Reg. Voters: ${e.registered_voters.toLocaleString()}</small></p>
            </div>
            <button class="btn-submit" style="width:auto; padding:6px 12px; font-size:12px; background:${e.is_active ? '#dc2626' : '#16a34a'};" onclick="toggleElectionActive(${e.id}, ${e.is_active ? 0 : 1})">
              ${e.is_active ? 'Disable' : 'Enable'}
            </button>
          </div>`;
      });
      document.getElementById('electionsToggleList').innerHTML = html;
    });
  }
}

function toggleElectionActive(id, newStatus) {
  fetch('/api/admin/toggle-election', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ id: id, is_active: newStatus })
  }).then(res => res.json()).then(() => loadAdminTabContent());
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
    const roleSel = document.getElementById('adminUserRole');
    if (currentUser.role === 'Super Admin') {
      roleSel.innerHTML = `
        <option value="LGA Admin">LGA Admin (Assigned to 1 LGA)</option>
        <option value="Viewer">Viewer (Read Only)</option>`;
    } else if (currentUser.role === 'LGA Admin') {
      roleSel.innerHTML = `
        <option value="Collation Admin">Collation Admin (Assigned to 1 Ward)</option>
        <option value="Field Officer">Field Officer (Assigned to 1 PU)</option>
        <option value="Viewer">Viewer (Read Only)</option>`;
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

function closeAdminModals() {
  document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
}

function submitCreateUser() {
  const puSelect = document.getElementById('adminUserPu');
  const selectedPuOpt = puSelect.options[puSelect.selectedIndex];
  fetch('/api/admin/users', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
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
    alert(res.message);
    closeAdminModals();
    loadAdminData('users');
  });
}

function submitCreateCandidate() {
  const name = document.getElementById('adminCandName').value.trim();
  const party = document.getElementById('adminCandParty').value;
  const election = document.getElementById('adminCandElection').value;
  if (!name || !party || !election) return alert("Please fill Candidate Name, Party, and Election Category.");
  const fd = new FormData();
  fd.append('full_name', name);
  fd.append('party', party);
  fd.append('election_name', election);
  const photoInput = document.getElementById('adminCandPhoto');
  if (photoInput && photoInput.files[0]) fd.append('photo', photoInput.files[0]);
  fetch('/api/admin/candidates', { method: 'POST', body: fd })
    .then(res => res.json()).then(res => {
      alert(res.message);
      closeAdminModals();
      loadLiveResults();
    });
}

function loadAdminData(type) {
  fetch(`/api/admin/${type}?username=${encodeURIComponent(currentUser.username)}`).then(res => res.json()).then(data => {
    let html = `<h4 style="color:#0c235c; margin-bottom:8px;">STAFF REGISTRY (${data.length})</h4><div class="party-counter-grid">`;
    data.forEach(item => {
      html += `
        <div class="party-card" style="display:flex; align-items:center; gap:10px;">
          👤
          <div>
            <strong>${item.full_name || item.name} (@${item.username||''})</strong>
            <p><small>Role: <b>${item.role}</b>
              ${item.assigned_lga ? '| LGA: ' + item.assigned_lga : ''}
              ${item.assigned_ward ? '| Ward: ' + item.assigned_ward : ''}
              ${item.assigned_pu_code ? '| PU: ' + item.assigned_pu_code : ''}
            </small></p>
          </div>
        </div>`;
    });
    document.getElementById('adminDataDisplay').innerHTML = html + '</div>';
  });
}

function triggerSystemReset() {
  if (confirm("⚠️ Reset all Ogun East collation tallies to 0?\n\nThis will delete ALL submissions. This cannot be undone.")) {
    fetch('/api/admin/reset-system', { method: 'POST' }).then(res => res.json()).then(res => {
      alert(res.message);
      loadLiveResults();
      loadWardTable();
    });
  }
}

/* =============================================
   WARD/PU EDITOR — THE NEW FEATURE
   ============================================= */
function openWardPUEditor() {
  document.getElementById('wardPUEditorModal').classList.add('active');
  refreshWardPUTree();
}

function closeWardPUEditor() {
  document.getElementById('wardPUEditorModal').classList.remove('active');
}

function refreshWardPUTree() {
  document.getElementById('wardPUTreeContainer').innerHTML = '<p style="text-align:center; padding:20px; color:#64748b;">Loading...</p>';
  fetch('/api/admin/locations/tree')
    .then(res => res.json())
    .then(tree => {
      wardPUTreeCache = tree;
      renderWardPUTree(tree);
    })
    .catch(err => {
      document.getElementById('wardPUTreeContainer').innerHTML = '<p style="color:#dc2626; padding:10px;">Error loading tree: ' + err + '</p>';
    });
}

function renderWardPUTree(tree, filterText) {
  const container = document.getElementById('wardPUTreeContainer');
  let html = '';
  let grandTotalPU = 0;
  let lgaCount = 0;

  Object.keys(tree).sort().forEach(lga => {
    lgaCount++;
    const wards = tree[lga];
    let lgaPUCount = 0;
    Object.keys(wards).forEach(w => { lgaPUCount += wards[w].length; });
    grandTotalPU += lgaPUCount;

    html += `<div class="tree-lga" onclick="toggleLgaExpand(this)">
      <span>📍 ${lga}</span>
      <span class="count-badge">${Object.keys(wards).length} wards · ${lgaPUCount} PUs</span>
    </div>`;
    html += `<div class="lga-body" style="display:none;">`;

    Object.keys(wards).sort().forEach(ward => {
      const pus = wards[ward];
      const filtered = filterText
        ? pus.filter(p => (p.polling_unit + ' ' + p.pu_code).toLowerCase().includes(filterText.toLowerCase()))
        : pus;
      if (filterText && filtered.length === 0) return;

      html += `<div class="tree-ward" onclick="toggleWardExpand(this)">
        <span>🏛️ ${ward}</span>
        <div style="display:flex; align-items:center; gap:6px;">
          <span class="count-badge" style="background:#2563eb; color:#fff;">${pus.length} PUs</span>
          <button class="mini-btn mini-btn-edit" onclick="event.stopPropagation(); openRenameWard('${lga.replace(/'/g,"\\'")}', '${ward.replace(/'/g,"\\'")}')">✏️ Rename</button>
        </div>
      </div>`;
      html += `<div class="ward-body" style="display:none;">`;
      filtered.forEach(p => {
        html += `<div class="tree-pu">
          <div>
            <strong>${p.polling_unit}</strong><br>
            <span class="tree-pu-code">${p.pu_code}</span>
          </div>
          <div class="tree-actions">
            <button class="mini-btn mini-btn-edit" onclick="openEditPu(${p.id}, '${p.polling_unit.replace(/'/g,"\\'")}', '${p.pu_code}')">✏️</button>
            <button class="mini-btn mini-btn-del" onclick="confirmDeletePu(${p.id}, '${p.polling_unit.replace(/'/g,"\\'")}')">🗑️</button>
          </div>
        </div>`;
      });
      html += `</div>`;
    });
    html += `</div>`;
  });

  if (!html) {
    html = '<p style="text-align:center; padding:20px; color:#64748b;">No polling units found matching filter.</p>';
  } else {
    html = `<div style="text-align:center; padding:8px; background:#0c235c; color:#fff; border-radius:8px; margin-bottom:10px; font-size:12px; font-weight:700;">
      🌐 ${lgaCount} LGAs · ${grandTotalPU} Polling Units
    </div>` + html;
  }
  container.innerHTML = html;
}

function filterWardPUTree() {
  if (!wardPUTreeCache) return;
  const filterText = document.getElementById('puSearchBox').value.trim();
  renderWardPUTree(wardPUTreeCache, filterText);
}

function toggleLgaExpand(el) {
  const body = el.nextElementSibling;
  if (body) body.style.display = body.style.display === 'none' ? 'block' : 'none';
}

function toggleWardExpand(el) {
  const body = el.nextElementSibling;
  if (body) body.style.display = body.style.display === 'none' ? 'block' : 'none';
}

/* EDIT PU */
function openEditPu(id, name, code) {
  document.getElementById('editPuId').value = id;
  document.getElementById('editPuName').value = name;
  document.getElementById('editPuCode').value = code;
  document.getElementById('editPuModal').classList.add('active');
}

function savePuEdit() {
  const id = document.getElementById('editPuId').value;
  const polling_unit = document.getElementById('editPuName').value.trim();
  const pu_code = document.getElementById('editPuCode').value.trim();
  if (!polling_unit || !pu_code) return alert("Name and code are required.");
  fetch('/api/admin/locations/update-pu', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ id: parseInt(id), polling_unit, pu_code })
  }).then(res => res.json()).then(res => {
    alert(res.message);
    document.getElementById('editPuModal').classList.remove('active');
    refreshWardPUTree();
  });
}

/* DELETE PU */
function confirmDeletePu(id, name) {
  if (!confirm(`🗑️ Delete this polling unit?\n\n"${name}"\n\nThis cannot be undone. Existing submissions keep their record but the PU will no longer appear in new uploads.`)) return;
  fetch('/api/admin/locations/delete-pu', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ id: id })
  }).then(res => res.json()).then(res => {
    alert(res.message);
    refreshWardPUTree();
  });
}

/* RENAME WARD */
function openRenameWard(lga, oldWard) {
  document.getElementById('renameWardLga').value = lga;
  document.getElementById('renameWardOld').value = oldWard;
  document.getElementById('renameWardLgaDisplay').value = lga;
  document.getElementById('renameWardOldDisplay').value = oldWard;
  document.getElementById('renameWardNew').value = oldWard;
  document.getElementById('renameWardModal').classList.add('active');
}

function saveWardRename() {
  const lga = document.getElementById('renameWardLga').value;
  const old_ward = document.getElementById('renameWardOld').value;
  const new_ward = document.getElementById('renameWardNew').value.trim();
  if (!new_ward) return alert("New ward name is required.");
  if (new_ward === old_ward) return alert("New name is the same as old name.");
  fetch('/api/admin/locations/rename-ward', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ lga, old_ward, new_ward })
  }).then(res => res.json()).then(res => {
    alert(res.message);
    document.getElementById('renameWardModal').classList.remove('active');
    refreshWardPUTree();
  });
}

function confirmDeleteWard() {
  const lga = document.getElementById('renameWardLga').value;
  const ward = document.getElementById('renameWardOld').value;
  if (!confirm(`⚠️ DELETE ENTIRE WARD?\n\nLGA: ${lga}\nWard: ${ward}\n\nAll polling units under this ward will be permanently removed. Existing submissions keep their records, but the ward will no longer be usable.\n\nThis cannot be undone. Continue?`)) return;
  if (!confirm(`Final confirmation — delete "${ward}" from ${lga}?`)) return;
  fetch('/api/admin/locations/delete-ward', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ lga, ward })
  }).then(res => res.json()).then(res => {
    alert(res.message);
    document.getElementById('renameWardModal').classList.remove('active');
    refreshWardPUTree();
    initDropdowns();
  });
}

/* ADD NEW PU */
function openAddPuModal() {
  fetch('/api/locations/lgas').then(res => res.json()).then(lgas => {
    const sel = document.getElementById('addPuLga');
    sel.innerHTML = lgas.map(l => `<option value="${l}">${l}</option>`).join('');
    onAddPuLgaChanged();
    document.getElementById('addPuModal').classList.add('active');
  });
}

function onAddPuLgaChanged() {
  const lga = document.getElementById('addPuLga').value;
  fetch(`/api/locations/wards?lga=${encodeURIComponent(lga)}`).then(res => res.json()).then(wards => {
    document.getElementById('addPuWard').innerHTML = wards.map(w => `<option value="${w}">${w}</option>`).join('');
  });
}

function saveNewPu() {
  const lga = document.getElementById('addPuLga').value;
  const ward = document.getElementById('addPuWard').value;
  const polling_unit = document.getElementById('addPuName').value.trim();
  const pu_code = document.getElementById('addPuCode').value.trim();
  if (!polling_unit || !pu_code) return alert("Polling Unit Name and PU Code are required.");
  fetch('/api/admin/locations/add-pu', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ lga, ward, polling_unit, pu_code })
  }).then(res => res.json()).then(res => {
    alert(res.message);
    if (res.success) {
      document.getElementById('addPuModal').classList.remove('active');
      document.getElementById('addPuName').value = '';
      document.getElementById('addPuCode').value = '';
      refreshWardPUTree();
      initDropdowns();
    }
  });
}
</script>
 
</body>
</html> ==========================================
HTML_TEMPLATE = ""  # Placeholder — Part 2 fills this


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


if __name__ == '__main__':
    print("=" * 60)
    print("  OGUN EAST 2027 WATCH — READY")
    print(f"  Database: {DB_NAME}")
    print(f"  Username: Willysmediaworld")
    print(f"  Password: Rotimi1972")
    print("=" * 60)
    print("  Open: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    
    