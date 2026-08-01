import os, smtplib, traceback

host = os.getenv('EMAIL_HOST', 'smtp-relay.brevo.com')
port = int(os.getenv('EMAIL_PORT', '587'))
user = os.getenv('EMAIL_HOST_USER')
pwd = os.getenv('EMAIL_HOST_PASSWORD')
to = os.getenv('TEST_EMAIL_TARGET') or user or 'test@example.com'

print("HOST,PORT:", host, port)
print("USER provided:", bool(user))
try:
    server = smtplib.SMTP(host, port, timeout=30)
    server.set_debuglevel(1) # печатает SMTP‑диалог
    server.ehlo()
    server.starttls()
    server.ehlo()
    print("STARTTLS ok, attempting login...")
    if user and pwd:
        server.login(user, pwd)
        print("LOGIN ok")
    else:
        print("No SMTP credentials provided (EMAIL_HOST_USER / EMAIL_HOST_PASSWORD empty)")
    from_addr = user or 'test@example.com'
    msg = "Subject: Test\n\nThis is a test message from Railway."
    server.sendmail(from_addr, to, msg)
    server.quit()
    print("SEND OK")
except Exception:
    traceback.print_exc()