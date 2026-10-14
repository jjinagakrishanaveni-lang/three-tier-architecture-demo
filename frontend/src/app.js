// API Configuration
const API_BASE_URL = window.location.origin.includes(':8000') 
    ? 'http://localhost:8000/api' 
    : '/api';

// State Management
const state = {
    token: localStorage.getItem('auth_jwt_token') || null,
    user: null,
    system: { db: false, redis: false, users_count: 0, pending_count: 0 },
    emails: []
};

// DOM Elements
const elements = {
    tabs: document.querySelectorAll('.tab-btn'),
    tabContents: document.querySelectorAll('.tab-content'),
    statusDbText: document.getElementById('status-db-text'),
    statusRedisText: document.getElementById('status-redis-text'),
    chipDb: document.getElementById('chip-db'),
    chipRedis: document.getElementById('chip-redis'),
    inboxBadge: document.getElementById('inbox-badge'),
    devInboxBtn: document.getElementById('dev-inbox-btn'),
    devModal: document.getElementById('dev-modal'),
    closeModalBtn: document.getElementById('close-modal-btn'),
    btnCloseModal: document.getElementById('btn-close-modal'),
    btnRefreshEmails: document.getElementById('btn-refresh-emails'),
    mailboxList: document.getElementById('mailbox-list'),
    
    // Forms
    registerForm: document.getElementById('register-form'),
    verifyForm: document.getElementById('verify-form'),
    loginForm: document.getElementById('login-form'),
    verifyTokenInput: document.getElementById('verify-token-input'),
    regResultBox: document.getElementById('reg-result-box'),
    regResultMsg: document.getElementById('reg-result-msg'),
    regQuickVerifyLink: document.getElementById('reg-quick-verify-link'),
    verifySuccessBox: document.getElementById('verify-success-box'),
    btnGoToLogin: document.getElementById('btn-go-to-login'),
    
    // Dashboard
    tabBtnDashboard: document.getElementById('tab-btn-dashboard'),
    dashAvatar: document.getElementById('dash-avatar'),
    dashUserName: document.getElementById('dash-user-name'),
    dashUserEmail: document.getElementById('dash-user-email'),
    dashUserId: document.getElementById('dash-user-id'),
    dashVerifiedAt: document.getElementById('dash-verified-at'),
    dashPgUsers: document.getElementById('dash-pg-users'),
    dashRedisPending: document.getElementById('dash-redis-pending'),
    jwtPreview: document.getElementById('jwt-preview'),
    btnLogout: document.getElementById('btn-logout'),
    btnRefreshProfile: document.getElementById('btn-refresh-profile'),
    
    // Workflow steps
    wfStep1: document.getElementById('wf-step-1'),
    wfStep2: document.getElementById('wf-step-2'),
    wfStep3: document.getElementById('wf-step-3'),
    wfStep4: document.getElementById('wf-step-4'),
    
    toastContainer: document.getElementById('toast-container')
};

// Show Toast Message
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '❌';
    
    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
    elements.toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}

