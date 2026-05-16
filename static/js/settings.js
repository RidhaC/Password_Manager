function showSection(id) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
  document.getElementById('section-' + id).classList.add('active');
  event.currentTarget.classList.add('active');
}

function status(id, msg, ok) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.style.color = ok ? 'var(--success)' : 'var(--danger)';
  setTimeout(() => el.textContent = '', 3000);
}

function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2200);
}

async function saveProfile() {
  const res = await fetch('/api/settings/profile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      first_name: document.getElementById('firstName').value.trim(),
      last_name: document.getElementById('lastName').value.trim(),
      email: document.getElementById('email').value.trim(),
    })
  });
  const d = await res.json();
  status('profileStatus', d.ok ? '✓ Saved' : 'Failed to save', d.ok);
}

function toggleNewPw(btn) {
  const inp = document.getElementById('newPw');
  inp.type = inp.type === 'password' ? 'text' : 'password';
  btn.textContent = inp.type === 'password' ? '👁' : '🙈';
}

function toggleConfirmPw(btn) {
  const inp = document.getElementById('confirmPw');
  inp.type = inp.type === 'password' ? 'text' : 'password';
  btn.textContent = inp.type === 'password' ? '👁' : '🙈';
}

function genNewPassword() {
  const len = Math.max(16, parseInt(document.getElementById('pwGenLen').value) || 20);
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?';
  const arr = new Uint32Array(len);
  crypto.getRandomValues(arr);
  const pwd = Array.from(arr, x => chars[x % chars.length]).join('');
  const newPw = document.getElementById('newPw');
  const confirmPw = document.getElementById('confirmPw');
  newPw.value = pwd;
  newPw.type = 'text';
  confirmPw.value = pwd;
  confirmPw.type = 'text';
  newPw.nextElementSibling.textContent = '🙈';
  confirmPw.nextElementSibling.textContent = '🙈';
  checkPwStrength();
}

function checkPwStrength() {
  const pwd = document.getElementById('newPw').value;
  const bar = document.getElementById('pwBar');
  const txt = document.getElementById('pwStrength');
  if (!pwd) { bar.style.width = '0'; txt.textContent = 'Strength: -'; return; }
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

async function savePassword() {
  const oldPw = document.getElementById('oldPw').value;
  const newPw = document.getElementById('newPw').value;
  const confirmPw = document.getElementById('confirmPw').value;
  if (newPw !== confirmPw) { status('pwStatus', 'Passwords do not match', false); return; }
  if (newPw.length < 16) { status('pwStatus', 'Must be at least 16 characters', false); return; }
  const res = await fetch('/api/settings/password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ old_password: oldPw, new_password: newPw })
  });
  const d = await res.json();
  if (d.ok) {
    document.getElementById('oldPw').value = '';
    document.getElementById('newPw').value = '';
    document.getElementById('confirmPw').value = '';
    status('pwStatus', '✓ Password updated', true);
  } else {
    status('pwStatus', d.error || 'Failed', false);
  }
}

async function addCategory() {
  const name = document.getElementById('catName').value.trim();
  const icon = document.getElementById('catIcon').value.trim() || '📁';
  const color = document.getElementById('catColor').value;
  if (!name) { status('catStatus', 'Name is required', false); return; }

  const res = await fetch('/api/categories');
  const existing = await res.json();
  const hidden = getHiddenCats();
  const visibleDefaults = DEFAULT_CATS.filter(c => !hidden.includes(c.id)).length;
  const total = 1 + visibleDefaults + existing.length; 

  if (total >= 10) {
    status('catStatus', 'Max 10 categories reached. Hide a default category first.', false);
    return;
  }

  const addRes = await fetch('/api/categories', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, icon, color })
  });
  const d = await addRes.json();
  if (d.ok) {
    document.getElementById('catName').value = '';
    document.getElementById('catIcon').value = '';
    status('catStatus', '✓ Category added', true);
    loadCustomCategories();
  } else {
    status('catStatus', 'Failed to add', false);
  }
}

async function deleteCategory(id) {
  const res = await fetch(`/api/categories/${id}`, { method: 'DELETE' });
  const d = await res.json();
  if (d.ok) loadCustomCategories();
}

async function setTheme(theme) {
  document.querySelectorAll('.theme-card').forEach(c => c.classList.remove('active'));
  event.currentTarget.classList.add('active');

  const themes = {
    dark:     { '--bg':'#13111a','--bg2':'#1a1825','--surface':'#1e1c2e','--surface2':'#252338','--surface3':'#2e2b45','--text':'#f0eeff','--text2':'#a09bc0','--text3':'#6b6688' },
    light:    { '--bg':'#f5f4ff','--bg2':'#eeecff','--surface':'#ffffff','--surface2':'#f0eeff','--surface3':'#e5e2ff','--text':'#1a1825','--text2':'#4a4570','--text3':'#8a85b0' },
    midnight: { '--bg':'#080810','--bg2':'#0d0b18','--surface':'#111020','--surface2':'#16142a','--surface3':'#1d1a35','--text':'#e8e5ff','--text2':'#8a85b0','--text3':'#4a4570' },
  };

  const vars = themes[theme];
  if (vars) {
    Object.entries(vars).forEach(([k, v]) => document.documentElement.style.setProperty(k, v));
  }

  const res = await fetch('/api/settings/theme', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ theme })
  });
  const d = await res.json();
  status('themeStatus', d.ok ? '✓ Theme applied' : 'Failed', d.ok);
}

