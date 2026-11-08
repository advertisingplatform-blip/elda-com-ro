#!/usr/bin/env python3
"""Generator de site static ELDA. Rulare: python3 build.py  ->  folderul dist/
Nu are dependențe externe (doar Python 3.9+). Datele se editează în data/ și content/."""
import csv, json, html, re, shutil, subprocess, datetime, unicodedata
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "dist"
E = html.escape
site = json.loads((ROOT / "data/site.json").read_text("utf-8"))
SERV = json.loads((ROOT / "data/servicii_rmn.json").read_text("utf-8"))
FAQ_RMN = json.loads((ROOT / "data/faq_rmn.json").read_text("utf-8"))
M = json.loads((ROOT / "assets/img/manifest.json").read_text("utf-8"))
URL = site["url"]
CL = site["clinici"]
TODAY = datetime.date.today().isoformat()
YEAR = datetime.date.today().year
PAGES = []  # (path, title, in_sitemap, lastmod)

def git_date(*paths):
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%cs", "--", *paths], cwd=ROOT, capture_output=True, text=True, timeout=20)
        return r.stdout.strip() or TODAY
    except Exception:
        return TODAY

def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def tel(s): return "tel:" + re.sub(r"\D", "", s)
def wa(s): return "https://wa.me/40" + re.sub(r"\D", "", s)[1:]
def lei(n): return f"{int(n)} lei"
def content(name): return (ROOT / "content" / name).read_text("utf-8")

