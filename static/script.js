let currentUploadData = {
    election_type: 'State House of Assembly',
    election_name: 'Ijebu East State House of Assembly Election 2027',
    election_id: 'ijebu_east_sha',
    ward: '',
    polling_unit: '',
    pu_code: ''
};

let activeModalSubmissionId = null;
let selectedPhotoFile = null;
let isGuestUser = false;

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const authPage = document.getElementById('authPage');
    const dashboardPage = document.getElementById('dashboardPage');
    const logoutBtn = document.getElementById('logoutBtn');
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');

    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const username = document.getElementById('username')?.value || 'Admin User';
            if (document.getElementById('userDisplayName')) {
                document.getElementById('userDisplayName').innerText = `${username} · SuperAdmin`;
            }
            isGuestUser = false;
            setGuestPermissions(false);

            authPage.classList.remove('active');
            dashboardPage.classList.add('active');
            window.scrollTo(0, 0);
            loadLiveResults();
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            dashboardPage.classList.remove('active');
            authPage.classList.add('active');
            window.scrollTo(0, 0);
        });
    }

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(nav => nav.classList.remove('active'));
            tabContents.forEach(tab => tab.classList.remove('active'));

            item.classList.add('active');
            const targetTab = item.getAttribute('data-tab');
            const targetTabId = `tab-${targetTab}`;
            
            const targetElement = document.getElementById(targetTabId);
            if (targetElement) targetElement.classList.add('active');
            window.scrollTo(0, 0);

            if (targetTab === 'live') loadLiveResults();
            if (targetTab === 'results') loadWardTable();
            if (targetTab === 'review') {
                loadReviewQueue();
                loadAuditLog();
            }
            if (targetTab === 'admin') loadAdminData('users');
        });
    });
});

function openGuestViewer() {
    isGuestUser = true;
    if (document.getElementById('userDisplayName')) {
        document.getElementById('userDisplayName').innerText = "Guest Observer · Read-Only Access";
    }
    
    setGuestPermissions(true);

    document.getElementById('authPage').classList.remove('active');
    document.getElementById('dashboardPage').classList.add('active');
    
    const liveNav = document.querySelector('.nav-item[data-tab="live"]');
    if (liveNav) liveNav.click();
    loadLiveResults();
}

function setGuestPermissions(isGuest) {
    const navUpload = document.getElementById('navUploadBtn');
    const navReview = document.getElementById('navReviewBtn');
    const navAdmin = document.getElementById('navAdminBtn');

    if (isGuest) {
        if (navUpload) navUpload.style.display = 'none';
        if (navReview) navReview.style.display = 'none';
        if (navAdmin) navAdmin.style.display = 'none';
    } else {
        if (navUpload) navUpload.style.display = 'flex';
        if (navReview) navReview.style.display = 'flex';
        if (navAdmin) navAdmin.style.display = 'flex';
    }
}

function openAdminModal(type) {
    closeAdminModals();
    if (type === 'user') document.getElementById('adminUserModal')?.classList.add('active');
    if (type === 'election') document.getElementById('adminElectionModal')?.classList.add('active');
    if (type === 'party') document.getElementById('adminPartyModal')?.classList.add('active');
    if (type === 'candidate') document.getElementById('adminCandidateModal')?.classList.add('active');
    if (type === 'location') document.getElementById('adminLocationModal')?.classList.add('active');
}

function closeAdminModals() {
    document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
}

function submitCreateUser() {
    const payload = {
        full_name: document.getElementById('adminUserFullName')?.value || '',
        username: document.getElementById('adminUsername')?.value || '',
        role: document.getElementById('adminUserRole')?.value || 'Viewer',
        email: document.getElementById('adminUserEmail')?.value || ''
    };
    fetch('/api/admin/users', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    }).then(res => res.json()).then(res => {
        alert(res.message || 'User created successfully!');
        closeAdminModals();
        loadAdminData('users');
    });
}

function submitCreateElection() {
    const payload = {
        name: document.getElementById('adminElectName')?.value || '',
        type: document.getElementById('adminElectType')?.value || 'State House of Assembly',
        constituency: document.getElementById('adminElectConstituency')?.value || '',
        registered_voters: document.getElementById('adminElectVoters')?.value || 50000
    };
    fetch('/api/admin/elections', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    }).then(res => res.json()).then(res => {
        alert(res.message || 'Election created!');
        closeAdminModals();
        loadAdminData('elections');
    });
}

