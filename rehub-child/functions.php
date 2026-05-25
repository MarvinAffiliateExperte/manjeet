<?php
/**
 * Rehub Child Theme - Performance & SEO Optimizations 2026
 * Website: kurs-erfahrungen.com
 *
 * INSTALLATION:
 * 1. Diesen Ordner "rehub-child" in wp-content/themes/ hochladen
 * 2. Im WordPress Backend unter Design > Themes aktivieren
 * 3. Alternativ: Snippets einzeln via Code Snippets Plugin einfuegen
 */

// =====================================================
// 1. PERFORMANCE: Unnoetige Scripts & Styles entfernen
// =====================================================

/**
 * Elementor & WordPress Bloat reduzieren
 * Entfernt ungenutzte Assets die die Ladezeit verlangsamen
 */
function ke_remove_unnecessary_assets() {
    // WordPress Emoji-Scripts entfernen (spart ~15KB)
    remove_action('wp_head', 'print_emoji_detection_script', 7);
    remove_action('wp_print_styles', 'print_emoji_styles');
    remove_action('admin_print_scripts', 'print_emoji_detection_script');
    remove_action('admin_print_styles', 'print_emoji_styles');

    // WordPress Embed entfernen (wenn nicht genutzt)
    wp_deregister_script('wp-embed');

    // jQuery Migrate entfernen (Rehub benoetigt es nicht mehr)
    if (!is_admin()) {
        wp_deregister_script('jquery-migrate');
    }

    // Dashicons im Frontend entfernen (nur fuer nicht-eingeloggte User)
    if (!is_user_logged_in()) {
        wp_deregister_style('dashicons');
    }

    // Block Library CSS entfernen wenn nur Elementor genutzt wird
    wp_dequeue_style('wp-block-library');
    wp_dequeue_style('wp-block-library-theme');
    wp_dequeue_style('wc-blocks-style'); // WooCommerce Blocks

    // Elementor Icons entfernen wenn Font Awesome genutzt wird
    wp_dequeue_style('elementor-icons');
}
add_action('wp_enqueue_scripts', 'ke_remove_unnecessary_assets', 100);

/**
 * DNS Prefetch & Preconnect fuer externe Ressourcen
 * Beschleunigt das Laden von externen Scripts
 */
function ke_add_resource_hints() {
    echo '<link rel="preconnect" href="https://fonts.googleapis.com" crossorigin>' . "\n";
    echo '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>' . "\n";
    echo '<link rel="dns-prefetch" href="//www.googletagmanager.com">' . "\n";
    echo '<link rel="dns-prefetch" href="//www.google-analytics.com">' . "\n";
    // Affiliate Netzwerke vorverbinden
    echo '<link rel="dns-prefetch" href="//www.digistore24.com">' . "\n";
    echo '<link rel="dns-prefetch" href="//www.copecart.com">' . "\n";
}
add_action('wp_head', 'ke_add_resource_hints', 1);

// =====================================================
// 2. BILDER: WebP/AVIF & Lazy Loading Optimierung
// =====================================================

/**
 * Native Lazy Loading fuer alle Bilder erzwingen
 * und Fetchpriority fuer Above-the-fold Bilder setzen
 */
function ke_optimize_image_attributes($attr, $attachment, $size) {
    // Lazy Loading ist Standard, aber sicherstellen
    if (!isset($attr['loading'])) {
        $attr['loading'] = 'lazy';
    }
    // Decoding async fuer bessere Rendering-Performance
    $attr['decoding'] = 'async';

    return $attr;
}
add_filter('wp_get_attachment_image_attributes', 'ke_optimize_image_attributes', 10, 3);

/**
 * Hero-Bild / LCP-Bild mit fetchpriority="high" markieren
 * Verhindert dass das wichtigste Bild lazy-loaded wird
 */