// Switch Active Tab
function switchTab(tabId) {
    elements.tabs.forEach(btn => {
        if (btn.getAttribute('data-target') === tabId) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    elements.tabContents.forEach(content => {
        if (content.id === tabId) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
}

// Update Workflow Visualizer
function updateWorkflow(stepNumber) {
    const steps = [elements.wfStep1, elements.wfStep2, elements.wfStep3, elements.wfStep4];
    steps.forEach((step, idx) => {
        if (idx < stepNumber) {
            step.classList.add('active');
        } else {
            step.classList.remove('active');
        }
    });
}

// Fetch System Status (DB & Redis)
async function fetchSystemStatus() {
    try {
        const res = await fetch(`${API_BASE_URL}/system/status`);
        if (!res.ok) throw new Error('Status endpoint unavailable');
        const data = await res.json();
        
        state.system = data;
        
        // Update DB Chip
        if (data.database === 'Connected') {
            elements.statusDbText.textContent = `Connected (${data.users_count} users)`;
            elements.chipDb.className = 'status-chip connected';
        } else {
            elements.statusDbText.textContent = data.database;
            elements.chipDb.className = 'status-chip disconnected';
        }

        // Update Redis Chip
        if (data.redis === 'Connected') {
            elements.statusRedisText.textContent = `Connected (${data.pending_registrations_count} pending)`;
            elements.chipRedis.className = 'status-chip connected';
        } else {
            elements.statusRedisText.textContent = data.redis;
            elements.chipRedis.className = 'status-chip disconnected';
        }

        if (elements.dashPgUsers) elements.dashPgUsers.textContent = data.users_count;
        if (elements.dashRedisPending) elements.dashRedisPending.textContent = data.pending_registrations_count;

    } catch (err) {
        elements.statusDbText.textContent = 'Offline';
        elements.statusRedisText.textContent = 'Offline';
        elements.chipDb.className = 'status-chip disconnected';
        elements.chipRedis.className = 'status-chip disconnected';
    }
}

// Fetch Simulated Dev Emails
async function fetchDevEmails() {
    try {
        const res = await fetch(`${API_BASE_URL}/dev/recent-emails`);
        if (!res.ok) return;
        const data = await res.json();
        state.emails = data.emails || [];
        
        elements.inboxBadge.textContent = state.emails.length;
        renderDevEmails();
    } catch (e) {
        console.error('Error fetching dev emails:', e);
    }
}

// Render Dev Mailbox List
function renderDevEmails() {
    if (!elements.mailboxList) return;
    
    if (state.emails.length === 0) {
        elements.mailboxList.innerHTML = `
            <div class="empty-mailbox">No emails dispatched yet. Register an account to see it appear here!</div>
        `;
        return;
    }

    elements.mailboxList.innerHTML = state.emails.map(email => `
        <div class="email-card">
            <div class="email-header-line">
                <span class="email-recipient">To: ${email.to_email} (${email.name})</span>
                <span class="email-time">${new Date(email.sent_at).toLocaleTimeString()}</span>
            </div>
            <div class="email-subject">${email.subject}</div>
            <div class="email-actions">
                <button class="btn btn-xs btn-accent quick-verify-btn" data-token="${email.token}">
                    ⚡ 1-Click Verify Token
                </button>
                <button class="btn btn-xs btn-outline copy-token-btn" data-token="${email.token}">
                    Copy Token
                </button>
            </div>
        </div>
    `).join('');

    // Attach click listeners to mailbox action buttons
    document.querySelectorAll('.quick-verify-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const token = e.currentTarget.getAttribute('data-token');
            elements.devModal.style.display = 'none';
            verifyEmailToken(token);
        });
    });

    document.querySelectorAll('.copy-token-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const token = e.currentTarget.getAttribute('data-token');
            navigator.clipboard.writeText(token);
            showToast('Token copied to clipboard!', 'info');
        });
    });
}

// Handle User Registration
async function handleRegister(e) {
    e.preventDefault();
    const btn = document.getElementById('btn-submit-register');
    const btnText = btn.querySelector('.btn-text');
    const spinner = btn.querySelector('.spinner');

    const name = document.getElementById('reg-name').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;

    btn.disabled = true;
    btnText.style.display = 'none';
    spinner.style.display = 'inline-block';

    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Registration failed');
        }

        updateWorkflow(3);
        showToast('Registration submitted! Details stored in Redis.', 'success');

        // Show confirmation box with quick verification link
        elements.regResultBox.style.display = 'flex';
        elements.regResultMsg.textContent = `${data.message} Pending in Redis for ${Math.round(data.expires_in_seconds / 60)} minutes.`;
        
        elements.regQuickVerifyLink.onclick = (evt) => {
            evt.preventDefault();
            verifyEmailToken(data.verification_token);
        };

        // Pre-fill verify form with token
        elements.verifyTokenInput.value = data.verification_token;

        // Refresh system counts and dev emails
        fetchSystemStatus();
        fetchDevEmails();

    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        btn.disabled = false;
        btnText.style.display = 'inline-block';
        spinner.style.display = 'none';
    }
}

