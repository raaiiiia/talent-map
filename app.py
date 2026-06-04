from __future__ import annotations

import csv
import base64
import hashlib
import hmac
import io
import json
import os
import random
import re
import smtplib
import sqlite3
import sys
import tempfile
import time
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree as ET


BASE_DIR = Path(__file__).resolve().parent


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip().strip('"').strip("'")
        os.environ[key] = value


load_env_file(BASE_DIR / ".env")

STATIC_DIR = BASE_DIR / "static"
DATA_DIR = Path(tempfile.gettempdir()) / "talent_map_data" if os.getenv("VERCEL") else BASE_DIR / "data"
DB_PATH = DATA_DIR / "talent_map.sqlite3"
FALLBACK_DB_PATH = DATA_DIR / "talent_map.app.sqlite3"
LOCAL_TZ = timezone(timedelta(hours=8))
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
KV_PREFIX = os.getenv("TALENT_MAP_KV_PREFIX", "talent_map").strip() or "talent_map"
KV_USER_ID_OFFSET = 1_000_000
SESSION_TTL_SECONDS = 14 * 24 * 60 * 60

DEFAULT_PROFILE = {
    "main_direction": "视频创作",
    "assistant_direction": "AI算法",
    "region": "长三角，杭州优先",
    "industries": ["互联网", "电商", "短视频"],
    "company_types": [
        "MCN机构",
        "电商公司",
        "短视频平台",
        "内容营销公司",
        "品牌方内容团队",
        "AI视频工具公司",
    ],
    "platforms": ["抖音", "小红书", "B站", "淘宝直播"],
    "content_types": ["品牌广告", "知识科普", "视频剪辑", "调色", "编剧", "文案", "AIGC"],
    "ai_algorithm_tags": [
        "推荐算法",
        "内容理解",
        "多模态",
        "视频生成",
        "AIGC工具",
        "投流/广告算法",
        "搜索排序",
    ],
    "levels": ["骨干", "专家"],
    "experience": "用户自由选择",
    "scoring_view": "业务视角优先",
    "source_policy": "仅检索公开可读数据和企业已授权数据源",
    "max_candidates_before_narrowing": 50,
}

STATUS_OPTIONS = ["待评估", "已收藏", "已排除", "待联系", "已联系", "待确认"]
JSON_FIELDS = {"skill_tags", "past_companies", "works", "source_links", "platforms"}

FIELD_ALIASES = {
    "姓名": "name",
    "名字": "name",
    "name": "name",
    "当前公司": "current_company",
    "公司": "current_company",
    "current_company": "current_company",
    "职位": "title",
    "岗位": "title",
    "title": "title",
    "城市": "city",
    "city": "city",
    "年限": "years",
    "经验": "years",
    "years": "years",
    "技能标签": "skill_tags",
    "技能": "skill_tags",
    "skill_tags": "skill_tags",
    "过往公司": "past_companies",
    "历史公司": "past_companies",
    "past_companies": "past_companies",
    "公开作品/项目": "works",
    "作品": "works",
    "项目": "works",
    "works": "works",
    "来源链接": "source_links",
    "链接": "source_links",
    "source_links": "source_links",
    "推荐理由": "recommendation_reason",
    "recommendation_reason": "recommendation_reason",
    "风险点": "risk_notes",
    "risk_notes": "risk_notes",
    "评分": "score",
    "score": "score",
    "平台": "platforms",
    "platforms": "platforms",
    "状态": "status",
    "status": "status",
}


def now_iso() -> str:
    return datetime.now(LOCAL_TZ).isoformat(timespec="seconds")


def resolve_db_path() -> Path:
    journal_path = DB_PATH.with_name(f"{DB_PATH.name}-journal")
    if DB_PATH.exists() and DB_PATH.stat().st_size == 0:
        try:
            DB_PATH.unlink(missing_ok=True)
            journal_path.unlink(missing_ok=True)
        except PermissionError:
            return FALLBACK_DB_PATH
    return DB_PATH


def db() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(resolve_db_path())
    conn.execute("PRAGMA journal_mode=MEMORY")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, (int, float)):
        return [str(value)]
    text = str(value).strip()
    if not text:
        return []
    parts = re.split(r"[、,，;/；\n]+", text)
    return [part.strip() for part in parts if part.strip()]


def to_json_text(value: Any) -> str:
    if value is None:
        return "[]"
    if isinstance(value, str):
        items = normalize_list(value)
        return json.dumps(items, ensure_ascii=False)
    if isinstance(value, list):
        return json.dumps([str(item).strip() for item in value if str(item).strip()], ensure_ascii=False)
    return json.dumps(value, ensure_ascii=False)


def from_json_text(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    text = str(value)
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if str(item)]
        if isinstance(parsed, str):
            return normalize_list(parsed)
    except json.JSONDecodeError:
        return normalize_list(text)
    return []


def pbkdf2_hash(password: str, salt: str | None = None) -> str:
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 220_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    if "$" not in stored:
        return False
    salt, digest = stored.split("$", 1)
    return hmac.compare_digest(pbkdf2_hash(password, salt).split("$", 1)[1], digest)


def kv_credentials() -> tuple[str | None, str | None]:
    url = os.getenv("KV_REST_API_URL") or os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("KV_REST_API_TOKEN") or os.getenv("UPSTASH_REDIS_REST_TOKEN")
    return (url.rstrip("/") if url else None, token.strip() if token else None)


def kv_enabled() -> bool:
    url, token = kv_credentials()
    return bool(url and token)


def kv_key(*parts: object) -> str:
    return ":".join([KV_PREFIX, *[str(part).strip().lower() for part in parts]])


def kv_command(*command: object):
    url, token = kv_credentials()
    if not url or not token:
        raise RuntimeError("KV storage is not configured.")
    body = json.dumps([str(part) for part in command], ensure_ascii=False).encode("utf-8")
    req = urlrequest.Request(
        url,
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8") or "{}")
    except (HTTPError, URLError, OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"KV storage request failed: {exc}") from exc
    if payload.get("error"):
        raise RuntimeError(f"KV storage error: {payload['error']}")
    return payload.get("result")


def kv_get_json(key: str):
    raw = kv_command("GET", key)
    if raw is None:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    return json.loads(str(raw))


def kv_set_json(key: str, value, ttl_seconds: int | None = None) -> None:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if ttl_seconds:
        kv_command("SET", key, payload, "EX", ttl_seconds)
    else:
        kv_command("SET", key, payload)


def kv_delete(key: str) -> None:
    kv_command("DEL", key)


def kv_next_id(name: str) -> int:
    return int(kv_command("INCR", kv_key("seq", name)))


def kv_user_key(user_id: int | str) -> str:
    return kv_key("user", user_id)


def kv_user_email_key(email: str) -> str:
    return kv_key("user_email", email.lower())


def kv_session_key(token: str) -> str:
    return kv_key("session", token)


def kv_verification_key(email: str) -> str:
    return kv_key("email_verification", email.lower())


def kv_rate_key(kind: str, value: str) -> str:
    return kv_key("rate", kind, value)


def kv_recent_timestamps(key: str, cutoff: str) -> list[str]:
    timestamps = kv_get_json(key) or []
    return [ts for ts in timestamps if isinstance(ts, str) and ts > cutoff]


def kv_store_timestamps(key: str, timestamps: list[str], ttl_seconds: int = 3600) -> None:
    kv_set_json(key, timestamps, ttl_seconds)


def kv_get_user_by_id(user_id: int | str) -> dict[str, Any] | None:
    user = kv_get_json(kv_user_key(user_id))
    return user if isinstance(user, dict) else None


def kv_get_user_by_email(email: str) -> dict[str, Any] | None:
    user_id = kv_command("GET", kv_user_email_key(email))
    return kv_get_user_by_id(user_id) if user_id else None


def kv_save_user(user: dict[str, Any]) -> None:
    kv_set_json(kv_user_key(user["id"]), user)
    kv_command("SET", kv_user_email_key(user["email"]), user["id"])


def ensure_sqlite_user_for_kv_user(user: dict[str, Any]) -> None:
    user_id = int(user["id"])
    values = (
        user_id,
        user["email"],
        user.get("name") or "",
        user.get("password_hash") or "",
        user.get("role") or "registered",
        user.get("created_at") or now_iso(),
        int(user.get("email_verified", 1)),
        int(user.get("free_searches_remaining", 0)),
    )
    with db() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE id = ? OR email = ? ORDER BY CASE WHEN id = ? THEN 0 ELSE 1 END LIMIT 1",
            (user_id, user["email"], user_id),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE users
                SET id = ?, email = ?, name = ?, password_hash = ?, role = ?, created_at = ?,
                    email_verified = ?, free_searches_remaining = ?
                WHERE id = ?
                """,
                (*values, existing["id"]),
            )
            return
        conn.execute(
            """
            INSERT INTO users (id, email, name, password_hash, role, created_at, email_verified, free_searches_remaining)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )


def kv_create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    kv_command("SET", kv_session_key(token), user_id, "EX", SESSION_TTL_SECONDS)
    return token


