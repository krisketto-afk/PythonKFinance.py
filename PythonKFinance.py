"""
VALUE SCOUT — Report Settimanale Deep Value
============================================
Invia ogni sabato mattina un'analisi AI di stock con sconto 150%+.

SETUP (10 minuti):
1. Vai su https://www.pythonanywhere.com — registrati gratis
2. Carica questo file
3. Installa: pip install anthropic (nella console PythonAnywhere)
4. Compila le variabili sotto (ANTHROPIC_API_KEY, EMAIL_FROM, EMAIL_TO, EMAIL_PASSWORD)
5. In "Tasks" su PythonAnywhere: imposta ogni sabato alle 07:00
   → comando: python3 /home/TUO_USERNAME/value_scout_weekly.py

CREDENZIALI GMAIL:
- Vai su myaccount.google.com → Sicurezza → Password app
- Genera una "App password" per "Mail" → usala come EMAIL_PASSWORD
- NON usare la tua password Gmail normale
"""

import anthropic
import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# ============================================================
# ⚙️  CONFIGURA QUESTE VARIABILI
# ============================================================
import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
EMAIL_FROM        = os.environ.get("EMAIL_FROM")
EMAIL_PASSWORD    = os.environ.get("EMAIL_PASSWORD")
EMAIL_TO          = os.environ.get("EMAIL_TO")
# ============================================================

SYSTEM_PROMPT = """Sei un analista finanziario senior specializzato in deep value investing.
Il tuo approccio: cerchi azioni con sconto del 150-200% rispetto al valore intrinseco,
usando analisi fondamentale (P/E, P/B, EV/EBITDA, DCF, backlog ordini, cassa netta)
combinata con analisi tecnica settimanale (Bande di Bollinger, Heikin Ashi, Stocastico, MACD).

Prediligi: small/mid cap italiane ed europee su EGM/STAR, industrial, infrastrutture,
semiconduttori, energia. Eviti le big tech già pienamente prezzate.

Rispondi SOLO con JSON valido, nessun testo fuori dal JSON."""

USER_PROMPT = """Oggi è {date}. Genera il report settimanale deep value.

Rispondi SOLO con questo JSON (nessun testo extra, nessun markdown):
{{
  "week": "{date}",
  "marketMood": "Bullish | Neutral | Bearish",
  "moodSummary": "2-3 righe sul contesto macro della settimana",
  "picks": [
    {{
      "ticker": "TICKER",
      "name": "Nome Azienda",
      "exchange": "BIT | NYSE | NASDAQ | XETRA | ecc.",
      "sector": "settore",
      "country": "Italia | USA | Germania | ecc.",
      "currentPrice": "prezzo",
      "currency": "EUR | USD",
      "fairValue": "valore intrinseco stimato",
      "discount": "sconto rispetto al fair value es: -42%",
      "upsidePotential": "potenziale rialzo es: +150%",
      "fundamentals": "2 righe sui fondamentali chiave",
      "technicalSetup": "setup tecnico settimanale (BB, MACD, Stocastico)",
      "catalyst": "catalizzatore atteso nei prossimi 3-6 mesi",
      "mainRisk": "rischio principale",
      "conviction": "Alta | Media | Speculativa",
      "action": "Accumula | Aspetta pullback | Entry immediata | Solo watchlist"
    }}
  ],
  "watchlist": [
    {{"ticker": "TICK", "note": "perché tenerlo d'occhio"}}
  ],
  "weeklyInsight": "osservazione di mercato più importante della settimana, 3-4 righe",
  "avoidList": ["TICKER1", "TICKER2"],
  "avoidReason": "perché evitare questi titoli ora"
}}

Fornisci:
- 2 pick USA/internazionali con forte sconto fondamentale
- 1 pick italiano o europeo piccolo/medio (EGM, STAR, Euronext)
- 1 pick speculativo high-risk/high-reward
- 3-4 titoli in watchlist con nota
- 2 titoli da evitare

Usa dati e contesto reale aggiornato a oggi."""


def get_weekly_analysis():
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    today = datetime.now().strftime("%A %d %B %Y")

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT.format(date=today)
        }]
    )

    raw = message.content[0].text
    
    # Pulizia più aggressiva del JSON
    import re
    # Cerca il primo { e l'ultimo } e prende tutto in mezzo
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        clean = match.group(0)
    else:
        clean = raw.replace("```json", "").replace("```", "").strip()
    
    # Debug: stampa i primi 200 caratteri se c'è errore
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        print(f"\n  ⚠️ Raw response (primi 500 char):\n{raw[:500]}")
        raise

