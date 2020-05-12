import os


class Config(object):
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or 'some-key-that-should-not-get-hacked'
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = 'koolbhavya.epic@gmail.com'
    MAIL_PASSWORD = 'lasxavunqnhxsjef'
    SECURITY_PASSWORD_SALT = 'mysaltvariable'
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'dbuser'
    MYSQL_PASSWORD = 'password'
    MYSQL_DB = 'testHotel'
    MYSQL_CURSORCLASS = 'DictCursor'