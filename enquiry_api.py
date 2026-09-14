"""Contact form enquiries: saved to PostgreSQL (DATABASE_URL) first, then emailed to the team when SMTP is configured."""
import csv
import logging
import re
import smtplib
import ssl
import sys
import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from datetime import timezone
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import pg8000.dbapi
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from chat_api import check_origin, setting

router = APIRouter()
log = logging.getLogger('uvicorn.error')
EMAIL = re.compile(r'[^@\s]+@[^@\s]+\.[^@\s]+')
UNAVAILABLE = 'We could not save your request right now. Please try again shortly.'
attempts = defaultdict(deque)

# Versioned, append-only schema changes: never edit an applied migration, add a new one.
MIGRATIONS = (
    (1, 'CREATE TABLE IF NOT EXISTS website_enquiries ('
        'id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, '
        'created_at TIMESTAMPTZ NOT NULL DEFAULT now(), '
        'name TEXT NOT NULL CHECK (char_length(name) <= 100), '
        'company TEXT NOT NULL CHECK (char_length(company) <= 120), '
        'email TEXT NOT NULL CHECK (char_length(email) <= 200), '
        'problem TEXT NOT NULL CHECK (char_length(problem) <= 2000), '
        'emailed BOOLEAN NOT NULL DEFAULT FALSE)'),
)
# Arbitrary constant that serialises migrations when several instances start at once.
SCHEMA_LOCK_ID = 7310442019
_schema_ready = False
_schema_lock = threading.Lock()


class DatabaseNotConfigured(RuntimeError):
    """DATABASE_URL is missing or unusable. Messages never include the URL itself."""


DB_ERRORS = (DatabaseNotConfigured, OSError, pg8000.dbapi.Error)


class Enquiry(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    company: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=200)
    problem: str = Field(min_length=1, max_length=2000)
    # Honeypot: hidden from people, usually filled in by spam bots.
    website: str = Field(default='', max_length=200)

    @field_validator('name', 'company', 'email', 'problem')
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError('This field is required.')
        return value.strip()

    @field_validator('name', 'company', 'email')
    @classmethod
    def single_line(cls, value):
        # Also stops visitor text from injecting email headers.
        if '\r' in value or '\n' in value:
            raise ValueError('Use a single line.')
        return value

    @field_validator('email')
    @classmethod
    def valid_email(cls, value):
        if not EMAIL.fullmatch(value):
            raise ValueError('Enter a valid email address.')
        return value


def connect():
    url = setting('DATABASE_URL')
    if not url:
        raise DatabaseNotConfigured('DATABASE_URL is not set')
    try:
        parts = urlsplit(url)
        port = parts.port or 5432
    except ValueError:
        raise DatabaseNotConfigured('DATABASE_URL is not a valid URL') from None
    if parts.scheme not in ('postgres', 'postgresql') or not parts.hostname or not parts.username:
        raise DatabaseNotConfigured('DATABASE_URL must look like postgresql://user:password@host:port/database')
    # libpq sslmode semantics: require encrypts without certificate checks; verify-ca/verify-full check it.
    mode = parse_qs(parts.query).get('sslmode', ['prefer'])[0]
    if mode in ('disable', 'allow', 'prefer'):
        context = None
    elif mode in ('require', 'verify-ca', 'verify-full'):
        context = ssl.create_default_context()
        context.check_hostname = mode == 'verify-full'
        if mode == 'require':
            context.verify_mode = ssl.CERT_NONE
    else:
        raise DatabaseNotConfigured(f'Unsupported sslmode {mode!r} in DATABASE_URL')
    return pg8000.dbapi.connect(
        user=unquote(parts.username), password=unquote(parts.password) if parts.password is not None else None,
        host=parts.hostname, port=port, database=unquote(parts.path.lstrip('/')) or None,
        ssl_context=context, timeout=10, application_name='optimizer-website')


@contextmanager
def transaction():
    db = connect()
    try:
        cursor = db.cursor()
        yield cursor
        db.commit()
    finally:
        try:
            db.close()
        except DB_ERRORS:
            pass


def ensure_schema():
    global _schema_ready
    if _schema_ready:
        return
    with _schema_lock:
        if _schema_ready:
            return
        with transaction() as cursor:
            cursor.execute('SELECT pg_advisory_xact_lock(%s)', (SCHEMA_LOCK_ID,))
            cursor.execute('CREATE TABLE IF NOT EXISTS website_schema_migrations ('
                           'version INTEGER PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())')
            cursor.execute('SELECT version FROM website_schema_migrations')
            applied = {row[0] for row in cursor.fetchall()}
            for version, statement in MIGRATIONS:
                if version not in applied:
                    cursor.execute(statement)
                    cursor.execute('INSERT INTO website_schema_migrations (version) VALUES (%s)', (version,))
        _schema_ready = True


