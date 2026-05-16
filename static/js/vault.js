let secrets = [];
let current = null;
let editMode = false;
let activeCategory = 'all';
let selectMode = false;
let selectedLabels = new Set();
let currentSort = 'last_used';

const CATS = [
  { id: 'all',      label: 'All',      icon: '🔑', color: '#7c5cbf' },
  { id: 'social',   label: 'Social',   icon: '💬', color: '#5b8dee' },
  { id: 'work',     label: 'Work',     icon: '💼', color: '#4ec994' },
  { id: 'finance',  label: 'Finance',  icon: '💳', color: '#e8a44a' },
  { id: 'email',    label: 'Email',    icon: '✉️',  color: '#e05c6a' },
  { id: 'shopping', label: 'Shopping', icon: '🛍️', color: '#9b7fd4' },
  { id: 'other',    label: 'Other',    icon: '📁',  color: '#6b6688' },
];

function getCat(id) {
  if (window.ALL_CATS) {
    return window.ALL_CATS.find(c => c.id === id || c.id === String(id)) 
      || { id: 'other', label: 'Other', icon: '📁', color: '#6b6688' };
  }
  return { id: 'other', label: 'Other', icon: '📁', color: '#6b6688' };
}

function avatarColor(label) {
  const colors = ['#7c5cbf','#5b8dee','#4ec994','#e8a44a','#e05c6a','#9b7fd4','#3fb950','#f85149'];
  let h = 0;
  for (let i = 0; i < label.length; i++) h = (h * 31 + label.charCodeAt(i)) % colors.length;
  return colors[h];
}

async function buildCategories() {
  let custom = [];
  try {
    const res = await fetch('/api/categories');
    if (res.ok) custom = await res.json();
  } catch(e) { custom = []; }
  const hidden = JSON.parse(localStorage.getItem('hidden_cats') || '[]');

  const defaults = [
    { id: 'all',      label: 'All',      icon: '🔑', color: '#7c5cbf' },
    { id: 'social',   label: 'Social',   icon: '💬', color: '#5b8dee' },
    { id: 'work',     label: 'Work',     icon: '💼', color: '#4ec994' },
    { id: 'finance',  label: 'Finance',  icon: '💳', color: '#e8a44a' },
    { id: 'email',    label: 'Email',    icon: '✉️',  color: '#e05c6a' },
    { id: 'shopping', label: 'Shopping', icon: '🛍️', color: '#9b7fd4' },
    { id: 'other',    label: 'Other',    icon: '📁',  color: '#6b6688' },
  ].filter(c => c.id === 'all' || !hidden.includes(c.id));

  const customCats = custom.map(c => ({
    id: String(c.id),
    label: c.name,
    icon: c.icon,
    color: c.color,
  }));

  window.ALL_CATS = [...defaults, ...customCats];

  const el = document.getElementById('catList');
  el.innerHTML = window.ALL_CATS.map(c => `
    <div class="cat-pill ${c.id === activeCategory ? 'active' : ''}" onclick="selectCategory('${c.id}')">
      <div class="cat-pill-icon ${c.id === activeCategory ? 'active' : ''}"
           style="background:${c.color}22;border-color:${c.id === activeCategory ? c.color : 'transparent'}">
        ${c.icon}
      </div>
      <div class="cat-pill-label">${c.label}</div>
    </div>
  `).join('');
}

function selectCategory(id) {
  activeCategory = id;
  buildCategories();
  renderList(filterSecrets());
}

function showConfirm(title, msg, onOk) {
  document.getElementById('confirmTitle').textContent = title;
  document.getElementById('confirmMsg').textContent = msg;
  document.getElementById('confirmModal').classList.add('active');
  document.getElementById('confirmOkBtn').onclick = () => { closeConfirm(); onOk(); };
}

function closeConfirm() {
  document.getElementById('confirmModal').classList.remove('active');
}

let _inactivityTimer = null;
const INACTIVITY_MS = 15 * 60 * 1000;