function ke_prioritize_lcp_image($content) {
    if (!is_front_page()) {
        return $content;
    }

    // Erstes grosses Bild auf der Startseite priorisieren
    $count = 0;
    $content = preg_replace_callback(
        '/<img([^>]*?)loading=["\']lazy["\']([^>]*?)>/i',
        function ($matches) use (&$count) {
            $count++;
            if ($count <= 1) {
                // Erstes Bild: lazy entfernen, fetchpriority hinzufuegen
                $img = '<img' . $matches[1] . $matches[2] . ' fetchpriority="high">';
                return str_replace('loading="lazy"', '', $img);
            }
            return $matches[0];
        },
        $content
    );

    return $content;
}
add_filter('the_content', 'ke_prioritize_lcp_image', 99);

// =====================================================
// 3. CORE WEB VITALS: CLS, LCP, INP Optimierung
// =====================================================

/**
 * Aspect Ratio fuer Bilder setzen um CLS zu vermeiden
 */
function ke_add_image_dimensions_style() {
    if (!is_front_page()) {
        return;
    }
    ?>
    <style id="ke-cls-prevention">
        /* CLS Prevention: Feste Seitenverhaeltnisse */
        .elementor-widget-image img,
        .rehub-main-font img,
        .wpsm-comptable img,
        .gallery_top_widget img {
            aspect-ratio: attr(width) / attr(height);
            height: auto;
            max-width: 100%;
        }

        /* Platzhalter fuer Affiliate-Boxen damit Layout nicht springt */
        .rehub_woo_review,
        .wpsm_box,
        .rehub-main-color-border {
            min-height: 50px;
            contain: layout style;
        }

        /* Skeleton Loading fuer dynamische Inhalte */
        .elementor-widget-container:empty {
            min-height: 100px;
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: ke-skeleton 1.5s ease-in-out infinite;
            border-radius: 8px;
        }

        @keyframes ke-skeleton {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
    </style>
    <?php
}
add_action('wp_head', 'ke_add_image_dimensions_style', 5);

/**
 * INP (Interaction to Next Paint) Optimierung
 * Nicht-kritisches JavaScript deferred laden
 */
function ke_defer_non_critical_scripts($tag, $handle, $src) {
    // Scripts die deferred geladen werden sollen
    $defer_scripts = [
        'elementor-frontend',
        'elementor-pro-frontend',
        'rehub-scripts',
        'wpsm-scripts',
        'jquery-ui-core',
        'jquery-ui-widget',
    ];

    // Scripts die async geladen werden sollen
    $async_scripts = [
        'google-analytics',
        'gtag',
        'google-tag-manager',
    ];

    if (in_array($handle, $defer_scripts)) {
        return str_replace(' src=', ' defer src=', $tag);
    }

    if (in_array($handle, $async_scripts)) {
        return str_replace(' src=', ' async src=', $tag);
    }

    return $tag;
}
add_filter('script_loader_tag', 'ke_defer_non_critical_scripts', 10, 3);

// =====================================================
// 4. SEO: Schema.org Markup fuer Kurs-Bewertungen
// =====================================================

/**
 * Erweitertes Schema Markup fuer die Startseite
 * Verbessert Rich Snippets in Google-Suchergebnissen
 */
function ke_homepage_schema_markup() {
    if (!is_front_page()) {
        return;
    }

    $schema = [
        '@context' => 'https://schema.org',
        '@graph' => [
            [
                '@type' => 'WebSite',
                '@id' => home_url('/#website'),
                'url' => home_url('/'),
                'name' => 'Kurs Erfahrungen',
                'description' => 'Ehrliche Erfahrungsberichte und Tests zu Online-Kursen',
                'publisher' => [
                    '@id' => home_url('/#organization'),
                ],
                'potentialAction' => [
                    '@type' => 'SearchAction',
                    'target' => [
                        '@type' => 'EntryPoint',
                        'urlTemplate' => home_url('/?s={search_term_string}'),
                    ],
                    'query-input' => 'required name=search_term_string',
                ],
            ],
            [
                '@type' => 'Organization',
                '@id' => home_url('/#organization'),
                'name' => 'Kurs Erfahrungen',
                'url' => home_url('/'),
                'logo' => [
                    '@type' => 'ImageObject',
                    'url' => get_site_icon_url(),
                ],
            ],
            [
                '@type' => 'CollectionPage',
                '@id' => home_url('/#webpage'),
                'url' => home_url('/'),
                'name' => get_bloginfo('name') . ' - ' . get_bloginfo('description'),
                'isPartOf' => [
                    '@id' => home_url('/#website'),
                ],
                'about' => [
                    '@type' => 'Thing',
                    'name' => 'Online-Kurs Bewertungen und Erfahrungsberichte',
                ],
                'description' => 'Finde die besten Online-Kurse mit echten Erfahrungsberichten und detaillierten Tests.',
            ],
        ],
    ];

    echo '<script type="application/ld+json">' . wp_json_encode($schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) . '</script>' . "\n";
}
add_action('wp_head', 'ke_homepage_schema_markup', 2);

// =====================================================
// 5. CACHING & PRELOADING Optimierungen
// =====================================================

/**
 * Kritische Ressourcen preloaden
 */
function ke_preload_critical_resources() {
    if (!is_front_page()) {
        return;
    }

    // Hauptschriftart preloaden (an eigene Schriftart anpassen!)
    // echo '<link rel="preload" href="/wp-content/themes/flavor/flavor/flavor/flavor.woff2" as="font" type="font/woff2" crossorigin>' . "\n";

    // Rehub Haupt-CSS preloaden
    $theme_uri = get_template_directory_uri();
    echo '<link rel="preload" href="' . esc_url($theme_uri . '/style.css') . '" as="style">' . "\n";
}
add_action('wp_head', 'ke_preload_critical_resources', 1);

/**
 * Browser-Caching Header fuer statische Ressourcen
 * (Nur relevant wenn kein Caching-Plugin wie WP Rocket aktiv ist)
 */
function ke_add_cache_headers() {
    if (is_admin()) {
        return;
    }

    // Nur fuer die Startseite spezifische Cache-Header setzen
    if (is_front_page()) {
        header('Cache-Control: public, max-age=3600, s-maxage=86400');
        header('Vary: Accept-Encoding');
    }
}
add_action('send_headers', 'ke_add_cache_headers');

// =====================================================
// 6. ELEMENTOR: Ungenutzte Features deaktivieren
// =====================================================

/**
 * Elementor Optimierungen
 */
// Google Fonts von Elementor deaktivieren (wenn eigene Fonts genutzt werden)
add_filter('elementor/frontend/print_google_fonts', '__return_false');

// Elementor Font Awesome inline laden statt externe Datei
add_action('elementor/frontend/after_register_styles', function() {
    // Nur wenn Font Awesome nicht benoetigt wird:
    // wp_deregister_style('font-awesome');
    // wp_deregister_style('font-awesome-5-all');
}, 20);

/**
 * Elementor Dialog/Lightbox nur laden wenn benoetigt
 */
function ke_elementor_disable_dialog_on_homepage() {
    if (is_front_page()) {
        wp_dequeue_script('elementor-dialog');
        wp_dequeue_style('elementor-animations');
    }
}
add_action('wp_enqueue_scripts', 'ke_elementor_disable_dialog_on_homepage', 999);

// =====================================================
// 7. HEARTBEAT API: Admin Performance
// =====================================================

/**
 * Heartbeat API im Frontend komplett deaktivieren
 * Im Backend auf 60 Sekunden limitieren
 */
function ke_optimize_heartbeat($settings) {
    if (!is_admin()) {
        wp_deregister_script('heartbeat');
    } else {
        $settings['interval'] = 60;
    }
    return $settings;
}
add_filter('heartbeat_settings', 'ke_optimize_heartbeat');

// =====================================================
// 8. SECURITY & CLEANUP
// =====================================================

/**
 * Unnoetige WordPress Header entfernen
 */
remove_action('wp_head', 'wp_generator');
remove_action('wp_head', 'wlwmanifest_link');
remove_action('wp_head', 'rsd_link');
remove_action('wp_head', 'wp_shortlink_wp_head');
remove_action('wp_head', 'rest_output_link_wp_head');
remove_action('wp_head', 'wp_oembed_add_discovery_links');
remove_action('wp_head', 'wp_resource_hints', 2);

/**
 * XML-RPC deaktivieren (Sicherheit + Performance)
 */
add_filter('xmlrpc_enabled', '__return_false');

/**
 * Self-Pingbacks deaktivieren
 */
function ke_disable_self_pingbacks(&$links) {
    $home = get_option('home');
    foreach ($links as $l => $link) {
        if (0 === strpos($link, $home)) {
            unset($links[$l]);
        }
    }
}
add_action('pre_ping', 'ke_disable_self_pingbacks');

// =====================================================
// 9. WOOCOMMERCE: Review-Site Optimierungen
// =====================================================

/**
 * "In den Warenkorb" → "Zum Testbericht lesen"
 * Erfahrungsberichte sind keine Kaufprodukte
 */
function ke_wc_loop_button_text() {
    return 'Zum Testbericht lesen &#8594;';
}
add_filter('woocommerce_product_add_to_cart_text', 'ke_wc_loop_button_text');
add_filter('woocommerce_product_single_add_to_cart_text', 'ke_wc_loop_button_text');

/**
 * Cart-Fragments AJAX-Call deaktivieren
 * Spart ~1 unnötigen HTTP-Request pro Seitenaufruf
 */
function ke_remove_wc_cart_fragments() {
    if ( ! is_cart() && ! is_checkout() ) {
        wp_dequeue_script('wc-cart-fragments');
    }
}
add_action('wp_enqueue_scripts', 'ke_remove_wc_cart_fragments', 11);

/**
 * WooCommerce Produkt-Tabs umbenennen
 * "Beschreibung" → "Testbericht", "Bewertungen" → "Lesererfahrungen"
 */
function ke_rename_wc_product_tabs($tabs) {
    if (isset($tabs['description'])) {
        $tabs['description']['title'] = 'Testbericht';
    }
    if (isset($tabs['reviews'])) {
        $tabs['reviews']['title'] = 'Lesererfahrungen (%d)';
    }
    return $tabs;
}
add_filter('woocommerce_product_tabs', 'ke_rename_wc_product_tabs', 98);

/**
 * Kurzbeschreibung im Produkt-Loop anzeigen (unter dem Titel)
 * Erscheint in den Homepage-Shortcodes [products ...]
 */
function ke_product_loop_short_description() {
    global $product;
    if ( ! $product ) {
        return;
    }
    $excerpt = $product->get_short_description();
    if ( $excerpt ) {
        echo '<p class="ke-loop-excerpt">' . wp_trim_words( wp_strip_all_tags( $excerpt ), 18, '&hellip;' ) . '</p>';
    }
}
add_action('woocommerce_after_shop_loop_item_title', 'ke_product_loop_short_description', 15);

/**
 * Review Schema (schema.org/Review) auf WooCommerce Produktseiten
 * Ermöglicht Google Rich Snippets mit Sternebewertung
 */
function ke_product_review_schema() {
    if ( ! is_singular('product') ) {
        return;
    }

    global $post;
    $product = wc_get_product( $post->ID );
    if ( ! $product ) {
        return;
    }

    $rating       = (float) $product->get_average_rating();
    $review_count = (int)   $product->get_review_count();
    $title        = get_the_title();
    $excerpt      = wp_strip_all_tags( $product->get_short_description() );
    $url          = get_permalink();
    $image        = get_the_post_thumbnail_url( $post->ID, 'large' );

    $schema = [
        '@context'      => 'https://schema.org',
        '@type'         => 'Review',
        'name'          => $title . ' Erfahrungen & Test ' . date('Y'),
        'description'   => $excerpt ?: 'Erfahrungsbericht und Test von Marvin Seelhöfer.',
        'url'           => $url,
        'datePublished' => get_the_date('c'),
        'dateModified'  => get_the_modified_date('c'),
        'author'        => [
            '@type' => 'Person',
            'name'  => 'Marvin Seelhöfer',
            'url'   => home_url('/author/kurs-erfahrungen/'),
        ],
        'publisher' => [
            '@type' => 'Organization',
            'name'  => 'Kurs Erfahrungen',
            'url'   => home_url('/'),
        ],
        'itemReviewed' => [
            '@type'       => 'Product',
            'name'        => $title,
            'description' => $excerpt,
        ],
    ];

    if ( $rating > 0 ) {
        $schema['reviewRating'] = [
            '@type'       => 'Rating',
            'ratingValue' => number_format( $rating, 1 ),
            'bestRating'  => '5',
            'worstRating' => '1',
        ];
        if ( $review_count > 0 ) {
            $schema['itemReviewed']['aggregateRating'] = [
                '@type'       => 'AggregateRating',
                'ratingValue' => number_format( $rating, 1 ),
                'reviewCount' => $review_count,
                'bestRating'  => '5',
                'worstRating' => '1',
            ];
        }
    }

    if ( $image ) {
        $schema['image'] = $image;
    }

    echo '<script type="application/ld+json">'
        . wp_json_encode( $schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE )
        . '</script>' . "\n";
}
add_action('wp_head', 'ke_product_review_schema');

/**
 * Person-Schema für Marvin Seelhöfer (Startseite & Autor-Archiv)
 */
function ke_author_person_schema() {
    if ( ! is_front_page() && ! is_author() ) {
        return;
    }

    $schema = [
        '@context'    => 'https://schema.org',
        '@type'       => 'Person',
        'name'        => 'Marvin Seelhöfer',
        'url'         => home_url('/author/kurs-erfahrungen/'),
        'jobTitle'    => 'Online-Marketing-Analyst',
        'description' => 'Marvin Seelhöfer analysiert seit 2021 Online-Kurse, Coaching-Programme und digitale Produkte im deutschsprachigen Raum. Über 500 Produkte getestet – mit eigenem Geld, vollständig und unabhängig.',
        'sameAs'      => [
            'https://www.youtube.com/c/KursErfahrungen',
            'https://www.provenexpert.com/de-de/kurs-erfahrungen-com/',
        ],
        'worksFor' => [
            '@type' => 'Organization',
            'name'  => 'Kurs Erfahrungen',
            'url'   => home_url('/'),
        ],
        'knowsAbout' => [
            'Online-Marketing',
            'Affiliate-Marketing',
            'Online-Kurse',
            'Coaching-Programme',
            'Digitale Geschäftsmodelle',
        ],
    ];

    echo '<script type="application/ld+json">'
        . wp_json_encode( $schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE )
        . '</script>' . "\n";
}
add_action('wp_head', 'ke_author_person_schema');

/**
 * WooCommerce: Unnötige Skripte auf Nicht-Shop-Seiten entfernen
 */
function ke_remove_wc_scripts_on_non_shop_pages() {
    if ( is_shop() || is_product() || is_product_category() || is_cart() || is_checkout() || is_account_page() ) {
        return;
    }
    wp_dequeue_style('woocommerce-general');
    wp_dequeue_style('woocommerce-layout');
    wp_dequeue_style('woocommerce-smallscreen');
}
// Kommentar: Deaktiviert lassen bis getestet – Rehub überschreibt WC-Styles evtl. global
// add_action('wp_enqueue_scripts', 'ke_remove_wc_scripts_on_non_shop_pages', 99);

/**
 * WooCommerce: CSS-Klasse "ke-products-wrap" per Filter an Shortcode-Output hängen
 * Sorgt dafür dass das Homepage-CSS greift
 */
function ke_wc_products_shortcode_wrapper($output, $atts) {
    return '<div class="ke-products-wrap">' . $output . '</div>';
}
add_filter('woocommerce_shortcode_products_query_results', function($results) {
    return $results; // Daten unverändert – Wrapper kommt per CSS-Klasse im Template
});

/**
 * WooCommerce: "Weitere Informationen"-Tab entfernen (bei Reviews nicht nötig)
 */
function ke_remove_wc_additional_info_tab($tabs) {
    unset($tabs['additional_information']);
    return $tabs;
}
add_filter('woocommerce_product_tabs', 'ke_remove_wc_additional_info_tab', 99);