def prepare_database():
    """Apply pending migrations at startup. Never fatal: the website keeps serving and enquiries retry."""
    if not setting('DATABASE_URL'):
        log.warning('DATABASE_URL is not set: contact form enquiries will be refused until it is configured.')
        return
    try:
        ensure_schema()
    except DB_ERRORS as error:
        log.error('Enquiry database is not ready (%s: %s). It will be retried on the next enquiry.',
                  type(error).__name__, error)


def rate_limit(request: Request):
    now = time.monotonic()
    for key in list(attempts):
        if not attempts[key] or attempts[key][-1] <= now - 600:
            del attempts[key]
    recent = attempts[request.client.host if request.client else 'unknown']
    while recent and recent[0] <= now - 600:
        recent.popleft()
    if len(recent) >= 5:
        raise HTTPException(429, 'Too many requests. Please try again in ten minutes.')
    recent.append(now)


def save(body: Enquiry):
    ensure_schema()
    with transaction() as cursor:
        cursor.execute('INSERT INTO website_enquiries (name, company, email, problem) '
                       'VALUES (%s, %s, %s, %s) RETURNING id',
                       (body.name, body.company, body.email, body.problem))
        return cursor.fetchone()[0]


def notify(enquiry_id: int, body: Enquiry):
    host, to = setting('SMTP_HOST'), setting('ENQUIRY_TO_EMAIL')
    if not (host and to):
        return False
    message = EmailMessage()
    message['Subject'] = f'New website enquiry #{enquiry_id}: {body.company}'
    message['From'] = setting('SMTP_FROM') or setting('SMTP_USER') or to
    message['To'] = to
    message['Reply-To'] = body.email
    message.set_content(f'Name: {body.name}\nCompany: {body.company}\nEmail: {body.email}\n\n'
                        f'What they would like to improve:\n{body.problem}\n')
    port = int(setting('SMTP_PORT', '587'))
    # Port 465 is implicit TLS; other ports upgrade with STARTTLS.
    with (smtplib.SMTP_SSL if port == 465 else smtplib.SMTP)(host, port, timeout=15) as smtp:
        if port != 465:
            smtp.starttls()
        if setting('SMTP_USER'):
            smtp.login(setting('SMTP_USER'), setting('SMTP_PASSWORD', ''))
        smtp.send_message(message)
    return True


def deliver(enquiry_id: int, body: Enquiry):
    try:
        if notify(enquiry_id, body):
            with transaction() as cursor:
                cursor.execute('UPDATE website_enquiries SET emailed = TRUE WHERE id = %s', (enquiry_id,))
    except (ValueError, *DB_ERRORS) as error:
        # The enquiry is already saved, so a mail problem never loses the lead.
        log.warning('Enquiry %s was saved, but the email notification failed: %s', enquiry_id, error)


@router.post('/api/enquiry')
def enquiry(body: Enquiry, request: Request, background: BackgroundTasks):
    check_origin(request)
    rate_limit(request)
    if not body.website:
        # Honeypot hits get the same response, so bots cannot tell they were discarded.
        try:
            enquiry_id = save(body)
        except DB_ERRORS as error:
            log.error('Enquiry was not saved (%s: %s).', type(error).__name__, error)
            raise HTTPException(503, UNAVAILABLE) from None
        background.add_task(deliver, enquiry_id, body)
    return JSONResponse({'ok': True}, headers={'Cache-Control': 'no-store'})


if __name__ == '__main__':
    # Export saved enquiries for a spreadsheet: python enquiry_api.py [enquiries.csv]
    target = Path(sys.argv[1] if len(sys.argv) > 1 else 'enquiries.csv')
    ensure_schema()
    with transaction() as cursor:
        cursor.execute('SELECT id, created_at, name, company, email, problem, emailed '
                       'FROM website_enquiries ORDER BY id')
        rows = cursor.fetchall()
    with open(target, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['id', 'received_utc', 'name', 'company', 'email', 'problem', 'emailed'])
        for id_, created_at, *fields, emailed in rows:
            # A leading = + - @ would run as a spreadsheet formula; visitor text must stay text.
            fields = [f"'{v}" if v and v[0] in '=+-@' else v for v in fields]
            writer.writerow([id_, created_at.astimezone(timezone.utc).isoformat(timespec='seconds'), *fields, emailed])
    print(f'Exported {len(rows)} enquiries to {target}')
