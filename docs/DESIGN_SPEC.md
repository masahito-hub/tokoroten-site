# DESIGN SPEC v1

## Concept
「ところてんが好き！ — 水辺の小さな研究所」

## Keywords
夏 / 水 / 透明感 / 清潔感 / 少し和風 / 古すぎない

## Color Tokens
| Token | Value | Usage |
|-------|-------|-------|
| --tklab-bg | #F6FBFA | 全体背景 |
| --tklab-water | #DDF4F0 | 水色アクセント |
| --tklab-primary | #28777A | 見出し・リンク |
| --tklab-text | #173F42 | 本文 |
| --tklab-muted | #597477 | 補助テキスト |
| --tklab-accent | #D7B46A | ボタン・強調 |
| --tklab-white | #FFFFFF | カード背景 |

## Typography
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Hiragino Sans", sans-serif

## Target Elements
- ヘッダー・ナビゲーション
- 全体背景
- 記事一覧カード
- 記事本文
- H2/H3
- 表・引用
- ボタン
- フッター
- スマホ表示

## File Structure
theme/cocoon-child-master/
├── style.css
├── functions.php
└── assets/css/tokoroten-design-v1.css

## CSS Class Prefix
tklab-

## Constraints
- 親テーマ編集禁止
- !important乱用禁止
- 外部フォント禁止
- 重いJS禁止
- CSS 20KB以内目標
