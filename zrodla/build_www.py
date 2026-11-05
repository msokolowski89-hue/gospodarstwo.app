import re
import os
HERE=os.path.dirname(os.path.abspath(__file__))
src=open(os.path.join(HERE,"claude-artifact.html")).read()
OUT=os.path.join(HERE,"..","index.html")
# split head-ish part (title, meta, links, style) from body
style_end=src.index("</style>")+len("</style>")
head_part=src[:style_end].replace('<meta name="claude:viewport-fit-sides" content="cover">\n','')
body_part=src[style_end:]
# --- start section replacement
start=body_part.index("/* ---------- start ---------- */")
end=body_part.index("})();\n</script>")
new_start=r'''/* ---------- start (Firebase) ---------- */
route();
downloads = { save: async ({ filename, data }) => { const a = document.createElement("a"); a.href = URL.createObjectURL(data); a.download = filename; document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000); } };
const st = $("#status");
const AUTH = { user: null };
function showLogin(msg) {
  $("#quick").hidden = true; $("#userbox").hidden = true;
  $("#view").innerHTML = `<div class="panel" style="padding:24px;display:grid;gap:12px;max-width:60ch">
    <h2 style="margin:0;font:800 22px var(--f-display)">Zaloguj się</h2>
    <p style="margin:0;color:var(--muted)">Dane gospodarstwa są dostępne tylko dla uprawnionych kont Google.</p>
    ${msg ? `<p class="err" style="margin:0">${esc(msg)}</p>` : ""}
    <div><button class="primary" data-act="login">Zaloguj przez Google</button></div></div>`;
}
if (!window.firebase || !window.FIREBASE_CONFIG || !window.FIREBASE_CONFIG.apiKey || /WPISZ/.test(window.FIREBASE_CONFIG.apiKey)) {
  st.textContent = "Brak konfiguracji Firebase. Uzupełnij plik firebase-config.js (instrukcja w README.md)."; st.className = "bad";
} else {
  firebase.initializeApp(window.FIREBASE_CONFIG);
  const fdb = firebase.firestore();
  try { fdb.settings({ ignoreUndefinedProperties: true, merge: true }); } catch (_) {}
  fdb.enablePersistence({ synchronizeTabs: true }).catch(() => {});   // praca w polu przy słabym zasięgu
  const auth = firebase.auth();
  auth.getRedirectResult().catch(e => showLogin("Logowanie nie powiodło się: " + (e.message || e.code)));
  let unsubs = [];
  auth.onAuthStateChanged(u => {
    unsubs.forEach(f => f()); unsubs = [];
    AUTH.user = u;
    if (!u) { db = null; st.hidden = true; showLogin(); return; }
    db = fdb; S.canWrite = true;
    $("#userbox").hidden = false; $("#who").textContent = u.email || u.displayName || "";
    st.hidden = false; st.className = ""; st.textContent = "Wczytywanie danych gospodarstwa…";
    S.loaded = Object.fromEntries(COLS.map(c => [c, false])); S.herdErr = null;
    const timer = setTimeout(() => { st.textContent = "Brak połączenia z bazą. Pokazuję dane zapisane na tym urządzeniu; zmiany wyślą się po odzyskaniu zasięgu."; st.className = "bad"; }, 10000);
    for (const col of COLS) {
      unsubs.push(db.collection(col).onSnapshot({ includeMetadataChanges: true }, snap => {
        const m = new Map(); snap.docs.forEach(d => m.set(d.id, d.data()));
        S[col] = m; if (!snap.metadata.fromCache) S.loaded[col] = true;
        if (Object.values(S.loaded).every(Boolean)) { clearTimeout(timer); st.textContent = ""; st.className = ""; st.hidden = true; }
        if (!drawerState) render();
      }, err => {
        if (HERD_COLS.includes(col)) { S.herdErr = err.code; S.loaded[col] = true;   // stado bez reguł nie blokuje pól
          if (Object.values(S.loaded).every(Boolean)) { clearTimeout(timer); st.hidden = true; }
          if (!drawerState) render(); return; }
        clearTimeout(timer); st.hidden = false; st.className = "bad";
        st.textContent = err.code === "permission-denied"
          ? `Konto ${u.email} nie ma dostępu do danych. Dodaj ten adres w regułach Firestore (plik firestore.rules) albo zaloguj się innym kontem.`
          : "Nie można wczytać danych (" + err.code + "). Odśwież stronę później.";
      }));
    }
  });
  document.addEventListener("click", async e => {
    const el = e.target.closest("[data-act]"); if (!el) return;
    if (el.dataset.act === "login") {
      const p = new firebase.auth.GoogleAuthProvider();
      try { await auth.signInWithPopup(p); } catch (err) { if (/popup/i.test(err.code || "")) auth.signInWithRedirect(p); else showLogin("Logowanie nie powiodło się: " + (err.message || err.code)); }
    }
    if (el.dataset.act === "logout") auth.signOut();
    if (el.dataset.act === "backup") exportBackup();
    if (el.dataset.act === "import") $("#import-file").click();
  });
  $("#import-file").addEventListener("change", async e => { const f = e.target.files[0]; e.target.value = ""; if (f) importBackup(f); });
}
async function exportBackup() {
  const out = { wersja: 1, data: new Date().toISOString() };
  for (const col of COLS) out[col] = Object.fromEntries(S[col]);
  await downloads.save({ filename: `gospodarstwo-kopia-${new Date().toISOString().slice(0, 10)}.json`, data: new Blob([JSON.stringify(out, null, 1)], { type: "application/json" }) });
}
async function importBackup(file) {
  if (!db) return;
  let data; try { data = JSON.parse(await file.text()); } catch (_) { toast("To nie jest poprawny plik JSON"); return; }
  const cols = COLS.filter(c => data[c] && typeof data[c] === "object");
  const n = cols.reduce((a, c) => a + Object.keys(data[c]).length, 0);
  if (!n) { toast("W pliku nie ma pól, upraw, zabiegów ani danych stada"); return; }
  if (!confirm(`Zaimportować ${n} rekordów (${cols.map(c => c + ": " + Object.keys(data[c]).length).join(", ")})?\nRekordy o tych samych identyfikatorach zostaną nadpisane.`)) return;
  st.hidden = false; st.className = ""; st.textContent = "Importowanie…";
  try {
    let batch = db.batch(), k = 0, done = 0;
    for (const c of cols) for (const [id, doc] of Object.entries(data[c])) {
      batch.set(db.collection(c).doc(id), doc); k++; done++;
      if (k === 400) { await batch.commit(); batch = db.batch(); k = 0; st.textContent = `Importowanie… ${done}/${n}`; }
    }
    if (k) await batch.commit();
    st.hidden = true; toast(`Zaimportowano rekordy: ${n}`);
  } catch (err) { st.className = "bad"; st.textContent = "Import przerwany: " + (err.code || err.message); }
}
'''
body_part=body_part[:start]+new_start+body_part[end:]
# user box + import input in header
a='''      <div class="yearbox">'''
assert body_part.count(a)==1
body_part=body_part.replace(a,'''      <div class="userbox" id="userbox" hidden>
        <span id="who" class="sub"></span>
        <button data-act="backup" title="Pobierz kopię wszystkich danych (JSON)">Kopia danych</button>
        <button data-act="import" title="Wczytaj dane z pliku JSON">Import</button>
        <button data-act="logout">Wyloguj</button>
        <input type="file" id="import-file" accept=".json,application/json" hidden>
      </div>
      <div class="yearbox">''',1)
