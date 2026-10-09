"""Email reminders for products that are expiring soon or already expired.

Configure with environment variables (never hard-code passwords):
    SMTP_HOST   (default smtp.gmail.com)
    SMTP_PORT   (default 465; use 587 if 465 is blocked)
    SMTP_USER   your email address
    SMTP_PASS   an app password
    REMINDER_TO who receives the reminder (default: SMTP_USER)

Run from the command line:
    python reminders.py            send the email
    python reminders.py --preview  only print the email (no login needed)
"""
import os
import smtplib
import sys
from email.message import EmailMessage


def build_message(products):
    """Return (subject, body) for the given products, or None if nothing needs attention."""
    soon = [p for p in products if p["status"] == "Expiring Soon"]
    expired = [p for p in products if p["status"] == "Expired"]
    if not soon and not expired:
        return None

    lines = []
    if soon:
        lines.append("Expiring soon:")
        lines += [f"  - {p['name']}: {p['days_left']} day(s) left (expires {p['expiry_date']})" for p in soon]
    if expired:
        lines.append("")
        lines.append("Already expired:")
        lines += [f"  - {p['name']} (expired {p['expiry_date']})" for p in expired]
    lines += ["", "Open ExpiryWise to see recommendations on how to use them."]

    subject = f"ExpiryWise: {len(soon)} expiring soon, {len(expired)} expired"
    return subject, "\n".join(lines)


def smtp_configured():
    return bool(os.environ.get("SMTP_USER") and os.environ.get("SMTP_PASS"))


def send_reminders(products):
    """Send one summary email. Returns True if an email was sent."""
    content = build_message(products)
    if content is None or not smtp_configured():
        return False
    subject, body = content

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ.get("REMINDER_TO", os.environ["SMTP_USER"])
    msg.set_content(body)

    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    if port == 465:
        server = smtplib.SMTP_SSL(host, port, timeout=20)
    else:
        server = smtplib.SMTP(host, port, timeout=20)
        server.starttls()
    with server:
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        server.send_message(msg)
    return True


if __name__ == "__main__":
    from app import create_table, get_products

    create_table()
    products = get_products()

    if "--preview" in sys.argv:
        content = build_message(products)
        if content is None:
            print("No products are expiring soon or expired.")
        else:
            print("Subject:", content[0])
            print()
            print(content[1])
    else:
        try:
            sent = send_reminders(products)
            print("Reminder email sent." if sent else "Nothing to send (or SMTP not configured).")
        except (smtplib.SMTPException, OSError) as error:
            print(f"Could not send email: {error}")