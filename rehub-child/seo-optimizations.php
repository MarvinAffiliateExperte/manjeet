<?php
/**
 * SEO-Optimierungen fuer kurs-erfahrungen.com
 * Marvin Seelhofer – Online-Marketing-Analyst
 *
 * Einbinden via functions.php:
 * require_once get_stylesheet_directory() . '/seo-optimizations.php';
 */

// =====================================================
// 1. META TAGS
// =====================================================

/**
 * Dynamische Meta-Description fuer die Startseite
 * Nur aktiv wenn kein SEO-Plugin (Yoast / RankMath) installiert ist
 */
function ke_custom_meta_description() {
    if ( ! is_front_page() ) {
        return;
    }
    if ( defined('WPSEO_VERSION') || class_exists('RankMath') ) {
        return;
    }
    $year = date('Y');
    echo '<meta name="description" content="Marvin Seelhofer testet Online-Kurse & Coaching-Programme im deutschsprachigen Raum seit 2021. '
        . '500+ ehrliche Erfahrungsberichte – unabhaengig, vollstaendig & ohne Gratiszugang. '
        . 'Finde den richtigen Kurs ' . esc_attr($year) . '.">' . "\n";
}
add_action('wp_head', 'ke_custom_meta_description', 1);

// =====================================================
// 2. OPEN GRAPH / TWITTER CARD
// =====================================================

function ke_open_graph_tags() {
    if ( ! is_front_page() ) {
        return;
    }
    if ( defined('WPSEO_VERSION') || class_exists('RankMath') ) {
        return;
    }

    $site_name   = 'Kurs Erfahrungen';
    $title       = 'Ehrliche Online-Kurs Testberichte & Erfahrungen ' . date('Y');
    $description = 'Marvin Seelhofer testet Online-Kurse, Coachings & digitale Produkte im deutschsprachigen Raum – mit eigenem Geld, vollstaendig und unabhaengig. 500+ Berichte seit 2021.';
    $url         = home_url('/');
    $image       = get_site_icon_url(1200);
    ?>
    <meta property="og:type"        content="website">
    <meta property="og:locale"      content="de_DE">
    <meta property="og:site_name"   content="<?php echo esc_attr($site_name); ?>">
    <meta property="og:title"       content="<?php echo esc_attr($title); ?>">
    <meta property="og:description" content="<?php echo esc_attr($description); ?>">
    <meta property="og:url"         content="<?php echo esc_url($url); ?>">
    <?php if ($image) : ?>
    <meta property="og:image"       content="<?php echo esc_url($image); ?>">
    <meta property="og:image:width"  content="1200">
    <meta property="og:image:height" content="630">
    <?php endif; ?>
    <meta name="twitter:card"        content="summary_large_image">
    <meta name="twitter:title"       content="<?php echo esc_attr($title); ?>">
    <meta name="twitter:description" content="<?php echo esc_attr($description); ?>">
    <?php if ($image) : ?>
    <meta name="twitter:image"       content="<?php echo esc_url($image); ?>">
    <?php endif; ?>
    <?php
}
add_action('wp_head', 'ke_open_graph_tags', 2);

// =====================================================
// 3. FAQ SCHEMA (Shortcode [ke_faq_schema])
// =====================================================

/**
 * FAQPage Schema – passend zu den echten FAQs auf kurs-erfahrungen.com
 * Nutzung: Shortcode [ke_faq_schema] in einem Elementor-HTML-Widget
 */
function ke_faq_schema_shortcode() {
    $faqs = [
        [
            'question' => 'Kaufst du die Kurse wirklich selbst?',
            'answer'   => 'Ja – jeder Kurs auf kurs-erfahrungen.com wurde von Marvin Seelhofer persoenlich mit eigenem Geld gekauft. Es wird kein kostenloser Zugang vom Anbieter akzeptiert und kein Vertrag mit Anbietern eingegangen. Nur so sind die Bewertungen 100 % unabhaengig.',
        ],
        [
            'question' => 'Wie verdient kurs-erfahrungen.com Geld?',
            'answer'   => 'Die Seite finanziert sich ueber Affiliate-Links. Wenn du ueber einen Link einen Kurs kaufst, erhaelt Marvin eine Provision – fuer dich ohne Mehrkosten. Die Bewertungen werden davon nicht beeinflusst. Negative Erfahrungen werden genauso veroeffentlicht wie positive.',
        ],
        [
            'question' => 'Was passiert, wenn ein Kurs schlecht ist?',
            'answer'   => 'Dann erscheint ein ehrlicher negativer Testbericht. Es werden keine Ausnahmen gemacht, auch wenn ein Anbieter hoehere Provision zahlt. Schlechte Kurse werden klar als solche gekennzeichnet – zum Schutz der Leser.',
        ],
        [
            'question' => 'Welche Kursplattformen werden getestet?',
            'answer'   => 'Es werden Produkte von allen gaengigen deutschsprachigen Plattformen getestet: Digistore24, Copecart, elopage, CopeCart sowie selbst-gehostete Kurse einzelner Anbieter. Der Schwerpunkt liegt auf dem deutschsprachigen Markt.',
        ],
        [
            'question' => 'Kann ich einen Kurs zur Bewertung vorschlagen?',
            'answer'   => 'Ja, Vorschlaege sind willkommen. Einfach ueber das Kontaktformular auf kurs-erfahrungen.com/kontakt/ einreichen. Kein kostenloser Zugang, keine Provision fuer positive Bewertungen.',
        ],
    ];

    $schema = [
        '@context'   => 'https://schema.org',
        '@type'      => 'FAQPage',
        'mainEntity' => [],
    ];

    ob_start();
    echo '<div class="ke-faq-schema-block">';
    foreach ($faqs as $faq) {
        $schema['mainEntity'][] = [
            '@type' => 'Question',
            'name'  => $faq['question'],
            'acceptedAnswer' => [
                '@type' => 'Answer',
                'text'  => $faq['answer'],
            ],
        ];
    }
    echo '</div>';
    echo '<script type="application/ld+json">'
        . wp_json_encode($schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE)
        . '</script>';

    return ob_get_clean();
}
add_shortcode('ke_faq_schema', 'ke_faq_schema_shortcode');

