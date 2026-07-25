"""Passenger WSGI エントリポイント (cPanel 系レンタルサーバー用)。

cPanel の「Setup Python App」は起動時にこのファイルの `application` を探す。
gunicorn / Coolify 経由のデプロイ (Procfile) はこのファイルを読まないため、
既存の本番構成には影響しない。

cPanel の環境変数 UI は項目数が増えると扱いづらいので、
アプリケーションディレクトリ直下の .env も読み込む (.env.example を参照)。
"""
import os
import sys

_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)


def _load_dotenv(path):
    """.env を環境変数へ読み込む。既に設定済みの環境変数は上書きしない。"""
    if not os.path.exists(path):
        return
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(os.path.join(_BASE, '.env'))

from app import app as application  # noqa: E402
