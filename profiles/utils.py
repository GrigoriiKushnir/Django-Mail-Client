import imaplib
import re
import base64
import dateparser
from smtplib import SMTP_SSL as SMTP
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from . import utf


def get_folders(username, password, imap):
    mail = imaplib.IMAP4_SSL(imap)
    mail.login(username, password)
    temp_folders = []
    folders = []
    utf_names = []
    names = {}
    for i in mail.list()[1]:
        l = i.decode().split(' "/" ')
        if 'noselect' not in l[0].lower():
            if '&' in l[1]:
                temp_folders.append(utf.decode(l[1].replace('"', '').encode()))
            else:
                temp_folders.append(l[1].replace('"', ''))
            utf_names.append(l[1])
    for f in temp_folders:
        if '[Gmail]/' in f:
            folders.append(f.replace('[Gmail]/', ''))
        else:
            folders.append(f)
    # print(folders)
    # print(utf_names)
    for f, u in zip(folders, utf_names):
        names[f] = u
    # print(names)
    # print(folders)
    # print(names)
    return folders, names


def get_mailbox(username, password, imap, folder):
    list_headers = list()
    mail = imaplib.IMAP4_SSL(imap)
    mail.login(username, password)
    print('get: ', folder)

    mail.select(folder)

    result, data = mail.search(None, "ALL")

    ids = data[0]
    id_list = ids.split()

    for email_id in reversed(id_list):
        if int(email_id.decode()) == int(id_list[-1].decode()) - 3:
            break
        prefix = '=?UTF-8?B?'
        suffix = '?='
        header = mail.fetch(email_id, '(BODY[HEADER.FIELDS (FROM SUBJECT DATE)])')
        data = header[1][0][1].decode()
        from_data = re.search('From.*', data)
        subject_data = re.search('Subject.*', data)
        date = re.search('Date.*', data).group(0)
        date = date[6:-1]
        c = 0
        for i in date:
            if i == '(':
                date = date[:c - 1]
            c += 1
        if '-0000' in date:
            date = date[:-5]
        date_datetime = dateparser.parse(date)
        date = date_datetime.strftime('%H:%M - %d %b %Y')
        from_data = from_data.group(0)
        subject_data = subject_data.group(0)
        if prefix in from_data:
            email = ""
            if '<' and '>' in from_data:
                email = re.search('<.*?>', from_data)
                email = email.group(0)
                from_data = re.search('=\?UTF-8.*?=', from_data).group(0)[len(prefix):len(from_data) - len(suffix)]
            try:
                from_data = base64.b64decode(from_data).decode()
            except Exception as exc:
                print(exc)
                pass
            print(from_data)
            if email:
                from_data = from_data + ' ' + email
        if prefix in subject_data:
            subject_data = re.search('=\?UTF-8.*?=', subject_data).group(0)[len(prefix):len(subject_data)]
            try:
                subject_data = base64.b64decode(subject_data).decode()
            except Exception as exc:
                print(exc)
                pass
        if '\r' in subject_data:
            subject_data = subject_data.replace('\r', '')
        if '\r' in from_data:
            from_data = from_data.replace('\r', '')
        from_data = from_data.replace('From: ', '')
        if '<' and '>' in from_data:
            start = from_data.index('<') + len('>')
            end = from_data.index('>', start)
            from_data = from_data[start:end]
        list_headers.append([from_data, subject_data[:100].replace('Subject: ', ''), date])
    return list_headers


def delete_mails(imap, username, password, boxes, folder):
    print('delete: ', folder)
    mail = imaplib.IMAP4_SSL(imap)
    mail.login(username, password)
    mail.list()
    mail.select(folder)
    result, data = mail.search(None, "ALL")
    ids = data[0]
    id_list = ids.split()
    for box in boxes:
        box = int(id_list[-1]) - int(box)
        try:
            mail.store(str(box), '+FLAGS', '\\Deleted')
            mail.expunge()
        except Exception as exc:
            print(type(box))
            print(exc)
    mail.close()


def validate_input(email, password, imap, smtp):
    try:
        conn = SMTP(smtp, timeout=5)
        try:
            conn.login(email, password)
        finally:
            conn.quit()
    except Exception as exc:
        if '535' in str(exc):
            return 'Wrong credentials!'
        if 'getaddrinfo failed' in str(exc):
            return 'Wrong SMTP server!'
        return "SMTP - " + str(exc)

    try:
        mail = imaplib.IMAP4_SSL(imap)
        try:
            mail.login(email, password)
        finally:
            mail.logout()
    except Exception as exc:
        if 'AUTHENTICATIONFAILED' in str(exc):
            return 'Wrong credentials!'
        if 'getaddrinfo failed' in str(exc):
            return 'Wrong IMAP server!'
        return "IMAP - " + str(exc)


def get_email_body(username, password, imap, email_id, folder):
    mail = imaplib.IMAP4_SSL(imap)
    mail.login(username, password)

    try:
        mail.select(folder)
        result, data = mail.search(None, "ALL")

        ids = data[0]
        id_list = ids.split()
        current_email_id = int(id_list[-1]) - int(email_id)
        result, data = mail.fetch(str(current_email_id), "(RFC822)")
        raw_email = data[0][1].decode("utf-8")
        return raw_email
    except Exception as ex:
        print(ex)


def send(smtp, username, password, to, subject, message, files=None):
    try:
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = username
        msg.attach(MIMEText(message))
        if len(files) != 0:
            for f in files:
                name = str(f)
                part = MIMEApplication(
                    f.read(),
                    name=name
                )
                part['Content-Disposition'] = 'attachment; filename="{}"'.format(name)
                msg.attach(part)
        conn = SMTP(smtp, timeout=5)
        try:
            conn.login(username, password)
            conn.sendmail(username, to, msg.as_string())
        finally:
            conn.quit()
    except Exception as exc:
        print("Error: ", exc)
        return exc
