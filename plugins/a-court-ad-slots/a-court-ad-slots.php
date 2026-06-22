<?php
/**
 * Plugin Name: A-court Ad Slots
 * Description: テーマ非依存の広告枠管理プラグイン
 * Version: 1.0.0
 * Author: A-court
 */
if (!defined('ABSPATH')) exit;

class ACourtAdSlots {
    private static $instance = null;
    private $options;
    
    public static function instance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    private function __construct() {
        $this->options = get_option('acourt_ad_slots', $this->defaults());
        add_action('admin_menu', [$this, 'add_menu']);
        add_action('admin_init', [$this, 'register_settings']);
        add_filter('the_content', [$this, 'insert_ads'], 20);
        add_action('wp_head', [$this, 'add_styles']);
    }

    private function defaults() {
        return [
            'enabled' => 1,
            'test_mode' => 1,
            'slot_top' => 1,
            'slot_middle' => 1,
            'slot_bottom' => 1,
        ];
    }
    
    public function add_menu() {
        add_options_page(
            'A-court広告枠',
            'A-court広告枠',
            'manage_options',
            'acourt-ad-slots',
            [$this, 'settings_page']
        );
    }

    public function register_settings() {
        register_setting('acourt_ad_slots_group', 'acourt_ad_slots', [
            'sanitize_callback' => [$this, 'sanitize']
        ]);
    }
    
    public function sanitize($input) {
        $out = [];
        $out['enabled'] = isset($input['enabled']) ? 1 : 0;
        $out['test_mode'] = isset($input['test_mode']) ? 1 : 0;
        $out['slot_top'] = isset($input['slot_top']) ? 1 : 0;
        $out['slot_middle'] = isset($input['slot_middle']) ? 1 : 0;
        $out['slot_bottom'] = isset($input['slot_bottom']) ? 1 : 0;
        return $out;
    }

    public function settings_page() {
        if (!current_user_can('manage_options')) return;
        $o = $this->options;
        echo '<div class="wrap"><h1>A-court広告枠</h1>';
        echo '<form method="post" action="options.php">';
        settings_fields('acourt_ad_slots_group');
        echo '<table class="form-table">';
        $this->checkbox('enabled', '全体ON/OFF', $o);
        $this->checkbox('test_mode', 'テスト表示', $o);
        $this->checkbox('slot_top', '上部枠', $o);
        $this->checkbox('slot_middle', '中央枠', $o);
        $this->checkbox('slot_bottom', '下部枠', $o);
        echo '</table>';
        submit_button();
        echo '</form></div>';
    }

    private function checkbox($name, $label, $o) {
        $c = !empty($o[$name]) ? ' checked' : '';
        echo "<tr><th>$label</th><td><input type='checkbox' name='acourt_ad_slots[$name]' value='1'$c></td></tr>";
    }
    
    public function insert_ads($content) {
        if (!$this->should_show()) return $content;
        static $done = false;
        if ($done) return $content;
        $done = true;
        $o = $this->options;
        $top = $o['slot_top'] ? $this->slot('top', '記事上部') : '';
        $bottom = $o['slot_bottom'] ? $this->slot('bottom', '記事下部') : '';
        $mid = '';
        if ($o['slot_middle'] && strpos($content, '<!-- ad-middle -->') !== false) {
            $mid = $this->slot('middle', '記事中央');
            $content = str_replace('<!-- ad-middle -->', $mid, $content);
        }
        return $top . $content . $bottom;
    }

    private function should_show() {
        if (!$this->options['enabled']) return false;
        if (is_admin() || is_feed() || defined('REST_REQUEST')) return false;
        if (!is_singular('post') || !is_main_query()) return false;
        if (post_password_required()) return false;
        return true;
    }
    
    private function slot($pos, $label) {
        if (!$this->options['test_mode']) return '';
        return sprintf(
            '<div class="acourt-ad-slot acourt-ad-slot--%s"><span class="acourt-ad-slot__label">広告 %sテスト枠</span></div>',
            esc_attr($pos), esc_html($label)
        );
    }

    public function add_styles() {
        if (!$this->should_show() || !$this->options['test_mode']) return;
        echo '<style>
.acourt-ad-slot{background:#DDF4F0;border:2px dashed #28777A;border-radius:8px;padding:1.5em;margin:1.5em 0;text-align:center}
.acourt-ad-slot__label{color:#28777A;font-size:0.9em}
</style>';
    }
}
ACourtAdSlots::instance();