function resetInactivityTimer() {
  if (_inactivityTimer) clearTimeout(_inactivityTimer);
  _inactivityTimer = setTimeout(() => {
    document.getElementById('inactivityModal').classList.add('active');
  }, INACTIVITY_MS);
}

['mousemove','keydown','click','scroll','touchstart'].forEach(evt => {
  document.addEventListener(evt, resetInactivityTimer, { passive: true });
});

resetInactivityTimer();

function changeSort(val) {
  currentSort = val;
  loadSecrets(val);
}

function toggleSortDropdown() {
  const menu = document.getElementById('sortMenu');
  menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
}

function pickSort(val, label) {
  document.getElementById('sortLabel').childNodes[0].textContent = label + ' ';
  document.querySelectorAll('.sort-opt').forEach(o => o.classList.remove('sort-opt-active'));
  event.currentTarget.classList.add('sort-opt-active');
  document.getElementById('sortMenu').style.display = 'none';
  changeSort(val);
}

document.addEventListener('click', e => {
  if (!document.getElementById('sortDropdown').contains(e.target)) {
    document.getElementById('sortMenu').style.display = 'none';
  }
});

function filterSecrets() {
  const q = document.getElementById('search').value.toLowerCase();
  return secrets.filter(s => {
    const matchCat = activeCategory === 'all' || (s.category || 'other') === activeCategory;
    const matchQ = !q || s.label.toLowerCase().includes(q) || s.account_username.toLowerCase().includes(q);
    return matchCat && matchQ;
  });
}

async function loadSecrets(sort = currentSort) {
  const res = await fetch(`/api/secrets?sort=${sort}`);
  if (!res.ok) { console.error('Failed to load secrets:', await res.text()); return; }
  const data = await res.json();
  secrets = Array.isArray(data) ? data : [];
  await buildCategories();
  renderList(filterSecrets());
  checkForAlerts();
}

function checkForAlerts() {
  const SIX = 180 * 24 * 60 * 60 * 1000;
  const now = Date.now();
  const seen = {};
  let hasAlert = false;

  const unique = Object.values(secrets.reduce((acc, s) => { acc[s.label] = s; return acc; }, {}));

  unique.forEach(s => {
    if (s.last_updated && now - new Date(s.last_updated).getTime() > SIX) hasAlert = true;
    if (s.password) { seen[s.password] = seen[s.password] || []; seen[s.password].push(s.label); }
  });

  if (Object.values(seen).some(sites => sites.length > 1)) hasAlert = true;

  const alertBtn = document.querySelectorAll('.rail-btn')[1];
  if (hasAlert) {
    alertBtn.innerHTML = `🔔<span style="position:absolute;top:6px;right:6px;width:8px;height:8px;background:var(--danger);border-radius:50%;border:2px solid var(--bg2)"></span>`;
  } else {
    alertBtn.innerHTML = `🔔`;
  }
}