def kv_user_for_token(token: str) -> dict[str, Any] | None:
    user_id = kv_command("GET", kv_session_key(token))
    if not user_id:
        return None
    user = kv_get_user_by_id(user_id)
    if not user:
        kv_delete(kv_session_key(token))
        return None
    ensure_sqlite_user_for_kv_user(user)
    return user


def kv_consume_free_search(user_id: int) -> bool:
    user = kv_get_user_by_id(user_id)
    if not user:
        return False
    if user.get("role") != "registered":
        return True
    remaining = int(user.get("free_searches_remaining", 0))
    if remaining <= 0:
        return False
    user["free_searches_remaining"] = remaining - 1
    kv_save_user(user)
    ensure_sqlite_user_for_kv_user(user)
    return True


def ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def user_to_api(user: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    data = dict(user)
    return {
        "id": data["id"],
        "name": data["name"],
        "role": data["role"],
        "free_searches_remaining": int(data.get("free_searches_remaining") or 0),
    }


def is_metered_user(user: sqlite3.Row | dict[str, Any]) -> bool:
    return dict(user).get("role") == "registered"


def has_search_quota(user: sqlite3.Row | dict[str, Any]) -> bool:
    if not is_metered_user(user):
        return True
    return int(dict(user).get("free_searches_remaining") or 0) > 0


def consume_free_search(user_id: int) -> bool:
    if kv_enabled() and int(user_id) >= KV_USER_ID_OFFSET:
        return kv_consume_free_search(int(user_id))
    with db() as conn:
        row = conn.execute("SELECT role, free_searches_remaining FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return False
        if row["role"] != "registered":
            return True
        if int(row["free_searches_remaining"] or 0) <= 0:
            return False
        conn.execute(
            "UPDATE users SET free_searches_remaining = free_searches_remaining - 1 WHERE id = ? AND free_searches_remaining > 0",
            (user_id,),
        )
        return True


def code_hash(email: str, code: str) -> str:
    return hashlib.sha256(f"{email.lower()}:{code}".encode("utf-8")).hexdigest()


def challenge_hash(challenge_id: str, answer: str) -> str:
    return hashlib.sha256(f"{challenge_id}:{answer.strip().upper()}".encode("utf-8")).hexdigest()


def create_bot_challenge() -> dict[str, str]:
    width = 136
    height = 48
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"
    answer = "".join(random.choice(alphabet) for _ in range(4))
    dots = []
    for _ in range(28):
        cx, cy = random.randint(0, width), random.randint(0, height)
        radius = random.choice(["0.9", "1.2", "1.6", "2"])
        color = random.choice(["#2f8f47", "#d65f8f", "#6843a3", "#1f5d9c", "#d28a2a"])
        dots.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}" fill-opacity="0.55"/>')
    letters = []
    for idx, char in enumerate(answer):
        x = 10 + idx * 31 + random.randint(-2, 2)
        y = 38 + random.randint(-3, 3)
        rotation = random.randint(-13, 13)
        skew = random.randint(-10, 10)
        scale_x = random.choice(["0.92", "0.98", "1.04", "1.10"])
        letters.append(
            f'<g transform="translate({x} {y}) rotate({rotation}) skewX({skew}) scale({scale_x} 1)">'
            f'<text x="0" y="0" font-family="Trebuchet MS,Arial,sans-serif" font-size="43" '
            f'font-weight="500" fill="#4da33f" fill-opacity="0.92" filter="url(#softBlur)">{escape(char)}</text>'
            "</g>"
        )
    line_y1 = random.randint(23, 33)
    line_y2 = random.randint(5, 15)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        "<defs>"
        '<filter id="softBlur"><feGaussianBlur stdDeviation="0.35"/></filter>'
        "</defs>"
        f'<rect width="{width}" height="{height}" rx="3" fill="#f8fbf5"/>'
        f'<path d="M-8 {line_y1} L{width + 10} {line_y2}" stroke="#bf8756" stroke-opacity="0.72" stroke-width="1.7"/>'
        f'{"".join(dots)}'
        f'{"".join(letters)}'
        "</svg>"
    )
    image = "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")
    challenge_id = uuid.uuid4().hex
    expires_at = (datetime.now(LOCAL_TZ) + timedelta(minutes=10)).isoformat(timespec="seconds")
    with db() as conn:
        conn.execute(
            "INSERT INTO bot_challenges (id, question, answer_hash, expires_at, created_at) VALUES (?, ?, ?, ?, ?)",
            (challenge_id, answer, challenge_hash(challenge_id, answer), expires_at, now_iso()),
        )
    return {"id": challenge_id, "image": image, "length": 4}


def verify_bot_challenge(payload: dict[str, Any]) -> None:
    if str(payload.get("website") or "").strip():
        raise RuntimeError("机器人检测未通过，请重新提交。")
    challenge_id = str(payload.get("challenge_id") or "").strip()
    answer = str(payload.get("challenge_answer") or "").strip()
    if not challenge_id or not answer:
        raise RuntimeError("请先完成机器人检测。")
    with db() as conn:
        row = conn.execute("SELECT * FROM bot_challenges WHERE id = ?", (challenge_id,)).fetchone()
        if not row or row["used_at"]:
            raise RuntimeError("机器人检测已失效，请刷新后重试。")
        if row["expires_at"] < now_iso():
            raise RuntimeError("机器人检测已过期，请刷新后重试。")
        if not hmac.compare_digest(row["answer_hash"], challenge_hash(challenge_id, answer)):
            raise RuntimeError("机器人检测答案不正确。")
        conn.execute("UPDATE bot_challenges SET used_at = ? WHERE id = ?", (now_iso(), challenge_id))


def send_verification_email(email: str, code: str) -> None:
    smtp_user = os.getenv("SMTP_USER", "raaaaiiia1@gmail.com").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port = safe_int(os.getenv("SMTP_PORT"), 587)
    smtp_from = os.getenv("SMTP_FROM", smtp_user).strip() or smtp_user
    if not smtp_password:
        raise RuntimeError("邮件服务尚未配置 SMTP_PASSWORD，请使用 Gmail 应用专用密码。")
    message = EmailMessage()
    message["From"] = smtp_from
    message["To"] = email
    message["Subject"] = "人才地图注册验证码"
    message.set_content(f"你的注册验证码是：{code}\n\n验证码 10 分钟内有效。若非本人操作，请忽略这封邮件。")
    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as smtp:
        if os.getenv("SMTP_USE_TLS", "1") != "0":
            smtp.starttls()
        smtp.login(smtp_user, smtp_password)
        smtp.send_message(message)


