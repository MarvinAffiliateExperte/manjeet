# Startseiten-Optimierung kurs-erfahrungen.com (2026)

## Rehub Theme + Elementor Optimierungsplan

---

## Uebersicht der Dateien

| Datei | Zweck |
|-------|-------|
| `rehub-child/functions.php` | Performance-Optimierungen, Asset-Bereinigung, Schema Markup |
| `rehub-child/style.css` | Critical CSS, CLS Prevention, Mobile Optimierung |
| `rehub-child/seo-optimizations.php` | SEO Meta Tags, FAQ Schema, Open Graph |
| `rehub-child/htaccess-optimizations.txt` | Server-seitige Optimierungen (Caching, Komprimierung) |
| `rehub-child/homepage-elementor-template.json` | Empfohlene Seitenstruktur fuer Elementor |

---

## 1. Performance-Optimierungen (Core Web Vitals)

### LCP (Largest Contentful Paint) - Ziel: < 2.5s

- [x] Hero-Bild mit `fetchpriority="high"` markieren (functions.php)
- [ ] Bilder in WebP/AVIF Format konvertieren (Plugin: ShortPixel oder Imagify)
- [ ] **Caching-Plugin installieren**: WP Rocket (empfohlen) oder LiteSpeed Cache
- [ ] **CDN aktivieren**: Cloudflare (kostenlos) oder BunnyCDN
- [ ] Kritische CSS inline laden (WP Rocket kann das automatisch)
- [ ] Ungenutzte CSS/JS entfernen (functions.php entfernt bereits einiges)

### CLS (Cumulative Layout Shift) - Ziel: < 0.1

- [x] Feste Dimensionen fuer Bilder und Container (style.css)
- [ ] Schriftarten mit `font-display: swap` laden
- [ ] Keine Inhalte nachladen die Layout verschieben
- [ ] Werbebanner mit festen Plaetzen reservieren

### INP (Interaction to Next Paint) - Ziel: < 200ms

- [x] Non-critical JS deferred laden (functions.php)
- [ ] Event-Handler optimieren (keine schweren Berechnungen im Main Thread)
- [ ] Elementor Animationen auf der Startseite minimieren
- [ ] Third-Party Scripts (Tracking, Chat) verzögert laden

---

## 2. SEO-Optimierungen

### On-Page SEO

- [ ] **H1 Tag**: Genau 1x auf der Startseite, mit Hauptkeyword
  - Empfehlung: "Online-Kurs Erfahrungen & Tests 2026"
- [ ] **Meta Title**: `Kurs Erfahrungen 2026 - Ehrliche Online-Kurs Tests & Vergleiche`
- [ ] **Meta Description**: Dynamisch mit aktuellem Monat/Jahr (seo-optimizations.php)
- [ ] **H2 Tags**: Fuer jede Hauptsektion (siehe homepage-elementor-template.json)
- [ ] **Interne Verlinkung**: Jede Kategorie und Top-Kurse von der Startseite verlinken

### Schema Markup (Structured Data)

- [x] WebSite Schema mit SearchAction (functions.php)
- [x] Organization Schema (functions.php)
- [x] CollectionPage Schema (functions.php)
- [x] FAQ Schema per Shortcode (seo-optimizations.php)
- [x] Breadcrumb Schema (seo-optimizations.php)
- [ ] Review Schema auf einzelnen Testberichten (Rehub hat das teilweise eingebaut)

### E-E-A-T Signale (Experience, Expertise, Authoritativeness, Trustworthiness)

- [ ] **Autoren-Boxen** mit Foto, Bio und Qualifikationen auf Testberichten
- [ ] **"Wie wir testen" Sektion** auf der Startseite (siehe Template)
- [ ] **Aktualisierungsdaten** sichtbar anzeigen ("Zuletzt aktualisiert: ...")
- [ ] **Impressum & Datenschutz** prominent verlinkt
- [ ] **Affiliate-Offenlegung** sichtbar auf jeder Seite

---

## 3. Elementor-spezifische Optimierungen

### In den Elementor Einstellungen

1. **Elementor > Einstellungen > Erweitert**
   - CSS-Druckmethode: "Externe Datei" waehlen
   - Google Fonts laden: Deaktivieren (wird per functions.php gesteuert)

2. **Elementor > Einstellungen > Performance** (Elementor 3.x+)
   - Improved Asset Loading: Aktivieren
   - Improved CSS Loading: Aktivieren
   - Lazy Load Background Images: Aktivieren
   - Element Caching: Aktivieren