const DEFAULT_CATS = [
  { id: 'social',   name: 'Social',   icon: '💬', color: '#5b8dee' },
  { id: 'work',     name: 'Work',     icon: '💼', color: '#4ec994' },
  { id: 'finance',  name: 'Finance',  icon: '💳', color: '#e8a44a' },
  { id: 'email',    name: 'Email',    icon: '✉️',  color: '#e05c6a' },
  { id: 'shopping', name: 'Shopping', icon: '🛍️', color: '#9b7fd4' },
  { id: 'other',    name: 'Other',    icon: '📁',  color: '#6b6688' },
];

function getHiddenCats() {
  try { return JSON.parse(localStorage.getItem('hidden_cats') || '[]'); } catch { return []; }
}

function saveHiddenCats(arr) {
  localStorage.setItem('hidden_cats', JSON.stringify(arr));
}

async function loadCustomCategories() {
  const res = await fetch('/api/categories');
  const custom = await res.json();
  const hidden = getHiddenCats();
  const el = document.getElementById('allCatList');

  const defaultHTML = DEFAULT_CATS.map(c => {
    const isHidden = hidden.includes(c.id);
    return `
      <div class="custom-cat-item">
        <div class="custom-cat-icon" style="background:${c.color}22">${c.icon}</div>
        <div class="custom-cat-name">${c.name} <span style="font-size:0.72rem;color:var(--text3)">(default)</span></div>
        <button class="custom-cat-delete" onclick="toggleDefaultCat('${c.id}', this)">
          ${isHidden ? 'Show' : 'Hide'}
        </button>
      </div>`;
  }).join('');

  const customHTML = custom.length ? custom.map(c => `
    <div class="custom-cat-item">
      <div class="custom-cat-icon" style="background:${c.color}22">${c.icon}</div>
      <div class="custom-cat-name">${c.name}</div>
      <button class="custom-cat-delete" onclick="deleteCategory(${c.id})">Remove</button>
    </div>
  `).join('') : '';

  el.innerHTML = defaultHTML + customHTML;
}

function toggleDefaultCat(id, btn) {
  const hidden = getHiddenCats();
  const idx = hidden.indexOf(id);
  if (idx === -1) { hidden.push(id); btn.textContent = 'Show'; }
  else { hidden.splice(idx, 1); btn.textContent = 'Hide'; }
  saveHiddenCats(hidden);
}

document.addEventListener('DOMContentLoaded', () => {
  loadCustomCategories();
});

let parsedEntries = [];

function detectFormat(headers) {
  const h = headers.map(x => x.toLowerCase().trim());
  if (h.includes('totp') && h.includes('name') && h.includes('username')) return 'proton';
  if (h.some(x => x.includes('login_username'))) return 'bitwarden';
  if (h.includes('grouping') || (h.includes('url') && h.includes('username') && h.includes('password') && h.includes('name') && !h.includes('login_uri'))) return 'lastpass';
  if (h.includes('title') && h.includes('username') && h.includes('password')) return '1password';
  return 'generic';
}