// =====================================================
// 4. BREADCRUMB SCHEMA
// =====================================================

function ke_homepage_breadcrumb_schema() {
    if ( ! is_front_page() ) {
        return;
    }

    $schema = [
        '@context' => 'https://schema.org',
        '@type'    => 'BreadcrumbList',
        'itemListElement' => [
            [
                '@type'    => 'ListItem',
                'position' => 1,
                'name'     => 'Startseite',
                'item'     => home_url('/'),
            ],
        ],
    ];

    echo '<script type="application/ld+json">'
        . wp_json_encode($schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE)
        . '</script>' . "\n";
}
add_action('wp_head', 'ke_homepage_breadcrumb_schema', 3);

// =====================================================
// 5. WOOCOMMERCE PRODUKT-SCHEMA (Einzelseite)
// =====================================================

/**
 * AggregateRating Schema fuer WooCommerce Produktseiten (Experten-Seiten)
 * Wird zusaetzlich zum Review-Schema in functions.php ausgegeben
 */
function ke_product_aggregate_rating_schema() {
    if ( ! is_singular('product') ) {
        return;
    }

    global $post;
    $product = wc_get_product($post->ID);
    if ( ! $product ) {
        return;
    }

    $rating       = (float) $product->get_average_rating();
    $review_count = (int)   $product->get_review_count();

    if ( $rating <= 0 || $review_count <= 0 ) {
        return;
    }

    $categories = wp_get_post_terms($post->ID, 'product_cat', ['fields' => 'names']);

    $schema = [
        '@context' => 'https://schema.org',
        '@type'    => 'Product',
        'name'     => get_the_title(),
        'url'      => get_permalink(),
        'aggregateRating' => [
            '@type'       => 'AggregateRating',
            'ratingValue' => number_format($rating, 1),
            'reviewCount' => $review_count,
            'bestRating'  => '5',
            'worstRating' => '1',
        ],
    ];

    $image = get_the_post_thumbnail_url($post->ID, 'large');
    if ($image) {
        $schema['image'] = $image;
    }

    if (!empty($categories)) {
        $schema['category'] = implode(', ', $categories);
    }

    echo '<script type="application/ld+json">'
        . wp_json_encode($schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE)
        . '</script>' . "\n";
}
add_action('wp_head', 'ke_product_aggregate_rating_schema');

// =====================================================
// 6. SITEMAP-PRIORITAETEN
// =====================================================

function ke_sitemap_entry($entry, $post_type, $post) {
    if ($post->ID === (int) get_option('page_on_front')) {
        $entry['changefreq'] = 'daily';
        $entry['priority']   = '1.0';
    }
    return $entry;
}
add_filter('wpseo_sitemap_entry', 'ke_sitemap_entry', 10, 3);

// =====================================================
// 7. CORE WEB VITALS DEBUG (nur fuer eingeloggte Admins)
// =====================================================

function ke_web_vitals_debug() {
    if ( ! is_user_logged_in() || ! current_user_can('manage_options') ) {
        return;
    }
    if ( ! is_front_page() && ! is_singular('product') ) {
        return;
    }
    ?>
    <script type="module">
    if (window.PerformanceObserver) {
        new PerformanceObserver(list => {
            const e = list.getEntries().at(-1);
            console.log('%c[KE] LCP: ' + Math.round(e.startTime) + 'ms', 'color:#22c55e;font-weight:700');
        }).observe({type:'largest-contentful-paint', buffered:true});

        let cls = 0;
        new PerformanceObserver(list => {
            for (const e of list.getEntries()) {
                if (!e.hadRecentInput) cls += e.value;
            }
            console.log('%c[KE] CLS: ' + cls.toFixed(4), 'color:#f59e0b;font-weight:700');
        }).observe({type:'layout-shift', buffered:true});

        new PerformanceObserver(list => {
            for (const e of list.getEntries()) {
                if (e.duration > 100) {
                    console.log('%c[KE] INP: ' + e.name + ' – ' + Math.round(e.duration) + 'ms', 'color:#ef4444;font-weight:700');
                }
            }
        }).observe({type:'event', buffered:true, durationThreshold:16});
    }
    </script>
    <?php
}
add_action('wp_footer', 'ke_web_vitals_debug', 999);