def conviction_badge(conv):
    colors = {
        "Alta":        ("#d4f57a", "#1a2600"),
        "Media":       ("#ffd97a", "#261a00"),
        "Speculativa": ("#ff8a8a", "#260000"),
    }
    bg, fg = colors.get(conv, ("#aaa", "#000"))
    return f'<span style="background:{bg};color:{fg};padding:2px 10px;border-radius:3px;font-size:11px;font-weight:bold;letter-spacing:1px">{conv.upper()}</span>'


def action_badge(action):
    colors = {
        "Accumula":        "#d4f57a",
        "Entry immediata": "#ff8a8a",
        "Aspetta pullback": "#ffd97a",
        "Solo watchlist":  "#aaa",
    }
    color = colors.get(action, "#aaa")
    return f'<span style="color:{color};font-weight:bold">{action}</span>'


def build_html(data):
    today = datetime.now().strftime("%d %B %Y")
    mood_color = {"Bullish": "#d4f57a", "Bearish": "#ff8a8a", "Neutral": "#ffd97a"}.get(data.get("marketMood", ""), "#aaa")

    picks_html = ""
    for i, p in enumerate(data.get("picks", []), 1):
        picks_html += f"""
        <div style="background:#0f0f1a;border:1px solid #2a2a3a;border-left:4px solid #c8f060;
                    margin-bottom:20px;padding:22px;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px">
            <div>
              <span style="font-size:22px;font-weight:bold;color:#c8f060;letter-spacing:-0.5px">
                {p.get('ticker','')}
              </span>
              <span style="color:#555;font-size:13px;margin-left:10px">{p.get('name','')}</span><br>
              <span style="color:#444;font-size:11px">{p.get('exchange','')} · {p.get('sector','')} · {p.get('country','')}</span>
            </div>
            <div style="text-align:right">
              {conviction_badge(p.get('conviction',''))}
            </div>
          </div>

          <table style="width:100%;border-collapse:collapse;margin-bottom:14px">
            <tr>
              <td style="padding:8px 12px;background:#080810;border:1px solid #1a1a28;text-align:center">
                <div style="font-size:10px;color:#444;letter-spacing:2px;margin-bottom:4px">PREZZO</div>
                <div style="font-size:16px;color:#aaa;font-weight:bold">{p.get('currentPrice','')} {p.get('currency','')}</div>
              </td>
              <td style="padding:8px 12px;background:#080810;border:1px solid #1a1a28;text-align:center">
                <div style="font-size:10px;color:#444;letter-spacing:2px;margin-bottom:4px">FAIR VALUE</div>
                <div style="font-size:16px;color:#aaa;font-weight:bold">{p.get('fairValue','')} {p.get('currency','')}</div>
              </td>
              <td style="padding:8px 12px;background:#080810;border:1px solid #1a1a28;text-align:center">
                <div style="font-size:10px;color:#444;letter-spacing:2px;margin-bottom:4px">SCONTO</div>
                <div style="font-size:16px;color:#ff8a8a;font-weight:bold">{p.get('discount','')}</div>
              </td>
              <td style="padding:8px 12px;background:#080810;border:1px solid #1a1a28;text-align:center">
                <div style="font-size:10px;color:#444;letter-spacing:2px;margin-bottom:4px">UPSIDE</div>
                <div style="font-size:16px;color:#c8f060;font-weight:bold">{p.get('upsidePotential','')}</div>
              </td>
            </tr>
          </table>

          <div style="margin-bottom:10px">
            <span style="font-size:10px;color:#555;letter-spacing:2px">FONDAMENTALI: </span>
            <span style="font-size:12px;color:#999">{p.get('fundamentals','')}</span>
          </div>
          <div style="margin-bottom:10px">
            <span style="font-size:10px;color:#555;letter-spacing:2px">SETUP TECNICO: </span>
            <span style="font-size:12px;color:#c8f060">{p.get('technicalSetup','')}</span>
          </div>
          <div style="margin-bottom:10px">
            <span style="font-size:10px;color:#555;letter-spacing:2px">CATALIZZATORE: </span>
            <span style="font-size:12px;color:#ffd97a">{p.get('catalyst','')}</span>
          </div>
          <div style="margin-bottom:14px">
            <span style="font-size:10px;color:#555;letter-spacing:2px">RISCHIO: </span>
            <span style="font-size:12px;color:#ff8a8a">{p.get('mainRisk','')}</span>
          </div>
          <div style="padding:10px 14px;background:#080810;border:1px solid #1a1a28;
                      font-size:12px;color:#666;letter-spacing:1px">
            AZIONE SUGGERITA: {action_badge(p.get('action',''))}
          </div>
        </div>"""

    watchlist_rows = ""
    for w in data.get("watchlist", []):
        watchlist_rows += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #1a1a28;color:#c8f060;font-weight:bold;
                     font-size:14px;white-space:nowrap">{w.get('ticker','')}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #1a1a28;color:#666;font-size:12px">
            {w.get('note','')}</td>
        </tr>"""

    avoid_items = ""
    for t in data.get("avoidList", []):
        avoid_items += f'<span style="background:#1a0808;border:1px solid #f44;color:#f88;padding:4px 12px;margin-right:8px;font-size:12px">{t}</span>'

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  body {{ margin:0;padding:0;background:#050d1a;font-family:'Courier New',monospace;color:#e8e0d0; }}
  @media only screen and (max-width:600px) {{
    .container {{ padding:16px !important; }}
    table.prices td {{ padding:6px 6px !important; }}
  }}
</style></head>
<body>
<div class="container" style="max-width:680px;margin:0 auto;padding:32px 24px">

  <!-- Header -->
  <div style="border-bottom:2px solid #c8f060;padding-bottom:20px;margin-bottom:28px">
    <div style="font-size:10px;letter-spacing:4px;color:#444;margin-bottom:6px">VALUE SCOUT · REPORT SETTIMANALE</div>
    <div style="font-size:28px;font-weight:bold;color:#c8f060;letter-spacing:-0.5px">DEEP VALUE RADAR</div>
    <div style="font-size:12px;color:#444;margin-top:4px">{today} · 150%+ discount filter · Fondamentali + Tecnica</div>
  </div>

  <!-- Market Mood -->
  <div style="background:#0f0f1a;border:1px solid #1e1e30;padding:18px;margin-bottom:28px">
    <div style="font-size:10px;letter-spacing:3px;color:#444;margin-bottom:10px">SENTIMENT DI MERCATO</div>
    <div style="display:inline-block;padding:4px 16px;background:{mood_color}22;border:1px solid {mood_color};
                color:{mood_color};font-size:13px;font-weight:bold;letter-spacing:2px;margin-bottom:12px">
      {data.get('marketMood','').upper()}
    </div>
    <div style="font-size:13px;color:#888;line-height:1.6">{data.get('moodSummary','')}</div>
  </div>

  <!-- Picks -->
  <div style="font-size:10px;letter-spacing:3px;color:#444;margin-bottom:16px">I PICKS DELLA SETTIMANA</div>
  {picks_html}

  <!-- Watchlist -->
  <div style="background:#0c0c16;border:1px solid #1e1e30;padding:20px;margin-bottom:20px">
    <div style="font-size:10px;letter-spacing:3px;color:#444;margin-bottom:14px">WATCHLIST</div>
    <table style="width:100%;border-collapse:collapse">
      {watchlist_rows}
    </table>
  </div>

  <!-- Avoid -->
  <div style="background:#0c0c16;border:1px solid #1e1e30;padding:20px;margin-bottom:20px">
    <div style="font-size:10px;letter-spacing:3px;color:#f44;margin-bottom:12px">DA EVITARE QUESTA SETTIMANA</div>
    <div style="margin-bottom:10px">{avoid_items}</div>
    <div style="font-size:12px;color:#666">{data.get('avoidReason','')}</div>
  </div>

  <!-- Insight -->
  <div style="background:#0c0c16;border-left:4px solid #c8f060;padding:20px;margin-bottom:28px">
    <div style="font-size:10px;letter-spacing:3px;color:#444;margin-bottom:12px">INSIGHT DELLA SETTIMANA</div>
    <div style="font-size:14px;color:#c8f060;line-height:1.7;font-style:italic">
      "{data.get('weeklyInsight','')}"
    </div>
  </div>

  <!-- Footer -->
  <div style="border-top:1px solid #1a1a28;padding-top:16px;font-size:10px;color:#333;line-height:1.6">
    ⚠️ Questo report è generato da AI a scopo informativo.<br>
    Non costituisce consulenza finanziaria. Verifica sempre i dati su TradingView prima di operare.<br>
    <span style="color:#1e1e30">VALUE SCOUT · Deep Value Weekly · {today}</span>
  </div>

</div>
</body></html>"""


def send_email(html_content, subject):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_FROM
    msg["To"]      = EMAIL_TO
    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())


def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Value Scout — avvio scan settimanale...")

    try:
        print("  → Chiamata a Claude API...")
        data = get_weekly_analysis()
        print(f"  → {len(data.get('picks',[]))} picks generati")

        print("  → Generazione email HTML...")
        today = datetime.now().strftime("%d %B %Y")
        html  = build_html(data)

        mood  = data.get("marketMood", "")
        subject = f"📊 Value Scout — {today} · {mood} · {len(data.get('picks',[]))} picks"

        print("  → Invio email...")
        send_email(html, subject)
        print(f"  ✅ Report inviato a {EMAIL_TO}")

    except json.JSONDecodeError as e:
        print(f"  ❌ Errore parsing JSON: {e}")
    except smtplib.SMTPException as e:
        print(f"  ❌ Errore invio email: {e}")
    except Exception as e:
        print(f"  ❌ Errore: {e}")
        raise


if __name__ == "__main__":
    main()

    