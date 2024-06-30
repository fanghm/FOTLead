from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP
from typing import List
import re

def convertAsEmail(address: str):
    """Fix given address if it is email display name"""
    if address.find('@') != -1:
        return address

    matches = re.split(r'\(', address)
    org = matches[-1].strip()
    mail = "@nokia.com"
    if org.startswith("NSB"):
        mail = "@nokia-sbell.com"
    if org.startswith("EXT-NSB"):
        mail = ".ext@nokia-sbell.com"

    fullName = matches[0]
    if org.find('-') != -1:
        # Old format
        pieces = [x.strip() for x in fullName.split(',')]
        if len(pieces) != 2:
            print("Invalid address={}, parsed names={}".format(address, pieces))

        surname, givenName = pieces[:]
        surname = surname.replace(' ', '_').lower()
        pieces = re.split(r',|\.|\s', givenName)
        names = [n.lower() for n in pieces if n != '']
        if len(names) == 0:
            print("Invalid address={}, parsed names={}".format(address, names))

        prefix = '.'.join(names) + '.' + surname
    else:
        # New format
        pieces = [x.strip() for x in fullName.replace('.', ' ').split(' ')]
        pieces = [x.lower() for x in pieces if len(x) > 0]
        prefix = '.'.join(pieces)

    return prefix + mail

class Mailer(object):
    def __init__(self, sender):
        self._sender = sender
        self._smtp = SMTP(host=settings.EMAIL_HOST, port=settings.EMAIL_PORT)
        self._toAddresses = []
        self._ccAddresses = []

    def addAddresses(self, to: List[str] = [], cc: List[str] = []):
        self._toAddresses.extend([convertAsEmail(it) for it in to])
        self._ccAddresses.extend([convertAsEmail(it) for it in cc])

    def sendMessage(self, subject: str, content: str, html=''):
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self._sender
        message["To"] = ', '.join(self._toAddresses)
        message["Cc"] = ', '.join(self._ccAddresses)
        part1 = MIMEText(content, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)

        print("Mailer - Sending email to: ", self._toAddresses, " cc: ", self._ccAddresses, " subject: ", subject, " content: ", content)
        try:
            self._smtp.send_message(message)
        except smtplib.SMTPException as e:
            print(f"Failed to send mail: {e}")

    def __del__(self):
        self._smtp.quit()

def _get_mail_content(email_type, context):
    template_content = render_to_string(f'mail/{email_type}.html', context)
    subject_match = re.search('<!-- Subject: "(.*?)" -->', template_content)
    if subject_match:
        subject = subject_match.group(1)
    else:
        subject = f'[Action Required] {email_type} request for {context["fid"]}'

    html_content = re.sub('<!--.*?-->', '', template_content, flags=re.DOTALL).strip()
    text_content = strip_tags(html_content)  # for compatibility with email clients that don't support HTML

    return (subject, text_content, html_content)
    
def send_email(email_type, context):
    mailer = Mailer("Frank Fang<frank.fang@nokia-sbell.com>")   #TODO: replace as login user
    toAddress = ["frank.fang@nokia-sbell.com"]  #TODO: replace as context['apo_email']
    ccAddress = []  #TODO: cc APM
    mailer.addAddresses(toAddress, ccAddress)

    mailer.sendMessage(*_get_mail_content(email_type, context))