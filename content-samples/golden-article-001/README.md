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
├── gen_images.py      # 画像生成スクリプト（Python stdlib のみ、依存なし）
├── gen_images.js      # 画像生成スクリプト（Node.js stdlib のみ、参考用）
└── images/
    ├── featured.png   # アイキャッチ画像 1200×630（要生成）
    └── comparison.png # 比較図 1200×800（要生成）
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

### comparison.png（1200×800）

- 用途: 記事内比較図
- コンセプト: ところてんと寒天の差を左右に並べて視覚化
- 左列: ところてん
- 右列: 寒天
- 比較行: 原料 / 製法 / 食感 / 主用途 / 共通点

## 画像生成手順

### gen_images.py（正本・依存パッケージなし）

Python 標準ライブラリ（`struct`, `zlib`, `math`, `os`）のみを使用します。
外部パッケージのインストールは不要です。

```bash
# リポジトリルートで実行
python3 content-samples/golden-article-001/gen_images.py

# 確認
ls -lh content-samples/golden-article-001/images/
# → featured.png (1200×630) と comparison.png (1200×800) が生成される
```

### gen_images.js（参考用・依存パッケージなし）

Node.js 標準ライブラリ（`zlib`, `fs`, `path`）のみを使用します。
gen_images.py と同様の視覚構造を生成しますが、gen_images.py を正本とします。

```bash
node content-samples/golden-article-001/gen_images.js
```

## 広告マーカー

本文 `post.md` の中央付近に以下のマーカーが1箇所だけ挿入されています。

```
<!-- acourt-ad-middle -->
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

## スクリプト構成

| ファイル | 言語 | 依存 | 役割 |
|----------|------|------|------|
| `gen_images.py` | Python 3 | なし（stdlib のみ） | **正本**。featured.png と comparison.png を生成 |
| `gen_images.js` | Node.js | なし（stdlib のみ） | 参考用。gen_images.py と同等の出力 |

どちらのスクリプトも外部パッケージを追加しません（Issue #5 の依存追加禁止に準拠）。

## 検証

| チェック項目 | 結果 |
|-------------|------|
| 指定ファイル（post.md / metadata.json / source-notes.md）が存在 | ✓ |
| metadata.json が valid JSON | ✓ |
| post.md に `<!-- acourt-ad-middle -->` が1回だけ存在 | ✓ |
| 主要事実が source-notes と対応 | ✓ |
| source-notes の栄養成分出典が八訂増補2023年版に対応 | ✓ |
| gen_images.py が外部パッケージなしで動作（stdlib のみ） | ✓ |
| 変更範囲が golden-article-001/ のみ | ✓ |
| featured.png が存在・サイズ 1200×630 | △ 要生成（上記手順を参照） |
| comparison.png が存在・サイズ 1200×800 | △ 要生成（上記手順を参照） |
