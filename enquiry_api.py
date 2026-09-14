"""Contact form enquiries: saved to SQLite first, then emailed to the team when SMTP is configured."""
import csv
import logging
import re
import smtplib
import sqlite3
import sys
import time
from collections import defaultdict, deque
from contextlib import closing
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from chat_api import check_origin, setting

router = APIRouter()
log = logging.getLogger('uvicorn.error')
DB_PATH = Path(__file__).with_name('enquiries.sqlite3')
EMAIL = re.compile(r'[^@\s]+@[^@\s]+\.[^@\s]+')
attempts = defaultdict(deque)


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
    db = sqlite3.connect(DB_PATH, timeout=5)
    db.execute('CREATE TABLE IF NOT EXISTS enquiries (id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, '
               'name TEXT NOT NULL, company TEXT NOT NULL, email TEXT NOT NULL, problem TEXT NOT NULL, '
               'emailed INTEGER NOT NULL DEFAULT 0)')
    return db


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
    with closing(connect()) as db, db:
        return db.execute('INSERT INTO enquiries (created_at, name, company, email, problem) VALUES (?,?,?,?,?)',
                          (datetime.now(timezone.utc).isoformat(timespec='seconds'),
                           body.name, body.company, body.email, body.problem)).lastrowid


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
            with closing(connect()) as db, db:
                db.execute('UPDATE enquiries SET emailed=1 WHERE id=?', (enquiry_id,))
    except (OSError, ValueError) as error:
        # The enquiry is already saved, so a mail problem never loses the lead.
        log.warning('Enquiry %s was saved, but the email notification failed: %s', enquiry_id, error)


@router.post('/api/enquiry')
def enquiry(body: Enquiry, request: Request, background: BackgroundTasks):
    check_origin(request)
    rate_limit(request)
    if not body.website:
        # Honeypot hits get the same response, so bots cannot tell they were discarded.
        background.add_task(deliver, save(body), body)
    return JSONResponse({'ok': True}, headers={'Cache-Control': 'no-store'})


if __name__ == '__main__':
    # Export saved enquiries for a spreadsheet: python enquiry_api.py [enquiries.csv]
    target = Path(sys.argv[1] if len(sys.argv) > 1 else 'enquiries.csv')
    with closing(connect()) as db:
        rows = db.execute('SELECT id, created_at, name, company, email, problem, emailed '
                          'FROM enquiries ORDER BY id').fetchall()
    with open(target, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['id', 'received_utc', 'name', 'company', 'email', 'problem', 'emailed'])
        # A leading = + - @ would run as a spreadsheet formula; visitor text must stay text.
        writer.writerows([[f"'{v}" if isinstance(v, str) and v and v[0] in '=+-@' else v for v in row]
                          for row in rows])
    print(f'Exported {len(rows)} enquiries to {target}')
