// Antigravity Quota Monitor App Logic

function getColor(pct) {
    if (pct >= 50) return 'var(--green)';
    if (pct >= 20) return 'var(--yellow)';
    return 'var(--red)';
}

function renderCard(acc) {
    const isLocal = acc.type === 'local_active';
    const emailDisplay = isLocal ? (acc.email || 'user@gmail.com') : acc.email;
    const isCustomName = acc.name && acc.name !== emailDisplay;
    const titleText = isCustomName ? acc.name : emailDisplay;
    const subtitleText = isCustomName ? emailDisplay : (isLocal ? 'Active Local Session' : 'Connected Google Account');

    if (acc.status !== 'online') {
        return `
        <div class="account-card">
            <div class="card-top">
                <div class="acc-info-header">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <h3>${titleText}</h3>
                        <button class="edit-btn" title="Rename Session" onclick="openRenameModal('${acc.name}')">✏️</button>
                    </div>
                    <div class="acc-email">${subtitleText}</div>
                </div>
                <div class="top-badges">
                    <span class="badge-plan" style="color: var(--red); border-color: var(--red);">Offline</span>
                    ${!isLocal ? `<button class="delete-btn" title="Remove Account" onclick="removeAccount('${acc.name}')">🗑</button>` : ''}
                </div>
            </div>
            <div style="background: rgba(248,81,73,0.1); border: 1px solid var(--red); color: #ff7b72; padding: 12px; border-radius: 6px; font-size: 13px;">
                ⚠️ ${acc.error || 'Unable to connect'}
            </div>
        </div>`;
    }

    const gem = acc.gemini || {};
    const cgpt = acc.claude_gpt || {};
    const gemAnchored = gem.weekly_anchored;
    const cgptAnchored = cgpt.weekly_anchored;
    const canKickstart = !isLocal && acc.type === 'oauth';
    const anyUnanchored = canKickstart && (!gemAnchored || !cgptAnchored);

    return `
    <div class="account-card">
        <div class="card-top">
            <div class="acc-info-header">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <h3>${titleText}</h3>
                    <button class="edit-btn" title="Rename Session" onclick="openRenameModal('${acc.name}')">✏️</button>
                </div>
                <div class="acc-email">${subtitleText}</div>
            </div>
            <div class="top-badges">
                ${canKickstart ? `<button class="kickstart-btn" onclick="kickstartAccount('${acc.name}', ['gemini', 'claude_gpt'])" title="Send micro-ping to start/refresh 7-day countdown on both pools">⚡ Kickstart</button>` : ''}
                <span class="badge-plan">${acc.plan || 'Active Plan'}</span>
                ${!isLocal ? `<button class="delete-btn" title="Remove Account" onclick="removeAccount('${acc.name}')">🗑</button>` : ''}
            </div>
        </div>

        <!-- Gemini Models Pool -->
        <div class="pool-section">
            <div class="pool-title">
                <span>✦</span> Gemini Models
            </div>
            <div class="quota-item">
                <div class="quota-meta">
                    <span style="color: var(--text-secondary);">5-Hour Limit</span>
                    <span class="quota-pct" style="color: ${getColor(gem['5h_remaining'])};">${gem['5h_remaining']}%</span>
                </div>
                <div class="progress-track">
                    <div class="progress-fill" style="width: ${gem['5h_remaining']}%; background: ${getColor(gem['5h_remaining'])};"></div>
                </div>
                <div class="quota-reset">Reset: ${gem['5h_reset']}</div>
            </div>

            <div class="quota-item">
                <div class="quota-meta">
                    <span style="color: var(--text-secondary);">Weekly Limit</span>
                    <span class="quota-pct" style="color: ${getColor(gem['weekly_remaining'])};">${gem['weekly_remaining']}%</span>
                </div>
                <div class="progress-track">
                    <div class="progress-fill" style="width: ${gem['weekly_remaining']}%; background: ${getColor(gem['weekly_remaining'])};"></div>
                </div>
                <div class="quota-reset" style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px;">
                    <span>Reset: ${gem['weekly_reset']} ${gemAnchored ? '<span class="badge-anchored">Active</span>' : '<span class="badge-idle">Idle</span>'}</span>
                    ${canKickstart ? `<button class="kickstart-btn" onclick="kickstartAccount('${acc.name}', ['gemini'])" title="Send micro-ping to kickstart Gemini 7-day timer">⚡ Ping</button>` : ''}
                </div>
            </div>
        </div>

        <!-- Claude / GPT Pool -->
        <div class="pool-section" style="margin-bottom: 0;">
            <div class="pool-title">
                <span>✦</span> Claude &amp; GPT Models
            </div>
            <div class="quota-item">
                <div class="quota-meta">
                    <span style="color: var(--text-secondary);">5-Hour Limit</span>
                    <span class="quota-pct" style="color: ${getColor(cgpt['5h_remaining'])};">${cgpt['5h_remaining']}%</span>
                </div>
                <div class="progress-track">
                    <div class="progress-fill" style="width: ${cgpt['5h_remaining']}%; background: ${getColor(cgpt['5h_remaining'])};"></div>
                </div>
                <div class="quota-reset">Reset: ${cgpt['5h_reset']}</div>
            </div>

            <div class="quota-item">
                <div class="quota-meta">
                    <span style="color: var(--text-secondary);">Weekly Limit</span>
                    <span class="quota-pct" style="color: ${getColor(cgpt['weekly_remaining'])};">${cgpt['weekly_remaining']}%</span>
                </div>
                <div class="progress-track">
                    <div class="progress-fill" style="width: ${cgpt['weekly_remaining']}%; background: ${getColor(cgpt['weekly_remaining'])};"></div>
                </div>
                <div class="quota-reset" style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px;">
                    <span>Reset: ${cgpt['weekly_reset']} ${cgptAnchored ? '<span class="badge-anchored">Active</span>' : '<span class="badge-idle">Idle</span>'}</span>
                    ${canKickstart ? `<button class="kickstart-btn" onclick="kickstartAccount('${acc.name}', ['claude_gpt'])" title="Send micro-ping to kickstart Claude 7-day timer">⚡ Ping</button>` : ''}
                </div>
            </div>
        </div>
    </div>`;
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${type === 'success' ? '⚡' : '⚠️'}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

async function kickstartAccount(name, pools) {
    showToast(`Starting countdown for ${name}...`, 'success');
    try {
        const resp = await fetch('/api/kickstart-account', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ identifier: name, pools: pools })
        });
        const res = await resp.json();
        if (res.status === 'ok') {
            showToast(`✓ Countdown anchored for ${name}!`, 'success');
            await refreshData();
        } else {
            showToast(`Failed: ${res.error || 'Unknown error'}`, 'error');
        }
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