function submitCreateParty() {
    const payload = {
        name: document.getElementById('adminPartyName')?.value || '',
        acronym: document.getElementById('adminPartyAcronym')?.value || '',
        inec_code: document.getElementById('adminPartyCode')?.value || '',
        is_active: document.getElementById('adminPartyActive')?.checked || true
    };
    fetch('/api/admin/parties', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    }).then(res => res.json()).then(res => {
        alert(res.message || 'Party saved!');
        closeAdminModals();
        loadAdminData('parties');
    });
}

function submitCreateCandidate() {
    const formData = new FormData();
    formData.append('full_name', document.getElementById('adminCandName')?.value || '');
    formData.append('party', document.getElementById('adminCandParty')?.value || '');
    formData.append('election_name', document.getElementById('adminCandElection')?.value || '');
    
    const photoInput = document.getElementById('adminCandPhoto');
    if (photoInput && photoInput.files[0]) {
        formData.append('photo', photoInput.files[0]);
    }

    fetch('/api/admin/candidates', {
        method: 'POST',
        body: formData
    }).then(res => res.json()).then(res => {
        alert(res.message || 'Candidate saved!');
        closeAdminModals();
        loadAdminData('candidates');
    });
}

function submitCreateLocation() {
    const payload = {
        state: document.getElementById('adminLocState')?.value || 'Ogun',
        lga: document.getElementById('adminLocLGA')?.value || 'Ijebu East',
        ward: document.getElementById('adminLocWard')?.value || '',
        polling_unit: document.getElementById('adminLocPU')?.value || '',
        pu_code: document.getElementById('adminLocCode')?.value || ''
    };
    fetch('/api/admin/locations', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    }).then(res => res.json()).then(res => {
        alert(res.message || 'Location saved!');
        closeAdminModals();
        loadAdminData('locations');
    });
}

function loadAdminData(type) {
    fetch(`/api/admin/${type}`)
    .then(res => res.json())
    .then(data => {
        const display = document.getElementById('adminDataDisplay');
        if (!display) return;

        if (!Array.isArray(data) || data.length === 0) {
            display.innerHTML = `<p style="font-size:13px; color:#64748b; padding:10px;">No registered ${type} records found in database.</p>`;
            return;
        }

        let html = `<h4 style="color:#0c235c; margin-bottom:8px;">Registered ${type.toUpperCase()} (${data.length})</h4><div class="candidate-list">`;
        data.forEach(item => {
            html += `
            <div class="candidate-card" style="padding:10px; display:flex; align-items:center; gap:12px;">
                ${item.photo_url ? `<img src="${item.photo_url}" style="width:45px; height:45px; border-radius:50%; object-fit:cover;">` : ''}
                <div>
                    <strong>${item.full_name || item.name || item.acronym || item.polling_unit}</strong>
                    <p><small>${item.role || item.type || item.party || item.ward || ''} ${item.email ? '· ' + item.email : ''} ${item.pu_code ? '(' + item.pu_code + ')' : ''}</small></p>
                </div>
            </div>`;
        });
        html += '</div>';
        display.innerHTML = html;
    });
}

function triggerSystemReset() {
    const confirmReset = confirm("⚡ DANGER ZONE: Are you sure you want to reset the entire system to default? This will wipe all test submissions, uploaded image files, and clear live tallies to 0!");
    
    if (confirmReset) {
        fetch('/api/admin/reset-system', { method: 'POST' })
        .then(res => res.json())
        .then(res => {
            alert(res.message || "System reset complete!");
            loadLiveResults();
            loadWardTable();
            loadReviewQueue();
            loadAuditLog();
        });
    }
}

function goToUploadStep(stepNumber) {
    const steps = document.querySelectorAll('.wizard-step');
    const dots = document.querySelectorAll('.dots-indicator .dot');

    steps.forEach(step => step.classList.remove('active'));
    dots.forEach(dot => dot.classList.remove('active'));

    const currentStep = document.getElementById(`uploadStep${stepNumber}`);
    if (currentStep) currentStep.classList.add('active');
    if (dots[stepNumber - 1]) dots[stepNumber - 1].classList.add('active');
}

function selectType(type) {
    currentUploadData.election_type = type;
    goToUploadStep(2);
}

function selectElection(name, id = 'ijebu_east_sha') {
    currentUploadData.election_name = name;
    currentUploadData.election_id = id;
    goToUploadStep(3);
}

function selectWard(wardName) {
    currentUploadData.ward = wardName;
    goToUploadStep(4);
}

