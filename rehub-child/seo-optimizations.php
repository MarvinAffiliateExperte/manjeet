<?php
/**
 * SEO-spezifische Optimierungen fuer kurs-erfahrungen.com
 * Kann in functions.php eingebunden werden via:
 * require_once get_stylesheet_directory() . '/seo-optimizations.php';
 */

// =====================================================
// 1. META TAGS: Optimierte Meta-Beschreibung fuer Startseite
// =====================================================

/**
 * Dynamische Meta-Description fuer die Startseite
 * (Nur verwenden wenn kein SEO-Plugin wie Yoast/RankMath aktiv ist)
 */
function ke_custom_meta_description() {
    if (is_front_page() && !defined('WPSEO_VERSION') && !class_exists('RankMath')) {
        $month_year = date_i18n('F Y');
        echo '<meta name="description" content="Die besten Online-Kurse im Test ' . esc_attr($month_year) . '. Ehrliche Erfahrungsberichte, Vergleiche und Bewertungen. Finde den perfekten Kurs fuer dich!">' . "\n";
    }
}
add_action('wp_head', 'ke_custom_meta_description', 1);

// =====================================================
// 2. OPEN GRAPH: Social Media Optimierung
// =====================================================

/**
 * Open Graph Tags fuer besseres Social Sharing
 * (Nur verwenden wenn kein SEO-Plugin aktiv ist)
 */
function ke_open_graph_tags() {
    if (!is_front_page()) {
        return;
    }

    if (defined('WPSEO_VERSION') || class_exists('RankMath')) {
        return;
    }

    $site_name = get_bloginfo('name');
    $description = 'Die besten Online-Kurse im Test. Ehrliche Erfahrungsberichte und Vergleiche.';
    $logo_url = get_site_icon_url(1200);
    ?>
    <meta property="og:type" content="website">
    <meta property="og:title" content="<?php echo esc_attr($site_name); ?> - Online-Kurs Erfahrungen & Tests">
    <meta property="og:description" content="<?php echo esc_attr($description); ?>">
    <meta property="og:url" content="<?php echo esc_url(home_url('/')); ?>">
    <meta property="og:site_name" content="<?php echo esc_attr($site_name); ?>">
    <?php if ($logo_url) : ?>
    <meta property="og:image" content="<?php echo esc_url($logo_url); ?>">
    <?php endif; ?>
    <meta property="og:locale" content="de_DE">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="<?php echo esc_attr($site_name); ?>">
    <meta name="twitter:description" content="<?php echo esc_attr($description); ?>">
    <?php
}
add_action('wp_head', 'ke_open_graph_tags', 2);

// =====================================================
// 3. INTERNAL LINKING: Automatische interne Verlinkung
// =====================================================

/**
 * Breadcrumb Schema fuer die Startseite
 */
function ke_homepage_breadcrumb_schema() {
    if (!is_front_page()) {
        return;
    }

    $schema = [
        '@context' => 'https://schema.org',
        '@type' => 'BreadcrumbList',
        'itemListElement' => [
            [
                '@type' => 'ListItem',
                'position' => 1,
                'name' => 'Startseite',
                'item' => home_url('/'),
            ],
        ],
    ];

    echo '<script type="application/ld+json">' . wp_json_encode($schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) . '</script>' . "\n";
}
add_action('wp_head', 'ke_homepage_breadcrumb_schema', 3);

// =====================================================
// 4. FAQ SCHEMA: Automatisches FAQ Schema
// =====================================================

/**
 * FAQ Schema Markup per Shortcode einfuegen
 * Nutzung: [ke_faq_schema] in Elementor Text Widget
 *
 * FAQ Eintraege werden in der functions.php definiert
 */