# empty state text
body_part=body_part.replace("Zacznij od dodania pól gospodarstwa. Potem przypiszesz im uprawy na kolejne lata i będziesz zapisywać zabiegi.",
  "Zacznij od dodania pól gospodarstwa albo wczytaj kopię danych przyciskiem „Import” u góry strony (plik gospodarstwo-dane.json).")
css_add='''
.userbox { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.userbox button { padding: 5px 10px; font-size: 13px; }
'''
head_part=head_part.replace("</style>",css_add+"</style>")
firebase='''<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-auth-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore-compat.js"></script>
<script src="firebase-config.js"></script>
'''
reset='''html { color-scheme: light; }
body { margin: 0; font-size: 14px; }
img { max-width: 100%; }
'''
head_part=head_part.replace("<style>","<style>\n"+reset,1)
doc='<!doctype html>\n<html lang="pl">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n<meta name="robots" content="noindex">\n'+head_part+"\n"+firebase+"</head>\n<body>\n"+body_part.strip()+"\n</body>\n</html>\n"
doc=doc.replace("function showLogin(msg) {\n", "function showLogin(msg) {\n  S.needLogin = true;\n",1)
doc=doc.replace("    if (!u) { db = null; st.hidden = true; showLogin(); return; }\n    db = fdb;", "    if (!u) { db = null; st.hidden = true; showLogin(); return; }\n    S.needLogin = false; db = fdb;",1)
a='  $("#quick").hidden = !db || !S.canWrite || herd;\n'
assert doc.count(a)==1
doc=doc.replace(a, a+'  if (S.needLogin) { showLogin(); return; }\n',1)
# sanity
assert "window.claude" not in doc, [m.start() for m in re.finditer("window.claude",doc)]
open(OUT,"w").write(doc); print("ok", len(doc))
