// AWTRIX Mirror -- Scriptable-Widget (iOS, kein Mac noetig)
// -----------------------------------------------------------------------------
// Spiegelt die TC001-Kennzahlen auf den iPhone-Home-/Sperrbildschirm:
//   Follower (+Tageszuwachs), 100k-Ziel (fehlend + Prognose), Einnahmen, Krypto.
// Daten kommen aus Supabase (RPC awtrix_get_snapshot), das main.py bei jedem
// Cron-Lauf schreibt. Setup siehe scriptable/README.md.
//
// Unterstuetzt Widget-Groessen: klein + mittel. Ausserhalb des Widgets zeigt
// das Skript eine Vorschau (mittel).
// -----------------------------------------------------------------------------

// --- Konfiguration (oeffentlich-sicher: RLS aktiv, RPC liefert nur Anzeige-JSON)
const SUPABASE_URL = "https://yayfjzetdpofpcoklwrr.supabase.co";
const SUPABASE_KEY = "sb_publishable_5LSC86Vn81iJG17-eYLZkQ_mab2MtVp";

// --- Markenfarben (identisch zu awtrix.py) ---
const COLORS = {
  igPink: "#E1306C",
  homeLime: "#A6E22E",
  revenueGreen: "#39FF14",
  growthGreen: "#2ECC40",
  dropRed: "#FF4136",
  white: "#FFFFFF",
  bg: "#0E0E12",
  subtle: "#8A8A93",
};

// --- Daten holen -------------------------------------------------------------
async function fetchSnapshot() {
  const req = new Request(`${SUPABASE_URL}/rest/v1/rpc/awtrix_get_snapshot`);
  req.method = "POST";
  req.headers = {
    apikey: SUPABASE_KEY,
    Authorization: `Bearer ${SUPABASE_KEY}`,
    "Content-Type": "application/json",
  };
  req.body = "{}";
  req.timeoutInterval = 20;
  return await req.loadJSON(); // RPC liefert das Objekt direkt
}

// --- Formatierung (deutscher Stil, wie auf der Uhr) --------------------------
function fmtInt(n) {
  if (n === null || n === undefined) return "—";
  return Math.round(n).toLocaleString("de-DE");
}
function signedInt(n) {
  if (n === null || n === undefined) return null;
  const r = Math.round(n);
  return (r >= 0 ? "+" : "-") + fmtInt(Math.abs(r));
}
function signedPct(n) {
  if (n === null || n === undefined) return null;
  return (n >= 0 ? "+" : "-") + Math.abs(n).toFixed(1) + "%";
}
function money(n, sign, decimals) {
  if (n === null || n === undefined) return "—";
  const s = decimals
    ? n.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : fmtInt(n);
  return `${s} ${sign || "EUR"}`;
}
function etaShort(iso) {
  if (!iso) return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!m) return null;
  return `${m[3]}.${m[2]}.${m[1].slice(2)}`;
}
function deltaColor(n) {
  if (n === null || n === undefined) return COLORS.subtle;
  return n >= 0 ? COLORS.growthGreen : COLORS.dropRed;
}

// --- kleine View-Helfer ------------------------------------------------------
function addLabel(stack, text) {
  const t = stack.addText(text.toUpperCase());
  t.font = Font.semiboldSystemFont(9);
  t.textColor = new Color(COLORS.subtle);
}
function addValue(stack, text, hex, size) {
  const t = stack.addText(text);
  t.font = Font.boldSystemFont(size || 22);
  t.textColor = new Color(hex);
  t.lineLimit = 1;
  t.minimumScaleFactor = 0.6;
}
function addNote(stack, text, hex) {
  const t = stack.addText(text);
  t.font = Font.semiboldSystemFont(12);
  t.textColor = new Color(hex);
  t.lineLimit = 1;
}

// Eine Kennzahl (Label + Wert + optionale Notiz) als vertikaler Block.
function metricBlock(parent, { title, value, valueColor, note, noteColor }) {
  const col = parent.addStack();
  col.layoutVertically();
  col.spacing = 1;
  addLabel(col, title);
  addValue(col, value, valueColor, 20);
  if (note) addNote(col, note, noteColor);
  return col;
}