3. **Elementor > Tools > Allgemein**
   - CSS regenerieren nach Aenderungen

### Auf der Startseite

- [ ] Maximal **8-10 Sektionen** auf der Startseite (nicht ueberladen)
- [ ] **Keine verschachtelten Sections** (max. 1 Ebene tief)
- [ ] **Container statt Sections** verwenden (neues Elementor Flex Layout)
- [ ] **Animationen minimieren**: Nur dezente Fade-Ins, keine aufwaendigen Animationen
- [ ] **Custom CSS minimieren**: Nur noetige Styles, Rest im Child Theme

---

## 4. Plugin-Empfehlungen

### Muss-Plugins

| Plugin | Zweck | Kostenlos? |
|--------|-------|------------|
| WP Rocket | Caching, CSS/JS Minifizierung | Nein (49 EUR/Jahr) |
| ShortPixel | Bildoptimierung WebP/AVIF | Freemium |
| RankMath SEO | SEO Management | Freemium |
| Perfmatters | Asset Management pro Seite | Nein (24 EUR/Jahr) |

### Alternative kostenlose Kombination

| Plugin | Zweck |
|--------|-------|
| LiteSpeed Cache | Caching (wenn LiteSpeed Server) |
| Converter for Media | WebP Konvertierung |
| Yoast SEO | SEO Management |
| Asset CleanUp | Unnoetige Assets pro Seite deaktivieren |

### Plugins die auf der Startseite deaktiviert werden sollten

Ueber Perfmatters oder Asset CleanUp folgende Plugins **nur auf der Startseite** deaktivieren:
- Kontaktformular-Plugins (Contact Form 7, WPForms)
- Kommentar-Plugins
- Social Sharing Plugins (wenn nicht auf Startseite genutzt)
- WooCommerce Scripts (wenn Startseite kein Shop ist)

---

## 5. Empfohlene Startseiten-Struktur (Elementor)

Siehe `homepage-elementor-template.json` fuer Details.

```
1. Hero Section          - H1, USP, CTA (Above the Fold)
2. Trust Bar             - Social Proof, Logos, Zahlen
3. Top Kurse 2026        - Vergleichstabelle/Cards mit CTA
4. Kategorie-Navigation  - Icon/Card Grid zu Kategorien
5. Neueste Testberichte  - Blog Post Grid (6-9 Posts)
6. Wie wir testen        - E-E-A-T Section (Methodik)
7. FAQ Section           - Accordion mit Schema
8. Newsletter CTA        - Email Opt-in
```

---

## 6. Installation der Optimierungen

### Schritt 1: Child Theme installieren

```
1. Ordner "rehub-child" per FTP/SFTP hochladen nach:
   /wp-content/themes/rehub-child/

2. Im WordPress Backend:
   Design > Themes > "Rehub Child" aktivieren
```

### Schritt 2: SEO Optimierungen aktivieren

In `rehub-child/functions.php` am Ende einfuegen:
```php
require_once get_stylesheet_directory() . '/seo-optimizations.php';
```

### Schritt 3: .htaccess Regeln

Inhalte aus `htaccess-optimizations.txt` in die `.htaccess` Datei
im WordPress Root-Verzeichnis einfuegen (VOR den WordPress Regeln).

### Schritt 4: Elementor Startseite umbauen

Die Startseite in Elementor anhand der Empfehlungen in
`homepage-elementor-template.json` ueberarbeiten.

---

## 7. Erfolgsmessung

### Tools

- **Google PageSpeed Insights**: https://pagespeed.web.dev/
- **Google Search Console**: Core Web Vitals Report
- **GTmetrix**: Detaillierte Performance-Analyse
- **Chrome DevTools > Lighthouse**: Lokale Tests

### Zielwerte

| Metrik | Aktuell (geschaetzt) | Ziel |
|--------|---------------------|------|
| LCP | > 4s | < 2.5s |
| CLS | > 0.15 | < 0.1 |
| INP | > 300ms | < 200ms |
| PageSpeed Mobile | < 50 | > 80 |
| PageSpeed Desktop | < 70 | > 90 |

### Tracking

Nach jeder Aenderung testen mit PageSpeed Insights und Ergebnisse dokumentieren.
Optimierungen einzeln einbauen um die Auswirkung jeder Massnahme messen zu koennen.