function renderList(items) {
  const el = document.getElementById('vaultList');
  if (!items.length) {
    el.innerHTML = '<div style="font-size:0.8rem;color:var(--text3);padding:1rem;text-align:center">No entries found</div>';
    return;
  }

  const now = Date.now();
  const DAY = 24 * 60 * 60 * 1000;
  const WEEK = 7 * DAY;
  const TWO_WEEKS = 14 * DAY;

  function getGroup(s) {
    if (!s.last_used) return 3;
    const diff = now - new Date(s.last_used).getTime();
    if (diff < WEEK) return 0;
    if (diff < TWO_WEEKS) return 1;
    return 2;
  }

  const groupLabels = ['This Week', 'Last Week', 'Last Month', 'Older'];
  let lastGroup = -1;

  el.innerHTML = items.map((s, i) => {
    const cat = getCat(s.category || 'other');
    const color = cat.color;
    const checked = selectedLabels.has(s.label) ? 'checked' : '';
    const group = getGroup(s);
    let separator = '';
    if (group !== lastGroup) {
      lastGroup = group;
      separator = `<div style="font-size:0.68rem;font-weight:600;color:var(--text3);letter-spacing:0.08em;text-transform:uppercase;padding:10px 10px 4px">${groupLabels[group]}</div>`;
    }
    return separator + `
      <div class="entry-item ${current && current.label === s.label ? 'active' : ''}"
           id="ei-${i}" onclick="handleEntryClick('${esc(s.label)}', event)">
        <input type="checkbox" class="entry-checkbox" ${checked}
               onchange="toggleSelect('${esc(s.label)}', this.checked)" onclick="event.stopPropagation()"/>
        <div class="entry-avatar" style="background:${color}22;color:${color}" id="avatar-${i}">
          ${s.url ? `<img src="https://www.google.com/s2/favicons?domain=${encodeURIComponent(s.url)}&sz=64" 
            style="width:24px;height:24px;object-fit:contain;border-radius:4px"
            onerror="this.style.display='none';this.parentElement.innerHTML='${s.label.slice(0,2).toUpperCase()}'"
            onload="this.parentElement.style.background='transparent';this.parentElement.style.border='1px solid var(--border)'"/>` 
            : s.label.slice(0,2).toUpperCase()}
        </div>
        <div class="entry-info">
          <div class="entry-label">${esc(s.label)}</div>
          <div class="entry-user">${esc(s.account_username)}</div>
        </div>
        <button class="btn-icon entry-copy" onclick="event.stopPropagation();copyPw('${esc(s.label)}')" title="Copy password">📋</button>
      </div>
    `;
  }).join('');

  if (selectMode) {
    document.getElementById('vaultList').classList.add('select-mode');
  }
}

function handleEntryClick(label, event) {
  if (selectMode) {
    const checkbox = event.currentTarget.querySelector('.entry-checkbox');
    checkbox.checked = !checkbox.checked;
    toggleSelect(label, checkbox.checked);
  } else {
    const s = secrets.find(x => x.label === label);
    if (s) { current = s; showDetail(s); }
    document.querySelectorAll('.entry-item').forEach(e => e.classList.remove('active'));
    event.currentTarget.classList.add('active');
  }
}

function toggleSelect(label, checked) {
  if (checked) selectedLabels.add(label);
  else selectedLabels.delete(label);
  document.getElementById('bulkCount').textContent = selectedLabels.size;
  document.getElementById('bulkDeleteBtn').style.display = selectedLabels.size > 0 ? 'flex' : 'none';
}

function toggleSelectMode() {
  selectMode = !selectMode;
  selectedLabels.clear();
  document.getElementById('bulkCount').textContent = '0';
  document.getElementById('bulkDeleteBtn').style.display = 'none';
  document.getElementById('selectModeBtn').classList.toggle('active', selectMode);
  document.getElementById('selectModeBtn').textContent = selectMode ? '✕ Cancel' : '☑ Select';
  const list = document.getElementById('vaultList');
  list.classList.toggle('select-mode', selectMode);
  renderList(filterSecrets());
}

async function confirmBulkDelete() {
  const count = selectedLabels.size;
  if (!count) return;
  showConfirm('Delete Entries', `Delete ${count} password${count > 1 ? 's' : ''}? This cannot be undone`, async () => {

  for (const label of selectedLabels) {
    await fetch('/api/secrets/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ label })
    });
  }

  selectedLabels.clear();
  current = null;
  selectMode = false;
  document.getElementById('selectModeBtn').classList.remove('active');
  document.getElementById('selectModeBtn').textContent = '☑ Select';
  document.getElementById('bulkDeleteBtn').style.display = 'none';
  document.getElementById('vaultList').classList.remove('select-mode');
  document.getElementById('detailView').classList.remove('active');
  document.getElementById('emptyState').style.display = 'flex';
  toast(`${count} password${count > 1 ? 's' : ''} deleted`);
  await loadSecrets();
  });
}

function closeDetail() {
  current = null;
  document.getElementById('detailView').classList.remove('active');
  document.getElementById('emptyState').style.display = 'flex';
  document.querySelectorAll('.entry-item').forEach(e => e.classList.remove('active'));
}

function filterList() {
  renderList(filterSecrets());
}

function copyPw(label) {
  const s = secrets.find(x => x.label === label);
  if (s) copyText(s.password, label);
}