def init_db() -> None:
    with db() as conn:
        schema_sql = """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT '普通用户',
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                email_verified INTEGER NOT NULL DEFAULT 1,
                free_searches_remaining INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                profile_json TEXT NOT NULL,
                saved INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT '进行中',
                created_by INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(created_by) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                current_company TEXT DEFAULT '',
                title TEXT DEFAULT '',
                city TEXT DEFAULT '',
                years TEXT DEFAULT '',
                skill_tags TEXT DEFAULT '[]',
                past_companies TEXT DEFAULT '[]',
                works TEXT DEFAULT '[]',
                source_links TEXT DEFAULT '[]',
                platforms TEXT DEFAULT '[]',
                recommendation_reason TEXT DEFAULT '',
                risk_notes TEXT DEFAULT '',
                score INTEGER DEFAULT NULL,
                score_band TEXT DEFAULT '',
                confidence INTEGER DEFAULT NULL,
                aigc_usage TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT '待评估',
                raw_evidence TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                title TEXT DEFAULT '',
                content_excerpt TEXT DEFAULT '',
                source_type TEXT DEFAULT 'public_web',
                status TEXT DEFAULT '已采集',
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor TEXT DEFAULT '',
                action TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS email_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                code_hash TEXT NOT NULL,
                ip_address TEXT DEFAULT '',
                expires_at TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                sent_at TEXT NOT NULL,
                verified_at TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS bot_challenges (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                answer_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used_at TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );
            """
        for statement in schema_sql.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(statement)
        ensure_column(conn, "users", "email_verified", "email_verified INTEGER NOT NULL DEFAULT 1")
        ensure_column(conn, "users", "free_searches_remaining", "free_searches_remaining INTEGER NOT NULL DEFAULT 0")
        existing = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        if existing == 0:
            admin_email = os.getenv("TALENT_MAP_ADMIN_EMAIL", "admin@local").strip().lower()
            admin_name = os.getenv("TALENT_MAP_ADMIN_NAME", "管理员").strip() or "管理员"
            admin_password = os.getenv("TALENT_MAP_ADMIN_PASSWORD")
            if not admin_password:
                admin_password = uuid.uuid4().hex if os.getenv("VERCEL") else "admin123"
            conn.execute(
                """
                INSERT INTO users (email, name, role, password_hash, created_at, email_verified, free_searches_remaining)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (admin_email, admin_name, "管理员", pbkdf2_hash(admin_password), now_iso(), 1, 0),
            )
        defaults = {
            "deepseek_model": "deepseek-chat",
            "tavily_max_results": "8",
            "max_web_pages": "50",
            "search_provider": "tavily",
        }
        for key, value in defaults.items():
            conn.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", (key, value))


def get_config() -> dict[str, str]:
    with db() as conn:
        rows = conn.execute("SELECT key, value FROM config").fetchall()
    return {row["key"]: row["value"] for row in rows}


def set_config(values: dict[str, Any]) -> None:
    allowed = {
        "deepseek_api_key",
        "deepseek_model",
        "tavily_api_key",
        "tavily_max_results",
        "max_web_pages",
        "search_provider",
    }
    with db() as conn:
        for key, value in values.items():
            if key not in allowed:
                continue
            if value is None:
                continue
            text = str(value).strip()
            if text == "":
                continue
            if text == "__clear__":
                conn.execute("DELETE FROM config WHERE key = ?", (key,))
            else:
                conn.execute(
                    "INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (key, text),
                )


def audit(actor: str, action: str, payload: dict[str, Any]) -> None:
    with db() as conn:
        conn.execute(
            "INSERT INTO audit_log (actor, action, payload_json, created_at) VALUES (?, ?, ?, ?)",
            (actor, action, json.dumps(payload, ensure_ascii=False), now_iso()),
        )


def project_to_api(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["profile"] = json.loads(data.pop("profile_json"))
    data["saved"] = bool(data["saved"])
    return data


def infer_project_title(profile: dict[str, Any], answers: list[dict[str, Any]] | None = None) -> str:
    chunks = [
        str(profile.get("raw_requirements") or ""),
        str(profile.get("scoring_notes") or ""),
        str(profile.get("workflow_notes") or ""),
    ]
    for item in answers or []:
        if isinstance(item, dict):
            chunks.append(str(item.get("answer") or ""))
            chunks.append(str(item.get("question") or ""))
    text = " ".join(chunks)
    explicit_roles = [
        "AI算法工程师",
        "算法工程师",
        "AIGC创作者",
        "短视频编导",
        "视频剪辑师",
        "内容策划",
        "内容运营",
        "直播运营",
        "品牌广告策划",
    ]
    for role in explicit_roles:
        if role in text:
            return role
    if re.search(r"(AI|AIGC|大模型|算法|机器学习|深度学习|推荐|搜索)", text, re.I):
        return "AI算法工程师"
    if re.search(r"(编导|导演|分镜)", text):
        return "短视频编导"
    if re.search(r"(剪辑|调色|后期|包装)", text):
        return "视频剪辑师"
    if re.search(r"(直播|主播|场控)", text):
        return "直播运营"
    if re.search(r"(内容|选题|脚本|文案|策划)", text):
        return "内容策划"
    return "视频创作人才"


def candidate_to_api(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    for field in JSON_FIELDS:
        data[field] = from_json_text(data.get(field))
    return data


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def score_band(score: int | None) -> str:
    if score is None:
        return ""
    if score >= 85:
        return "强推荐"
    if score >= 70:
        return "可跟进"
    if score >= 55:
        return "待观察"
    return "不建议"


def rule_score_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(
        [
            str(candidate.get("recommendation_reason", "")),
            str(candidate.get("risk_notes", "")),
            " ".join(normalize_list(candidate.get("skill_tags"))),
            " ".join(normalize_list(candidate.get("works"))),
            str(candidate.get("title", "")),
        ]
    )
    score = 52
    positives = {
        "爆款": 8,
        "选题": 7,
        "品牌": 7,
        "商业": 7,
        "转化": 7,
        "剪辑": 5,
        "调色": 5,
        "审美": 5,
        "编导": 5,
        "AIGC": 6,
        "AI": 4,
        "知识科普": 4,
        "直播": 4,
        "投流": 4,
        "方法论": 5,
        "团队": 5,
    }
    negatives = {
        "模板": -10,
        "同质化": -12,
        "搬运": -12,
        "证据不足": -8,
        "信息不足": -6,
        "过度依赖": -8,
    }
    for word, weight in positives.items():
        if word.lower() in text.lower():
            score += weight
    for word, weight in negatives.items():
        if word in text:
            score += weight
    if normalize_list(candidate.get("works")):
        score += 8
    if normalize_list(candidate.get("source_links")):
        score += 5
    years = re.search(r"\d+", str(candidate.get("years", "")))
    if years:
        score += min(safe_int(years.group(0)), 8)
    bounded = max(20, min(96, score))
    return {"score": bounded, "score_band": score_band(bounded), "confidence": 55 if bounded < 70 else 68}


def build_profile_from_answers(answers: list[dict[str, str]] | None, draft: dict[str, Any] | None = None) -> dict[str, Any]:
    profile = json.loads(json.dumps(DEFAULT_PROFILE, ensure_ascii=False))
    draft = draft or {}
    profile.update({k: v for k, v in draft.items() if v not in (None, "", [])})
    if not answers:
        return profile
    text = "\n".join([str(item.get("answer", "")) for item in answers])
    if text.strip():
        profile["raw_requirements"] = text.strip()
    city_terms = [term for term in ["杭州", "上海", "苏州", "南京", "宁波", "无锡", "合肥", "嘉兴"] if term in text]
    if city_terms:
        profile["region"] = "、".join(dict.fromkeys(city_terms))
    platform_terms = [term for term in ["抖音", "小红书", "B站", "淘宝直播", "视频号", "快手"] if term in text]
    if platform_terms:
        profile["platforms"] = platform_terms
    content_terms = [term for term in ["品牌广告", "知识科普", "视频剪辑", "调色", "编剧", "文案", "AIGC", "直播", "短剧"] if term in text]
    if content_terms:
        profile["content_types"] = content_terms
    return profile


def build_search_plan(profile: dict[str, Any]) -> dict[str, Any]:
    cities = normalize_list(profile.get("region")) or ["杭州", "上海", "苏州", "南京"]
    platforms = normalize_list(profile.get("platforms")) or DEFAULT_PROFILE["platforms"]
    content_types = normalize_list(profile.get("content_types")) or DEFAULT_PROFILE["content_types"]
    industries = normalize_list(profile.get("industries")) or DEFAULT_PROFILE["industries"]
    company_types = normalize_list(profile.get("company_types")) or DEFAULT_PROFILE["company_types"]

    related_keywords = list(
        dict.fromkeys(
            [
                "短视频编导",
                "内容策划",
                "品牌广告",
                "商业案例",
                "爆款选题",
                "剪辑节奏",
                "调色",
                "脚本",
                "文案",
                "AIGC视频",
                "AI辅助创作",
                "账号运营",
                "直播内容",
                "内容负责人",
                "创意总监",
                "作品集",
                "复盘",
            ]
            + content_types
            + platforms
        )
    )
    competitor_pool = list(
        dict.fromkeys(
            [
                "遥望科技",
                "无忧传媒",
                "谦寻",
                "交个朋友",
                "新片场",
                "青藤文化",
                "蓝色光标",
                "华扬联众",
                "字节跳动抖音电商",
                "小红书商业化",
                "B站商业化",
                "淘宝直播",
                "阿里妈妈",
                "美ONE",
                "三只羊网络",
            ]
        )
    )
    query_seeds = []
    for city in cities[:4]:
        for platform in platforms[:4]:
            query_seeds.append(f"{city} {platform} {' '.join(content_types[:3])} 作品 案例")
            query_seeds.append(f"{city} {platform} 内容负责人 编导 品牌广告 商业案例")
    for company in competitor_pool[:8]:
        query_seeds.append(f"{company} 短视频 内容 创意 编导 案例")
    for company_type in company_types[:4]:
        query_seeds.append(f"杭州 {company_type} 短视频 编导 内容策划 作品集")
    queries = list(dict.fromkeys(query_seeds))[:18]
    narrow_questions = [
        "优先锁定哪一个平台？例如抖音、小红书、B站或淘宝直播。",
        "作品类型是否先限定为品牌广告、知识科普、直播内容或AIGC视频？",
        "候选人优先看企业员工、独立创作者，还是两者都要但分开展示？",
        "经验年限是否限定为3-5年、5-8年或8年以上？",
    ]
    return {
        "cities": cities,
        "platforms": platforms,
        "content_types": content_types,
        "industries": industries,
        "company_types": company_types,
        "related_keywords": related_keywords,
        "competitor_pool": competitor_pool,
        "queries": queries,
        "narrow_questions": narrow_questions,
        "source_policy": DEFAULT_PROFILE["source_policy"],
    }


def format_http_error(code: int, detail: str) -> str:
    message = detail.strip()
    try:
        parsed = json.loads(detail)
        if isinstance(parsed, dict):
            error = parsed.get("error")
            if isinstance(error, dict):
                message = str(error.get("message") or message)
            else:
                message = str(parsed.get("message") or message)
    except json.JSONDecodeError:
        pass

    lower = message.lower()
    if code == 402 and ("insufficient balance" in lower or "balance" in lower):
        return "账户余额不足或额度已用完，请到服务商后台充值，或在设置里更换可用的 API Key 后重试。"
    if code in (401, 403):
        return "API Key 无效、权限不足或已过期，请检查设置中的 Key。"
    if code == 429:
        return "请求频率过高或额度暂时受限，请稍后重试。"
    return f"HTTP {code}: {message[:500]}"


def call_json_api(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: int = 45) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urlrequest.Request(url, data=body, headers=headers, method="POST")
    try:
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8", errors="replace")
            return json.loads(data)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(format_http_error(exc.code, detail)) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(str(exc)) from exc


def deepseek_chat(config: dict[str, str], messages: list[dict[str, str]], temperature: float = 0.2) -> str:
    api_key = config.get("deepseek_api_key") or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DeepSeek API Key 未配置")
    model = config.get("deepseek_model") or "deepseek-chat"
    data = call_json_api(
        "https://api.deepseek.com/chat/completions",
        {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        },
        {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=60,
    )
    return data["choices"][0]["message"]["content"]


def parse_json_payload(text: str) -> Any:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start_candidates = [idx for idx in [cleaned.find("{"), cleaned.find("[")] if idx >= 0]
        if not start_candidates:
            raise
        start = min(start_candidates)
        end = max(cleaned.rfind("}"), cleaned.rfind("]"))
        return json.loads(cleaned[start : end + 1])


def extract_candidates_with_ai(corpus: str, profile: dict[str, Any], config: dict[str, str]) -> list[dict[str, Any]]:
    prompt = f"""
你是企业HR的人才地图分析助手。请只基于给定公开文本抽取“可被人工复核的候选人线索”，不要编造姓名、公司、职位或作品。

业务方向：{json.dumps(profile, ensure_ascii=False)}

判断重点：
1. 作品/账号/商业案例优先；
2. 选题需要新颖、触及人心或有信息价值；
3. 剪辑节奏、画面、调色体现创作实力；
4. 品牌植入能自然融入即可，但需要有经验；
5. AIGC是加分项，要区分模板化AI生成、纯AI生成、人类创意主导+AI辅助、快速AIGC产能。

输出 JSON 对象，格式：
{{
  "candidates": [
    {{
      "name": "姓名或账号名；无法确认则不要输出该条",
      "current_company": "当前公司/机构/账号主体",
      "title": "职位/角色",
      "city": "城市",
      "years": "年限或空字符串",
      "skill_tags": ["技能"],
      "past_companies": ["过往公司"],
      "works": ["公开作品/项目/账号/案例"],
      "source_links": ["来源链接"],
      "platforms": ["抖音/小红书/B站/淘宝直播等"],
      "recommendation_reason": "推荐理由，必须引用公开证据",
      "risk_notes": "风险点，例如公开信息不足、个人贡献不清、作品同质化等",
      "score": 0到100的整数,
      "confidence": 0到100的整数,
      "aigc_usage": "无明显AIGC/AI辅助剪辑包装/AI辅助脚本分镜/AI图像视频生成/纯AI模板化生成/人类创意主导+AIGC提效/未知"
    }}
  ]
}}

公开文本：
{corpus[:42000]}
"""
    raw = deepseek_chat(
        config,
        [
            {"role": "system", "content": "你只输出合法 JSON，不输出解释。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )
    parsed = parse_json_payload(raw)
    if isinstance(parsed, dict):
        candidates = parsed.get("candidates", [])
    elif isinstance(parsed, list):
        candidates = parsed
    else:
        candidates = []
    return [item for item in candidates if isinstance(item, dict) and item.get("name")]


def tavily_search(query: str, config: dict[str, str], max_results: int) -> list[dict[str, str]]:
    api_key = config.get("tavily_api_key") or os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("Tavily API Key 未配置")
    data = call_json_api(
        "https://api.tavily.com/search",
        {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_raw_content": True,
            "include_answer": False,
        },
        {"Content-Type": "application/json"},
        timeout=45,
    )
    return data.get("results", []) if isinstance(data, dict) else []


def strip_html(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    raw = re.sub(r"&nbsp;?", " ", raw)
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip()


def fetch_public_page(url: str) -> dict[str, str]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise RuntimeError("仅支持 http/https 公开链接")
    req = urlrequest.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 TalentMapLocal/0.1 (+local research tool)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urlrequest.urlopen(req, timeout=25) as resp:
            data = resp.read(1_800_000)
            ctype = resp.headers.get("Content-Type", "")
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(str(exc)) from exc
    encoding_match = re.search(r"charset=([\w-]+)", ctype, re.I)
    encoding = encoding_match.group(1) if encoding_match else "utf-8"
    html = data.decode(encoding, errors="replace")
    title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    title = strip_html(title_match.group(1)) if title_match else parsed.netloc
    text = strip_html(html)
    return {"url": url, "title": title[:240], "content": text[:12000]}


def save_sources(project_id: int, sources: list[dict[str, str]]) -> None:
    with db() as conn:
        for source in sources:
            conn.execute(
                """
                INSERT INTO sources (project_id, url, title, content_excerpt, source_type, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    source.get("url", ""),
                    source.get("title", ""),
                    source.get("content", "")[:2000],
                    source.get("source_type", "public_web"),
                    source.get("status", "已采集"),
                    now_iso(),
                ),
            )