function ke_faq_schema_shortcode($atts) {
    $faqs = [
        [
            'question' => 'Wie werden die Online-Kurse getestet?',
            'answer' => 'Wir testen jeden Kurs persoenlich, bewerten Inhalt, Qualitaet, Support und Preis-Leistungs-Verhaeltnis nach einem standardisierten Bewertungsschema.',
        ],
        [
            'question' => 'Sind die Erfahrungsberichte echt?',
            'answer' => 'Ja, alle Erfahrungsberichte basieren auf echten Tests. Wir kaufen und durcharbeiten jeden Kurs selbst bevor wir eine Bewertung abgeben.',
        ],
        [
            'question' => 'Wie verdient kurs-erfahrungen.com Geld?',
            'answer' => 'Wir finanzieren uns ueber Affiliate-Links. Wenn du ueber unsere Links einen Kurs kaufst, erhalten wir eine Provision. Der Preis bleibt fuer dich gleich.',
        ],
        [
            'question' => 'Welche Online-Kurs Plattformen werden getestet?',
            'answer' => 'Wir testen Kurse von allen gaengigen Plattformen wie Udemy, Digistore24, Copecart, elopage und auch selbst-gehostete Kurse von einzelnen Anbietern.',
        ],
    ];

    $schema = [
        '@context' => 'https://schema.org',
        '@type' => 'FAQPage',
        'mainEntity' => [],
    ];

    $html = '<div class="ke-faq-section">';

    foreach ($faqs as $faq) {
        $schema['mainEntity'][] = [
            '@type' => 'Question',
            'name' => $faq['question'],
            'acceptedAnswer' => [
                '@type' => 'Answer',
                'text' => $faq['answer'],
            ],
        ];

        $html .= '<div class="ke-faq-item">';
        $html .= '<h3 class="ke-faq-question">' . esc_html($faq['question']) . '</h3>';
        $html .= '<div class="ke-faq-answer"><p>' . esc_html($faq['answer']) . '</p></div>';
        $html .= '</div>';
    }

    $html .= '</div>';
    $html .= '<script type="application/ld+json">' . wp_json_encode($schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) . '</script>';

    return $html;
}
add_shortcode('ke_faq_schema', 'ke_faq_schema_shortcode');

// =====================================================
// 5. PERFORMANCE MONITORING: Core Web Vitals Tracking
// =====================================================

/**
 * Web Vitals Tracking im Frontend (nur fuer Admins)
 * Zeigt LCP, FID/INP, CLS Werte in der Browser-Konsole
 */
function ke_web_vitals_debug() {
    if (!is_user_logged_in() || !current_user_can('manage_options')) {
        return;
    }

    if (!is_front_page()) {
        return;
    }
    ?>
    <script type="module">
    // Web Vitals Debug fuer Administratoren
    if (window.PerformanceObserver) {
        // LCP Tracking
        new PerformanceObserver((entryList) => {
            const entries = entryList.getEntries();
            const lastEntry = entries[entries.length - 1];
            console.log('%c[KE] LCP: ' + Math.round(lastEntry.startTime) + 'ms', 'color: #4CAF50; font-weight: bold');
            if (lastEntry.element) {
                console.log('[KE] LCP Element:', lastEntry.element);
            }
        }).observe({type: 'largest-contentful-paint', buffered: true});

        // CLS Tracking
        let clsValue = 0;
        new PerformanceObserver((entryList) => {
            for (const entry of entryList.getEntries()) {
                if (!entry.hadRecentInput) {
                    clsValue += entry.value;
                }
            }
            console.log('%c[KE] CLS: ' + clsValue.toFixed(4), 'color: #FF9800; font-weight: bold');
        }).observe({type: 'layout-shift', buffered: true});

        // INP Tracking (Interaction to Next Paint)
        new PerformanceObserver((entryList) => {
            for (const entry of entryList.getEntries()) {
                console.log('%c[KE] Interaction: ' + entry.name + ' - ' + Math.round(entry.duration) + 'ms', 'color: #2196F3; font-weight: bold');
            }
        }).observe({type: 'event', buffered: true, durationThreshold: 16});
    }
    </script>
    <?php
}
add_action('wp_footer', 'ke_web_vitals_debug', 999);

// =====================================================
// 6. SITEMAP: Startseite Prioritaet erhoehen
// =====================================================

/**
 * Sitemap Prioritaeten anpassen (fuer WordPress Core Sitemap)
 */
function ke_sitemap_entry($entry, $post_type, $post) {
    if ($post->ID === (int) get_option('page_on_front')) {
        $entry['changefreq'] = 'daily';
        $entry['priority'] = '1.0';
    }
    return $entry;
}

// Fuer Yoast SEO
add_filter('wpseo_sitemap_entry', 'ke_sitemap_entry', 10, 3);
