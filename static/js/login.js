function showErr(msg) {
  const e = document.getElementById('err');
  e.textContent = msg;
  e.style.display = 'block';
}

async function doLogin() {
  const u = document.getElementById('username').value.trim();
  const p = document.getElementById('password').value;
  if (!u || !p) { showErr('Please enter your username and password'); return; }

  const res = await fetch('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: u, password: p })
  });
  const data = await res.json();
  if (!res.ok) { showErr(data.error); return; }
  if (data.next === 'otp') {
    document.getElementById('otpOverlay').classList.add('active');
    document.getElementById('otpCode').focus();
  } else if (data.next === 'vault') {
    location.href = '/vault';
  }
}

async function verifyOTP(backup) {
  const code = document.getElementById('otpCode').value.trim();
  const status = document.getElementById('otpStatus');
  if (!code) { status.textContent = 'Please enter a code'; return; }

  const res = await fetch('/verify-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, backup })
  });
  const data = await res.json();
  if (!res.ok) { status.textContent = data.error; return; }
  location.href = data.next;
}

document.addEventListener('keydown', e => {
  if (e.key !== 'Enter') return;
  if (document.getElementById('otpOverlay').classList.contains('active')) verifyOTP(false);
  else doLogin();
});

function toggleLoginPw(btn) {
  const inp = document.getElementById('password');
  inp.type = inp.type === 'password' ? 'text' : 'password';
  btn.textContent = inp.type === 'password' ? '👁' : '🙈';
}