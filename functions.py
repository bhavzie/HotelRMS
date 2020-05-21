from flask import Flask, render_template, flash, request, session, url_for, session
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Mail, Message
from app import app

mail = Mail(app)

# Email Confirmations
def generateConfirmationToken(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def confirmToken(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except SignatureExpired:
        return 'The Token is expired'
    except:
        return False
    return email


def sendMail(subjectv, recipientsv, linkv, tokenv, bodyv, senderv):
    msg = Message(
        subject = subjectv,
        sender = app.config['MAIL_SENDER'],
        recipients = recipientsv.split())
    link = url_for(linkv, token=tokenv, _external=True)
    msg.body = bodyv + ' ' + link
    mail.send(msg)


# Mapping 1 => True, 0 => False and vice-versa
def getValC(value):
    if value == None:
        return 0
    else:
        return 1


def getValC2(value):
    if value == 1:
        return True
    else:
        return False