def normalize_candidate_payload(project_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    merged = dict(payload)
    if not merged.get("name"):
        merged["name"] = "待确认候选人"
    score = merged.get("score")
    if score in ("", None):
        scored = rule_score_candidate(merged)
        merged.update({k: v for k, v in scored.items() if not merged.get(k)})
    else:
        score_value = max(0, min(100, safe_int(score)))
        merged["score"] = score_value
        merged["score_band"] = score_band(score_value)
    if "confidence" not in merged or merged.get("confidence") in ("", None):
        merged["confidence"] = 55
    status = str(merged.get("status") or "待评估")
    if status not in STATUS_OPTIONS:
        status = "待评估"
    return {
        "project_id": project_id,
        "name": str(merged.get("name", "")).strip()[:120],
        "current_company": str(merged.get("current_company", "")).strip()[:160],
        "title": str(merged.get("title", "")).strip()[:160],
        "city": str(merged.get("city", "")).strip()[:80],
        "years": str(merged.get("years", "")).strip()[:80],
        "skill_tags": to_json_text(merged.get("skill_tags")),
        "past_companies": to_json_text(merged.get("past_companies")),
        "works": to_json_text(merged.get("works")),
        "source_links": to_json_text(merged.get("source_links")),
        "platforms": to_json_text(merged.get("platforms")),
        "recommendation_reason": str(merged.get("recommendation_reason", "")).strip(),
        "risk_notes": str(merged.get("risk_notes", "")).strip(),
        "score": safe_int(merged.get("score"), 0) or None,
        "score_band": str(merged.get("score_band") or score_band(safe_int(merged.get("score"), 0)) or ""),
        "confidence": safe_int(merged.get("confidence"), 55),
        "aigc_usage": str(merged.get("aigc_usage", "")).strip()[:120],
        "status": status,
        "raw_evidence": str(merged.get("raw_evidence", "")).strip(),
    }


def insert_candidates(project_id: int, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    created: list[dict[str, Any]] = []
    with db() as conn:
        for item in candidates:
            normalized = normalize_candidate_payload(project_id, item)
            cursor = conn.execute(
                """
                INSERT INTO candidates (
                    project_id, name, current_company, title, city, years, skill_tags,
                    past_companies, works, source_links, platforms, recommendation_reason,
                    risk_notes, score, score_band, confidence, aigc_usage, status, raw_evidence,
                    created_at, updated_at
                ) VALUES (
                    :project_id, :name, :current_company, :title, :city, :years, :skill_tags,
                    :past_companies, :works, :source_links, :platforms, :recommendation_reason,
                    :risk_notes, :score, :score_band, :confidence, :aigc_usage, :status, :raw_evidence,
                    :created_at, :updated_at
                )
                """,
                {**normalized, "created_at": now_iso(), "updated_at": now_iso()},
            )
            row = conn.execute("SELECT * FROM candidates WHERE id = ?", (cursor.lastrowid,)).fetchone()
            created.append(candidate_to_api(row))
    return created


def map_row_to_candidate(row: dict[str, Any]) -> dict[str, Any]:
    mapped: dict[str, Any] = {}
    for key, value in row.items():
        canonical = FIELD_ALIASES.get(str(key).strip(), str(key).strip())
        mapped[canonical] = value
    return mapped


def parse_csv_bytes(data: bytes) -> list[dict[str, Any]]:
    for encoding in ("utf-8-sig", "gb18030", "utf-8"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = data.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def column_index(cell_ref: str) -> int:
    letters = re.sub(r"\d+", "", cell_ref)
    value = 0
    for char in letters:
        value = value * 26 + (ord(char.upper()) - ord("A") + 1)
    return value - 1


def parse_xlsx_bytes(data: bytes) -> list[dict[str, Any]]:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root.iter():
                if si.tag.endswith("}si") or si.tag == "si":
                    texts = [node.text or "" for node in si.iter() if node.tag.endswith("}t") or node.tag == "t"]
                    shared.append("".join(texts))
        sheet_name = "xl/worksheets/sheet1.xml"
        if sheet_name not in zf.namelist():
            candidates = [name for name in zf.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")]
            if not candidates:
                return []
            sheet_name = candidates[0]
        root = ET.fromstring(zf.read(sheet_name))
        rows: list[list[str]] = []
        for row_node in root.iter():
            if not (row_node.tag.endswith("}row") or row_node.tag == "row"):
                continue
            cells: list[str] = []
            for c in row_node:
                if not (c.tag.endswith("}c") or c.tag == "c"):
                    continue
                idx = column_index(c.attrib.get("r", f"A{len(cells) + 1}"))
                while len(cells) <= idx:
                    cells.append("")
                cell_type = c.attrib.get("t")
                value = ""
                if cell_type == "inlineStr":
                    value = "".join([node.text or "" for node in c.iter() if node.tag.endswith("}t") or node.tag == "t"])
                else:
                    v = next((node.text for node in c if node.tag.endswith("}v") or node.tag == "v"), "")
                    if cell_type == "s" and str(v).isdigit():
                        value = shared[int(v)] if int(v) < len(shared) else ""
                    else:
                        value = str(v or "")
                cells[idx] = value
            if any(cell.strip() for cell in cells):
                rows.append(cells)
        if not rows:
            return []
        headers = [cell.strip() or f"字段{idx + 1}" for idx, cell in enumerate(rows[0])]
        return [dict(zip(headers, row + [""] * (len(headers) - len(row)))) for row in rows[1:]]


def extract_pdf_text(data: bytes) -> str:
    raw = data.decode("latin-1", errors="ignore")
    snippets = re.findall(r"\(([^()]{1,180})\)\s*Tj", raw)
    snippets += re.findall(r"\(([^()]{1,180})\)\s*TJ", raw)
    text = " ".join(snippets)
    text = text.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
    return re.sub(r"\s+", " ", text).strip()


def parse_multipart(content_type: str, body: bytes) -> dict[str, dict[str, Any]]:
    match = re.search(r"boundary=(.+)", content_type)
    if not match:
        raise RuntimeError("缺少 multipart boundary")
    boundary = match.group(1).strip().strip('"').encode("utf-8")
    result: dict[str, dict[str, Any]] = {}
    for part in body.split(b"--" + boundary):
        part = part.strip(b"\r\n")
        if not part or part == b"--":
            continue
        header_blob, _, content = part.partition(b"\r\n\r\n")
        headers = header_blob.decode("utf-8", errors="replace")
        name_match = re.search(r'name="([^"]+)"', headers)
        if not name_match:
            continue
        name = name_match.group(1)
        filename_match = re.search(r'filename="([^"]*)"', headers)
        result[name] = {
            "filename": filename_match.group(1) if filename_match else "",
            "content": content.rstrip(b"\r\n"),
            "headers": headers,
        }
    return result


def create_xlsx(candidates: list[dict[str, Any]]) -> bytes:
    headers = [
        "姓名",
        "当前公司",
        "职位",
        "城市",
        "年限",
        "技能标签",
        "过往公司",
        "公开作品/项目",
        "来源链接",
        "推荐理由",
        "风险点",
        "评分",
        "分档",
        "可信度",
        "状态",
    ]
    rows = [headers]
    for c in candidates:
        rows.append(
            [
                c.get("name", ""),
                c.get("current_company", ""),
                c.get("title", ""),
                c.get("city", ""),
                c.get("years", ""),
                "、".join(c.get("skill_tags", [])),
                "、".join(c.get("past_companies", [])),
                "；".join(c.get("works", [])),
                "；".join(c.get("source_links", [])),
                c.get("recommendation_reason", ""),
                c.get("risk_notes", ""),
                c.get("score", ""),
                c.get("score_band", ""),
                c.get("confidence", ""),
                c.get("status", ""),
            ]
        )

    def cell_ref(col: int, row: int) -> str:
        name = ""
        col += 1
        while col:
            col, rem = divmod(col - 1, 26)
            name = chr(65 + rem) + name
        return f"{name}{row}"

    sheet_rows = []
    for row_idx, row in enumerate(rows, start=1):
        cells = []
        for col_idx, value in enumerate(row):
            text = escape(str(value))
            cells.append(f'<c r="{cell_ref(col_idx, row_idx)}" t="inlineStr"><is><t>{text}</t></is></c>')
        sheet_rows.append(f'<row r="{row_idx}">{"".join(cells)}</row>')
    sheet_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<sheetData>{"".join(sheet_rows)}</sheetData>
</worksheet>"""
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>""")
        zf.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""")
        zf.writestr("xl/workbook.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="候选人" sheetId="1" r:id="rId1"/></sheets>
</workbook>""")
        zf.writestr("xl/_rels/workbook.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>""")
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return output.getvalue()


def candidates_for_project(project_id: int) -> list[dict[str, Any]]:
    with db() as conn:
        rows = conn.execute("SELECT * FROM candidates WHERE project_id = ? ORDER BY score IS NULL, score DESC, id DESC", (project_id,)).fetchall()
    return [candidate_to_api(row) for row in rows]


def build_report_html(project: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
    skills: dict[str, int] = {}
    platforms: dict[str, int] = {}
    statuses: dict[str, int] = {}
    for c in candidates:
        for skill in c.get("skill_tags", []):
            skills[skill] = skills.get(skill, 0) + 1
        for platform in c.get("platforms", []):
            platforms[platform] = platforms.get(platform, 0) + 1
        statuses[c.get("status", "待评估")] = statuses.get(c.get("status", "待评估"), 0) + 1
    top_skills = sorted(skills.items(), key=lambda item: item[1], reverse=True)[:12]
    top_platforms = sorted(platforms.items(), key=lambda item: item[1], reverse=True)[:8]
    strong = [c for c in candidates if safe_int(c.get("score")) >= 85]
    follow = [c for c in candidates if 70 <= safe_int(c.get("score")) < 85]
    risks = [c for c in candidates if c.get("risk_notes")]
    rows = "\n".join(
        f"<tr><td>{escape(c.get('name',''))}</td><td>{escape(c.get('current_company',''))}</td><td>{escape(c.get('title',''))}</td><td>{escape(str(c.get('score') or ''))}</td><td>{escape(c.get('score_band',''))}</td><td>{escape(c.get('recommendation_reason','')[:160])}</td></tr>"
        for c in candidates[:30]
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{escape(project["title"])} - 人才洞察报告</title>
<style>
body{{font-family:"Microsoft YaHei",sans-serif;margin:40px;color:#202124;line-height:1.65}}
h1,h2{{font-family:Georgia,"Microsoft YaHei",serif;letter-spacing:0}}
.muted{{color:#6b7280}} .grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
.metric{{border:1px solid #ddd;border-radius:8px;padding:16px}} .metric b{{display:block;font-size:28px}}
table{{width:100%;border-collapse:collapse;margin-top:12px}}td,th{{border-bottom:1px solid #e5e7eb;padding:8px;text-align:left;vertical-align:top}}
.pill{{display:inline-block;border:1px solid #d1d5db;border-radius:999px;padding:4px 10px;margin:3px;background:#f9fafb}}
button{{padding:8px 12px;border:1px solid #111;background:#111;color:white;border-radius:6px}}
@media print{{button{{display:none}} body{{margin:18mm}}}}
</style>
</head>
<body>
<button onclick="window.print()">打印 / 另存为 PDF</button>
<h1>{escape(project["title"])}</h1>
<p class="muted">业务人才洞察报告 · 生成时间 {now_iso()} · 数据来源为公开信息和/或企业授权导入，AI评分仅作辅助。</p>
<h2>人才池概览</h2>
<div class="grid">
<div class="metric"><span>候选人</span><b>{len(candidates)}</b></div>
<div class="metric"><span>强推荐</span><b>{len(strong)}</b></div>
<div class="metric"><span>可跟进</span><b>{len(follow)}</b></div>
<div class="metric"><span>含风险提示</span><b>{len(risks)}</b></div>
</div>
<h2>技能分布</h2>
<p>{''.join(f'<span class="pill">{escape(k)} · {v}</span>' for k, v in top_skills) or '暂无技能数据'}</p>
<h2>平台分布</h2>
<p>{''.join(f'<span class="pill">{escape(k)} · {v}</span>' for k, v in top_platforms) or '暂无平台数据'}</p>
<h2>流动路径</h2>
<p class="muted">第一版根据过往公司与当前公司生成方向性线索；公开信息不足时需人工确认。</p>
<h2>招聘建议</h2>
<p>优先约谈评分在70分以上、作品/账号/商业案例证据完整的人选；对“同质化严重、模板依赖、个人贡献不清”的候选人保持审慎。若人才池超过50人，建议先按平台、内容类型或经验年限缩小范围。</p>
<h2>候选人明细</h2>
<table><thead><tr><th>姓名</th><th>公司</th><th>职位</th><th>评分</th><th>分档</th><th>推荐理由</th></tr></thead><tbody>{rows}</tbody></table>
</body>
</html>"""


class TalentMapHandler(BaseHTTPRequestHandler):
    server_version = "TalentMapLocal/0.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[%s] %s\n" % (now_iso(), fmt % args))

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_bytes(self, body: bytes, content_type: str, filename: str | None = None, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if filename:
            safe_name = filename.encode("utf-8")
            self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{safe_name.decode('utf-8')}")
        self.end_headers()
        self.wfile.write(body)

    def read_body(self) -> bytes:
        length = safe_int(self.headers.get("Content-Length"), 0)
        return self.rfile.read(length) if length else b""

    def read_json(self) -> dict[str, Any]:
        body = self.read_body()
        if not body:
            return {}
        return json.loads(body.decode("utf-8"))

    def current_user(self) -> dict[str, Any] | None:
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        token = auth.removeprefix("Bearer ").strip()
        if kv_enabled():
            try:
                user = kv_user_for_token(token)
            except RuntimeError:
                user = None
            if user:
                return user
        with db() as conn:
            row = conn.execute(
                """
                SELECT users.* FROM sessions
                JOIN users ON users.id = sessions.user_id
                WHERE sessions.token = ? AND sessions.expires_at > ?
                """,
                (token, now_iso()),
            ).fetchone()
        return dict(row) if row else None

    def require_user(self) -> dict[str, Any] | None:
        user = self.current_user()
        if not user:
            self.send_json({"error": "请先登录"}, 401)
            return None
        return user

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        try:
            if self.path.startswith("/api/"):
                self.handle_api_get()
            else:
                self.serve_static()
        except Exception as exc:
            self.send_json({"error": str(exc)}, 500)

    def do_POST(self) -> None:
        try:
            self.handle_api_post()
        except Exception as exc:
            self.send_json({"error": str(exc)}, 500)

    def do_PUT(self) -> None:
        try:
            self.handle_api_put()
        except Exception as exc:
            self.send_json({"error": str(exc)}, 500)

    def serve_static(self) -> None:
        path = unquote(urlparse(self.path).path)
        if path == "/":
            target = STATIC_DIR / "index.html"
        else:
            target = (BASE_DIR / path.lstrip("/")).resolve()
        if not str(target).startswith(str(BASE_DIR.resolve())) or not target.exists() or not target.is_file():
            self.send_json({"error": "Not found"}, 404)
            return
        content_type = "text/plain; charset=utf-8"
        if target.suffix == ".html":
            content_type = "text/html; charset=utf-8"
        elif target.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        elif target.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"
        elif target.suffix == ".svg":
            content_type = "image/svg+xml"
        self.send_bytes(target.read_bytes(), content_type)

    def handle_api_get(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/bootstrap":
            self.send_json(
                {
                    "app": "人才地图本地版",
                    "date": now_iso(),
                }
            )
            return
        if path == "/api/register-challenge":
            self.send_json({"challenge": create_bot_challenge()})
            return
        user = self.require_user()
        if not user:
            return
        if path == "/api/me":
            self.send_json({"user": user_to_api(user)})
            return
        if path == "/api/config":
            config = get_config()
            self.send_json(
                {
                    "config": {
                        "deepseek_model": config.get("deepseek_model", "deepseek-chat"),
                        "search_provider": config.get("search_provider", "tavily"),
                        "tavily_max_results": config.get("tavily_max_results", "8"),
                        "max_web_pages": config.get("max_web_pages", "50"),
                        "has_deepseek_api_key": bool(config.get("deepseek_api_key") or os.getenv("DEEPSEEK_API_KEY")),
                        "has_tavily_api_key": bool(config.get("tavily_api_key") or os.getenv("TAVILY_API_KEY")),
                    }
                }
            )
            return
        if path == "/api/projects":
            with db() as conn:
                rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
            self.send_json({"projects": [project_to_api(row) for row in rows]})
            return
        project_match = re.fullmatch(r"/api/projects/(\d+)", path)
        if project_match:
            project_id = safe_int(project_match.group(1))
            with db() as conn:
                row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            if not row:
                self.send_json({"error": "项目不存在"}, 404)
                return
            project = project_to_api(row)
            self.send_json({"project": project, "plan": build_search_plan(project["profile"])})
            return
        candidates_match = re.fullmatch(r"/api/projects/(\d+)/candidates", path)
        if candidates_match:
            self.send_json({"candidates": candidates_for_project(safe_int(candidates_match.group(1)))})
            return
        csv_match = re.fullmatch(r"/api/projects/(\d+)/export.csv", path)
        if csv_match:
            candidates = candidates_for_project(safe_int(csv_match.group(1)))
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["姓名", "当前公司", "职位", "城市", "年限", "技能标签", "过往公司", "公开作品/项目", "来源链接", "推荐理由", "风险点", "评分", "分档", "可信度", "状态"])
            for c in candidates:
                writer.writerow(
                    [
                        c.get("name", ""),
                        c.get("current_company", ""),
                        c.get("title", ""),
                        c.get("city", ""),
                        c.get("years", ""),
                        "、".join(c.get("skill_tags", [])),
                        "、".join(c.get("past_companies", [])),
                        "；".join(c.get("works", [])),
                        "；".join(c.get("source_links", [])),
                        c.get("recommendation_reason", ""),
                        c.get("risk_notes", ""),
                        c.get("score", ""),
                        c.get("score_band", ""),
                        c.get("confidence", ""),
                        c.get("status", ""),
                    ]
                )
            self.send_bytes(output.getvalue().encode("utf-8-sig"), "text/csv; charset=utf-8", "candidates.csv")
            return
        xlsx_match = re.fullmatch(r"/api/projects/(\d+)/export.xlsx", path)
        if xlsx_match:
            candidates = candidates_for_project(safe_int(xlsx_match.group(1)))
            self.send_bytes(create_xlsx(candidates), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "candidates.xlsx")
            return
        report_match = re.fullmatch(r"/api/projects/(\d+)/report.html", path)
        if report_match:
            project_id = safe_int(report_match.group(1))
            with db() as conn:
                row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            if not row:
                self.send_json({"error": "项目不存在"}, 404)
                return
            project = project_to_api(row)
            html = build_report_html(project, candidates_for_project(project_id))
            self.send_bytes(html.encode("utf-8"), "text/html; charset=utf-8", "talent-report.html")
            return
        self.send_json({"error": "Not found"}, 404)

    def handle_api_post(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/login":
            payload = self.read_json()
            email = str(payload.get("email", "")).strip().lower()
            password = str(payload.get("password", ""))
            if kv_enabled():
                user = kv_get_user_by_email(email)
                if not user or not verify_password(password, str(user.get("password_hash") or "")):
                    self.send_json({"error": "账号或密码不正确"}, 401)
                    return
                ensure_sqlite_user_for_kv_user(user)
                token = kv_create_session(int(user["id"]))
                self.send_json({"token": token, "user": user_to_api(user)})
                return
            with db() as conn:
                user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
                if not user or not verify_password(password, user["password_hash"]):
                    self.send_json({"error": "账号或密码不正确"}, 401)
                    return
                token = uuid.uuid4().hex + uuid.uuid4().hex
                expires_at = (datetime.now(LOCAL_TZ) + timedelta(days=14)).isoformat(timespec="seconds")
                conn.execute(
                    "INSERT INTO sessions (token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
                    (token, user["id"], expires_at, now_iso()),
                )
            self.send_json({"token": token, "user": user_to_api(user)})
            return
        if path == "/api/register/send-code":
            self.api_register_send_code()
            return
        if path == "/api/register/complete":
            self.api_register_complete()
            return
        user = self.require_user()
        if not user:
            return
        if path == "/api/config":
            payload = self.read_json()
            set_config(payload)
            audit(user["email"], "update_config", {"keys": list(payload.keys())})
            self.send_json({"ok": True})
            return
        if path == "/api/projects":
            payload = self.read_json()
            answers = payload.get("answers") if isinstance(payload.get("answers"), list) else []
            profile = build_profile_from_answers(answers, payload.get("profile") if isinstance(payload.get("profile"), dict) else {})
            title = str(payload.get("title") or infer_project_title(profile, answers)).strip()
            saved = 1 if payload.get("saved", True) else 0
            with db() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO projects (title, profile_json, saved, status, created_by, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (title, json.dumps(profile, ensure_ascii=False), saved, "进行中", user["id"], now_iso(), now_iso()),
                )
                row = conn.execute("SELECT * FROM projects WHERE id = ?", (cursor.lastrowid,)).fetchone()
            project = project_to_api(row)
            audit(user["email"], "create_project", {"project_id": project["id"], "title": title})
            self.send_json({"project": project, "plan": build_search_plan(profile)}, 201)
            return
        plan_match = re.fullmatch(r"/api/projects/(\d+)/plan", path)
        if plan_match:
            project_id = safe_int(plan_match.group(1))
            with db() as conn:
                row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            if not row:
                self.send_json({"error": "项目不存在"}, 404)
                return
            project = project_to_api(row)
            self.send_json({"plan": build_search_plan(project["profile"])})
            return
        discover_match = re.fullmatch(r"/api/projects/(\d+)/discover", path)
        if discover_match:
            self.api_discover(safe_int(discover_match.group(1)), user)
            return
        links_match = re.fullmatch(r"/api/projects/(\d+)/links", path)
        if links_match:
            self.api_import_links(safe_int(links_match.group(1)), user)
            return
        candidate_match = re.fullmatch(r"/api/projects/(\d+)/candidates", path)
        if candidate_match:
            payload = self.read_json()
            created = insert_candidates(safe_int(candidate_match.group(1)), [payload])
            self.send_json({"candidate": created[0]}, 201)
            return
        rows_match = re.fullmatch(r"/api/projects/(\d+)/import-rows", path)
        if rows_match:
            payload = self.read_json()
            rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
            candidates = [map_row_to_candidate(row) for row in rows if isinstance(row, dict)]
            created = insert_candidates(safe_int(rows_match.group(1)), candidates)
            self.send_json({"created": created, "count": len(created)}, 201)
            return
        file_match = re.fullmatch(r"/api/projects/(\d+)/import-file", path)
        if file_match:
            self.api_import_file(safe_int(file_match.group(1)), user)
            return
        self.send_json({"error": "Not found"}, 404)

    def handle_api_put(self) -> None:
        user = self.require_user()
        if not user:
            return
        path = urlparse(self.path).path
        candidate_match = re.fullmatch(r"/api/candidates/(\d+)", path)
        if candidate_match:
            candidate_id = safe_int(candidate_match.group(1))
            payload = self.read_json()
            allowed = {
                "name",
                "current_company",
                "title",
                "city",
                "years",
                "recommendation_reason",
                "risk_notes",
                "aigc_usage",
                "status",
                "score",
                "confidence",
                "raw_evidence",
            }
            json_allowed = JSON_FIELDS
            updates: dict[str, Any] = {}
            for key, value in payload.items():
                if key in allowed:
                    updates[key] = value
                if key in json_allowed:
                    updates[key] = to_json_text(value)
            if "score" in updates:
                updates["score"] = safe_int(updates["score"])
                updates["score_band"] = score_band(updates["score"])
            if updates.get("status") and updates["status"] not in STATUS_OPTIONS:
                updates["status"] = "待评估"
            if not updates:
                self.send_json({"error": "没有可更新字段"}, 400)
                return
            updates["updated_at"] = now_iso()
            set_clause = ", ".join([f"{key} = :{key}" for key in updates])
            with db() as conn:
                updates["id"] = candidate_id
                conn.execute(f"UPDATE candidates SET {set_clause} WHERE id = :id", updates)
                row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
            if not row:
                self.send_json({"error": "候选人不存在"}, 404)
                return
            self.send_json({"candidate": candidate_to_api(row)})
            return
        self.send_json({"error": "Not found"}, 404)

    def api_register_send_code(self) -> None:
        payload = self.read_json()
        email = str(payload.get("email") or "").strip().lower()
        if not EMAIL_RE.fullmatch(email):
            self.send_json({"error": "请输入有效邮箱地址。"}, 400)
            return
        try:
            verify_bot_challenge(payload)
        except RuntimeError as exc:
            self.send_json({"error": str(exc)}, 400)
            return
        ip_address = self.client_address[0] if self.client_address else ""
        sent_cutoff = (datetime.now(LOCAL_TZ) - timedelta(seconds=60)).isoformat(timespec="seconds")
        hour_cutoff = (datetime.now(LOCAL_TZ) - timedelta(hours=1)).isoformat(timespec="seconds")
        code = f"{random.randint(0, 999999):06d}"
        if os.getenv("VERCEL") and not kv_enabled():
            self.send_json({"error": "线上注册需要先配置 KV_REST_API_URL 和 KV_REST_API_TOKEN，否则账号无法持久保存。"}, 503)
            return
        if kv_enabled():
            if kv_get_user_by_email(email):
                self.send_json({"error": "该邮箱已注册，请直接登录。"}, 400)
                return
            verification = kv_get_json(kv_verification_key(email))
            if verification and str(verification.get("sent_at") or "") > sent_cutoff:
                self.send_json({"error": "验证码发送太频繁，请稍后再试。"}, 429)
                return
            email_rate_key = kv_rate_key("email", email)
            ip_rate_key = kv_rate_key("ip", ip_address)
            email_times = kv_recent_timestamps(email_rate_key, hour_cutoff)
            ip_times = kv_recent_timestamps(ip_rate_key, hour_cutoff)
            if len(email_times) + len(ip_times) >= 8:
                self.send_json({"error": "验证码请求次数过多，请一小时后再试。"}, 429)
                return
            sent_at = now_iso()
            expires_at = (datetime.now(LOCAL_TZ) + timedelta(minutes=10)).isoformat(timespec="seconds")
            kv_set_json(
                kv_verification_key(email),
                {
                    "email": email,
                    "code_hash": code_hash(email, code),
                    "ip_address": ip_address,
                    "expires_at": expires_at,
                    "sent_at": sent_at,
                    "created_at": sent_at,
                    "attempts": 0,
                },
                600,
            )
            kv_store_timestamps(email_rate_key, [*email_times, sent_at])
            kv_store_timestamps(ip_rate_key, [*ip_times, sent_at])
            try:
                send_verification_email(email, code)
            except RuntimeError as exc:
                self.send_json({"error": str(exc)}, 500)
                return
            except (smtplib.SMTPException, OSError) as exc:
                self.send_json({"error": f"验证码邮件发送失败：{exc}"}, 502)
                return
            self.send_json({"ok": True, "message": "验证码已发送，请在 10 分钟内完成注册。"})
            return
        with db() as conn:
            if conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
                self.send_json({"error": "该邮箱已注册，请直接登录。"}, 400)
                return
            recent = conn.execute(
                "SELECT COUNT(*) AS c FROM email_verifications WHERE email = ? AND sent_at > ?",
                (email, sent_cutoff),
            ).fetchone()["c"]
            hourly = conn.execute(
                "SELECT COUNT(*) AS c FROM email_verifications WHERE (email = ? OR ip_address = ?) AND sent_at > ?",
                (email, ip_address, hour_cutoff),
            ).fetchone()["c"]
            if recent:
                self.send_json({"error": "验证码发送太频繁，请稍后再试。"}, 429)
                return
            if hourly >= 8:
                self.send_json({"error": "验证码请求次数过多，请一小时后再试。"}, 429)
                return
            expires_at = (datetime.now(LOCAL_TZ) + timedelta(minutes=10)).isoformat(timespec="seconds")
            conn.execute(
                """
                INSERT INTO email_verifications (email, code_hash, ip_address, expires_at, sent_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (email, code_hash(email, code), ip_address, expires_at, now_iso(), now_iso()),
            )
        try:
            send_verification_email(email, code)
        except RuntimeError as exc:
            self.send_json({"error": str(exc)}, 500)
            return
        except (smtplib.SMTPException, OSError) as exc:
            self.send_json({"error": f"验证码邮件发送失败：{exc}"}, 502)
            return
        self.send_json({"ok": True, "message": "验证码已发送，请在 10 分钟内完成注册。"})

    def api_register_complete(self) -> None:
        payload = self.read_json()
        email = str(payload.get("email") or "").strip().lower()
        name = str(payload.get("name") or "").strip() or email.split("@", 1)[0]
        password = str(payload.get("password") or "")
        code = str(payload.get("code") or "").strip()
        if not EMAIL_RE.fullmatch(email):
            self.send_json({"error": "请输入有效邮箱地址。"}, 400)
            return
        if len(password) < 8:
            self.send_json({"error": "密码至少需要 8 位。"}, 400)
            return
        if not re.fullmatch(r"\d{6}", code):
            self.send_json({"error": "请输入 6 位邮箱验证码。"}, 400)
            return
        if os.getenv("VERCEL") and not kv_enabled():
            self.send_json({"error": "线上注册需要先配置 KV_REST_API_URL 和 KV_REST_API_TOKEN，否则账号无法持久保存。"}, 503)
            return
        if kv_enabled():
            if kv_get_user_by_email(email):
                self.send_json({"error": "该邮箱已注册，请直接登录。"}, 400)
                return
            verification = kv_get_json(kv_verification_key(email))
            if not verification or str(verification.get("expires_at") or "") < now_iso():
                self.send_json({"error": "验证码不存在或已过期，请重新获取。"}, 400)
                return
            attempts = int(verification.get("attempts") or 0)
            if attempts >= 5:
                self.send_json({"error": "验证码尝试次数过多，请重新获取。"}, 400)
                return
            if not hmac.compare_digest(str(verification.get("code_hash") or ""), code_hash(email, code)):
                verification["attempts"] = attempts + 1
                kv_set_json(kv_verification_key(email), verification, 600)
                self.send_json({"error": "验证码不正确。"}, 400)
                return
            kv_delete(kv_verification_key(email))
            now = now_iso()
            user_id = KV_USER_ID_OFFSET + kv_next_id("users")
            user = {
                "id": user_id,
                "email": email,
                "name": name,
                "role": "registered",
                "password_hash": pbkdf2_hash(password),
                "created_at": now,
                "email_verified": 1,
                "free_searches_remaining": 1,
            }
            kv_save_user(user)
            ensure_sqlite_user_for_kv_user(user)
            token = kv_create_session(user_id)
            self.send_json({"token": token, "user": user_to_api(user)}, 201)
            return
        with db() as conn:
            if conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
                self.send_json({"error": "该邮箱已注册，请直接登录。"}, 400)
                return
            verification = conn.execute(
                """
                SELECT * FROM email_verifications
                WHERE email = ? AND verified_at = ''
                ORDER BY id DESC LIMIT 1
                """,
                (email,),
            ).fetchone()
            if not verification or verification["expires_at"] < now_iso():
                self.send_json({"error": "验证码不存在或已过期，请重新获取。"}, 400)
                return
            if verification["attempts"] >= 5:
                self.send_json({"error": "验证码尝试次数过多，请重新获取。"}, 400)
                return
            if not hmac.compare_digest(verification["code_hash"], code_hash(email, code)):
                conn.execute("UPDATE email_verifications SET attempts = attempts + 1 WHERE id = ?", (verification["id"],))
                self.send_json({"error": "验证码不正确。"}, 400)
                return
            now = now_iso()
            conn.execute("UPDATE email_verifications SET verified_at = ? WHERE id = ?", (now, verification["id"]))
            cursor = conn.execute(
                """
                INSERT INTO users (email, name, role, password_hash, created_at, email_verified, free_searches_remaining)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (email, name, "registered", pbkdf2_hash(password), now, 1, 1),
            )
            token = uuid.uuid4().hex + uuid.uuid4().hex
            expires_at = (datetime.now(LOCAL_TZ) + timedelta(days=14)).isoformat(timespec="seconds")
            conn.execute(
                "INSERT INTO sessions (token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
                (token, cursor.lastrowid, expires_at, now),
            )
            user = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
        self.send_json({"token": token, "user": user_to_api(user)}, 201)

    def api_discover(self, project_id: int, user: dict[str, Any]) -> None:
        with db() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            self.send_json({"error": "项目不存在"}, 404)
            return
        if not has_search_quota(user):
            self.send_json({"error": "免费检索体验已使用完，请联系管理员开通更多次数。"}, 403)
            return
        project = project_to_api(row)
        profile = project["profile"]
        plan = build_search_plan(profile)
        config = get_config()
        max_pages = min(max(safe_int(config.get("max_web_pages"), 50), 1), 80)
        max_results = min(max(safe_int(config.get("tavily_max_results"), 8), 1), 10)
        if not (config.get("tavily_api_key") or os.getenv("TAVILY_API_KEY")):
            self.send_json(
                {
                    "ok": False,
                    "message": "还没有配置 Tavily API Key。已生成检索方案，你可以先手动导入公开链接或到设置中填写 Key。",
                    "plan": plan,
                    "candidates": [],
                }
            )
            return
        sources: list[dict[str, str]] = []
        errors: list[str] = []
        seen: set[str] = set()
        for query in plan["queries"]:
            if len(sources) >= max_pages:
                break
            try:
                results = tavily_search(query, config, max_results)
            except RuntimeError as exc:
                errors.append(f"{query}: {exc}")
                continue
            for result in results:
                url = result.get("url", "")
                if not url or url in seen:
                    continue
                seen.add(url)
                sources.append(
                    {
                        "url": url,
                        "title": result.get("title", ""),
                        "content": result.get("raw_content") or result.get("content") or "",
                        "source_type": "tavily_public_search",
                    }
                )
                if len(sources) >= max_pages:
                    break
        if sources:
            save_sources(project_id, sources)
        if is_metered_user(user) and not consume_free_search(user["id"]):
            self.send_json({"error": "免费检索体验已使用完，请联系管理员开通更多次数。"}, 403)
            return
        if not (config.get("deepseek_api_key") or os.getenv("DEEPSEEK_API_KEY")):
            self.send_json(
                {
                    "ok": True,
                    "message": "已完成公开网页检索并保存来源。还没有配置 DeepSeek API Key，因此暂不自动抽取候选人。",
                    "plan": plan,
                    "sources": len(sources),
                    "errors": errors,
                    "candidates": [],
                }
            )
            return
        corpus = "\n\n---\n\n".join(
            f"标题：{source.get('title','')}\n链接：{source.get('url','')}\n正文：{source.get('content','')[:5000]}" for source in sources[:20]
        )
        try:
            extracted = extract_candidates_with_ai(corpus, profile, config)
        except RuntimeError as exc:
            self.send_json(
                {
                    "ok": False,
                    "message": f"DeepSeek 抽取失败：{exc}",
                    "plan": plan,
                    "sources": len(sources),
                    "errors": errors,
                    "candidates": [],
                }
            )
            return
        if len(extracted) > safe_int(profile.get("max_candidates_before_narrowing"), 50):
            self.send_json(
                {
                    "ok": False,
                    "requires_narrowing": True,
                    "message": "候选人超过50人，建议先缩小平台、城市、经验或作品类型。",
                    "narrow_questions": plan["narrow_questions"],
                    "preview_count": len(extracted),
                }
            )
            return
        for item in extracted:
            item.setdefault("raw_evidence", "Tavily公开检索 + DeepSeek辅助抽取，需人工确认。")
        created = insert_candidates(project_id, extracted)
        audit(user["email"], "discover_candidates", {"project_id": project_id, "sources": len(sources), "created": len(created)})
        self.send_json({"ok": True, "plan": plan, "sources": len(sources), "errors": errors, "candidates": created})

    def api_import_links(self, project_id: int, user: dict[str, Any]) -> None:
        payload = self.read_json()
        links = [link for link in normalize_list(payload.get("links")) if link.startswith(("http://", "https://"))][:20]
        config = get_config()
        with db() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            self.send_json({"error": "项目不存在"}, 404)
            return
        project = project_to_api(row)
        sources: list[dict[str, str]] = []
        errors: list[str] = []
        for link in links:
            try:
                sources.append(fetch_public_page(link))
            except RuntimeError as exc:
                errors.append(f"{link}: {exc}")
        if sources:
            save_sources(project_id, sources)
        created: list[dict[str, Any]] = []
        if sources and (config.get("deepseek_api_key") or os.getenv("DEEPSEEK_API_KEY")):
            corpus = "\n\n---\n\n".join(f"标题：{s['title']}\n链接：{s['url']}\n正文：{s['content'][:6000]}" for s in sources)
            try:
                extracted = extract_candidates_with_ai(corpus, project["profile"], config)
                for item in extracted:
                    item["status"] = "待确认"
                    item.setdefault("raw_evidence", "手动输入公开链接 + DeepSeek辅助抽取，需人工确认。")
                created = insert_candidates(project_id, extracted)
            except RuntimeError as exc:
                errors.append(f"DeepSeek 抽取失败：{exc}")
        audit(user["email"], "import_links", {"project_id": project_id, "links": len(links), "created": len(created)})
        message = "链接已采集。"
        if not created and not (config.get("deepseek_api_key") or os.getenv("DEEPSEEK_API_KEY")):
            message += " 未配置 DeepSeek API Key，暂未自动生成候选人。"
        self.send_json({"ok": True, "message": message, "sources": len(sources), "errors": errors, "candidates": created})

    def api_import_file(self, project_id: int, user: dict[str, Any]) -> None:
        content_type = self.headers.get("Content-Type", "")
        parts = parse_multipart(content_type, self.read_body())
        file_part = parts.get("file")
        if not file_part:
            self.send_json({"error": "未收到文件"}, 400)
            return
        filename = file_part["filename"]
        suffix = Path(filename).suffix.lower()
        content = file_part["content"]
        created: list[dict[str, Any]] = []
        message = ""
        if suffix == ".csv":
            rows = parse_csv_bytes(content)
            created = insert_candidates(project_id, [map_row_to_candidate(row) for row in rows])
            message = f"已导入 CSV 候选人 {len(created)} 条。"
        elif suffix == ".xlsx":
            rows = parse_xlsx_bytes(content)
            created = insert_candidates(project_id, [map_row_to_candidate(row) for row in rows])
            message = f"已导入 Excel 候选人 {len(created)} 条。"
        elif suffix == ".pdf":
            text = extract_pdf_text(content)
            config = get_config()
            with db() as conn:
                row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            if text and row and (config.get("deepseek_api_key") or os.getenv("DEEPSEEK_API_KEY")):
                project = project_to_api(row)
                extracted = extract_candidates_with_ai(f"简历文件：{filename}\n{text[:20000]}", project["profile"], config)
                for item in extracted:
                    item["status"] = "待确认"
                    item.setdefault("raw_evidence", "企业授权简历PDF + DeepSeek辅助评分，需人工确认。")
                created = insert_candidates(project_id, extracted)
                message = f"已尝试解析 PDF 并生成 {len(created)} 条候选人。"
            else:
                message = "PDF 已收到，但当前未配置 DeepSeek 或文本不可读。建议先复制简历文本，或配置 Key 后重试。"
        else:
            self.send_json({"error": "仅支持 CSV、XLSX、PDF"}, 400)
            return
        audit(user["email"], "import_file", {"project_id": project_id, "filename": filename, "created": len(created)})
        self.send_json({"ok": True, "message": message, "created": created, "count": len(created)}, 201)


def main() -> None:
    init_db()
    port = 8787
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            port = safe_int(sys.argv[idx + 1], port)
    server = ThreadingHTTPServer(("127.0.0.1", port), TalentMapHandler)
    print(f"人才地图本地版已启动：http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")


class handler(TalentMapHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        init_db()
        super().__init__(*args, **kwargs)


if __name__ == "__main__":
    main()
