'use strict';

/* ── Nord 16 colours for xterm.js ──────────────────────────────────────────── */
const NORD_THEME = {
  background:    '#2E3440',
  foreground:    '#D8DEE9',
  cursor:        '#88C0D0',
  cursorAccent:  '#2E3440',
  selectionBackground: 'rgba(136,192,208,0.25)',
  black:         '#3B4252',
  red:           '#BF616A',
  green:         '#A3BE8C',
  yellow:        '#EBCB8B',
  blue:          '#81A1C1',
  magenta:       '#B48EAD',
  cyan:          '#88C0D0',
  white:         '#E5E9F0',
  brightBlack:   '#4C566A',
  brightRed:     '#BF616A',
  brightGreen:   '#A3BE8C',
  brightYellow:  '#EBCB8B',
  brightBlue:    '#81A1C1',
  brightMagenta: '#B48EAD',
  brightCyan:    '#8FBCBB',
  brightWhite:   '#ECEFF4',
};

/* ── State ─────────────────────────────────────────────────────────────────── */
let socket = null;
let term   = null;
let fitAddon = null;
let isConnected = false;

const cfg = window.YUNA_CONFIG || { passwordRequired: false };

/* ── DOM refs ───────────────────────────────────────────────────────────────── */
const loginScreen  = document.getElementById('login-screen');
const app          = document.getElementById('app');
const pwInput      = document.getElementById('password-input');
const loginBtn     = document.getElementById('login-btn');
const loginError   = document.getElementById('login-error');
const connDot      = document.querySelector('.conn-dot');
const newSessBtn   = document.getElementById('new-session-btn');
const fullscreenBtn= document.getElementById('fullscreen-btn');
const fsExpand     = document.getElementById('fs-expand');
const fsShrink     = document.getElementById('fs-shrink');
const keyboardTrig = document.getElementById('keyboard-trigger');
const termEl       = document.getElementById('terminal');

/* ── Bootstrap ──────────────────────────────────────────────────────────────── */
function init() {
  if (cfg.passwordRequired) {
    show(loginScreen);
    bindLogin();
  } else {
    show(app);
    startTerminal();
  }
}

/* ── Login ──────────────────────────────────────────────────────────────────── */
function bindLogin() {
  loginBtn.addEventListener('click', doLogin);
  pwInput.addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });
}

async function doLogin() {
  const pw = pwInput.value;
  if (!pw) return;
  loginBtn.disabled = true;
  try {
    const res = await fetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: pw }),
    });
    if (res.ok) {
      hide(loginScreen);
      show(app);
      startTerminal();
    } else {
      show(loginError);
      pwInput.value = '';
      pwInput.focus();
    }
  } catch {
    show(loginError);
  } finally {
    loginBtn.disabled = false;
  }
}

/* ── Terminal ────────────────────────────────────────────────────────────────── */
function startTerminal() {
  term = new Terminal({
    theme: NORD_THEME,
    fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", "Courier New", monospace',
    fontSize: 14,
    lineHeight: 1.2,
    cursorBlink: true,
    cursorStyle: 'block',
    scrollback: 5000,
    allowTransparency: false,
    macOptionIsMeta: true,
  });

  fitAddon = new FitAddon.FitAddon();
  const webLinksAddon = new WebLinksAddon.WebLinksAddon();
  term.loadAddon(fitAddon);
  term.loadAddon(webLinksAddon);
  term.open(termEl);
  fitAddon.fit();

  connectSocket();

  term.onData(data => {
    if (socket && isConnected) {
      socket.emit('input', { data });
    }
  });

  /* resize observer */
  const ro = new ResizeObserver(() => {
    requestAnimationFrame(() => {
      fitAddon.fit();
      if (socket && isConnected) {
        socket.emit('resize', { cols: term.cols, rows: term.rows });
      }
    });
  });
  ro.observe(termEl);
  ro.observe(document.querySelector('.terminal-container'));

  window.addEventListener('resize', () => {
    fitAddon.fit();
  });

  /* touch: focus terminal on tap so virtual keyboard appears */
  termEl.addEventListener('touchstart', () => term.focus(), { passive: true });
}

/* ── Socket.IO ──────────────────────────────────────────────────────────────── */
function connectSocket() {
  const params = term ? `?cols=${term.cols}&rows=${term.rows}` : '';
  socket = io({ path: '/socket.io', query: { cols: term?.cols, rows: term?.rows } });

  socket.on('connect', () => {
    isConnected = true;
    connDot.className = 'conn-dot connected';
  });

  socket.on('output', data => {
    term.write(data.data);
  });

  socket.on('disconnect_terminal', () => {
    term.write('\r\n\x1b[31m[Session beendet]\x1b[0m\r\n');
  });

  socket.on('disconnect', () => {
    isConnected = false;
    connDot.className = 'conn-dot disconnected';
  });

  socket.on('connect_error', () => {
    connDot.className = 'conn-dot disconnected';
  });
}

/* ── New session ─────────────────────────────────────────────────────────────── */
newSessBtn?.addEventListener('click', () => {
  if (socket) socket.disconnect();
  term.clear();
  connectSocket();
});

/* ── Fullscreen ─────────────────────────────────────────────────────────────── */
fullscreenBtn?.addEventListener('click', () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().then(() => {
      hide(fsExpand); show(fsShrink);
    }).catch(() => {});
  } else {
    document.exitFullscreen().then(() => {
      show(fsExpand); hide(fsShrink);
    }).catch(() => {});
  }
});

document.addEventListener('fullscreenchange', () => {
  if (!document.fullscreenElement) {
    show(fsExpand); hide(fsShrink);
  }
  setTimeout(() => { fitAddon?.fit(); }, 200);
});

/* ── Mobile keyboard trigger ─────────────────────────────────────────────────── */
keyboardTrig?.addEventListener('click', () => {
  term?.focus();
});

/* ── Helpers ─────────────────────────────────────────────────────────────────── */
function show(el) { el?.classList.remove('hidden'); }
function hide(el) { el?.classList.add('hidden'); }

/* ── Start ───────────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', init);
