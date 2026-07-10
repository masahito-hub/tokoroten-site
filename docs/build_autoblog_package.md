# build_autoblog_package.py

Golden Article（品質保証済み記事パッケージ）をAuto-blog互換ZIPに変換するCLIツール。

## 概要

`tokoroten-site/content-samples/` の記事パッケージを、既存の `Auto-blog` パイプラインが受理できる入力ZIP形式に変換します。

**重要:** このツールはZIPを生成するだけです。WordPressへの投入は行いません。

## CLI使用方法

```bash
python3 tools/build_autoblog_package.py content-samples/golden-article-001
python3 tools/build_autoblog_package.py content-samples/golden-article-001 --output dist/
python3 tools/build_autoblog_package.py content-samples/golden-article-001 --force
```

## 入力構造

```
content-samples/golden-article-001/
├── post.md              # frontmatterなし、H1から始まる本文
├── metadata.json        # 記事メタデータ
├── source-notes.md      # 情報ソースの記録
├── README.md            # パッケージの説明
└── images/
    ├── *_featured.png   # 1200x630
    └── *_comparison.png # 1200x800（オプション）
```

## 出力構造

```
{slug}.zip
├── post.md              # YAML frontmatter + 本文（H1除去済み）
└── images/
    ├── *_featured.png
    └── *_comparison.png
```

## frontmatter変換表

| metadata.json | 出力frontmatter | 備考 |
|--------------|-----------------|------|
| title | title | そのまま |
| slug | slug | そのまま |
| status | status | **常に draft に固定** |
| description | description | そのまま |
| categories | categories | YAML配列形式 |
| featured_image | featured_image | 相対パス |

## H1除去の理由

元の post.md はH1（タイトル）から始まりますが、WordPressでは投稿タイトルが別途設定されるため、本文内のH1は重複になります。

このツールは本文からH1を自動的に除去し、H2以下の見出し構造を維持します。

## エラー処理

- **validation failed**: 入力パッケージが validate_content_package.py の検証に失敗
- **FileExistsError**: 出力ファイルが既に存在（--force で上書き可能）
- **FileNotFoundError**: 参照画像が見つからない
- **ValueError**: unsafe pathの検出、広告マーカーの重複/欠損

## テスト

```bash
python3 -m unittest tests.test_build_autoblog_package -v
```

テストケース:
1. Golden ArticleからZIP生成成功
2. ZIPルートにpost.mdが存在
3. frontmatterがmetadataと一致
4. statusが必ずdraft
5. H1が本文から除去
6. 広告マーカーが1回
7. 画像が同梱される
8-13. エラーハンドリング