// Verify Email Token
async function verifyEmailToken(token) {
    if (!token) return;

    switchTab('tab-verify');
    elements.verifyTokenInput.value = token;
    
    const btn = document.getElementById('btn-submit-verify');
    const btnText = btn.querySelector('.btn-text');
    const spinner = btn.querySelector('.spinner');

    btn.disabled = true;
    btnText.style.display = 'none';
    spinner.style.display = 'inline-block';

    try {
        const response = await fetch(`${API_BASE_URL}/auth/verify?token=${encodeURIComponent(token.trim())}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: token.trim() })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Verification failed');
        }

        updateWorkflow(4);
        showToast(data.message, 'success');

        // Show success banner
        elements.verifySuccessBox.style.display = 'flex';
        elements.verifySuccessDesc.textContent = `User ${data.user.name} (${data.user.email}) committed into PostgreSQL database.`;

        // Update system status
        fetchSystemStatus();
        fetchDevEmails();

    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        btn.disabled = false;
        btnText.style.display = 'inline-block';
        spinner.style.display = 'none';
    }
}

// Handle User Login
async function handleLogin(e) {
    e.preventDefault();
    const btn = document.getElementById('btn-submit-login');
    const btnText = btn.querySelector('.btn-text');
    const spinner = btn.querySelector('.spinner');

    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    btn.disabled = true;
    btnText.style.display = 'none';
    spinner.style.display = 'inline-block';

    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Login failed');
        }

        // Save JWT
        state.token = data.access_token;
        state.user = data.user;
        localStorage.setItem('auth_jwt_token', data.access_token);

        showToast(`Welcome back, ${data.user.name}!`, 'success');
        renderDashboard(data.user);
        switchTab('tab-dashboard');

    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        btn.disabled = false;
        btnText.style.display = 'inline-block';
        spinner.style.display = 'none';
    }
}

// Render Dashboard
function renderDashboard(user) {
    elements.tabBtnDashboard.style.display = 'flex';
    elements.dashAvatar.textContent = user.name ? user.name.charAt(0).toUpperCase() : 'U';
    elements.dashUserName.textContent = user.name;
    elements.dashUserEmail.textContent = user.email;
    elements.dashUserId.textContent = `#${user.id}`;
    elements.dashVerifiedAt.textContent = user.verified_at ? new Date(user.verified_at).toLocaleDateString() : 'Active';
    
    elements.jwtPreview.textContent = JSON.stringify({
        authenticated: true,
        user_id: user.id,
        email: user.email,
        verified: user.is_verified,
        jwt_token_sample: `${state.token.substring(0, 24)}...`
    }, null, 2);
}

// Fetch Logged-in User Profile
async function fetchUserProfile() {
    if (!state.token) return;

    try {
        const res = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });

        if (!res.ok) {
            // Token expired or invalid
            handleLogout();
            return;
        }

        const user = await res.json();
        state.user = user;
        renderDashboard(user);
        switchTab('tab-dashboard');
    } catch (e) {
        console.error('Error fetching profile:', e);
    }
}

// Logout
function handleLogout() {
    state.token = null;
    state.user = null;
    localStorage.removeItem('auth_jwt_token');
    elements.tabBtnDashboard.style.display = 'none';
    switchTab('tab-login');
    showToast('Logged out successfully', 'info');
}

// Check URL Params or Hash for Verification Token
function checkUrlForToken() {
    let token = null;

    // Check query params: ?token=xyz
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('token')) {
        token = urlParams.get('token');
    }

    // Check hash: #verify?token=xyz
    const hash = window.location.hash;
    if (hash.includes('token=')) {
        const hashParams = new URLSearchParams(hash.substring(hash.indexOf('?') + 1));
        if (hashParams.get('token')) {
            token = hashParams.get('token');
        }
    }

    if (token) {
        verifyEmailToken(token);
    }
}

// Event Listeners Initialization
function initEventListeners() {
    // Tab switching
    elements.tabs.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-target');
            switchTab(target);
        });
    });

    // Form Submissions
    elements.registerForm.addEventListener('submit', handleRegister);
    elements.verifyForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const token = elements.verifyTokenInput.value.trim();
        verifyEmailToken(token);
    });
    elements.loginForm.addEventListener('submit', handleLogin);

    elements.btnGoToLogin.addEventListener('click', () => {
        switchTab('tab-login');
    });

    elements.btnLogout.addEventListener('click', handleLogout);
    elements.btnRefreshProfile.addEventListener('click', () => {
        fetchUserProfile();
        fetchSystemStatus();
        showToast('Profile refreshed from PostgreSQL', 'info');
    });

    // Dev Mailbox Modal
    elements.devInboxBtn.addEventListener('click', () => {
        fetchDevEmails();
        elements.devModal.style.display = 'flex';
    });

    elements.closeModalBtn.addEventListener('click', () => {
        elements.devModal.style.display = 'none';
    });

    elements.btnCloseModal.addEventListener('click', () => {
        elements.devModal.style.display = 'none';
    });

    elements.btnRefreshEmails.addEventListener('click', () => {
        fetchDevEmails();
        showToast('Mailbox refreshed', 'info');
    });

    // Close modal on backdrop click
    elements.devModal.addEventListener('click', (e) => {
        if (e.target === elements.devModal) {
            elements.devModal.style.display = 'none';
        }
    });

    // Listen for hash change in case user clicks a link with hash
    window.addEventListener('hashchange', checkUrlForToken);
}

// App Initialization
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    fetchSystemStatus();
    fetchDevEmails();

    // Check if token in URL
    checkUrlForToken();

    // If already logged in, check profile
    if (state.token) {
        fetchUserProfile();
    }

    // Periodic status polling every 10 seconds
    setInterval(() => {
        fetchSystemStatus();
        fetchDevEmails();
    }, 10000);
});
