"""
Genera un file HTML autonomo con l'animazione dei travasi.

Uso:
    python3 genera_travasi.py

Crea il file "travasi.html" nella stessa cartella.
Poi basta aprirlo con doppio clic: nessun server, nessuna porta, nessun terminale
da lasciare acceso.

Per cambiare i parametri, modifica le tre righe sotto "IMPOSTAZIONI".
"""

import json
import os
import webbrowser

# ============================== IMPOSTAZIONI ==============================
CAPIENZA = 20.0   # litri per damigiana
MESTOLO = 1.0     # litri per mestolata
CICLI = 20        # numero di cicli completi (andata + ritorno)
# =========================================================================


def simula(capienza, mestolo, cicli):
    """
    Calcola lo stato dopo ogni mezzo travaso.

    Il mestolo preleva sempre in proporzione alla miscela presente:
    se una damigiana contiene B litri di bianco su T totali, il mestolo
    porta via B/T * mestolo litri di bianco (e il resto di rosso).
    """
    ab, ar = capienza, 0.0   # damigiana A: parte bianca pura
    bb, br = 0.0, capienza   # damigiana B: parte rossa pura

    stati = [{
        "ciclo": 0,
        "fase": "iniziale",
        "etichetta": "Situazione iniziale",
        "A": {"bianco": ab, "rosso": ar},
        "B": {"bianco": bb, "rosso": br},
    }]

    for c in range(1, cicli + 1):
        # --- mezzo passo a: un mestolo da A verso B ---
        tot = ab + ar
        q_bianco = ab / tot * mestolo
        q_rosso = ar / tot * mestolo
        ab -= q_bianco
        ar -= q_rosso
        bb += q_bianco
        br += q_rosso
        stati.append({
            "ciclo": c, "fase": "a",
            "etichetta": "Ciclo %d a) mestolo da A verso B" % c,
            "A": {"bianco": ab, "rosso": ar},
            "B": {"bianco": bb, "rosso": br},
        })

        # --- mezzo passo b: un mestolo da B verso A ---
        # ora B contiene capienza + mestolo litri: il divisore e' diverso
        tot = bb + br
        q_bianco = bb / tot * mestolo
        q_rosso = br / tot * mestolo
        bb -= q_bianco
        br -= q_rosso
        ab += q_bianco
        ar += q_rosso
        stati.append({
            "ciclo": c, "fase": "b",
            "etichetta": "Ciclo %d b) mestolo da B verso A" % c,
            "A": {"bianco": ab, "rosso": ar},
            "B": {"bianco": bb, "rosso": br},
        })

    return stati


