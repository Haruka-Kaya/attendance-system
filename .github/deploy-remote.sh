#!/bin/sh
# さくら側で実行されるデプロイ処理。GitHub Actions から `ssh ... 'sh -s'` に流し込む。
#
# さくらのログインシェルは csh なので、必ず sh に読ませること。
# ssh の引数として渡すと csh が解釈して `2>&1` 等で落ちる。
set -e

APP="$HOME/app/attendance_system"
WWW="$HOME/www/attendance"

mkdir -p "$APP" "$HOME/app/data"

tar xzf /tmp/app-deploy.tgz -C "$APP"
rm -f /tmp/app-deploy.tgz

# 静的ファイルは Apache に直接返させる (CGI を通すと 0.6 秒かかるものが 0.07 秒になる)
rm -rf "$WWW/static"
cp -R "$APP/static" "$WWW/static"

"$HOME/app/venv/bin/pip" install -q -r "$APP/requirements.txt"

echo "デプロイ完了: $(ls -1 "$APP" | wc -l | tr -d ' ') エントリ"