async function kickstartAllIdle() {
    const btn = document.getElementById('btn-kickstart-all');
    if (btn) btn.disabled = true;
    showToast('⚡ Sending micro-pings to lock 7-day countdown timers...', 'success');
    try {
        const resp = await fetch('/api/kickstart-all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pools: ['gemini', 'claude_gpt'], onlyUnanchored: false })
        });
        const res = await resp.json();
        if (res.status === 'ok') {
            const count = (res.results || []).filter(r => r.status === 'ok').length;
            showToast(`✓ Micro-pings confirmed for ${count} account(s)!`, 'success');
            await refreshData();
        } else {
            showToast('Failed to kickstart accounts', 'error');
        }
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    } finally {
        if (btn) btn.disabled = false;
    }
}

async function refreshData() {
    const grid = document.getElementById('accounts-grid');
    try {
        const resp = await fetch('/api/status');
        const data = await resp.json();
        if (!data || data.length === 0) {
            grid.innerHTML = `
                <div class="loading-state">
                    <p style="color: var(--yellow);">No accounts registered yet.</p>
                    <p style="font-size: 13px; margin-top: 8px;">Click <strong>+ Add Account</strong> to connect your Google accounts.</p>
                </div>`;
            return;
        }

        let idleCount = 0;
        data.forEach(acc => {
            if (acc.status === 'online' && acc.type === 'oauth') {
                const g = acc.gemini || {};
                const c = acc.claude_gpt || {};
                if (!g.weekly_anchored || !c.weekly_anchored) {
                    idleCount++;
                }
            }
        });
        const kickAllBtn = document.getElementById('btn-kickstart-all');
        const kickLabel = document.getElementById('kickstart-btn-label');
        if (kickLabel) {
            if (idleCount > 0) {
                kickLabel.innerText = `Kickstart Idle (${idleCount})`;
                if (kickAllBtn) kickAllBtn.title = `Send micro-ping to ${idleCount} idle account(s) to start 7-day countdown`;
            } else {
                kickLabel.innerText = 'Kickstart All Timers';
                if (kickAllBtn) kickAllBtn.title = 'All accounts anchored! Click to refresh or ping all timers';
            }
        }
        if (kickAllBtn) {
            kickAllBtn.classList.remove('hidden');
        }

        grid.innerHTML = data.map(renderCard).join('');
    } catch (err) {
        console.error("Failed to fetch quota:", err);
    }
}