function selectPU(puName, puCode) {
    currentUploadData.polling_unit = puName;
    currentUploadData.pu_code = puCode;

    const summaryElection = document.getElementById('summaryElection');
    const summaryWardPU = document.getElementById('summaryWardPU');
    
    if (summaryElection) summaryElection.innerText = currentUploadData.election_name;
    if (summaryWardPU) summaryWardPU.innerText = `Ward: ${currentUploadData.ward} | PU: ${puName} (${puCode})`;

    goToUploadStep(5);
}

function previewUploadImage(input) {
    if (input.files && input.files[0]) {
        selectedPhotoFile = input.files[0];
        const reader = new FileReader();

        reader.onload = function(e) {
            const imgElement = document.getElementById('uploadPreviewImg');
            const previewBox = document.getElementById('imagePreviewBox');
            const actionBtns = document.getElementById('uploadActionButtons');

            if (imgElement) imgElement.src = e.target.result;
            if (previewBox) previewBox.style.display = 'block';
            if (actionBtns) actionBtns.style.display = 'flex';
        };

        reader.readAsDataURL(input.files[0]);
    }
}

function submitPhotoOnly() {
    if (!selectedPhotoFile) {
        alert("Please select a result sheet photograph first.");
        return;
    }

    const formData = new FormData();
    formData.append('photo', selectedPhotoFile);
    formData.append('election_id', currentUploadData.election_id);
    formData.append('election_name', currentUploadData.election_name);
    formData.append('ward', currentUploadData.ward);
    formData.append('polling_unit', currentUploadData.polling_unit);
    formData.append('pu_code', currentUploadData.pu_code);
    formData.append('submitted_by', document.getElementById('username')?.value || 'Field Officer');

    fetch('/api/upload-photo-result', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(res => {
        alert("✓ Result sheet uploaded successfully and routed to Review Queue!");
        selectedPhotoFile = null;
        if (document.getElementById('imagePreviewBox')) document.getElementById('imagePreviewBox').style.display = 'none';
        if (document.getElementById('uploadActionButtons')) document.getElementById('uploadActionButtons').style.display = 'none';
        goToUploadStep(1);

        const reviewTabNav = document.querySelector('.nav-item[data-tab="review"]');
        if (reviewTabNav) reviewTabNav.click();
        
        loadReviewQueue();
    });
}

function switchReviewSubTab(type) {
    const btnPending = document.getElementById('btnViewPending');
    const btnAudit = document.getElementById('btnViewAudit');
    const subPending = document.getElementById('subTabPending');
    const subAudit = document.getElementById('subTabAudit');

    if (type === 'pending') {
        if (btnPending) btnPending.className = 'btn-select-option';
        if (btnAudit) btnAudit.className = 'btn-secondary';
        if (subPending) subPending.style.display = 'block';
        if (subAudit) subAudit.style.display = 'none';
        loadReviewQueue();
    } else {
        if (btnPending) btnPending.className = 'btn-secondary';
        if (btnAudit) btnAudit.className = 'btn-select-option';
        if (subPending) subPending.style.display = 'none';
        if (subAudit) subAudit.style.display = 'block';
        loadAuditLog();
    }
}

function loadReviewQueue() {
    fetch('/api/review-queue')
    .then(res => res.json())
    .then(queue => {
        const reviewContainer = document.getElementById('reviewQueueList');
        if (!reviewContainer) return;

        if (!Array.isArray(queue) || queue.length === 0) {
            reviewContainer.innerHTML = '<p style="text-align:center; padding:20px; color:#64748b;">No pending submissions in queue.</p>';
            return;
        }

        let html = '';
        queue.forEach(item => {
            html += `
            <div class="candidate-card" style="border-left-color: #d97706; margin-bottom:12px;">
                <span style="font-size:11px; font-weight:800; padding:2px 6px; border-radius:4px; background:#fef3c7; color:#92400e;">PENDING VERIFICATION</span>
                <h4 style="margin-top:6px;">#${item.id} ${item.election_name}</h4>
                <p><small>LGA: ${item.lga} | Ward: ${item.ward} | PU: ${item.polling_unit} (${item.pu_code})</small></p>
                <p><small>Officer: ${item.submitted_by} | ${item.timestamp}</small></p>
                <button class="btn-action" style="margin-top:10px; background:#0c235c;" onclick="openReviewModal(${item.id}, '${item.image_url}', '${item.ward}', '${item.polling_unit}', '${item.pu_code}', '${item.election_name}')">
                    🔍 Review & Collate Result Sheet
                </button>
            </div>`;
        });
        reviewContainer.innerHTML = html;
    });
}

function loadAuditLog() {
    fetch('/api/audit-log')
    .then(res => res.json())
    .then(logs => {
        const auditContainer = document.getElementById('auditLogList');
        if (!auditContainer) return;

        if (!Array.isArray(logs) || logs.length === 0) {
            auditContainer.innerHTML = '<p style="text-align:center; padding:20px; color:#64748b;">No verified results in audit archive yet.</p>';
            return;
        }

        let html = '';
        logs.forEach(item => {
            const isAccepted = item.status === 'ACCEPTED';
            const statusBg = isAccepted ? '#dcfce7' : '#fee2e2';
            const statusColor = isAccepted ? '#166534' : '#991b1b';

            html += `
            <div class="candidate-card" style="border-left-color: ${isAccepted ? '#16a34a' : '#dc2626'}; margin-bottom:12px;">
                <span style="font-size:11px; font-weight:800; padding:2px 6px; border-radius:4px; background:${statusBg}; color:${statusColor};">${item.status}</span>
                <h4 style="margin-top:6px;">#${item.id} ${item.election_name}</h4>
                <p><small>Ward: ${item.ward} | PU: ${item.polling_unit} (${item.pu_code})</small></p>
                <p><small>Audited By: <strong>${item.verified_by || 'Admin'}</strong> at ${item.verified_at || ''}</small></p>
                <p style="margin-top:4px;"><strong>Valid Votes: ${(item.valid_votes || 0).toLocaleString()}</strong></p>
                <button class="btn-secondary" style="margin-top:8px; padding:8px; font-size:12px;" onclick="openReviewModal(${item.id}, '${item.image_url}', '${item.ward}', '${item.polling_unit}', '${item.pu_code}', '${item.election_name}')">
                    📜 View Audit Sheet & Tally
                </button>
            </div>`;
        });
        auditContainer.innerHTML = html;
    });
}

function openReviewModal(id, imageUrl, ward, pu, puCode, electionName) {
    activeModalSubmissionId = id;
    
    const modalImg = document.getElementById('modalImage');
    const modalImgLink = document.getElementById('modalImageLink');
    const modalDetails = document.getElementById('modalDetails');
    const reviewModal = document.getElementById('reviewModal');

    if (modalImg) modalImg.src = imageUrl || 'https://via.placeholder.com/300x200?text=EC8A+Form';
    if (modalImgLink) modalImgLink.href = imageUrl || '#';
    if (modalDetails) {
        modalDetails.innerHTML = `
            <strong>${electionName}</strong><br>
            Ward: <strong>${ward}</strong> | PU: <strong>${pu} (${puCode})</strong>
        `;
    }
    
    if (reviewModal) reviewModal.classList.add('active');
}

function closeReviewModal() {
    document.getElementById('reviewModal')?.classList.remove('active');
}

function submitManualCollation(status) {
    const partyVotes = {
        "A": parseInt(document.getElementById('review_A')?.value || 0),
        "AA": parseInt(document.getElementById('review_AA')?.value || 0),
        "ADP": parseInt(document.getElementById('review_ADP')?.value || 0),
        "APC": parseInt(document.getElementById('review_APC')?.value || 0),
        "APGA": parseInt(document.getElementById('review_APGA')?.value || 0),
        "LP": parseInt(document.getElementById('review_LP')?.value || 0),
        "NNPP": parseInt(document.getElementById('review_NNPP')?.value || 0),
        "PDP": parseInt(document.getElementById('review_PDP')?.value || 0),
        "SDP": parseInt(document.getElementById('review_SDP')?.value || 0),
        "YPP": parseInt(document.getElementById('review_YPP')?.value || 0)
    };
    const rejectedVotes = parseInt(document.getElementById('review_Rejected')?.value || 0);
    const notes = document.getElementById('reviewNotes')?.value || '';

    fetch('/api/admin-verify-collate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            submission_id: activeModalSubmissionId,
            party_votes: partyVotes,
            rejected_votes: rejectedVotes,
            status: status,
            notes: notes,
            verified_by: document.getElementById('username')?.value || 'Super Admin'
        })
    })
    .then(res => res.json())
    .then(res => {
        alert(`✓ Submission #${activeModalSubmissionId} marked as ${status} and collated!`);
        closeReviewModal();
        loadReviewQueue();
        loadAuditLog();
        loadLiveResults();
        loadWardTable();
    });
}