function selectEntry(label) {
  const s = secrets.find(x => x.label === label);
  if (!s) return;
  current = s;
  document.querySelectorAll('.entry-item').forEach(e => e.classList.remove('active'));

  switchView('vault');
  showDetail(s);
}

function showDetail(s) {
  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('alertsView').classList.remove('active');
  const dv = document.getElementById('detailView');
  dv.classList.add('active');

  const color = avatarColor(s.label);
  const cat = getCat(s.category || 'other');

  document.getElementById('dTitle').textContent = s.label;
    document.getElementById('dCategory').textContent = cat.icon + ' ' + cat.label;
    const dav = document.getElementById('dAvatar');
    dav.style.background = cat.color + '22';
    dav.style.color = cat.color;
    if (s.url) {
      const domain = (() => { try { return new URL(s.url).hostname; } catch { return s.url; } })();
      dav.innerHTML = `<img src="https://www.google.com/s2/favicons?domain=${encodeURIComponent(domain)}&sz=64"
        style="width:32px;height:32px;object-fit:contain;border-radius:4px"
        onerror="this.parentElement.innerHTML='${s.label.slice(0,2).toUpperCase()}';this.parentElement.style.background='${cat.color}22'"
        onload="this.parentElement.style.background='transparent';this.parentElement.style.border='1px solid var(--border)'"/>`;
    } else {
      dav.innerHTML = s.label.slice(0,2).toUpperCase();
      dav.style.background = cat.color + '22';
      dav.style.border = '';
    }

  let pwVisible = false;
  document.getElementById('dFields').innerHTML = `
    ${fieldCard('Account Username', s.account_username, true)}
    <div class="field-card">
      <div class="field-card-label">Password</div>
      <div class="field-card-value">
        <span class="pw-dots" id="pwSpan">••••••••••••</span>
        <div class="field-actions">
          <button class="btn-icon" id="showPwBtn" onclick="toggleDetailPw()">👁</button>
          <button class="btn-icon" onclick="copyText('${esc(s.password)}', '${esc(s.label)}')">📋</button>
        </div>
      </div>
    </div>
    ${s.url ? fieldCard('URL', s.url, true) : ''}
    ${s.notes ? fieldCard('Notes', s.notes, false) : ''}
    ${fieldCard('Last Used', s.last_used ? new Date(s.last_used).toLocaleDateString() : 'Never', false)}
    ${fieldCard('Last Updated', s.last_updated ? new Date(s.last_updated).toLocaleDateString() : 'Unknown', false)}
  `;

  window._currentPw = s.password;
  window.toggleDetailPw = function() {
    pwVisible = !pwVisible;
    const span = document.getElementById('pwSpan');
    span.textContent = pwVisible ? window._currentPw : '••••••••••••';
    span.className = pwVisible ? '' : 'pw-dots';
    document.getElementById('showPwBtn').textContent = pwVisible ? '🙈' : '👁';
  };
}

function fieldCard(label, value, copyable) {
  return `
    <div class="field-card">
      <div class="field-card-label">${label}</div>
      <div class="field-card-value">
        <span>${esc(value)}</span>
        ${copyable ? `<button class="btn-icon" onclick="copyText('${esc(value)}')">📋</button>` : ''}
      </div>
    </div>`;
}

function switchView(view) {
  document.querySelectorAll('.rail-btn').forEach(b => b.classList.remove('active'));
  if (view === 'vault') {
    document.getElementById('emptyState').style.display = current ? 'none' : 'flex';
    document.getElementById('detailView').classList.toggle('active', !!current);
    document.getElementById('alertsView').classList.remove('active');
    document.querySelector('.rail-btn').classList.add('active');
  } else if (view === 'alerts') {
    document.getElementById('emptyState').style.display = 'none';
    document.getElementById('detailView').classList.remove('active');
    document.getElementById('alertsView').classList.add('active');
    document.querySelectorAll('.rail-btn')[1].classList.add('active');
    document.querySelectorAll('.rail-btn')[1].removeAttribute('data-alert');
    loadAlerts();
  }
}