MODELLO = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Travasi di vino</title>
<style>
  :root { --bianco:#e8d9a0; --rosso:#7b1230; --carta:#faf7f0; --inch:#2b2118; }
  * { box-sizing:border-box; }
  body { margin:0; padding:24px; background:var(--carta); color:var(--inch);
         font-family:Georgia,"Times New Roman",serif; }
  .wrap { max-width:980px; margin:0 auto; }
  h1 { font-size:26px; margin:0 0 4px; font-weight:normal; }
  .sub { font-size:14px; opacity:.65; margin-bottom:22px; }
  .pannello { display:flex; flex-wrap:wrap; gap:14px; align-items:center;
              padding:14px 16px; margin-bottom:22px; background:#fff;
              border:1px solid #e0d8c8; border-radius:6px; }
  button { font-family:inherit; font-size:14px; padding:8px 18px; cursor:pointer;
           border:1px solid var(--inch); border-radius:4px;
           background:var(--inch); color:var(--carta); }
  button.ghost { background:transparent; color:var(--inch); }
  button:hover { opacity:.78; }
  .campo { display:flex; flex-direction:column; gap:4px; }
  .campo label { font-size:11px; text-transform:uppercase; letter-spacing:.8px; opacity:.6; }
  .campo input { width:90px; padding:6px 8px; font-family:inherit; font-size:15px;
                 border:1px solid #d5cbb8; border-radius:4px; background:var(--carta); }
  .scena { display:flex; align-items:center; justify-content:center; gap:10px; margin-bottom:8px; }
  .stato { text-align:center; font-size:15px; min-height:24px; margin-bottom:18px; }
  .numeri { display:grid; grid-template-columns:1fr 1fr; gap:16px;
            margin:0 auto 26px; max-width:620px; }
  .scheda { background:#fff; border:1px solid #e0d8c8; border-radius:6px; padding:12px 14px; }
  .scheda h3 { margin:0 0 8px; font-size:13px; text-transform:uppercase;
               letter-spacing:1px; font-weight:normal; opacity:.6; }
  .riga { display:flex; justify-content:space-between; font-size:15px; padding:3px 0; }
  .riga b { font-variant-numeric:tabular-nums; font-weight:normal; }
  .barra { height:8px; border-radius:4px; overflow:hidden; display:flex; margin-top:9px; }
  .barra i { display:block; height:100%; transition:width .45s ease; }
  canvas { display:block; width:100%; max-width:900px; margin:0 auto; background:#fff;
           border:1px solid #e0d8c8; border-radius:6px; }
  .nota { font-size:12.5px; opacity:.6; text-align:center; margin-top:12px; line-height:1.6; }
</style>
</head>
<body>
<div class="wrap">

  <h1>Travasi tra due damigiane</h1>
  <div class="sub">Il mestolo preleva sempre in proporzione alla miscela presente, mai vino puro dopo il primo giro.</div>

  <div class="pannello">
    <button id="btnPlay">Avvia</button>
    <button id="btnStep" class="ghost">Passo</button>
    <button id="btnReset" class="ghost">Reset</button>
    <div class="campo"><label>Velocita (ms)</label><input id="velocita" type="number" value="700" min="80" step="50"></div>
    <div class="campo"><label>Parametri</label><span style="font-size:14px;padding-top:4px">__PARAMETRI__</span></div>
  </div>

  <div class="scena">
    <svg id="damA" width="200" height="260" viewBox="0 0 200 260"></svg>
    <svg id="freccia" width="150" height="260" viewBox="0 0 150 260"></svg>
    <svg id="damB" width="200" height="260" viewBox="0 0 200 260"></svg>
  </div>

  <div class="stato" id="stato">Situazione iniziale</div>

  <div class="numeri">
    <div class="scheda">
      <h3>Damigiana A</h3>
      <div class="riga"><span>Bianco</span><b id="aB"></b></div>
      <div class="riga"><span>Rosso</span><b id="aR"></b></div>
      <div class="riga"><span>Totale</span><b id="aT"></b></div>
      <div class="barra"><i id="barAB" style="background:var(--bianco)"></i><i id="barAR" style="background:var(--rosso)"></i></div>
    </div>
    <div class="scheda">
      <h3>Damigiana B</h3>
      <div class="riga"><span>Bianco</span><b id="bB"></b></div>
      <div class="riga"><span>Rosso</span><b id="bR"></b></div>
      <div class="riga"><span>Totale</span><b id="bT"></b></div>
      <div class="barra"><i id="barBB" style="background:var(--bianco)"></i><i id="barBR" style="background:var(--rosso)"></i></div>
    </div>
  </div>

  <canvas id="grafico" width="900" height="260"></canvas>


</div>

<script>
var STATI = __DATI__;
var CAPIENZA = __CAPIENZA__;

function $(id){ return document.getElementById(id); }
var idx = 0, timer = null;

function fmt(v){ return v.toFixed(4).replace('.', ',') + ' L'; }

function disegnaDamigiana(svg, bianco, rosso, etichetta){
  var tot = bianco + rosso;
  var fraz = tot > 0 ? bianco / tot : 0;
  var cB = [232,217,160], cR = [123,18,48];
  var mix = [0,1,2].map(function(i){ return Math.round(cR[i] + (cB[i]-cR[i]) * fraz); });
  var colore = 'rgb(' + mix.join(',') + ')';

  var pieno = Math.min(tot / CAPIENZA, 1.15);
  var yBase = 225, hMax = 130;
  var h = hMax * pieno;
  var y = yBase - h;

  svg.innerHTML =
    '<defs><clipPath id="cp' + svg.id + '">' +
    '<path d="M70,55 L70,95 Q40,115 40,160 L40,215 Q40,228 55,228 L145,228 Q160,228 160,215 L160,160 Q160,115 130,95 L130,55 Z"/>' +
    '</clipPath></defs>' +
    '<path d="M70,40 L70,95 Q40,115 40,160 L40,215 Q40,228 55,228 L145,228 Q160,228 160,215 L160,160 Q160,115 130,95 L130,40 Z" fill="rgba(255,255,255,.55)" stroke="#b9ae99" stroke-width="2"/>' +
    '<g clip-path="url(#cp' + svg.id + ')">' +
    '<rect x="30" y="' + y + '" width="140" height="' + (h+6) + '" fill="' + colore + '"/>' +
    '<ellipse cx="100" cy="' + y + '" rx="70" ry="5" fill="' + colore + '" opacity=".75"/>' +
    '</g>' +
    '<path d="M78,60 L78,100 Q52,118 52,158 L52,210" fill="none" stroke="rgba(255,255,255,.6)" stroke-width="4" stroke-linecap="round"/>' +
    '<rect x="66" y="30" width="68" height="14" rx="4" fill="#8a7a5e"/>' +
    '<text x="100" y="252" text-anchor="middle" font-family="Georgia,serif" font-size="14" fill="#2b2118">' + etichetta + '</text>';
}

function disegnaFreccia(fase){
  var svg = $('freccia');
  if (!fase || fase === 'iniziale'){ svg.innerHTML = ''; return; }
  var destra = (fase === 'a');
  var d = destra ? 'M20,120 L120,120' : 'M130,120 L30,120';
  var punta = destra
    ? '<polygon points="120,112 138,120 120,128" fill="#2b2118"/>'
    : '<polygon points="30,112 12,120 30,128" fill="#2b2118"/>';
  svg.innerHTML =
    '<path d="' + d + '" stroke="#2b2118" stroke-width="2.5" stroke-dasharray="7 5">' +
    '<animate attributeName="stroke-dashoffset" from="24" to="0" dur="0.6s" repeatCount="indefinite"/></path>' +
    punta +
    '<text x="75" y="104" text-anchor="middle" font-family="Georgia,serif" font-size="13" fill="#2b2118">1 mestolo</text>';
}

function mostra(i){
  var s = STATI[i], A = s.A, B = s.B;
  var tA = A.bianco + A.rosso, tB = B.bianco + B.rosso;

  disegnaDamigiana($('damA'), A.bianco, A.rosso, 'Damigiana A');
  disegnaDamigiana($('damB'), B.bianco, B.rosso, 'Damigiana B');
  disegnaFreccia(s.fase);

  $('stato').textContent = s.etichetta;
  $('aB').textContent = fmt(A.bianco);
  $('aR').textContent = fmt(A.rosso);
  $('aT').textContent = fmt(tA);
  $('bB').textContent = fmt(B.bianco);
  $('bR').textContent = fmt(B.rosso);
  $('bT').textContent = fmt(tB);

  $('barAB').style.width = (A.bianco / tA * 100) + '%';
  $('barAR').style.width = (A.rosso  / tA * 100) + '%';
  $('barBB').style.width = (B.bianco / tB * 100) + '%';
  $('barBR').style.width = (B.rosso  / tB * 100) + '%';

  disegnaGrafico(i);
}

function disegnaGrafico(fino){
  var cv = $('grafico'), ctx = cv.getContext('2d');
  var W = cv.width, H = cv.height, mt = 22, mr = 22, mb = 30, ml = 46;
  ctx.clearRect(0, 0, W, H);

  var n = STATI.length - 1;
  function px(i){ return ml + (W - ml - mr) * (i / n); }
  function py(p){ return mt + (H - mt - mb) * (1 - p); }

  ctx.strokeStyle = '#ece5d6'; ctx.lineWidth = 1;
  ctx.font = '11px Georgia'; ctx.fillStyle = '#9c9384'; ctx.textAlign = 'right';
  [0, .25, .5, .75, 1].forEach(function(p){
    ctx.beginPath(); ctx.moveTo(ml, py(p)); ctx.lineTo(W - mr, py(p)); ctx.stroke();
    ctx.fillText((p * 100) + '%', ml - 8, py(p) + 4);
  });

  ctx.strokeStyle = '#c4bba6'; ctx.setLineDash([4, 4]);
  ctx.beginPath(); ctx.moveTo(ml, py(.5)); ctx.lineTo(W - mr, py(.5)); ctx.stroke();
  ctx.setLineDash([]);

  function traccia(chiave, colore){
    ctx.strokeStyle = colore; ctx.lineWidth = 2; ctx.beginPath();
    for (var i = 0; i <= fino; i++){
      var d = STATI[i][chiave];
      var p = d.bianco / (d.bianco + d.rosso);
      if (i === 0) ctx.moveTo(px(i), py(p)); else ctx.lineTo(px(i), py(p));
    }
    ctx.stroke();
    var d2 = STATI[fino][chiave];
    var p2 = d2.bianco / (d2.bianco + d2.rosso);
    ctx.fillStyle = colore;
    ctx.beginPath(); ctx.arc(px(fino), py(p2), 4, 0, 6.284); ctx.fill();
  }
  traccia('A', '#b8860b');
  traccia('B', '#7b1230');

  ctx.textAlign = 'left'; ctx.font = '12px Georgia';
  ctx.fillStyle = '#b8860b'; ctx.fillText('% bianco in A', ml + 6, mt + 14);
  ctx.fillStyle = '#7b1230'; ctx.fillText('% bianco in B', ml + 110, mt + 14);
}

function ferma(){ if (timer){ clearInterval(timer); timer = null; } $('btnPlay').textContent = 'Avvia'; }
function passo(){ if (idx < STATI.length - 1){ idx++; mostra(idx); } else ferma(); }
function play(){
  if (timer){ ferma(); return; }
  if (idx >= STATI.length - 1){ idx = 0; mostra(0); }
  $('btnPlay').textContent = 'Pausa';
  var v = parseInt($('velocita').value) || 700;
  timer = setInterval(passo, Math.max(80, v));
}

$('btnPlay').onclick = play;
$('btnStep').onclick = function(){ ferma(); passo(); };
$('btnReset').onclick = function(){ ferma(); idx = 0; mostra(0); };

mostra(0);
</script>
</body>
</html>
"""


def main():
    stati = simula(CAPIENZA, MESTOLO, CICLI)

    parametri = "%g L per damigiana, mestolo da %g L, %d cicli" % (
        CAPIENZA, MESTOLO, CICLI)

    html = MODELLO
    html = html.replace("__DATI__", json.dumps(stati))
    html = html.replace("__CAPIENZA__", repr(CAPIENZA))
    html = html.replace("__PARAMETRI__", parametri)

    percorso = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "travasi.html")
    with open(percorso, "w", encoding="utf-8") as f:
        f.write(html)

    finale = stati[-1]
    print("Creato:", percorso)
    print()
    print("Risultato dopo %d cicli:" % CICLI)
    print("  Damigiana A -> bianco %.4f L   rosso %.4f L"
          % (finale["A"]["bianco"], finale["A"]["rosso"]))
    print("  Damigiana B -> bianco %.4f L   rosso %.4f L"
          % (finale["B"]["bianco"], finale["B"]["rosso"]))
    print()
    print("Verifica (devono restare pari alla capienza iniziale):")
    print("  bianco totale %.6f L" % (finale["A"]["bianco"] + finale["B"]["bianco"]))
    print("  rosso  totale %.6f L" % (finale["A"]["rosso"] + finale["B"]["rosso"]))

    try:
        webbrowser.open("file://" + percorso)
        print()
        print("Apertura nel browser...")
    except Exception:
        print()
        print("Apri il file con un doppio clic.")


if __name__ == "__main__":
    main()
