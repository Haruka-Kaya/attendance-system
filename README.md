# 部活動出欠管理システム (Flask Backend)

部活動向けの出欠管理 Web アプリ + REST API。Flutter モバイルクライアント ([attendance-app](https://github.com/Himanaraba/attendance-app)) と JWT 認証で連携。

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask)](https://flask.palletsprojects.com/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

本番: https://zenshin9498.duckdns.org

## アーキテクチャ

```
┌──────────┐   セッション+CSRF   ┌──────────────┐
│ Browser  │ ──────────────────▶ │   Flask 3.x  │
└──────────┘                     │              │      ┌──────────┐
                                 │  Web (HTML)  │ ───▶ │ SQLite   │
┌──────────┐         JWT         │  + REST API  │      │ (volume) │
│ Flutter  │ ──────────────────▶ │              │      └──────────┘
└──────────┘                     └──────────────┘
                                        │
                               ┌────────┴────────┐
                               │ Coolify (VPS)   │
                               │ + Traefik+LE    │
                               │ + GitHub Auto   │
                               │   Deploy        │
                               └─────────────────┘
```

- **Web 版**: Bootstrap 5 + FullCalendar、セッション + CSRF 認証
- **Mobile 版**: JWT (Access 2h / Refresh 30d)、JWT ブラックリスト対応

## 主な機能

### セキュリティ
- PBKDF2-SHA256 (600,000 iterations) パスワードハッシュ
- パスワードポリシー: 12文字以上 + 3種類以上 + haveibeenpwned k-anonymity 漏洩チェック
- 初回ログイン強制パスワード変更
- **段階的アカウントロック**: 3回→5分 / 5回→30分 / 10回→4時間 / 20回→24時間
- **JWT ブラックリスト** (`/api/v1/auth/logout` で即時無効化)
- **ブルートフォース検知**: 15分以内に20回失敗で critical ログ + Discord 通知
- レート制限: ログイン 5/分 + 30/時間
- CSRF トークン (Web)、JWT (API)
- 永続化 JWT 鍵 (`.jwt_secret` ファイル、Coolify 再デプロイ後もトークン保持)
- HTTPS 強制 (Traefik + Let's Encrypt 自動更新)

### セキュリティヘッダー (自動付与)

| ヘッダー | 値 |
|---|---|
| Content-Security-Policy | default-src 'self'、外部許可は pwned API/Discord/Google Fonts のみ |
| Strict-Transport-Security | max-age=63072000; includeSubDomains; preload |
| X-Frame-Options | DENY (clickjacking 防止) |
| X-Content-Type-Options | nosniff |
| Referrer-Policy | strict-origin-when-cross-origin |
| Permissions-Policy | geolocation/camera/microphone/payment/usb/sensors 全禁止 |
| Cross-Origin-Opener-Policy | same-origin |
| Cross-Origin-Resource-Policy | same-origin |
| Session Cookie | HttpOnly + Secure + SameSite=Lax + 8時間有効 |

### 監査ログ
- 全主要操作 (ログイン/出欠/イベント CRUD/ユーザー CRUD/バックアップ DL 等) を `audit_logs` に記録
- **Hash chain** (`prev_hash` + SHA-256 `record_hash`) で改ざん検知
- Severity 3段階: `info` / `warning` / `critical`
- `/admin/audit` 管理画面: action / severity / user / IP / 日付範囲フィルタ
- `/admin/audit/verify`: ワンクリック改ざん検知
- `/admin/audit/export.csv`: CSV エクスポート
- `critical` 操作 (role 変更, ユーザー削除, バックアップ DL 等) は Discord webhook で即通知

### ユーザー管理
- ロール: `user` / `manager` / `admin`
- 班: 技術班 / 運営班 / 顧問
- 学年: M1〜M3 / H1〜H4 / OB (任意)
- 自動欠席曜日設定

### 出欠
- 出席 / 部分参加 / 欠席 + 任意コメント
- 部分参加時刻記録
- 個人ダッシュボード (出席率・直近活動)
- 管理者: 日付別一括編集

### 活動管理
- CRUD + 重複・移動操作 (FullCalendar 連携)
- 週次テンプレートから自動生成
- 説明文サポート
- API レスポンスに全員の出欠サマリ (`attendees` + `summary`) を含む

### Discord 連携
- イベント追加/編集/削除を Webhook で通知
- ロール自動付与 (出席率に応じて HIGH/MID/LOW ロール切替、Bot API 経由)
- 重要操作 (critical 監査ログ) を webhook で通知

### エクスポート
- CSV (日別 / 期間別 / 個人 / 統計サマリ)
- 全データバックアップ (ZIP / JSON / SQLite DB ファイル)

### 国際化
- 日本語 / English (セッション保存)

### 公開ページ (App Store 審査用、ログイン不要)
- `/privacy`: プライバシーポリシー (日英)
- `/support`: サポート + FAQ (日英)

### モバイル連携
- `/api/v1/*` REST API
- `/api/v1/app/latest` で OTA アップデート情報配信
- CORS は `/api/v1/*` のみ許可

## 環境変数

| 変数 | デフォルト | 説明 |
|---|---|---|
| `SECRET_KEY` | ランダム生成 | Flask セッション用 (本番では固定値推奨) |
| `JWT_SECRET_KEY` | `.jwt_secret` ファイル | JWT 署名用 (ファイル自動永続化) |
| `DATABASE_URL` | `sqlite:///attendance.db` | DB接続 URL |
| `DISCORD_WEBHOOK_URL` | (空) | 設定時に Discord 通知有効化 |
| `DISCORD_BOT_TOKEN` | (空) | ロール自動付与用 (任意) |
| `DISCORD_GUILD_ID` | (空) | 同上 |
| `DISCORD_ROLE_HIGH/MID/LOW` | (空) | 出席率閾値ロールID |
| `APP_PUBLIC_URL` | `https://zenshin9498.duckdns.org` | Discord 埋め込みリンク用 |

## ローカル開発

```bash
# 1. 仮想環境
python -m venv venv
.\venv\Scripts\activate    # Windows
source venv/bin/activate    # Mac/Linux

# 2. 依存
pip install -r requirements.txt

# 3. DB 初期化
flask --app app init_db

# 4. 管理者作成
flask --app app create_admin

# 5. 起動
python app.py
# または
flask --app app run --debug --host=0.0.0.0
```

http://localhost:5000 でアクセス。

## 本番デプロイ (Coolify)

このリポジトリは **Coolify セルフホスト PaaS** で自動デプロイされる。

```
git push origin main
   │
   ▼
GitHub webhook
   │
   ▼
Coolify ビルド (Nixpacks: Procfile + runtime.txt 自動検出)
   │
   ▼
Docker コンテナ再作成 (永続ボリューム /app/data に SQLite)
   │
   ▼
Traefik 経由で HTTPS 配信 (Let's Encrypt 自動更新)
```

### 必要ファイル

- `Procfile`: `web: gunicorn -b 0.0.0.0:${PORT:-5000} --workers 2 --timeout 60 app:app`
- `runtime.txt`: `python-3.12`
- `requirements.txt`: 依存パッケージ (gunicorn 含む)

### Coolify 設定

- Build Pack: **Nixpacks**
- Port: `5000`
- Storage: `/app/data` (永続ボリューム、SQLite DB ファイル用)
- Environment Variables: 上記 `SECRET_KEY` 等
- Auto Deploy: ON (GitHub App 連携)

## API エンドポイント (JWT)

### 認証
| Method | Path | 説明 |
|---|---|---|
| POST | `/api/v1/auth/login` | email + password でトークン取得 |
| POST | `/api/v1/auth/refresh` | refresh_token でアクセストークン更新 |
| POST | `/api/v1/auth/logout` | JWT を即時失効 (ブラックリスト登録) |
| GET  | `/api/v1/auth/me` | 自分のユーザー情報 |
| POST | `/api/v1/auth/change_password` | パスワード変更 |
| POST | `/api/v1/auth/onboarding` | 初回ログイン時のセットアップ |

### 活動・出欠 (一般ユーザ)
| Method | Path | 説明 |
|---|---|---|
| GET  | `/api/v1/events` | 全活動 (期間フィルタ可、`attendees`/`summary` 同梱) |
| GET  | `/api/v1/events/upcoming` | 直近の活動 (同上) |
| GET  | `/api/v1/attendance/my` | 自分の出欠記録 |
| POST | `/api/v1/attendance/update` | 自分の出欠を更新 |

### 管理者向け (`@jwt_role('manager')` / `'admin'`)
| Method | Path | 説明 |
|---|---|---|
| POST/PUT/DELETE | `/api/v1/events*` | 活動 CRUD (admin) |
| GET  | `/api/v1/attendance/date/<date>` | 日付別全員の出欠 |
| POST | `/api/v1/attendance/bulk` | 一括更新 |
| GET/POST/PUT/DELETE | `/api/v1/users*` | ユーザー管理 (admin) |
| POST | `/api/v1/users/<id>/reset_password` | パスワードリセット (manager+) |
| GET/POST/PUT/DELETE | `/api/v1/templates*` | テンプレート管理 |
| POST | `/api/v1/templates/generate` | テンプレートからイベント一括生成 |
| GET  | `/api/v1/stats` | 全ユーザー出席統計 |

### モバイル OTA / 公開ページ
| Method | Path | 説明 |
|---|---|---|
| GET | `/api/v1/app/latest` | 最新版情報 (認証不要) |
| GET | `/privacy` | プライバシーポリシー (認証不要) |
| GET | `/support` | サポート + FAQ (認証不要) |

## DB マイグレーション

`apply_migrations()` (in `app.py`) で起動時に自動実行：

```python
_safe_add_column('audit_logs', 'severity',    "VARCHAR(10) DEFAULT 'info'")
_safe_add_column('audit_logs', 'prev_hash',   'VARCHAR(64)')
_safe_add_column('audit_logs', 'record_hash', 'VARCHAR(64)')
db.create_all()   # AuditLog / TokenBlocklist 等の新規テーブル
```

新カラム追加時はここに 1 行足してデプロイするだけ。

## CLI コマンド

```bash
flask --app app init_db                # テーブル作成
flask --app app create_admin           # 管理者作成 (対話 or --email/--password/--name)
flask --app app sync_discord_roles     # 出席率に応じて Discord ロール更新 (cron 用)
```

## プロジェクト構成

```
attendance_system/
├── app.py                    # メインアプリ (~2300行、ルート定義)
├── models.py                 # SQLAlchemy: User / Event / Attendance / AuditLog / TokenBlocklist / WeeklyTemplate
├── security.py               # 監査ログ (hash chain) / 段階的ロック / パスワードポリシー / Discord 通知
├── discord_service.py        # Discord Webhook + Bot API
├── requirements.txt
├── Procfile                  # gunicorn 起動コマンド
├── runtime.txt               # Python 3.12
├── app_version.json          # モバイルアプリの最新バージョン
├── static/
└── templates/                # Jinja2
    ├── base.html
    ├── login.html / dashboard.html / change_password.html
    ├── onboarding.html / guide.html / error.html
    ├── privacy.html / support.html         # App Store 公開ページ
    └── admin/
        ├── users.html / events.html / attendance.html
        ├── templates.html / backup.html
        └── audit.html                       # 監査ログ画面 (severity 色分け + 改ざん検知)
```

## ライセンス

[Apache License 2.0](LICENSE)

Copyright 2026 賀屋悠

## 関連リポジトリ

- **モバイルアプリ (Flutter)**: https://github.com/Himanaraba/attendance-app