async function loadAlerts() {
  const content = document.getElementById('alertsContent');
  const SIX = 180 * 24 * 60 * 60 * 1000;
  const now = Date.now();

  const unique = Object.values(secrets.reduce((acc, s) => { acc[s.label] = s; return acc; }, {}));

  const stale = unique.filter(s => s.last_updated && now - new Date(s.last_updated).getTime() > SIX);

  const pwMap = {};
  unique.forEach(s => {
    if (s.password) { pwMap[s.password] = pwMap[s.password] || []; pwMap[s.password].push(s.label); }
  });
  const dupes = Object.values(pwMap).filter(sites => sites.length > 1);

  if (!stale.length && !dupes.length) {
    content.innerHTML = `
      <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:3rem 0;text-align:center">
        <div style="width:52px;height:52px;border-radius:50%;background:var(--success-dim);border:1.5px solid var(--success);display:flex;align-items:center;justify-content:center">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
        </div>
        <div>
          <div style="font-family:var(--sans);font-weight:700;font-size:1rem;color:var(--text)">All Clear</div>
          <div style="font-size:0.83rem;color:var(--text3);margin-top:4px">All passwords are unique and up to date</div>
        </div>
      </div>`;
    return;
  }

  let html = '';

  if (dupes.length) {
    html += `
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
        <div style="width:36px;height:36px;border-radius:var(--radius-sm);background:var(--danger-dim);border:1px solid rgba(224,92,106,0.25);display:flex;align-items:center;justify-content:center;flex-shrink:0">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        </div>
        <div>
          <div style="font-family:var(--sans);font-weight:700;font-size:0.95rem;color:var(--danger)">Reused Passwords</div>
          <div style="font-size:0.78rem;color:var(--text3)">${dupes.length} password group${dupes.length > 1 ? 's' : ''} shared across multiple accounts</div>
        </div>
      </div>
      <div style="display:flex;flex-direction:column;gap:8px;margin-bottom:24px">`;
    dupes.forEach(sites => {
      html += `
        <div style="background:var(--surface);border:1px solid rgba(224,92,106,0.15);border-radius:var(--radius-md);overflow:hidden">
          <div style="padding:8px 14px;background:rgba(224,92,106,0.07);border-bottom:1px solid rgba(224,92,106,0.12);font-size:0.7rem;font-weight:600;color:var(--danger);letter-spacing:0.08em;text-transform:uppercase">
            Same password used for ${sites.length} accounts
          </div>
          <div style="padding:12px 14px;display:flex;flex-wrap:wrap;gap:6px">
            ${sites.map(label => `
              <div onclick="selectEntry('${esc(label)}')" style="display:flex;align-items:center;gap:6px;background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius-sm);padding:5px 10px 5px 6px;cursor:pointer;transition:all 0.15s" onmouseover="this.style.background='var(--surface3)';this.style.borderColor='rgba(224,92,106,0.4)'" onmouseout="this.style.background='var(--surface2)';this.style.borderColor='var(--border)'">
                <div style="width:22px;height:22px;border-radius:4px;background:rgba(224,92,106,0.15);color:var(--danger);font-size:0.62rem;font-weight:700;font-family:var(--sans);display:flex;align-items:center;justify-content:center;flex-shrink:0">${esc(label).slice(0,2).toUpperCase()}</div>
                <span style="font-size:0.8rem;font-weight:500;color:var(--text);white-space:nowrap">${esc(label)}</span>
              </div>`).join('')}
          </div>
        </div>`;
    });
    html += `</div>`;
  }

  if (stale.length) {
    html += `
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
        <div style="width:36px;height:36px;border-radius:var(--radius-sm);background:rgba(232,164,74,0.12);border:1px solid rgba(232,164,74,0.25);display:flex;align-items:center;justify-content:center;flex-shrink:0">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--warning)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        </div>
        <div>
          <div style="font-family:var(--sans);font-weight:700;font-size:0.95rem;color:var(--warning)">Outdated Passwords</div>
          <div style="font-size:0.78rem;color:var(--text3)">${stale.length} password${stale.length > 1 ? 's' : ''} not updated in over 6 months</div>
        </div>
      </div>
      <div style="display:flex;flex-direction:column;gap:6px">`;
    stale.forEach(s => {
      const months = Math.floor((now - new Date(s.last_updated).getTime()) / (30 * 24 * 60 * 60 * 1000));
      html += `
        <div onclick="selectEntry('${esc(s.label)}')" style="display:flex;align-items:center;gap:12px;background:var(--surface);border:1px solid rgba(232,164,74,0.2);border-left:3px solid var(--warning);border-radius:var(--radius-md);padding:10px 14px;cursor:pointer;transition:all 0.15s" onmouseover="this.style.background='var(--surface2)'" onmouseout="this.style.background='var(--surface)'">
          <div style="width:32px;height:32px;border-radius:var(--radius-sm);background:rgba(232,164,74,0.12);color:var(--warning);font-family:var(--sans);font-weight:700;font-size:0.75rem;display:flex;align-items:center;justify-content:center;flex-shrink:0">${esc(s.label).slice(0,2).toUpperCase()}</div>
          <div style="flex:1;min-width:0">
            <div style="font-size:0.88rem;font-weight:600;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(s.label)}</div>
            <div style="font-size:0.75rem;color:var(--text3)">Last updated ${months} month${months !== 1 ? 's' : ''} ago</div>
          </div>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--text3)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
        </div>`;
    });
    html += `</div>`;
  }

  content.innerHTML = html;
}

