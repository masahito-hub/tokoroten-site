# Auto-blog入力ZIPアダプター

`tools/build_autoblog_package.py` は、`content-samples/<article>/` の品質保証済み
記事パッケージ（正本）を、既存の `Auto-blog` が受理する入力ZIP（`article.zip`）へ
決定的かつ安全に変換するCLIです。

投稿経路は新設しません。生成したZIPは既存の `Auto-blog` へ手動で渡す想定の
中間成果物であり、本ツール自身はWordPress・VPS・Google Driveのいずれにも
一切アクセスしません。

## CLI使用方法

```bash
python3 tools/build_autoblog_package.py content-samples/golden-article-001 --output dist/
```

- `package_dir`（必須・位置引数）: `content-samples/<article>/` のようなパッケージディレクトリ
- `--output`（省略可・デフォルト `dist`）: ZIPの出力先ディレクトリ
- `--force`（省略可）: 出力先に同名ZIPが既に存在する場合、上書きを許可する
  - 指定しない場合、既存ファイルがあると **失敗（fail-closed）** します

成功すると `dist/<slug>.zip` を作成し、`OK: wrote <path>` を表示して終了コード0を返します。
失敗すると `ERROR: ...` を表示して終了コード1を返し、**不完全なZIPを残しません**
（一時ファイルへ書き込んだ後 `os.replace()` によるatomic renameで確定します）。

変換前に必ず `tools/validate_content_package.py` 相当の検証を実行し、
入力パッケージがPASSしない限り変換しません。

## 入力・出力構造

### 入力（正本パッケージ）

```text
content-samples/golden-article-001/
├── post.md            # frontmatterなし、H1から始まる本文
├── metadata.json       # title / slug / status / categories / description /
│                        # featured_image / comparison_image / middle_ad_marker
├── source-notes.md
├── README.md
└── images/
    ├── tokoroten_golden_featured.png
    └── tokoroten_golden_comparison.png
```

### 出力（Auto-blog入力ZIP）

```text
dist/tokoroten-vs-kanten.zip
├── post.md            # YAML frontmatter + Markdown本文（ZIPルート固定）
└── images/
    ├── tokoroten_golden_featured.png
    └── tokoroten_golden_comparison.png
```

`source-notes.md` / `README.md` / `metadata.json` はAuto-blog入力ZIPへ含めません。

## frontmatter変換表

| metadata.json                | 出力frontmatter    | 備考                                   |
|-------------------------------|---------------------|----------------------------------------|
| `title`                       | `title`              | そのままYAML文字列としてエスケープ出力 |
| `slug`                        | `slug`               | そのまま                               |
| `description`                 | `description`        | そのまま                               |
| `status`                      | `status`              | **入力値を無視し、常に `"draft"` 固定** |
| `categories`                  | `categories`          | YAMLリストとして出力                   |
| `featured_image`               | `featured_image`      | ZIP内相対パス `images/<basename>` へ正規化 |
| `comparison_image`             | （frontmatterへ出力しない） | 画像はZIPへ同梱するが本文挿入・参照は行わない |
| `source-notes.md` / `README.md` / `metadata.json` | （出力しない） | Auto-blog入力契約外 |

YAML文字列はダブルクォートで囲み、バックスラッシュ・ダブルクォート・改行を
エスケープします（外部YAMLライブラリは使用せず、Python標準ライブラリのみで
生成・パースします — 対象スキーマがフラットな文字列と単純なリストのみのため）。

## H1除去の理由

`post.md` の先頭H1見出しは、WordPress投稿タイトル（`title` frontmatter）と
内容が重複するため、変換後の本文から除去します。H1行とその直後の空行のみを
取り除き、H2以下の見出し・表・リスト・HTMLコメント（広告マーカー含む）は
一切書き換えません。

## comparison imageについて

`comparison_image` はZIPの `images/` へ同梱しますが、本文への挿入や
WordPressへのアップロードは本Gate（6B-2）の対象外です。次のGate
（6B-2A以降）で扱います。

## 手動投入の禁止

本ツールが生成するZIPは **手動でWordPressやVPSへ投入してはいけません**。
本Gateはローカルでの変換・検証までを対象とし、投稿・公開・VPS操作・
Google Driveへのアップロードは一切行いません。

## Auto-blog契約テスト

`Auto-blog` リポジトリをCIから直接checkoutする構成は本リポジトリでは
採用していません（外部リポジトリ依存はCIの安定性・権限管理上のリスクが
大きいと判断したため）。代わりに、`tests/test_autoblog_contract.py` へ
Auto-blogの**公開済み・文書化された入力契約**（本Issueに記載された契約）を
再現したローカルパーサーを実装し、生成した `post.md` が以下を満たすことを
検証しています。

- `---` で区切られたYAML frontmatterとしてparse可能であること
- `title` / `slug` が必須かつ非空であること
- `slug` が `^[a-z0-9]+(?:-[a-z0-9]+)*$` 形式であること
- UTF-8としてデコード可能であること
- `featured_image` の相対パスがZIP内に実在すること

このローカルcontract testは `tools/build_autoblog_package.py` 自身の
frontmatter生成ロジックとは独立した実装であり、生成側のバグをテスト側が
そのまま反映してしまう（ミラーリングによる誤検出漏れ）ことを避けています。
Auto-blog側の実際の契約（`Auto-blog/app/processor.py` の
`parse_post_md()` 相当）が変わった場合は、このパーサーと本ドキュメントを
あわせて更新してください。

## 次Gate（6B-2A以降）での未実装項目

以下は本Gateの対象外です。

- Auto-blogのカテゴリ名 → WordPressカテゴリID解決
- 本文中画像のWordPressアップロードとURL置換
- `comparison_image` の本文への挿入
- SEOプラグインのmeta description設定
- slug重複・再試行時のidempotency
- Google Drive受け渡し、manifest、checksum連携
- VPS配置・systemd操作
- WordPress下書き作成・公開・広告表示確認