function openAddModal() {
    document.getElementById('acc-name').value = '';
    const statusBox = document.getElementById('auth-status');
    statusBox.classList.add('hidden');
    statusBox.innerText = '';
    document.getElementById('btn-submit-auth').disabled = false;
    document.getElementById('add-modal').classList.remove('hidden');
}

function closeAddModal() {
    document.getElementById('add-modal').classList.add('hidden');
}

function openRenameModal(currentName) {
    document.getElementById('rename-old-id').value = currentName;
    const input = document.getElementById('rename-input');
    input.value = currentName;
    document.getElementById('rename-modal').classList.remove('hidden');
    input.focus();
    input.select();
}

function closeRenameModal() {
    document.getElementById('rename-modal').classList.add('hidden');
}

async function submitRename() {
    const oldId = document.getElementById('rename-old-id').value;
    const newName = document.getElementById('rename-input').value.trim();
    if (!newName) return;

    try {
        const resp = await fetch('/api/rename-account', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ identifier: oldId, newName: newName })
        });
        const res = await resp.json();
        if (res.status === 'ok') {
            closeRenameModal();
            refreshData();
        } else {
            alert('Failed to rename session.');
        }
    } catch (err) {
        alert('Error renaming session: ' + err.message);
    }
}

// Allow pressing Enter in rename modal
document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        const modal = document.getElementById('rename-modal');
        if (modal && !modal.classList.contains('hidden')) {
            submitRename();
        }
    } else if (e.key === 'Escape') {
        closeAddModal();
        closeRenameModal();
    }
});

async function startOAuthConnect() {
    const name = document.getElementById('acc-name').value.trim();
    const statusBox = document.getElementById('auth-status');
    const submitBtn = document.getElementById('btn-submit-auth');

    statusBox.classList.remove('hidden');
    statusBox.innerHTML = '⚡ Opening browser for Google login... Please approve the permission prompt.';
    submitBtn.disabled = true;

    try {
        await fetch('/api/add-account', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        });

        let attempts = 0;
        const interval = setInterval(async () => {
            attempts++;
            const resp = await fetch('/api/status');
            const data = await resp.json();
            if (data.length > 0) {
                closeAddModal();
                refreshData();
                clearInterval(interval);
            }
        }, 2000);
    } catch (err) {
        statusBox.innerHTML = `<span style="color: var(--red);">Error: ${err.message}</span>`;
        submitBtn.disabled = false;
    }
}

async function removeAccount(name) {
    if (!confirm(`Are you sure you want to remove account "${name}"?`)) return;
    try {
        await fetch('/api/remove-account', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ identifier: name })
        });
        refreshData();
    } catch (err) {
        alert("Failed to remove account: " + err.message);
    }
}

// Initial fetch and 15-second loop
refreshData();
setInterval(refreshData, 15000);
