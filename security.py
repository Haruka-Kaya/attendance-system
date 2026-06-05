"""セキュリティ関連のユーティリティ
- 監査ログ (hash chain で改ざん検知)
- 強パスワードポリシー
- ログイン通知 / 重要操作通知 (Discord)
- 段階的アカウントロック
"""
import hashlib
import json
import re
import urllib.error
from urllib.request import Request, urlopen

from flask import request, has_request_context
from models import db, AuditLog
import discord_service


# ── 監査ログ ──────────────────────────────────────────────────────────────────

_CRITICAL_ACTIONS = {
    'user.role_change', 'user.delete', 'user.reset_password',
    'admin.backup_download', 'admin.audit_export',
    'login.locked', 'login.brute_force_suspected',
    'token.revoke_all',
}
_WARNING_ACTIONS = {
    'login.fail', 'login.password_change',
    'user.lock', 'user.unlock',
    'event.delete', 'attendance.bulk_update',
}


def _severity_for(action):
    if action in _CRITICAL_ACTIONS:
        return 'critical'
    if action in _WARNING_ACTIONS:
        return 'warning'
    return 'info'


def _compute_record_hash(prev_hash, payload):
    """前ハッシュ + payload (sorted JSON) の SHA-256 を返す。
    payload には id 以外の主要フィールドを含める。"""
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    h = hashlib.sha256()
    h.update((prev_hash or '').encode('utf-8'))
    h.update(b'|')
    h.update(canonical.encode('utf-8'))
    return h.hexdigest()


def audit(action, user=None, target_type=None, target_id=None, detail=None, severity=None):
    """主要アクションを audit_logs に記録。エラーは握り潰してアプリは止めない。
    hash chain で改ざん検知できるよう prev_hash と record_hash を計算する。
    severity が critical の場合は Discord にも通知。"""
    try:
        ip = ua = None
        if has_request_context():
            ip = request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()
            ua = (request.headers.get('User-Agent') or '')[:255]

        sev = severity or _severity_for(action)

        # 前レコードの hash を取得
        prev = AuditLog.query.order_by(AuditLog.id.desc()).first()
        prev_hash = prev.record_hash if prev else None

        log = AuditLog(
            user_id=user.id if user else None,
            action=action,
            target_type=target_type,
            target_id=target_id,
            ip=ip,
            user_agent=ua,
            detail=json.dumps(detail, ensure_ascii=False, default=str) if detail else None,
            severity=sev,
            prev_hash=prev_hash,
        )
        # 自身の hash を計算
        log.record_hash = _compute_record_hash(prev_hash, {
            'user_id': log.user_id,
            'action': log.action,
            'target_type': log.target_type,
            'target_id': log.target_id,
            'ip': log.ip,
            'detail': log.detail,
            'severity': log.severity,
        })

        db.session.add(log)
        db.session.commit()

        # critical は Discord 通知
        if sev == 'critical' and discord_service.is_webhook_enabled():
            _notify_critical(action, user, detail, ip)
    except Exception:
        try: db.session.rollback()
        except Exception: pass


def verify_audit_chain(limit=None):
    """audit_logs の hash chain を検証する。
    戻り値: (ok: bool, broken_ids: list[int])"""
    q = AuditLog.query.order_by(AuditLog.id.asc())
    if limit:
        q = q.limit(limit)
    prev_hash = None
    broken = []
    for log in q.all():
        expected = _compute_record_hash(prev_hash, {
            'user_id': log.user_id,
            'action': log.action,
            'target_type': log.target_type,
            'target_id': log.target_id,
            'ip': log.ip,
            'detail': log.detail,
            'severity': log.severity,
        })
        if log.prev_hash != prev_hash or log.record_hash != expected:
            broken.append(log.id)
        prev_hash = log.record_hash
    return (len(broken) == 0, broken)


def _notify_critical(action, user, detail, ip):
    fields = [
        {'name': 'アクション', 'value': f'`{action}`', 'inline': True},
        {'name': 'IP',         'value': ip or '?',     'inline': True},
    ]
    if user:
        fields.insert(0, {'name': '実行ユーザー',
                          'value': f'{user.name} ({user.email})',
                          'inline': False})
    if detail:
        detail_str = json.dumps(detail, ensure_ascii=False, default=str)[:1024]
        fields.append({'name': '詳細', 'value': f'```json\n{detail_str}\n```', 'inline': False})
    discord_service.send_webhook(embeds=[{
        'title': '🚨 重要操作が実行されました',
        'color': 0xE53935,
        'fields': fields,
    }], username='出欠管理BOT/Audit')


