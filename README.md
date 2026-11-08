# ELDA Imagistică Medicală – site static

Site static (HTML/CSS/JS) pentru https://elda.com.ro, publicat prin GitHub Pages.
Fără WordPress, PHP sau MySQL. Paginile se generează automat din fișiere de date.

## Cum editezi prețurile
1. Deschide `data/preturi.csv` în GitHub (creion ✏️ sau „Edit this file”).
2. Schimbă valoarea din coloana `pret_lei` (doar numărul, ex. `750`).
3. Pentru un serviciu nou adaugi un rând: `categorie,serviciu,pret_lei`. O categorie nouă apare automat în pagina `/preturi`.
4. „Commit changes”. În ~1 minut site-ul se actualizează singur (tab-ul **Actions** arată progresul).

Prețul „de la X lei” de pe paginile RMN se calculează automat din acest fișier.

## Alte date
| Ce vrei să schimbi | Fișier |
|---|---|
| Telefoane, adrese, program, e-mail, WhatsApp, testimoniale, parteneri | `data/site.json` |
| Texte pagini RMN (descrieri, întrebări, durată) | `data/servicii_rmn.json` |
| Texte „Despre noi”, „Informații pacienți”, CT, întrebări frecvente, pagini legale | `content/*.html` |
| Culori / aspect | `assets/css/style.css` (culoarea siglei: `--brand: #800000`) |

## Publicare (o singură dată)
Settings → Pages → **Source: GitHub Actions**. Domeniul `elda.com.ro` rămâne setat prin fișierul `CNAME` (generat automat).

## Structura
```
build.py            generatorul (doar Python, fără pachete externe)
data/               date editabile (prețuri, clinici, servicii)
content/            texte lungi
assets/             css, js, imagini WebP
static/             favicon, iconițe (copiate în rădăcina site-ului)
.github/workflows/  publicare automată
```
Local: `python3 build.py` → rezultatul e în `dist/` (nu se încarcă în Git).

## SEO / GEO
Adresele (URL) paginilor existente sunt păstrate identic. Se generează automat: `sitemap.xml`, `robots.txt`, `llms.txt`, date structurate schema.org (clinici, FAQ, prețuri, breadcrumbs) și canonical pe fiecare pagină.