# ---------- prețuri (data/preturi.csv) ----------
CATS = {}
with open(ROOT / "data/preturi.csv", encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        CATS.setdefault(r["categorie"].strip(), []).append((r["serviciu"].strip(), int(r["pret_lei"])))
def pmin(cat): return min(p for _, p in CATS[cat])
PRICE_DATE = git_date("data/preturi.csv")

# ---------- elemente de HTML ----------
def img(k, alt, sizes="100vw", cls="", eager=False):
    m = M[k]; ws = m["sizes"]; w = ws[-1]; h = round(m["h"] * w / m["w"])
    srcset = ", ".join(f"/assets/img/{k}-{x}.webp {x}w" for x in ws)
    attrs = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    c = f' class="{cls}"' if cls else ""
    return f'<img{c} src="/assets/img/{k}-{w}.webp" srcset="{srcset}" sizes="{sizes}" width="{w}" height="{h}" alt="{E(alt)}" {attrs}>'

def btn_call(c, cls="", label=None):
    return f'<a class="btn {cls}" href="{tel(c["telefon"])}">📞 {label or "Sună: " + c["telefon"]}</a>'
def btn_wa(c, cls=""):
    return f'<a class="btn wa {cls}" href="{wa(c["whatsapp"])}" rel="noopener">WhatsApp {c["scurt"]}</a>'
def btn_prog(cls="ghost"):
    return f'<a class="btn {cls}" href="/contact">Solicită o programare</a>'

def faq_html(items):
    out = []
    for it in items:
        a = "".join(f"<p>{E(x)}</p>" for x in it["a"])
        if it.get("ul"): a += "<ul>" + "".join(f"<li>{E(x)}</li>" for x in it["ul"]) + "</ul>"
        out.append(f'<details class="faq"><summary>{E(it["q"])}</summary><div class="faq-a">{a}</div></details>')
    return "\n".join(out)

def faq_schema(items):
    return {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": it["q"], "acceptedAnswer": {"@type": "Answer", "text": " ".join(it["a"] + it.get("ul", []))}} for it in items]}

def blocks_html(blocks):
    out = []
    for b in blocks:
        if "p" in b: out.append(f"<p>{E(b['p'])}</p>")
        else: out.append("<ul>" + "".join(f"<li>{E(x)}</li>" for x in b["ul"]) + "</ul>")
    return "\n".join(out)

def price_table(cat, cid=None):
    rows = "".join(f"<tr><td>{E(n)}</td><td>{lei(p)}</td></tr>" for n, p in CATS[cat])
    idattr = f' id="{cid}"' if cid else ""
    return f'<section class="pcat"{idattr}><h3>{E(cat)}</h3><table class="ptable"><thead><tr><th>Serviciu</th><th>Preț</th></tr></thead><tbody>{rows}</tbody></table></section>'

def hours_table():
    p = site["program"]
    return f'<table class="hours"><tr><td>{p["zile"]}</td><td>{p["deschis"]} – {p["inchis"]}</td></tr><tr><td>Sâmbătă – Duminică</td><td>{p["weekend"]}</td></tr></table>'

def clinic_card(c):
    return f'''<article class="card"><h3><a href="/clinic/{c["slug"]}">{E(c["nume"])}</a></h3>
<p><strong>{c["servicii"]}</strong> · {E(c["sector"])}<br>{E(c["adresa"])}, {c["sector"]}, {c["cod"]}<br>Deschis {site["program"]["deschis"]} – {site["program"]["inchis"]} (Luni – Vineri)</p>
<div class="btns">{btn_call(c)}{btn_wa(c)}</div><a class="more" href="/clinic/{c["slug"]}">Detalii și cum ajungi →</a></article>'''

# ---------- schema.org ----------
def clinic_ld(c):
    p = site["program"]
    return {"@type": ["MedicalClinic", "LocalBusiness"], "@id": f"{URL}/clinic/{c['slug']}#clinic", "name": f"{site['nume']} – {c['nume']}",
        "url": f"{URL}/clinic/{c['slug']}", "image": f"{URL}/assets/img/og-default.jpg", "telephone": c["telefon"], "email": c["email"],
        "medicalSpecialty": "Radiology", "parentOrganization": {"@id": f"{URL}/#org"},
        "address": {"@type": "PostalAddress", "streetAddress": c["adresa"], "addressLocality": "București", "postalCode": c["cod"], "addressCountry": "RO"},
        "openingHoursSpecification": [{"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "opens": p["deschis"], "closes": p["inchis"]}],
        "sameAs": [c["facebook"]], "areaServed": "București", "priceRange": "RON"}
ORG_LD = {"@type": ["MedicalOrganization", "Organization"], "@id": f"{URL}/#org", "name": site["nume"], "alternateName": "Elda Imagistica Medicala", "url": URL + "/",
    "logo": f"{URL}/assets/img/logo-480.webp", "foundingDate": "1992", "sameAs": [site["facebook"]], "medicalSpecialty": "Radiology",
    "description": "Clinici de imagistică medicală în București: RMN (rezonanță magnetică) și CT, gratuite cu bilet de trimitere și decontate de CAS.",
    "department": [{"@id": f"{URL}/clinic/{c['slug']}#clinic"} for c in CL]}

NAV = [("RMN", "/rmn"), ("CT", "/ct-cu-bilet-de-trimitere"), ("Prețuri", "/preturi"), ("Clinici", "/clinici"), ("Despre noi", "/despre-noi"), ("Contact", "/contact")]

def layout(path, title, desc, body, crumbs=(), ld=(), og="/assets/img/og-default.jpg", noindex=False, in_sitemap=True, src=("build.py",), ptype="WebPage"):
    canon = URL + ("/" if path == "index" else "/" + path)
    graph = list(ld)
    if path == "index": graph = [ORG_LD] + [clinic_ld(c) for c in CL] + graph
    page_ld = {"@type": ptype, "@id": canon + "#page", "url": canon, "name": title, "description": desc, "inLanguage": "ro-RO", "isPartOf": {"@id": URL + "/#site"}, "publisher": {"@id": URL + "/#org"}}
    graph = [{"@type": "WebSite", "@id": URL + "/#site", "url": URL + "/", "name": site["nume"], "inLanguage": "ro-RO"}, page_ld] + graph
    if crumbs:
        items = [("Acasă", "/")] + list(crumbs)
        graph.append({"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": (URL + u) if u else canon} for i, (n, u) in enumerate(items)]})
    cur = "/" + path
    nav = "".join(f'<a href="{u}"{" aria-current=page" if cur == u or cur.startswith(u + "/") else ""}>{n}</a>' for n, u in NAV)
    bc = ""
    if crumbs:
        bc = '<nav class="crumbs wrap" aria-label="Breadcrumb"><a href="/">Acasă</a>' + "".join(f'<span>›</span>{'<a href="' + u + '">' + E(n) + "</a>" if u else E(n)}' for n, u in crumbs) + "</nav>"
    c5, c6 = CL
    robots = '<meta name="robots" content="noindex,follow">' if noindex else '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">'
    foot_clin = "".join(f'<p><strong><a href="/clinic/{c["slug"]}">{E(c["nume"])}</a></strong><br>{E(c["adresa"])}, {c["sector"]}, {c["cod"]}<br><a href="{tel(c["telefon"])}">{c["telefon"]}</a> · <a href="mailto:{c["email"]}">{c["email"]}</a></p>' for c in CL)
    parts = "".join(f'<li><img src="/assets/img/{p["img"]}-{M[p["img"]]["sizes"][-1]}.webp" alt="{E(p["nume"])}" height="46" width="{round(M[p["img"]]["w"]*46/M[p["img"]]["h"])}" loading="lazy" style="display:inline;height:46px;width:auto;margin:0 .6rem .4rem 0;background:#fff;border-radius:8px;padding:4px"></li>' for p in site["parteneri"])
    doc = f'''<!doctype html>
<html lang="ro" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
{robots}
<link rel="canonical" href="{canon}">
<meta name="theme-color" content="#800000">
<meta property="og:type" content="website"><meta property="og:locale" content="ro_RO"><meta property="og:site_name" content="{E(site["nume"])}">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{canon}"><meta property="og:image" content="{URL}{og}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="icon" type="image/png" href="/icon-192.png" sizes="192x192"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="stylesheet" href="/assets/css/style.css?v={YEAR}">
<script>document.documentElement.className="js"</script>
<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))}</script>
</head>
<body>
<a class="skip" href="#main">Sari la conținut</a>
<header class="hdr"><div class="wrap"><a class="logo" href="/" aria-label="{E(site["nume"])} – prima pagină"><img src="/assets/img/logo-480.webp" srcset="/assets/img/logo-240.webp 240w, /assets/img/logo-480.webp 480w" sizes="150px" width="240" height="76" alt="ELDA Imagistică Medicală"></a>
<button class="menu-btn" aria-expanded="false" aria-controls="nav">Meniu</button>
<nav class="nav" id="nav" aria-label="Principal">{nav}</nav></div></header>
{bc}
<main id="main">
{body}
</main>
<footer class="ftr"><div class="wrap"><div class="cols">
<div><img src="/assets/img/logo-alb-440.webp" width="220" height="66" alt="ELDA Imagistică Medicală" loading="lazy"><p>Imagistică medicală de diagnostic (RMN și CT) în București. Din 1992.</p><p>Program: {site["program"]["zile"]}, {site["program"]["deschis"]} – {site["program"]["inchis"]}</p></div>
<div><h3>Clinici</h3>{foot_clin}</div>
<div><h3>Informații</h3><ul><li><a href="/preturi">Prețuri RMN și CT</a></li><li><a href="/informatii-pacienti">Informații pacienți</a></li><li><a href="/intrebari-frecvente">Întrebări frecvente</a></li><li><a href="/#testimoniale">Testimoniale</a></li><li><a href="{site["chestionar"]}" rel="noopener">Chestionar satisfacție</a></li><li><a href="{site["facebook"]}" rel="noopener">Facebook</a></li></ul></div>
</div>
<h3 style="margin-top:1.5rem">În relații contractuale cu</h3><ul style="display:flex;flex-wrap:wrap">{parts}</ul>
<p><small>© {YEAR} {E(site["nume"])} · <a href="/protectie-datelor-personale">Protecția datelor personale</a> · <a href="/termeni-si-conditii">Termeni și condiții</a> · <a href="/sitemap">Harta site-ului</a></small></p></div></footer>
<div class="mbar"><a href="{tel(c5["telefon"])}">📞 {c5["telefon"]}<small>{c5["nume"]} · {c5["scurt"]}</small></a><a href="{tel(c6["telefon"])}">📞 {c6["telefon"]}<small>{c6["nume"]} · {c6["scurt"]}</small></a></div>
<script src="/assets/js/main.js" defer></script>
</body></html>'''
    fp = OUT / ("index.html" if path == "index" else path + ".html")
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(doc, "utf-8")
    PAGES.append((path, title, in_sitemap and not noindex, git_date(*src)))

def cta_band(h="Programează-te acum", p="Sună sau scrie-ne pe WhatsApp. Pentru investigații cu bilet de trimitere, RMN și CT sunt gratuite."):
    b = "".join(f'<div style="margin:.5rem 0"><strong>{E(c["nume"])}</strong><div class="btns">{btn_call(c, "light", c["telefon"])}{btn_wa(c, "")}</div></div>' for c in CL)
    return f'<section class="cta-band"><div class="wrap"><h2>{h}</h2><p>{p}</p>{b}</div></section>'

def hero(h1, lead, eyebrow="", bullets=(), image=None, btns=True, price=None):
    bl = '<ul class="check">' + "".join(f"<li>{E(b)}</li>" for b in bullets) + "</ul>" if bullets else ""
    pr = f'<p><span class="price-tag">De la {lei(price)}</span></p>' if price else ""
    bt = f'<div class="btns">{btn_call(CL[0])}{btn_prog()}</div>' if btns else ""
    im = f"<div>{image}</div>" if image else ""
    ey = f'<span class="eyebrow">{E(eyebrow)}</span>' if eyebrow else ""
    return f'<section class="hero"><div class="wrap"><div>{ey}<h1>{E(h1)}</h1><p class="lead">{E(lead)}</p>{bl}{pr}{bt}</div>{im}</div></section>'

# ================= PAGINI =================
def build():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    for d in ("assets",): shutil.copytree(ROOT / d, OUT / d)
    for f in (ROOT / "static").iterdir(): shutil.copy(f, OUT / f.name)
    (OUT / "CNAME").write_text("elda.com.ro\n"); (OUT / ".nojekyll").write_text("")
    S = {s["slug"]: s for s in SERV}

    # ---- Acasă
    cards = "".join(f'<a class="card" href="/rmn/{s["slug"]}"><h3>{E(s["h1"])}</h3><p>{E(s["subtitle"])}</p><span class="price-tag">De la {lei(pmin(s["price_category"]))}</span><span class="more">Află mai multe →</span></a>' for s in SERV)
    testi = "".join(f'<blockquote class="card quote"><p>„{E(t["text"])}”</p><cite>{E(t["nume"])}</cite></blockquote>' for t in site["testimoniale"])
    body = hero("Imagistică medicală RMN și CT în București", "Investigații RMN rapide și precise, gratuite cu bilet de trimitere. Aparatură de ultimă generație, specialiști de top și programare în câteva minute.", "Expert care, superior results",
        image=img("hero", "Medic care arată pacientului o scanare RMN a creierului", "(min-width:960px) 45vw, 100vw", eager=True)) \
    .replace('</ul>', '</ul>') 
    body = body.replace('<div class="btns">', '<ul class="trust"><li>Investigații decontate de CAS</li><li>RMN / CT gratuit cu bilet de trimitere</li><li>Rezultate în circa 2 zile</li></ul><div class="btns">', 1)
    body += f'''
<section class="sec"><div class="wrap"><div class="split"><div class="prose">
<h2>Cine suntem</h2>
<p>Clinicile de imagistică medicală ELDA oferă o gamă largă de investigații care să răspundă nevoilor individuale ale pacienților. Consultanții noștri, personal medical cu înaltă calificare, au acces la unele dintre cele mai avansate tehnologii disponibile pe piața serviciilor de imagistică medicală.</p>
<p>Ne mândrim cu menținerea celui mai înalt standard de profesionalism, într-un mediu prietenos și primitor.</p>
<h3>Ce îți oferim?</h3>
<ul class="check"><li><strong>RMN / CT rapid și precis</strong> – utilizăm tehnologie de ultimă generație pentru rezultate clare.</li><li><strong>RMN / CT cu trimitere gratuit</strong> – dacă ai un bilet de trimitere, consultația poate fi fără costuri.</li><li><strong>Programare ușoară</strong> – contactează-ne și stabilește-ți vizita în câteva minute.</li></ul></div>
<div class="card"><h2>Cum beneficiezi de RMN sau CT gratuit cu bilet de trimitere?</h2>
<ol class="steps"><li>Obține un bilet de trimitere de la medicul tău specialist.</li><li>Contactează-ne pentru a programa investigația.</li><li>Bucură-te de un proces rapid, fără griji!</li></ol>
<div class="btns"><a class="btn" href="/contact">Contactează-ne acum!</a></div></div></div></div></section>
<section class="sec soft"><div class="wrap"><h2>Servicii oferite</h2><p>Alege tipul de investigație RMN. Prețurile sunt orientative; lista completă este în <a href="/preturi">pagina de prețuri</a>.</p><div class="grid c3">{cards}</div>
<p style="margin-top:1rem"><a href="/ct-cu-bilet-de-trimitere">Tomografie computerizată (CT) →</a></p></div></section>
<section class="sec"><div class="wrap"><div class="split"><div class="prose"><h2>Despre RMN – Rezonanța Magnetică Nucleară</h2>
<ul class="check"><li>Rezultate rapide</li><li>Metodă neiradiantă</li><li>Excelentă în diagnosticarea cancerului</li><li>Metodă de investigație cu exactitate</li></ul>
<p>Scanarea RMN (Rezonanță Magnetică) este un examen neinvaziv, care efectuează imagini ale întregului corp fără a expune pacientul la radiații ionizante. Tehnologia utilizează magneți și unde radio pentru a crea imagini transversale din interiorul corpului dumneavoastră, ajutând medicii să diagnosticheze și să monitorizeze o gamă largă de afecțiuni. Scanarea RMN este nedureroasă, fără disconfort.</p>
<a class="btn ghost" href="/rmn">Tot despre RMN</a></div>{img("rmn-scan", "Pacient pregătit pentru examinare RMN, alături de medic", "(min-width:960px) 45vw, 100vw", "photo")}</div></div></section>
<section class="sec tint" id="testimoniale"><div class="wrap"><h2>Ce spun pacienții</h2><div class="grid c3">{testi}</div>
<p class="note" style="margin-top:1rem">Evaluare medie 4,59 din 5 (109 recenzii).</p></div></section>
<section class="sec"><div class="wrap">{img("aparatura", "Aparat de rezonanță magnetică ELDA", "100vw", "photo")}<div class="split" style="margin-top:1.5rem"><div class="prose"><h2>Aparatură de ultimă generație</h2>
<ul class="check"><li>Toate mașinile noastre sunt aprobate de FDA cu tehnologie de vârf</li><li>Echipamentul nostru este medical clasificat</li><li>Imagini de înaltă rezoluție de la cap la vârf cu bobine de canal înalt</li><li>Bobinele ușoare pentru pacienți permit o mai mare flexibilitate</li></ul></div>
<div class="prose"><h2>Avantajele examinării RMN</h2><p>RMN este o metodă care, prin realizarea unor imagini extrem de precise, tridimensionale ale corpului, ajută la obiectivarea modificărilor de la nivelul diverselor structuri din corp, facilitând diagnosticul și urmărirea cu precizie a tratamentului multor afecțiuni. Imaginile ajută, de asemenea, la îmbunătățirea evaluării chirurgicale și a procedurilor preoperatorii și postoperatorii. Scanarea RMN poate fi asociată cu alte evaluări imagistice, cum ar fi angiografia cu rezonanță magnetică, în care medicul obține imagini RMN ale vaselor dumneavoastră, după injectarea unei substanțe de contrast.</p>
<ul class="check"><li>Creierul și măduva spinării</li><li>Ureche, nas și gât</li><li>Oase și articulații (leziuni sportive, traumatice sau afecțiuni cronice)</li><li>Sâni</li><li>Cord și vase de sânge</li><li>Organe genitale</li></ul></div></div></div></section>
<section class="sec soft"><div class="wrap"><h2>Găsește cea mai apropiată clinică din București</h2><div class="grid c2">{"".join(clinic_card(c) for c in CL)}</div></div></section>
{cta_band()}'''
    layout("index", "ELDA Imagistică Medicală | RMN și CT în București – gratuit cu bilet de trimitere",
        "Clinicile de imagistică medicală ELDA realizează investigații RMN rapide și precise! Beneficiază de RMN sau CT gratuit cu bilet de trimitere și află cum poți programa o consultație chiar acum.",
        body, src=("data/site.json", "build.py"))

    # ---- RMN (prezentare)
    gcards = "".join(f'<a class="card" href="/rmn/{s["slug"]}"><h3>{E(s["h1"])}</h3><ul class="check">' + "".join(f"<li>{E(b)}</li>" for b in s["bullets"]) + f'</ul><span class="price-tag">De la {lei(pmin(s["price_category"]))}</span></a>' for s in SERV)
    body = hero("RMN – Rezonanța Magnetică Nucleară", "Metodă neiradiantă, excelentă în diagnosticarea cancerului, cu exactitate ridicată.", "Investigații", ["Metodă neiradiantă", "Excelent în diagnosticarea cancerului", "Metodă de investigație cu exactitate"], img("rmn-scan", "Examinare RMN la clinicile ELDA", "(min-width:960px) 45vw, 100vw", eager=True))
    body += f'<section class="sec"><div class="wrap"><h2>Tipuri de investigații RMN</h2><div class="grid c3">{gcards}</div></div></section>'
    body += f'<section class="sec soft"><div class="wrap prose">{content("rmn-detalii.html")}<div class="btns">{btn_call(CL[0], "", "Sună acum pentru programare!")}</div></div></section>'
    body += f'<section class="sec"><div class="wrap prose"><h2>Întrebări frecvente despre RMN</h2>{faq_html(FAQ_RMN)}</div></section>' + cta_band()
    layout("rmn", "RMN București – Rezonanță Magnetică Nucleară | ELDA", "Află tot ce trebuie să știi despre RMN: cum se desfășoară, cine poate efectua investigația, cât costă și cum beneficiezi gratuit cu bilet de trimitere la clinicile ELDA din București.",
        body, [("RMN", None)], [faq_schema(FAQ_RMN)], src=("data/faq_rmn.json", "content/rmn-detalii.html", "data/servicii_rmn.json"))

    # ---- pagini RMN individuale
    imgs = {"coloana": "echipa", "articular": "ortopedie", "abdominal": "sala-rmn", "pelvin": "doctori", "extremitati": "examinare", "cerebro-medular": "sala-larga", "cerebral": "hero"}
    for s in SERV:
        pm = pmin(s["price_category"]); sib = "".join(f'<a class="card" href="/rmn/{o["slug"]}"><h3>{E(o["h1"])}</h3><p>{E(o["subtitle"])}</p><span class="price-tag">De la {lei(pmin(o["price_category"]))}</span></a>' for o in SERV if o["slug"] != s["slug"])
        facts = f'<div class="facts"><div class="fact"><b>Preț</b><span>de la {lei(pm)}</span></div><div class="fact"><b>Durată</b><span>{E(s["durata"])}</span></div><div class="fact"><b>Substanță de contrast</b><span>{E(s["injectii"])}</span></div><div class="fact"><b>Rezultate</b><span>{E(s["rezultate"])}</span></div></div>'
        faq = f'<h2>Întrebări frecvente</h2>{faq_html([{"q": f["q"], "a": f["a"]} for f in s["faq"]])}' if s["faq"] else ""
        body = hero(s["h1"], s["subtitle"], "RMN București", s["bullets"], img(imgs[s["slug"]], f'{s["h1"]} – examinare la clinicile ELDA', "(min-width:960px) 45vw, 100vw", eager=True), price=pm)
        body += f'<section class="sec"><div class="wrap prose"><h2>Pe scurt</h2>{facts}{blocks_html(s["blocks"])}{faq}</div></section>'
        body += f'<section class="sec soft"><div class="wrap prose"><h2>Prețuri {E(s["h1"])}</h2><p class="note">Actualizat: {PRICE_DATE}. {E(site["preturi_nota"])}</p>{price_table(s["price_category"])}<a class="btn ghost" href="/preturi">Vezi lista completă de prețuri</a></div></section>'
        body += f'<section class="sec"><div class="wrap"><h2>Alte investigații RMN</h2><div class="grid c3">{sib}</div></div></section>' + cta_band()
        ld = [{"@type": "MedicalProcedure", "name": s["h1"] + " (rezonanță magnetică)", "procedureType": "https://schema.org/NoninvasiveProcedure", "description": s["seo_description"]}]
        if s["faq"]: ld.append(faq_schema([{"q": f["q"], "a": f["a"]} for f in s["faq"]]))
        title = f'{s["h1"]} București – preț de la {lei(pm)} | ELDA'
        layout(f"rmn/{s['slug']}", title, s["seo_description"], body, [("RMN", "/rmn"), (s["h1"], None)], ld, src=("data/servicii_rmn.json", "data/preturi.csv"), ptype="MedicalWebPage")

    # ---- redirect vechi (pagină care nu era în sitemap)
    OUT.joinpath("rmn").mkdir(exist_ok=True)
    (OUT / "rmn/rezonanta-magnetica-nucleara.html").write_text(f'<!doctype html><html lang="ro"><head><meta charset="utf-8"><title>RMN – ELDA Imagistică Medicală</title><link rel="canonical" href="{URL}/rmn"><meta http-equiv="refresh" content="0;url=/rmn"><meta name="robots" content="noindex,follow"></head><body><p><a href="/rmn">Pagina RMN</a></p></body></html>', "utf-8")

    # ---- CT
    ctc = "".join(f'<a class="card" href="/preturi#{slugify(k)}"><h3>{E(k)}</h3><span class="price-tag">De la {lei(pmin(k))}</span></a>' for k in CATS if k.startswith(("CT", "Angio", "Servicii")) and k.startswith(("CT", "Angio")))
    body = hero("CT – Tomografie computerizată", "Imagini detaliate ale corpului, obținute rapid. Gratuit cu bilet de trimitere, la Complex Malcoci.", "Investigații", image=img("sala-rmn", "Sală de investigații cu aparat CT/RMN", "(min-width:960px) 45vw, 100vw", eager=True))
    body += f'<section class="sec"><div class="wrap prose"><p class="note">Program: {site["program"]["zile"]}, {site["program"]["deschis"]} – {site["program"]["inchis"]}. Sâmbătă și duminică: {site["program"]["weekend"].lower()}.</p>{content("ct.html")}</div></section>'
    body += f'<section class="sec soft"><div class="wrap"><h2>Prețuri CT</h2><div class="grid c3">{ctc}</div></div></section>' + cta_band()
    layout("ct-cu-bilet-de-trimitere", "CT București cu bilet de trimitere – Tomografie computerizată | ELDA", "Gama extinsă de servicii de imagistică medicală gratuite, decontate de CAS, cu bilet de trimitere. Află ce este CT-ul, cum funcționează și când este recomandat.", body, [("CT", None)], src=("content/ct.html", "data/preturi.csv"))

    # ---- Prețuri
    chips = "".join(f'<a href="#{slugify(k)}">{E(k)}</a>' for k in CATS)
    tables = "".join(price_table(k, slugify(k)) for k in CATS)
    offers = [{"@type": "ListItem", "position": i + 1, "item": {"@type": "Offer", "priceCurrency": "RON", "price": str(p), "itemOffered": {"@type": "MedicalProcedure", "name": n}, "seller": {"@id": URL + "/#org"}}} for i, (n, p) in enumerate(x for k in CATS for x in CATS[k])]
    body = hero("Prețuri RMN și CT", "Servicii și tarife actualizate. Investigațiile cu bilet de trimitere sunt gratuite.", btns=False)
    body += f'<section class="sec"><div class="wrap prose" style="max-width:860px"><p class="note">Actualizat: {PRICE_DATE}. {E(site["preturi_nota"])}</p><label for="cauta"><strong>Caută o investigație</strong></label><input id="cauta" class="search" type="search" placeholder="ex: genunchi, coloană, abdomen…" autocomplete="off"><nav class="chips" aria-label="Categorii">{chips}</nav><p id="fara-rezultate" class="hide">Nicio investigație găsită. Sună-ne pentru detalii.</p>{tables}</div></section>' + cta_band("Nu găsești investigația căutată?", "Sună-ne și îți spunem prețul exact.")
    layout("preturi", "Prețuri RMN și CT – Servicii și Tarife | ELDA Imagistică Medicală București", "Prețuri RMN și CT în București: lista completă de servicii și tarife ELDA. RMN și CT gratuit cu bilet de trimitere.", body, [("Prețuri", None)],
        [{"@type": "ItemList", "name": "Prețuri RMN și CT", "itemListElement": offers}], src=("data/preturi.csv",))

    # ---- Clinici
    body = hero("Clinici de imagistică medicală în București", "Alege clinica cea mai apropiată de tine.", btns=False)
    body += f'<section class="sec"><div class="wrap"><div class="grid c2">{"".join(clinic_card(c) for c in CL)}</div><div class="prose" style="margin-top:2rem"><h2>Program</h2>{hours_table()}</div></div></section>' + cta_band()
    layout("clinici", "Clinici imagistică medicală RMN și CT București | ELDA", "Clinici de imagistică medicală RMN și CT în București: Complex Malcoci (Sector 5) și Drumul Taberei 115 (Sector 6). Program, adrese și telefoane.", body, [("Clinici", None)], [clinic_ld(c) for c in CL], src=("data/site.json",))

    # ---- pagini clinică
    for c in CL:
        tr = "".join(f"<dt>{E(a)}</dt><dd>{E(b)}</dd>" for a, b in c["transport"])
        desc = "".join(f"<p>{E(x)}</p>" for x in c["descriere"])
        body = hero(f'{c["nume"]} – {c["servicii"]}, {c["sector"]}', f'{c["adresa"]}, {c["sector"]}, {c["cod"]}', "Clinică ELDA", image=img("receptie" if False else "doctori", f'Clinica {c["nume"]}', "(min-width:960px) 45vw, 100vw", eager=True), btns=False)
        body = body.replace("</p></div><div>", f'</p><div class="btns">{btn_call(c)}{btn_wa(c)}<a class="btn ghost" href="mailto:{c["email"]}">{c["email"]}</a></div></div><div>', 1)
        body += f'<section class="sec"><div class="wrap"><div class="split"><div class="prose"><h2>Despre clinica noastră</h2>{desc}<p>Pentru informații și programări ne puteți contacta telefonic, în timpul programului de lucru, la <a href="{tel(c["telefon"])}">{c["telefon"]}</a>, pe WhatsApp la <a href="{wa(c["whatsapp"])}">{c["whatsapp"]}</a>, prin e-mail la <a href="mailto:{c["email"]}">{c["email"]}</a> sau pe <a href="{c["facebook"]}" rel="noopener">Facebook</a>.</p></div><div class="card"><h2>Program</h2>{hours_table()}<h2 style="margin-top:1.2rem">Unde ne găsiți</h2><p>{E(c["adresa"])}, {c["sector"]} {c["cod"]}</p><dl class="dl">{tr}</dl></div></div></div></section>' + cta_band()
        layout(f"clinic/{c['slug']}", c["seo_title"], c["seo_description"], body, [("Clinici", "/clinici"), (c["nume"], None)], [clinic_ld(c)], src=("data/site.json",))

    # ---- text pages
    def textpage(path, title, desc, h1, lead, crumb, frag, image=None, extra="", **kw):
        b = hero(h1, lead, btns=False, image=image) + f'<section class="sec"><div class="wrap prose">{extra}{content(frag)}</div></section>' + cta_band()
        layout(path, title, desc, b, [(crumb, None)], src=(f"content/{frag}",), **kw)
    textpage("despre-noi", "Despre noi – ELDA Imagistică Medicală", "ELDA și-a început activitatea în 1992. Ne-am propus să oferim servicii la nivel cât mai înalt în imagistica medicală RMN și CT.", "Despre noi", "ELDA Imagistică Medicală", "Despre noi", "despre-noi.html", img("echipa", "Echipa medicală ELDA", "(min-width:960px) 45vw, 100vw", eager=True))
    textpage("informatii-pacienti", "Informații pacienți – pregătire și desfășurare RMN | ELDA", "Cum te pregătești pentru RMN, cât durează examinarea, cum se plătește și când primești rezultatul. Informații pentru pacienții ELDA.", "Informații pacienți", "Rezonanța Magnetică Nucleară – ce trebuie să știi înainte, în timpul și după scanare.", "Informații pacienți", "informatii-pacienti.html", extra=f'<h2>Program general</h2>{hours_table()}')
    b = hero("Întrebări frecvente", "Rezonanța magnetică nucleară – răspunsuri la cele mai comune întrebări.", btns=False) + f'<section class="sec"><div class="wrap prose">{content("intrebari-frecvente.html")}</div></section>' + cta_band()
    faq_all = []
    for m in re.finditer(r'<summary>(.*?)</summary><div class="faq-a">(.*?)</div></details>', content("intrebari-frecvente.html"), re.S):
        faq_all.append({"q": html.unescape(m.group(1)), "a": [html.unescape(re.sub(r"<[^>]+>", " ", m.group(2)).strip())]})
    layout("intrebari-frecvente", "Întrebări frecvente despre RMN | ELDA Imagistică Medicală", "Răspunsuri la întrebările frecvente despre RMN: indicații, pregătire, substanță de contrast, sarcină, copii, imobilitate în timpul scanării.", b, [("Întrebări frecvente", None)], [faq_schema(faq_all)], src=("content/intrebari-frecvente.html",))
    textpage("protectie-datelor-personale", "Protecția datelor personale – ELDA", "Prelucrarea și stocarea datelor cu caracter personal la ELDA Imagistică Medicală.", "Protecția datelor personale", "", "Protecția datelor personale", "protectie-datelor-personale.html")
    textpage("termeni-si-conditii", "Termeni și condiții – ELDA", "Termenii și condițiile de utilizare a website-ului ELDA Imagistică Medicală.", "Termeni și condiții", "", "Termeni și condiții", "termeni-si-conditii.html")

    # ---- contact
    form = ""
    if site.get("formular_endpoint"):
        opts = "".join(f'<option>{E(c["nume"])}</option>' for c in CL)
        form = f'<form class="card" method="post" action="{E(site["formular_endpoint"])}"><h2>Solicită o programare</h2><p><label>Clinica<br><select name="clinica" required class="search">{opts}</select></label></p><p><label>Nume<br><input class="search" name="nume" required autocomplete="name"></label></p><p><label>Telefon<br><input class="search" name="telefon" type="tel" required autocomplete="tel"></label></p><p><label>Mesaj<br><textarea class="search" name="mesaj" rows="3"></textarea></label></p><button class="btn" type="submit">Trimite cererea</button></form>'
    body = hero("Contact și programări", "Sună sau scrie-ne pe WhatsApp. Un reprezentant ELDA te poate ajuta să stabilești detaliile vizitei tale medicale.", btns=False)
    body += f'<section class="sec"><div class="wrap"><div class="grid c2">{"".join(clinic_card(c) for c in CL)}</div>{"<div style=margin-top:1.5rem>" + form + "</div>" if form else ""}<div class="prose" style="margin-top:2rem"><h2>Program</h2>{hours_table()}</div></div></section>'
    layout("contact", "Contact și programări – ELDA Imagistică Medicală București", "Programează-te la RMN sau CT: telefoane, WhatsApp, e-mail și adrese pentru clinicile ELDA din București.", body, [("Contact", None)], [clinic_ld(c) for c in CL], src=("data/site.json",))

    # ---- 404
    layout("404", "Pagina nu a fost găsită – ELDA", "Pagina căutată nu există.", hero("Pagina nu a fost găsită", "Link-ul poate fi vechi. Întoarce-te la prima pagină sau alege din meniu.", btns=False) + '<section class="sec"><div class="wrap"><a class="btn" href="/">Prima pagină</a></div></section>', noindex=True)
    (OUT / "404.html").write_text((OUT / "404.html").read_text("utf-8"), "utf-8")

    # ---- sitemap html
    lst = "".join(f'<li><a href="/{"" if p == "index" else p}">{E(t)}</a></li>' for p, t, ok, _ in sorted(PAGES) if ok)
    layout("sitemap", "Harta site-ului – ELDA", "Toate paginile site-ului ELDA Imagistică Medicală.", hero("Harta site-ului", "", btns=False) + f'<section class="sec"><div class="wrap prose"><ul>{lst}</ul></div></section>', [("Harta site-ului", None)], in_sitemap=True)

    # ---- sitemap.xml, robots, llms, manifest
    urls = "".join(f'<url><loc>{URL}{"/" if p == "index" else "/" + p}</loc><lastmod>{d}</lastmod></url>' for p, t, ok, d in sorted(PAGES, key=lambda x: (x[0] != "index", x[0])) if ok)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>', "utf-8")
    bots = "\n".join(f"User-agent: {b}\nAllow: /\n" for b in ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "PerplexityBot", "Google-Extended", "Applebot-Extended", "CCBot"])
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\n{bots}\nSitemap: {URL}/sitemap.xml\n", "utf-8")
    (OUT / "manifest.webmanifest").write_text(json.dumps({"name": site["nume"], "short_name": "ELDA", "start_url": "/", "display": "browser", "theme_color": "#800000", "background_color": "#ffffff", "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}]}, ensure_ascii=False), "utf-8")
    L = [f"# {site['nume']}", "", "> Clinici de imagistică medicală în București: RMN (rezonanță magnetică nucleară) și CT (tomografie computerizată). Activ din 1992. Investigațiile cu bilet de trimitere sunt gratuite (decontate de CAS).", "", "## Fapte cheie",
         f"- Program: {site['program']['zile']}, {site['program']['deschis']}–{site['program']['inchis']}; weekend închis."]
    for c in CL: L.append(f"- {c['nume']} ({c['servicii']}): {c['adresa']}, {c["sector"]}, {c['cod']}; tel {c['telefon']}; WhatsApp {c['whatsapp']}; {c['email']}; {URL}/clinic/{c['slug']}")
    L += [f"- Prețuri: de la {lei(min(pmin(s['price_category']) for s in SERV))} (RMN) și de la {lei(min(pmin(k) for k in CATS if k.startswith(('CT', 'Angio'))))} (CT); listă completă la {URL}/preturi (actualizată {PRICE_DATE})", "", "## Pagini"]
    for p, t, ok, _ in sorted(PAGES):
        if ok and p != "sitemap": L.append(f"- [{t}]({URL}{'/' if p == 'index' else '/' + p})")
    (OUT / "llms.txt").write_text("\n".join(L) + "\n", "utf-8")

def check():
    """Verifică dacă toate link-urile interne duc la pagini existente."""
    bad = 0
    for f in OUT.rglob("*.html"):
        for h in re.findall(r'href="(/[^"#?]*)', f.read_text("utf-8")):
            t = h.rstrip("/") or "/"
            cand = [OUT / (t[1:] + ".html"), OUT / t[1:], OUT / "index.html"] if t != "/" else [OUT / "index.html"]
            if not any(c.is_file() for c in cand[:2] + (cand[2:] if t == "/" else [])): print("LINK RUPT:", f.relative_to(OUT), "->", h); bad += 1
    print("Link-uri interne verificate:", "OK" if not bad else f"{bad} probleme")

if __name__ == "__main__":
    build(); check(); print(len(PAGES), "pagini generate în", OUT)
