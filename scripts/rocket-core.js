/* Shared plain-script helpers for Rocket Rally. No modules: file:// remains usable. */
const ROCKET_SYNC_CHANNEL = 'rocket-rally';
const ROCKET_STORE_KEY = 'rocket-rally-fallback';

const ROCKET_TEMPLATES = {
  classic: { label: 'Classic Rocket', file: 'templates/classic.svg', mask: 'M105 32 C77 65 70 106 72 169 L48 211 L78 202 L87 245 L105 265 L123 245 L132 202 L162 211 L138 169 C140 106 133 65 105 32 Z', engines: [[.5, .94]], flame: ['#FFF6E3', '#6FE9FF'] },
  shuttle: { label: 'Winged Shuttle', file: 'templates/shuttle.svg', mask: 'M105 33 C82 67 81 113 87 159 L40 205 L86 194 L93 247 L105 265 L117 247 L124 194 L170 205 L123 159 C129 113 128 67 105 33 Z', engines: [[.45, .93], [.55, .93]], flame: ['#FFF6E3', '#FFC24A'] },
  heavy: { label: 'Heavy-Lift Booster', file: 'templates/heavy.svg', mask: 'M105 27 C85 59 84 108 88 169 L65 222 L82 216 L87 256 L105 270 L123 256 L128 216 L145 222 L122 169 C126 108 125 59 105 27 Z', engines: [[.38, .93], [.5, .96], [.62, .93]], flame: ['#FF4D9D', '#FFC24A'] },
  explorer: { label: 'Star Explorer', file: 'templates/explorer.svg', mask: 'M105 34 C73 62 65 113 77 161 L44 206 L83 197 L91 244 L105 264 L119 244 L127 197 L166 206 L133 161 C145 113 137 62 105 34 Z', engines: [[.5, .94]], flame: ['#6FE9FF', '#6B4FD8'] },
  saucer: { label: 'Saucer Scout', file: 'templates/saucer.svg', mask: 'M105 70 C75 78 30 96 26 140 L50 160 L38 205 L66 192 L84 214 L105 220 L126 214 L144 192 L172 205 L160 160 L184 140 C180 96 135 78 105 70 Z', engines: [[.18, .69], [.82, .69]], flame: ['#6FE9FF', '#FFF6E3'] },
  whale: { label: 'Star Whale', file: 'templates/whale.svg', mask: 'M105 40 C70 55 55 95 60 145 L28 168 L55 172 L48 215 L70 230 L38 258 L80 246 L105 252 L130 246 L172 258 L140 230 L162 215 L155 172 L182 168 C150 95 140 55 105 40 Z', engines: [[.5, .85]], flame: ['#3DFFB0', '#6FE9FF'] },
  cat: { label: 'Comet Cat', file: 'templates/cat.svg', mask: 'M76 42 L98 66 L132 42 L122 72 C144 96 138 130 128 160 L118 195 L105 214 L92 195 L82 160 C72 130 66 96 88 72 Z M123 180 C132 187 143 179 148 169 C153 160 152 148 159 144 C164 141 169 145 168 151 C166 165 162 180 153 188 C144 197 128 196 119 189 C115 186 117 181 123 180 Z', engines: [[.5, .72]], flame: ['#FF4D9D', '#FFC24A'] },
  jelly: { label: 'Jelly Drifter', file: 'templates/jelly.svg', mask: 'M105 50 C68 58 52 92 54 128 L34 190 L58 172 L46 240 L80 210 L105 226 L130 210 L164 240 L152 172 L176 190 L156 128 C158 92 142 58 105 50 Z', engines: [[.16, .64], [.22, .81], [.78, .81], [.84, .64]], flame: ['#6B4FD8', '#FF4D9D'] },
  dart: { label: 'Dart Cruiser', file: 'templates/dart.svg', mask: 'M105 30 C95 55 90 85 92 130 L35 175 L88 168 L78 215 L98 208 L92 250 L105 258 L118 250 L112 208 L132 215 L122 168 L175 175 L118 130 C120 85 115 55 105 30 Z', engines: [[.37, .72], [.63, .72]], flame: ['#FFF6E3', '#6FE9FF'] },
  hopper: { label: 'Moon Hopper', file: 'templates/hopper.svg', mask: 'M105 55 L100 82 C75 84 62 108 66 142 L40 168 L62 178 L52 218 L78 200 L105 210 L132 200 L158 218 L148 178 L170 168 L144 142 C148 108 135 84 110 82 Z', engines: [[.19, .57], [.25, .73], [.75, .73], [.81, .57]], flame: ['#FFC24A', '#FFF6E3'] }
};

function rocketId() {
  return (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error('Could not load image.'));
    image.src = src;
  });
}

function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }
function easeOutCubic(t) { return 1 - Math.pow(1 - clamp(t, 0, 1), 3); }
function easeInOutCubic(t) { t = clamp(t, 0, 1); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }

const RocketStore = (() => {
  const DB_NAME = 'rocket-rally';
  const STORE_NAME = 'rockets';
  let dbPromise = null;
  function fallbackRead() {
    try { const records = JSON.parse(localStorage.getItem(ROCKET_STORE_KEY) || '[]'); return Array.isArray(records) ? records : []; } catch (_) { return []; }
  }
  function fallbackWrite(records) { try { localStorage.setItem(ROCKET_STORE_KEY, JSON.stringify(records)); } catch (_) {} }
  function open() {
    if (!('indexedDB' in window)) return Promise.reject(new Error('IndexedDB unavailable'));
    if (dbPromise) return dbPromise;
    dbPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, 1);
      request.onupgradeneeded = () => { if (!request.result.objectStoreNames.contains(STORE_NAME)) request.result.createObjectStore(STORE_NAME, { keyPath: 'id' }); };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
    return dbPromise;
  }
  async function all() {
    try { const db = await open(); return await new Promise((resolve, reject) => { const req = db.transaction(STORE_NAME).objectStore(STORE_NAME).getAll(); req.onsuccess = () => resolve(req.result); req.onerror = () => reject(req.error); }); }
    catch (_) { return fallbackRead(); }
  }
  async function put(record) {
    try { const db = await open(); await new Promise((resolve, reject) => { const tx = db.transaction(STORE_NAME, 'readwrite'); tx.objectStore(STORE_NAME).put(record); tx.oncomplete = resolve; tx.onerror = () => reject(tx.error); }); }
    catch (_) { const records = fallbackRead().filter(item => item.id !== record.id); records.push(record); fallbackWrite(records); }
  }
  async function remove(id) {
    try { const db = await open(); await new Promise((resolve, reject) => { const tx = db.transaction(STORE_NAME, 'readwrite'); tx.objectStore(STORE_NAME).delete(id); tx.oncomplete = resolve; tx.onerror = () => reject(tx.error); }); }
    catch (_) { fallbackWrite(fallbackRead().filter(item => item.id !== id)); }
  }
  async function clear() {
    try { const db = await open(); await new Promise((resolve, reject) => { const tx = db.transaction(STORE_NAME, 'readwrite'); tx.objectStore(STORE_NAME).clear(); tx.oncomplete = resolve; tx.onerror = () => reject(tx.error); }); }
    catch (_) { fallbackWrite([]); }
  }
  return { all, put, remove, clear };
})();
