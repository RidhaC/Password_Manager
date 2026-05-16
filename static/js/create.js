let _codes = [];

function toggleCreatePw(id, btn) {
  const inp = document.getElementById(id);
  inp.type = inp.type === 'password' ? 'text' : 'password';
  btn.textContent = inp.type === 'password' ? '👁' : '🙈';
}

function checkStrength() {
  const pwd = document.getElementById('password').value;
  const bar = document.getElementById('sbar');
  const txt = document.getElementById('stext');
  if (!pwd) { bar.style.width = '0'; txt.textContent = 'Strength: -'; txt.style.color = 'var(--text3)'; return; }
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

function genPassword() {
  const len = Math.max(16, parseInt(document.getElementById('genlen').value) || 20);
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?';
  const arr = new Uint32Array(len);
  crypto.getRandomValues(arr);
  const pwd = Array.from(arr, x => chars[x % chars.length]).join('');
  const pw = document.getElementById('password');
  const cf = document.getElementById('confirm');
  pw.value = pwd;
  cf.value = pwd;
  pw.type = 'text';
  cf.type = 'text';
  pw.nextElementSibling.textContent = '🙈';
  cf.nextElementSibling.textContent = '🙈';
  checkStrength();
}

function showErr(msg) {
  const e = document.getElementById('err');
  e.textContent = msg; e.style.display = 'block';
}

async function doCreate() {
  const u = document.getElementById('username').value.trim();
  const p = document.getElementById('password').value;
  const c = document.getElementById('confirm').value;
  if (!u || !p) { showErr('Username and password are required'); return; }
  if (p !== c) { showErr('Passwords do not match'); return; }

  const res = await fetch('/create-account', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: u, password: p, confirm: c })
  });
  const data = await res.json();
  if (!res.ok) { showErr(data.error); return; }

  document.getElementById('qrImg').src = 'data:image/png;base64,' + data.qr;
  document.getElementById('qrModal').classList.add('active');
  document.getElementById('setupCode').focus();
}

async function verify2FA() {
  const code = document.getElementById('setupCode').value.trim();
  const status = document.getElementById('setupStatus');
  if (!code) { status.textContent = 'Enter the code'; return; }

  const res = await fetch('/setup-2fa', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code })
  });
  const data = await res.json();
  if (!res.ok) { status.textContent = data.error; return; }

  _codes = data.backup_codes;
  document.getElementById('qrModal').classList.remove('active');
  const grid = document.getElementById('codesGrid');
  grid.innerHTML = _codes.map(c => `<div class="code-chip">${c}</div>`).join('');
  document.getElementById('backupModal').classList.add('active');
}

function saveCodes() {
  const blob = new Blob([_codes.join('\n')], { type: 'text/plain' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'access_guardians_backup_codes.txt';
  a.click();
}

document.addEventListener('keydown', e => {
  if (e.key !== 'Enter') return;
  if (document.getElementById('qrModal').classList.contains('active')) verify2FA();
  else doCreate();
});