function parseCSV(text) {
  const lines = text.trim().split('\n');
  const headers = lines[0].split(',').map(h => h.replace(/"/g,'').trim());
  return lines.slice(1).map(line => {
    const vals = [];
    let cur = '', inQ = false;
    for (let i = 0; i < line.length; i++) {
      if (line[i] === '"') { inQ = !inQ; continue; }
      if (line[i] === ',' && !inQ) { vals.push(cur.trim()); cur = ''; continue; }
      cur += line[i];
    }
    vals.push(cur.trim());
    const obj = {};
    headers.forEach((h, i) => obj[h] = vals[i] || '');
    return obj;
  }).filter(r => Object.values(r).some(v => v));
}

function normalizeEntry(row, format) {
  const f = format === 'auto' ? detectFormat(Object.keys(row)) : format;
  if (f === 'proton') return { label: row['name'] || row['title'] || '', username: row['username'] || row['email'] || '', password: row['password'] || '', url: row['url'] || '', notes: row['note'] || row['notes'] || '' };
  if (f === 'bitwarden') return { label: row['name'] || '', username: row['login_username'] || '', password: row['login_password'] || '', url: row['login_uri'] || '', notes: row['notes'] || '' };
  if (f === 'lastpass') return { label: row['name'] || '', username: row['username'] || '', password: row['password'] || '', url: row['url'] || '', notes: row['extra'] || row['notes'] || '' };
  if (f === '1password') return { label: row['title'] || '', username: row['username'] || '', password: row['password'] || '', url: row['url'] || '', notes: row['notes'] || '' };
  if (f === 'chrome') return { label: row['name'] || '', username: row['username'] || '', password: row['password'] || '', url: row['url'] || '', notes: '' };
  return { label: row['name'] || row['title'] || row['label'] || '', username: row['username'] || row['email'] || row['login'] || '', password: row['password'] || '', url: row['url'] || '', notes: row['notes'] || row['note'] || '' };
}

function handleFileChange(input) {
  const file = input.files[0];
  document.getElementById('importFileName').textContent = file ? file.name : 'No file chosen';
  document.getElementById('importFileName').style.color = file ? 'var(--text)' : 'var(--text3)';
  document.getElementById('previewBtn').style.display = file ? 'inline-flex' : 'none';
  document.getElementById('importBtn').style.display = file ? 'inline-flex' : 'none';
  parsedEntries = [];
  document.getElementById('importPreview').style.display = 'none';
}

function selectSource(val, btn) {
  document.getElementById('importSource').value = val;
  document.querySelectorAll('.import-source-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

function previewImport() {
  const file = document.getElementById('importFile').files[0];
  const source = document.getElementById('importSource').value;
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    try {
      const rows = parseCSV(e.target.result);
      parsedEntries = rows.map(r => normalizeEntry(r, source)).filter(e => e.label && e.password);
      if (!parsedEntries.length) { status('importStatus', 'No valid entries found', false); return; }

      document.getElementById('importCount').textContent = `${parsedEntries.length} entries found`;

      const list = document.getElementById('importList');
      const items = parsedEntries.slice(0, 10).map(e => `
        <div class="preview-entry" style="display:flex;align-items:center;gap:10px;padding:8px 12px;background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius-sm);animation:fadeSlideIn 0.2s ease forwards;opacity:0">
          <div style="width:28px;height:28px;border-radius:6px;background:var(--purple-dim);border:1px solid var(--purple-glow);display:flex;align-items:center;justify-content:center;flex-shrink:0">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--purple-light)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
          </div>
          <div style="min-width:0;flex:1">
            <div style="font-size:0.85rem;font-weight:600;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${e.label}</div>
            <div style="font-size:0.75rem;color:var(--text3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${e.username}</div>
          </div>
        </div>
      `).join('');

      const more = parsedEntries.length > 10
        ? `<div style="font-size:0.78rem;color:var(--text3);padding:6px 2px">+${parsedEntries.length - 10} more not shown</div>`
        : '';

      list.innerHTML = items + more;

      list.querySelectorAll('.preview-entry').forEach((el, i) => {
        el.style.animationDelay = `${i * 40}ms`;
      });

      const preview = document.getElementById('importPreview');
      preview.style.display = 'block';
      preview.style.animation = 'fadeSlideIn 0.25s ease forwards';

    } catch (err) {
      status('importStatus', 'Failed to parse: ' + err.message, false);
    }
  };
  reader.readAsText(file);
}

async function doImport() {
  if (!parsedEntries.length) {
    await new Promise(resolve => {
      const file = document.getElementById('importFile').files[0];
      const source = document.getElementById('importSource').value;
      if (!file) { status('importStatus', 'Please select a file first', false); return; }
      const reader = new FileReader();
      reader.onload = e => {
        try {
          const rows = parseCSV(e.target.result);
          parsedEntries = rows.map(r => normalizeEntry(r, source)).filter(e => e.label && e.password);
        } catch(err) {}
        resolve();
      };
      reader.readAsText(file);
    });
    if (!parsedEntries.length) { status('importStatus', 'No valid entries found', false); return; }
  }
  document.getElementById('importBtn').disabled = true;
  document.getElementById('loadingBody').style.display = 'flex';
  document.getElementById('successBody').style.display = 'none';
  document.getElementById('loadingModal').classList.add('active');

  const res = await fetch('/api/import', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ entries: parsedEntries })
  });
  const d = await res.json();

  if (d.ok) {
    document.getElementById('loadingBody').style.display = 'none';
    const dupMsg = d.duplicates ? `, ${d.duplicates} duplicates skipped` : '';
    const skipMsg = d.skipped ? `, ${d.skipped} failed` : '';
    document.getElementById('successMsg').textContent = `Imported ${d.imported} password${d.imported !== 1 ? 's' : ''}${dupMsg}${skipMsg}`;
    document.getElementById('successBody').style.display = 'flex';
    parsedEntries = [];
    document.getElementById('importFile').value = '';
    setTimeout(() => location.href = '/vault', 2500);
  } else {
    document.getElementById('loadingModal').classList.remove('active');
    document.getElementById('importBtn').disabled = false;
    status('importStatus', 'Import failed', false);
  }
}