// --- Widgets bauen -----------------------------------------------------------
function buildSmall(w, s) {
  w.setPadding(14, 16, 14, 16);

  addLabel(w, "Follower");
  addValue(w, fmtInt(s.followers), COLORS.igPink, 30);
  const d = signedInt(s.follower_delta);
  if (d) addNote(w, `${d} heute`, deltaColor(s.follower_delta));

  w.addSpacer(); // Ziel-Zeile nach unten schieben

  if (s.goal_missing !== null && s.goal_missing !== undefined) {
    const row = w.addStack();
    row.layoutHorizontally();
    row.spacing = 4;
    const a = row.addText("100k");
    a.font = Font.mediumSystemFont(11);
    a.textColor = new Color(COLORS.homeLime);
    const b = row.addText(`-${fmtInt(s.goal_missing)}`);
    b.font = Font.mediumSystemFont(11);
    b.textColor = new Color(COLORS.white);
    const eta = etaShort(s.goal_eta);
    if (eta) {
      const c = row.addText(`~${eta}`);
      c.font = Font.mediumSystemFont(11);
      c.textColor = new Color(COLORS.subtle);
    }
  }
}

function buildMedium(w, s) {
  w.setPadding(16, 18, 16, 18);
  const sign = s.currency || "EUR";

  // Zeile 1: Follower | Ziel
  const row1 = w.addStack();
  row1.layoutHorizontally();
  metricBlock(row1, {
    title: "Follower",
    value: fmtInt(s.followers),
    valueColor: COLORS.igPink,
    note: signedInt(s.follower_delta) ? `${signedInt(s.follower_delta)} heute` : null,
    noteColor: deltaColor(s.follower_delta),
  });
  row1.addSpacer();
  metricBlock(row1, {
    title: "Ziel 100k",
    value: s.goal_missing != null ? `-${fmtInt(s.goal_missing)}` : "—",
    valueColor: COLORS.homeLime,
    note: etaShort(s.goal_eta) ? `~${etaShort(s.goal_eta)}` : null,
    noteColor: COLORS.growthGreen,
  });

  w.addSpacer(10);

  // Zeile 2: Einnahmen | Krypto
  const row2 = w.addStack();
  row2.layoutHorizontally();
  metricBlock(row2, {
    title: "Einnahmen heute",
    value: money(s.revenue_today, sign, true),
    valueColor: COLORS.revenueGreen,
  });
  row2.addSpacer();
  metricBlock(row2, {
    title: "Krypto",
    value: money(s.crypto_total, sign, false),
    valueColor: COLORS.homeLime,
    note: signedPct(s.crypto_pct),
    noteColor: deltaColor(s.crypto_pct),
  });
}

function buildError(w, msg) {
  w.setPadding(16, 16, 16, 16);
  const t = w.addText("AWTRIX Mirror");
  t.font = Font.semiboldSystemFont(12);
  t.textColor = new Color(COLORS.subtle);
  w.addSpacer(6);
  const e = w.addText(msg || "Keine Daten");
  e.font = Font.systemFont(12);
  e.textColor = new Color(COLORS.dropRed);
}

// --- Hauptablauf -------------------------------------------------------------
async function main() {
  const w = new ListWidget();
  w.backgroundColor = new Color(COLORS.bg);
  w.refreshAfterDate = new Date(Date.now() + 30 * 60 * 1000); // ~alle 30 Min

  let snap = null;
  try {
    snap = await fetchSnapshot();
  } catch (err) {
    buildError(w, "Verbindung fehlgeschlagen");
  }

  if (snap) {
    const family = config.widgetFamily || "medium";
    if (family === "small") buildSmall(w, snap);
    else buildMedium(w, snap);
  }

  if (config.runsInWidget) {
    Script.setWidget(w);
  } else {
    // Manuell im Scriptable-App gestartet -> Vorschau zeigen.
    await w.presentMedium();
  }
  Script.complete();
}

await main();
