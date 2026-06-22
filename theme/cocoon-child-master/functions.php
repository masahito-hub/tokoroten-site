<?php //子テーマ用関数
if ( !defined( 'ABSPATH' ) ) exit;

//子テーマ用のビジュアルエディタースタイルを適用
add_editor_style();

// ところてん.tokyo Design v1 CSS
function tklab_enqueue_design_css() {
    $css_path = get_stylesheet_directory() . '/assets/css/tokoroten-design-v1.css';
    $css_url = get_stylesheet_directory_uri() . '/assets/css/tokoroten-design-v1.css';
    if (file_exists($css_path)) {
        wp_enqueue_style('tklab-design-v1', $css_url, array(), filemtime($css_path));
    }
}
add_action('wp_enqueue_scripts', 'tklab_enqueue_design_css');

//以下に子テーマ用の関数を書く
