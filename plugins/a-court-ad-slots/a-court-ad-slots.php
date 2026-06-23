<?php
/**
 * Plugin Name: A-court Ad Slots
 * Description: テーマ非依存の広告枠管理プラグイン
 * Version: 1.1.0
 * Author: A-court
 */
if (!defined('ABSPATH')) exit;

register_activation_hook(__FILE__, function() {
    if (!get_option('acourt_ad_slots')) {
        add_option('acourt_ad_slots', [
            'enabled'=>0,'test_mode'=>1,'slot_top'=>1,
            'slot_middle'=>1,'slot_bottom'=>1,'test_post_id'=>0
        ]);
    }
});

class ACourtAdSlots {
    private const MIDDLE_MARKER = '<!-- acourt-ad-middle -->';
    private static $instance = null;
    private $options;

    public static function instance() {
        if (self::$instance === null) self::$instance = new self();
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
        return ['enabled'=>0,'test_mode'=>1,'slot_top'=>1,'slot_middle'=>1,'slot_bottom'=>1,'test_post_id'=>0];
    }

    public function add_menu() {
        add_options_page('A-court広告枠','A-court広告枠','manage_options','acourt-ad-slots',[$this,'settings_page']);
    }
    
    public function register_settings() {
        register_setting('acourt_ad_slots_group', 'acourt_ad_slots', ['sanitize_callback'=>[$this,'sanitize']]);
    }
    
    public function sanitize($input) {
        return [
            'enabled' => isset($input['enabled']) ? 1 : 0,
            'test_mode' => isset($input['test_mode']) ? 1 : 0,
            'slot_top' => isset($input['slot_top']) ? 1 : 0,
            'slot_middle' => isset($input['slot_middle']) ? 1 : 0,
            'slot_bottom' => isset($input['slot_bottom']) ? 1 : 0,
            'test_post_id' => absint($input['test_post_id'] ?? 0),
        ];
    }

    public function settings_page() {
        if (!current_user_can('manage_options')) return;
        $o = $this->options;
        echo '<div class="wrap"><h1>A-court広告枠</h1><form method="post" action="options.php">';
        settings_fields('acourt_ad_slots_group');
        echo '<table class="form-table">';
        $this->checkbox('enabled', '全体ON/OFF', $o);
        $this->checkbox('test_mode', 'テストモード', $o);
        $this->number('test_post_id', 'テスト対象投稿ID', $o);
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
    
    private function number($name, $label, $o) {
        $v = intval($o[$name] ?? 0);
        echo "<tr><th>$label</th><td><input type='number' name='acourt_ad_slots[$name]' value='$v' min='0'></td></tr>";
    }

    public function insert_ads($content) {
        if (!$this->should_show()) return $content;
        static $done = false;
        if ($done) return $content;
        $done = true;
        $o = $this->options;
        $top = $o['slot_top'] ? $this->slot('top', '記事上部') : '';
        $bottom = $o['slot_bottom'] ? $this->slot('bottom', '記事下部') : '';
        if ($o['slot_middle'] && strpos($content, self::MIDDLE_MARKER) !== false) {
            $mid = $this->slot('middle', '記事中央');
            $content = str_replace(self::MIDDLE_MARKER, $mid, $content);
        }
        return $top . $content . $bottom;
    }

    private function should_show() {
        $o = $this->options;
        if (!$o['enabled']) return false;
        if (is_admin() || is_feed() || (defined('REST_REQUEST') && REST_REQUEST)) return false;
        if (!is_singular('post') || !in_the_loop()) return false;
        if (get_queried_object_id() !== get_the_ID()) return false;
        if (post_password_required()) return false;
        if ($o['test_mode']) {
            $tid = absint($o['test_post_id'] ?? 0);
            if ($tid === 0 || $tid !== get_the_ID()) return false;
        }
        return true;
    }

    private function slot($pos, $label) {
        if (!$this->options['test_mode']) return '';
        return sprintf('<div class="acourt-ad-slot acourt-ad-slot--%s"><span class="acourt-ad-slot__label">広告 %sテスト枠</span></div>',
            esc_attr($pos), esc_html($label));
    }

    public function add_styles() {
        if (!$this->should_show() || !$this->options['test_mode']) return;
        echo '<style>.acourt-ad-slot{background:#DDF4F0;border:2px dashed #28777A;border-radius:8px;padding:1.5em;margin:1.5em 0;text-align:center}.acourt-ad-slot__label{color:#28777A;font-size:0.9em}</style>';
    }
}
ACourtAdSlots::instance();
