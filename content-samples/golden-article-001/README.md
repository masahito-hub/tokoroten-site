# Golden Article 001 — ところてんと寒天は何が違う？

## 概要

| 項目 | 値 |
|------|----|
| タイトル | ところてんと寒天は何が違う？原料・作り方・食感を比較 |
| slug | tokoroten-vs-kanten |
| カテゴリー | 基礎知識 |
| WordPress status | draft |
| 作成日 | 2026-06-27 |

## ファイル構成

```
golden-article-001/
├── post.md            # 記事本文（Markdown）
├── metadata.json      # WordPress投稿メタデータ
├── source-notes.md    # 参照事実・出典候補・注意点
├── README.md          # 本ファイル
└── images/
    ├── featured.png   # アイキャッチ画像 1200×630
    └── comparison.png # 比較図 1200×800
```

## 画像情報

### featured.png（1200×630）

- 用途: WordPress アイキャッチ画像（OGP対応サイズ）
- コンセプト: 水辺の研究所のブランドイメージに合わせた落ち着いたビジュアル
- 配色: サイトデザイン仕様（DESIGN_SPEC.md）に準拠
  - 背景: `#F6FBFA`（tklab-bg）
  - アクセント帯: `#DDF4F0`（tklab-water）
  - 見出し色: `#28777A`（tklab-primary）
  - テキスト: `#173F42`（tklab-text）
  - ゴールドアクセント: `#D7B46A`（tklab-accent）

**生成方法:**
Pythonスクリプト `scripts/gen_images.py` にて標準ライブラリ（`struct`, `zlib`）のみを使用して生成。
外部パッケージ不使用。スクリプトは本ディレクトリ内の `gen_images.py` に保存。

**再生成方法:**
```bash
python3 content-samples/golden-article-001/gen_images.py
```
カレントディレクトリはリポジトリルートで実行すること。

### comparison.png（1200×800）

- 用途: 記事内比較図
- コンセプト: ところてんと寒天の差を左右に並べて視覚化
- 左側: ところてん（製法・食感・用途）
- 右側: 寒天（製法・食感・用途）
- 中央: 共通原料（テングサ）

**生成方法・再生成方法:** featured.png と同じ

## 広告マーカー

本文 `post.md` の中央付近に以下のマーカーが1箇所だけ挿入されています。

```
<!-- MIDDLE_AD -->
```

WordPress側でこのマーカーを検出して広告コードに置換する想定です（Gate 6B 以降の工程）。

## 変更禁止事項

このパッケージは `content-samples/golden-article-001/` の範囲のみ変更対象です。
以下には一切触れていません。

- `theme/`
- `plugins/`
- `scripts/`
- 既存投稿 ID 37
- WordPress REST API
- Xserver

## 検証

| チェック項目 | 結果 |
|-------------|------|
| 指定ファイルが全て存在する | ✓ |
| metadata.json が valid JSON | ✓ |
| featured.png サイズ 1200×630 | ✓ |
| comparison.png サイズ 1200×800 | ✓ |
| post.md に `<!-- MIDDLE_AD -->` が1回だけ存在 | ✓ |
| 主要事実が source-notes と対応している | ✓ |
| 変更範囲が golden-article-001/ のみ | ✓ |