function alertItem() {}

function buildCategorySelect() {
  const sel = document.getElementById('fCategory');
  const cats = (window.ALL_CATS || []).filter(c => c.id !== 'all');
  sel.innerHTML = '<option value="" disabled>Select category</option>' +
    cats.map(c => `<option value="${c.id}">${c.icon} ${c.label}</option>`).join('');
}

function openAdd() {
  editMode = false;
  document.getElementById('formTitle').textContent = 'Add Password';
  ['fLabel','fUser','fPass','fUrl','fNotes'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('fPass').type = 'password';
  document.getElementById('fLabel').removeAttribute('readonly');
  document.getElementById('fLabel').style.opacity = '1';
  document.getElementById('fLabel').style.cursor = 'text';
  document.getElementById('fSbar').style.width = '0';
  document.getElementById('fStext').textContent = 'Strength: -';
  document.getElementById('formStatus').textContent = '';
  buildCategorySelect();
  document.getElementById('fCategory').value = '';
  document.getElementById('formModal').classList.add('active');
  document.getElementById('fLabel').focus();
}

function openEdit() {
  if (!current) return;
  editMode = true;
  document.getElementById('formTitle').textContent = 'Edit Entry';
  document.getElementById('fLabel').value = current.label;
  document.getElementById('fLabel').removeAttribute('readonly');
  document.getElementById('fLabel').style.opacity = '1';
  document.getElementById('fLabel').style.cursor = 'text';
  document.getElementById('fUser').value = current.account_username;
  document.getElementById('fPass').value = current.password;
  document.getElementById('fPass').type = 'text';
  document.getElementById('fUrl').value = current.url || '';
  document.getElementById('fNotes').value = current.notes || '';
  document.getElementById('formStatus').textContent = '';
  buildCategorySelect();
  document.getElementById('fCategory').value = current.category || 'other';
  checkModalStrength();
  document.getElementById('formModal').classList.add('active');
}

function closeModal() {
  document.getElementById('formModal').classList.remove('active');
}

function toggleFPass() {
  const inp = document.getElementById('fPass');
  inp.type = inp.type === 'password' ? 'text' : 'password';
  document.getElementById('fPassBtn').textContent = inp.type === 'password' ? '👁' : '🙈';
}

function checkModalStrength() {
  const pwd = document.getElementById('fPass').value;
  const bar = document.getElementById('fSbar');
  const txt = document.getElementById('fStext');
  if (!pwd) { bar.style.width = '0'; txt.textContent = 'Strength: —'; txt.style.color = 'var(--text3)'; return; }
  let score = 0;
  if (pwd.length >= 16) score += 40; else if (pwd.length >= 12) score += 25; else score += pwd.length * 2;
  if (/[a-z]/.test(pwd)) score += 10;
  if (/[A-Z]/.test(pwd)) score += 10;
  if (/[0-9]/.test(pwd)) score += 10;
  if (/[^a-zA-Z0-9]/.test(pwd)) score += 15;
  if (new Set(pwd).size > 10) score += 10;
  score = Math.min(score, 99);
  const lbl = score < 40 ? 'Weak' : score < 70 ? 'Medium' : 'Strong';
  const col = score < 40 ? 'var(--danger)' : score < 70 ? 'var(--warning)' : 'var(--success)';
  bar.style.width = score + '%'; bar.style.background = col;
  txt.textContent = `Strength: ${lbl} (${score}%)`; txt.style.color = col;
}
document.getElementById('fPass').addEventListener('input', checkModalStrength);

function genModalPassword() {
  const len = Math.max(16, parseInt(document.getElementById('fGenLen').value) || 20);
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?';
  const arr = new Uint32Array(len);
  crypto.getRandomValues(arr);
  const fPass = document.getElementById('fPass');
  fPass.value = Array.from(arr, x => chars[x % chars.length]).join('');
  fPass.type = 'text';
  document.getElementById('fPassBtn').textContent = '🙈';
  checkModalStrength();
}

async function submitForm() {
  const label    = document.getElementById('fLabel').value.trim();
  const user     = document.getElementById('fUser').value.trim();
  const pass     = document.getElementById('fPass').value;
  const category = document.getElementById('fCategory').value;
  const url      = document.getElementById('fUrl').value.trim();
  const notes    = document.getElementById('fNotes').value.trim();
  const status   = document.getElementById('formStatus');

  if (!label || !user || !pass || !category) {
      status.textContent = 'Label, username, password and category are all required';
      status.style.color = 'var(--warning)';
      return;
    }

  const endpoint = editMode ? '/api/secrets/0' : '/api/secrets';
  const method = editMode ? 'PUT' : 'POST';
  const body = editMode
    ? { old_label: current.label, label, account_username: user, password: pass, url, notes, category }
    : { label, account_username: user, password: pass, url, notes, category };

  const res = await fetch(endpoint, {
    method, headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  const d = await res.json();
  if (d.ok) {
    closeModal();
    toast(editMode ? 'Entry updated' : 'Entry saved');
    await loadSecrets();
    if (editMode) {
      current = secrets.find(s => s.label === label) || null;
      if (current) showDetail(current);
    }
  } else {
    status.textContent = 'Save failed. Try again';
    status.style.color = 'var(--danger)';
  }
}

async function doDelete() {
  if (!current) return;
  showConfirm('Delete Entry', `Delete "${current.label}"? This cannot be undone`, async () => {
    const res = await fetch('/api/secrets/delete', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ label: current.label })
    });
    const d = await res.json();
    if (d.ok) {
      current = null;
      toast('Entry deleted.');
      document.getElementById('detailView').classList.remove('active');
      document.getElementById('emptyState').style.display = 'flex';
      await loadSecrets();
    }
  });
}

let _clipboardTimer = null;

function copyText(text, label) {
  navigator.clipboard.writeText(text).then(() => {
    toast('Copied - clears in 30 seconds');
    if (_clipboardTimer) clearTimeout(_clipboardTimer);
    _clipboardTimer = setTimeout(() => {
      navigator.clipboard.writeText('').then(() => toast('Clipboard cleared'));
      _clipboardTimer = null;
    }, 30000);
    if (label) {
      fetch('/api/secrets/used', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label })
      }).then(() => {
        const s = secrets.find(x => x.label === label);
        if (s) s.last_used = new Date().toISOString();
        secrets.sort((a, b) => {
          const ta = a.last_used || a.last_updated || '1970';
          const tb = b.last_used || b.last_updated || '1970';
          return tb.localeCompare(ta);
        });
        renderList(filterSecrets());
      });
    }
  });
}

function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2200);
}

function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

loadSecrets();