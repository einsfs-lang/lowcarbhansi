import json, sys
from reportlab import rl_config
rl_config.useA85 = 0
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import Paragraph, Frame, Table, TableStyle, Spacer
from reportlab.lib.styles import ParagraphStyle
from xml.sax.saxutils import escape as x

w = json.load(open(sys.argv[1], encoding="utf-8"))
W, M = 105 * mm, 5 * mm
IW = W - 2 * M
INK, MUT, LINE, DARK = HexColor("#1C2320"), HexColor("#5E6B64"), HexColor("#DDE3DE"), HexColor("#1F3D30")
KC = {"b": (HexColor("#B5651D"), HexColor("#F8ECE1"), "FRÜHSTÜCK"), "m": (HexColor("#2E6A4E"), HexColor("#E3EEE7"), "MITTAG"), "a": (HexColor("#3F4F8C"), HexColor("#E7EAF6"), "ABEND")}
S = lambda n, **k: ParagraphStyle(n, fontName=k.pop("f", "Helvetica"), fontSize=k.pop("s", 9.5), leading=k.pop("l", 12.5), textColor=k.pop("c", INK), **k)
body, small, lab = S("b"), S("s", s=8.5, l=11), S("l", f="Helvetica-Bold", s=7, l=9, c=MUT)
h2 = S("h2", f="Helvetica-Bold", s=12, l=14.5)
P = lambda t, st=body: Paragraph(t, st)

def box(rows, bg=None, pad=3 * mm, width=None):
    t = Table([[r] for r in rows], colWidths=[width or IW])
    st = [("LEFTPADDING", (0, 0), (-1, -1), pad), ("RIGHTPADDING", (0, 0), (-1, -1), pad),
          ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
          ("TOPPADDING", (0, 0), (-1, 0), pad * .8), ("BOTTOMPADDING", (0, -1), (-1, -1), pad * .8),
          ("BOX", (0, 0), (-1, -1), .6, LINE)]
    if bg: st.append(("BACKGROUND", (0, 0), (-1, -1), bg))
    t.setStyle(TableStyle(st)); return t

def checklist(items, cols=2):
    cells = [P("<font name='ZapfDingbats' color='#8A968F' size='7'>o</font>&nbsp;" + x(i), small) for i in items]
    if cols == 1: rows = [[c] for c in cells]
    else:
        half = (len(cells) + 1) // 2
        a, b = cells[:half], cells[half:] + [""] * (half - len(cells[half:]))
        rows = list(zip(a, b))
    t = Table(rows, colWidths=[(IW - 6 * mm) / cols] * cols)
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 2), ("TOPPADDING", (0, 0), (-1, -1), .6), ("BOTTOMPADDING", (0, 0), (-1, -1), .6), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t

def meal(m):
    fg, bg, _ = KC[m["k"]]
    head = Table([[P(f"<font color='#{fg.hexval()[2:]}'><b>{x(m['label']).upper()}</b></font>", S('x', s=7.5, l=9)), P(x(m["time"]), S('t', s=8, l=9, c=MUT, alignment=2))],
                  [P(x(m["name"]), h2), ""]], colWidths=[IW * .62, IW * .38])
    head.setStyle(TableStyle([("SPAN", (0, 1), (1, 1)), ("BACKGROUND", (0, 0), (-1, -1), bg), ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm), ("TOPPADDING", (0, 0), (-1, 0), 2.2 * mm), ("BOTTOMPADDING", (0, 1), (-1, 1), 2.2 * mm), ("BOX", (0, 0), (-1, -1), .6, LINE)]))
    steps = [P(f"<b>{i}.</b> {x(s)}", body) for i, s in enumerate(m["steps"], 1)]
    rows = [P("ZUTATEN", lab), checklist(m["ing"]), Spacer(1, 2 * mm), P("ZUBEREITUNG", lab)] + steps
    if m.get("prep"): rows += [Spacer(1, 1.5 * mm), box([P(f"<font color='#8A5A00'><b>Für morgen:</b></font> {x(m['prep'])}", small)], HexColor("#FBF1D9"), 2.2 * mm, IW - 6 * mm)]
    return [head, box(rows), Spacer(1, 4 * mm)]

def band(title, sub, tag=None):
    return (title, sub, tag)

pages = []
ov = []
for d in w["days"]:
    rows = [P(f"<b>{x(d['title'])}</b> · {x(d['date'])}", body)]
    for m in d["meals"]:
        fg = KC[m["k"]][0]
        rows.append(P(f"<font color='#{fg.hexval()[2:]}' size='7'><b>{KC[m['k']][2]}</b></font>&nbsp;&nbsp;{x(m['name'])}", small))
    ov += [box(rows), Spacer(1, 2.5 * mm)]
rules = [P("• Abends die doppelte Menge kochen – die zweite Portion ist dein Mittagessen am nächsten Tag.", body),
         P("• Samstag einkaufen (Liste auf Seite 2), Sonntagabend das Mittagessen für Montag vorbereiten.", body),
         P("• Snacks bei Bedarf: " + x(w.get("snacks", "")), body), Spacer(1, 3 * mm)]
pages.append((("Low-Carb Woche", w["title"], "Eine Seite pro Tag – einfach weiterblättern"), rules + ov))
shop = []
for s in w["shopping"]:
    shop += [P(x(s["section"]).upper(), S("sh", f="Helvetica-Bold", s=8, l=10, c=HexColor("#2E6A4E"))), Spacer(1, 1 * mm), checklist(s["items"], 1), Spacer(1, 3.5 * mm)]
pages.append((("Einkaufsliste", "Für die ganze Woche · Samstag erledigen", None), shop))
for d in w["days"]:
    dinner = next((m for m in d["meals"] if m["k"] == "a"), None)
    fl = []
    for m in d["meals"]: fl += meal(m)
    pages.append(((d["title"], d["date"] + (" · " + d["hint"] if d.get("hint") else ""), ("Heute kochen: " + dinner["time"]) if dinner else None), fl))

c = canvas.Canvas(sys.argv[2], pageCompression=1)
c.setTitle("Low-Carb Wochenplan " + w["title"])
BH = 22 * mm
for (title, sub, tag), fl in pages:
    hs = [f.wrap(IW, 10000)[1] for f in fl]
    H = max(BH + 5 * mm + sum(hs) + 6 * mm, 190 * mm)
    c.setPageSize((W, H))
    c.setFillColor(DARK); c.rect(0, H - BH, W, BH, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("Helvetica-Bold", 18); c.drawString(M, H - 10 * mm, title)
    c.setFont("Helvetica", 9); c.drawString(M, H - 15 * mm, sub)
    if tag:
        c.setFont("Helvetica-Bold", 8); tw = c.stringWidth(tag, "Helvetica-Bold", 8)
        c.setFillColor(HexColor("#E9C26A")); c.roundRect(M, H - 20.3 * mm, tw + 4 * mm, 4.4 * mm, 1.5 * mm, fill=1, stroke=0)
        c.setFillColor(DARK); c.drawString(M + 2 * mm, H - 19.1 * mm, tag)
    y = H - BH - 5 * mm
    for f, h in zip(fl, hs):
        f.drawOn(c, M, y - h); y -= h
    c.showPage()
c.save()
print("ok")