# ── 段階的アカウントロック ───────────────────────────────────────────────────

def compute_lock_minutes(failed_count):
    """失敗回数に応じてロック時間 (分) を返す。
    3回未満は 0 (ロックなし)、3-4: 5分、5-9: 30分、10-19: 4時間、20+: 24時間"""
    if failed_count < 3:
        return 0
    if failed_count < 5:
        return 5
    if failed_count < 10:
        return 30
    if failed_count < 20:
        return 240
    return 1440


# ── パスワードポリシー ────────────────────────────────────────────────────────

_COMMON = {
    'password', 'password1', '12345678', '123456789', 'qwerty123',
    'abc12345', 'admin1234', 'welcome1', 'iloveyou', 'monkey123',
    'football1', 'baseball1', 'sunshine1', 'master123', 'letmein1',
    'passw0rd', 'p@ssw0rd', '11111111', 'aaaaaaaa', 'qwertyui',
    'attendance', 'shukketsu',
}


def check_password_strength(pw, user_email=None):
    """強パスワードポリシーチェック。OK=None、NG=エラーメッセージ。"""
    if not pw or len(pw) < 12:
        return '12文字以上で設定してください'
    if len(pw) > 128:
        return '128文字以下で設定してください'

    classes = sum([
        bool(re.search(r'[a-z]', pw)),
        bool(re.search(r'[A-Z]', pw)),
        bool(re.search(r'\d',    pw)),
        bool(re.search(r'[^a-zA-Z\d]', pw)),
    ])
    if classes < 3:
        return '英大文字・英小文字・数字・記号のうち3種類以上を含めてください'

    if pw.lower() in _COMMON:
        return 'よく使われる弱いパスワードです。別のものを使用してください'

    if user_email:
        local = user_email.split('@')[0].lower()
        if local and len(local) >= 4 and local in pw.lower():
            return 'メールアドレスの一部を含めないでください'

    try:
        sha1 = hashlib.sha1(pw.encode('utf-8')).hexdigest().upper()
        prefix, suffix = sha1[:5], sha1[5:]
        req = Request(
            f'https://api.pwnedpasswords.com/range/{prefix}',
            headers={'User-Agent': 'AttendanceApp-PasswordCheck/1.0'},
        )
        with urlopen(req, timeout=3) as resp:
            for line in resp.read().decode('ascii').splitlines():
                hash_suffix, _count = line.split(':')
                if hash_suffix.strip() == suffix:
                    return 'このパスワードは過去に漏洩したことがあります。別のものを使用してください'
    except (urllib.error.URLError, OSError, TimeoutError):
        pass
    except Exception:
        pass

    return None


# ── ログイン通知 ──────────────────────────────────────────────────────────────

def notify_login(user, success=True, reason=None):
    """ログイン成功/失敗を Discord 通知。Webhook 設定がなければ no-op。"""
    if not discord_service.is_webhook_enabled():
        return
    ip = '?'
    ua = '?'
    if has_request_context():
        ip = request.headers.get('X-Forwarded-For', request.remote_addr or '?').split(',')[0].strip()
        ua = (request.headers.get('User-Agent') or '?')[:120]

    if success:
        title  = '🟢 ログイン成功'
        color  = 0x4CAF50
    else:
        title  = '🔴 ログイン失敗'
        color  = 0xE53935

    fields = [{'name': 'IP', 'value': ip, 'inline': True}]
    if user:
        fields.insert(0, {'name': 'ユーザー', 'value': f'{user.name} ({user.email})', 'inline': False})
    if reason:
        fields.append({'name': '理由', 'value': reason, 'inline': False})
    fields.append({'name': 'User-Agent', 'value': f'`{ua}`', 'inline': False})

    discord_service.send_webhook(embeds=[{
        'title': title,
        'color': color,
        'fields': fields,
    }], username='出欠管理BOT/Auth')


# ── ブルートフォース検知 ─────────────────────────────────────────────────────

def detect_brute_force(ip, window_minutes=15, threshold=20):
    """直近 window_minutes 分間に同一 IP からの login.fail が threshold 件以上なら True。"""
    if not ip:
        return False
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
    count = AuditLog.query.filter(
        AuditLog.action == 'login.fail',
        AuditLog.ip == ip,
        AuditLog.created_at >= cutoff,
    ).count()
    return count >= threshold