function loadLiveResults() {
    const electionSelect = document.getElementById('liveElectionSelect');
    const selectedId = electionSelect ? electionSelect.value : 'ijebu_east_sha';

    fetch(`/api/live-results?election_id=${selectedId}`)
    .then(res => res.json())
    .then(data => renderLiveUI(data));
}

function renderLiveUI(data) {
    if (!data) return;

    if (document.getElementById('leaderTitle')) document.getElementById('leaderTitle').innerText = data.leader?.candidate || 'Awaiting Verified Results';
    if (document.getElementById('leaderParty')) document.getElementById('leaderParty').innerText = data.leader?.party !== 'N/A' ? `Party: ${data.leader?.party}` : '';
    if (document.getElementById('leaderVotes')) document.getElementById('leaderVotes').innerText = (data.leader?.votes || 0).toLocaleString();
    if (document.getElementById('leaderPct')) document.getElementById('leaderPct').innerText = data.leader?.percentage || '0%';

    const avatarBox = document.getElementById('leaderAvatar');
    if (avatarBox) {
        if (data.leader?.photo) {
            avatarBox.innerHTML = `<img src="${data.leader.photo}" style="width:100%; height:100%; border-radius:50%; object-fit:cover;">`;
        } else {
            avatarBox.innerText = '👤';
        }
    }

    if (document.getElementById('statCast')) document.getElementById('statCast').innerText = (data.metrics?.votes_cast || 0).toLocaleString();
    if (document.getElementById('statTurnout')) document.getElementById('statTurnout').innerText = data.metrics?.turnout || '0.0%';
    if (document.getElementById('statValid')) document.getElementById('statValid').innerText = (data.metrics?.valid || 0).toLocaleString();
    if (document.getElementById('statRejected')) document.getElementById('statRejected').innerText = (data.metrics?.rejected || 0).toLocaleString();
    if (document.getElementById('statPUs')) document.getElementById('statPUs').innerText = data.metrics?.pus_verified || '0/154';

    if (document.getElementById('progressPctText')) document.getElementById('progressPctText').innerText = data.metrics?.progress_pct || '0.0%';
    if (document.getElementById('progressFill')) document.getElementById('progressFill').style.width = data.metrics?.progress_pct || '0%';

    const standingsContainer = document.getElementById('standingsContainer');
    if (standingsContainer) {
        if (!data.standings || !Array.isArray(data.standings) || data.standings.length === 0) {
            standingsContainer.innerHTML = '<p style="text-align:center; padding:15px; color:#64748b;">No collated votes recorded yet.</p>';
            return;
        }

        let html = '';
        data.standings.forEach((item, index) => {
            html += `
            <div class="candidate-card">
                <div class="candidate-info">
                    <div style="display:flex; align-items:center; gap:12px;">
                        ${item.photo ? `<img src="${item.photo}" style="width:48px; height:48px; border-radius:50%; object-fit:cover; border:2px solid #0c235c;">` : `<div style="width:48px; height:48px; border-radius:50%; background:#e2e8f0; display:flex; justify-content:center; align-items:center; font-size:22px;">👤</div>`}
                        <div>
                            <h4>${item.candidate}</h4>
                            <p style="font-weight:700; color:#0c235c;">${item.party}</p>
                        </div>
                    </div>
                    <div class="candidate-score">
                        <span class="votes">${(item.votes || 0).toLocaleString()}</span>
                        <span class="percent">${item.percentage}</span>
                    </div>
                </div>
                <div class="progress-track sm">
                    <div class="progress-fill" style="width: ${item.percent_num || 0}%;"></div>
                </div>
            </div>`;
        });
        standingsContainer.innerHTML = html;
    }
}

function loadWardTable() {
    fetch('/api/ward-results?election_id=ijebu_east_sha')
    .then(res => res.json())
    .then(rows => {
        const tbody = document.getElementById('resultsTableBody');
        if (!tbody) return;

        if (!Array.isArray(rows) || rows.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">No collated results yet.</td></tr>';
            return;
        }

        let html = '';
        rows.forEach(r => {
            const votes = r.party_votes || {};
            html += `
            <tr>
                <td>${r.ward}</td>
                <td>${r.polling_unit}<br><small>${r.pu_code}</small></td>
                <td>${votes.APC || 0}</td>
                <td>${votes.PDP || 0}</td>
                <td>${votes.LP || 0}</td>
                <td>${votes.NNPP || 0}</td>
                <td><strong>${(r.valid_votes || 0).toLocaleString()}</strong></td>
            </tr>`;
        });
        tbody.innerHTML = html;
    });
}
