from flask import Flask, render_template, flash, request, session, url_for, session, jsonify, redirect, Response
from config import Config
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from functools import wraps
import smtplib
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from flask_mysqldb import MySQL
import datetime
import math
import json
import csv
from xlsxwriter.workbook import Workbook
from passlib.hash import sha256_crypt

app = Flask(__name__)
app.config.from_object(Config)

mail = Mail(app)
mysql = MySQL(app)


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

def sendMail(subjectv, recipientsv, linkv, tokenv, bodyv):
    msg = Message(
        subject = subjectv,
        sender = app.config['MAIL_SENDER'],
        recipients = recipientsv.split(),
        bcc = ['trompar.sales@gmail.com']
        )
    link = url_for(linkv, token=tokenv, _external=True)
    msg.body = bodyv + ' ' + link
    mail.send(msg)

def sendMailQ(subjectv, recipientsv, linkv, tokenv, bodyv):
    msg = Message(
        subject = subjectv,
        sender = app.config['MAIL_SENDER'],
        recipients = recipientsv.split(),
        bcc = ['trompar.sales@gmail.com']
        )
    link = url_for(linkv, id=tokenv, _external=True)
    msg.body = bodyv +  'Press on the link  ' + link + '  to view & accept your rate quote \n\n Rooms & Rate are subject to availability at the time of booking. \n \n Thanks, \n The Row Hotel | 408-111-2255 \n Do Not Reply to this email'
    msg.html = render_template('/mails/quote.html', link = link)
    mail.send(msg)

def sendMail2(subjectv, recipientsv, bodyv):    
    # Confirm Email
    msg = Message(
        subject = subjectv,
        sender = app.config['MAIL_SENDER'],
        recipients = recipientsv.split(),
        bcc = ['trompar.sales@gmail.com']
        )

    msg.body = bodyv
    mail.send(msg)

def sendMailA(subjectv, recipientsv, bodyv, attachv):
    msg = Message(
        subject = subjectv,
        sender = app.config['MAIL_SENDER'],
        recipients = recipientsv.split(),
        bcc = ['trompar.sales@gmail.com']
        )

    msg.body = bodyv
    msg.attach(attachv)
    mail.send(msg)
    


# DB Queries
def dbQueryInsert(table, myDict):
    placeholders = ', '.join(['%s'] * len(myDict))
    columns = ', '.join(myDict.keys())
    values = myDict.values()
    sql = 'Insert into %s ( %s ) VALUES ( %s )' %(table, columns, placeholders)
    cursor = mysql.connection.cursor()
    cursor.execute(sql, myDict.values())

    mysql.connection.commit()
    cursor.close()

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

def procArr(value):
    if value is None:
        return ''
    return ' '.join(value)

def procArr2(value):
    string = ''
    if value != None:
        if value.count('cq') > 0:
            string += 'Cheque, '
        if value.count('bt') > 0:
            string += ' Bank Transfer, '
        if value.count('cc') > 0:
            string += 'Credit Card, '
    
    try:
        string = string[:string.rindex(',')]
    except:
        string = string
    return string

def checkOverride(value):
    pre = value.split('(')
    if len(pre) == 1:
        return False
    else:
        try:
            val = float(pre[0])
            val2 = float(pre[1].split(" : ")[1].split('[')[0])
            if (val != val2):
                return True
            else:
                return False
        except:
            return False

def alterTables():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables  where TABLE_SCHEMA="testHotel";')
    data = cursor.fetchall()
    for d in data:
        table = d['table_name']
        if table != 'mapHotelId':
            query = 'UPDATE {} set hotelId = 1 where 1 = 1'.format(table)
            cursor.execute(query)
    mysql.connection.commit()
    cursor.close()

# Decorators
# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized, Please Login", 'danger')
            return render_template('login.html', title='Login')
    return wrap

# Global Status Values
statusval1 = 'NEW'
statusval2 = 'QUOTED'
statusval3 = 'NEGOTIATED'
statusval4 = 'ACCEPTED'
statusval5 = 'CUSTOMER DECLINED'
statusval6 = 'DELETED'
statusval7 = 'SENT FOR REVIEW'
statusval8 = 'HOTEL DECLINED'
statusval9 = 'EXPIRED'
statusval10 = 'CONFIRMED'
statusval11 = 'NOT CONFIRMED'
url = app.config['SERVER_URL']


@app.errorhandler(404)
def error_404(e):
    return render_template('error/404.html'), 404

@app.errorhandler(403)
def error_403(e):
    return render_template('error/403.html'), 403

@app.errorhandler(500)
def error_500(e):
    return render_template('error/500.html'), 500


@app.route('/confirm_email/<token>', methods=['GET', 'POST'])
def confirm_email(token):
    email = confirmToken(token)

    if (email == False):
        flash('Your email could not be verified', 'danger')
        return render_template('login.html', title = 'Login')
    else:
        # DB ADD the Verified Email Flag
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users where email = %s', [email])
        data = cursor.fetchall()
        data = data[0]

        if data['userType'] == 'customer':
            cursor.execute('UPDATE customers SET email_verified = 1 WHERE email = %s', [email])
        elif data['userType'] == 'IATA':
            cursor.execute('UPDATE iataUsers SET email_verified = 1 WHERE email = %s', [email])
        elif data['userType'] == 'hoteluser':
            cursor.execute('UPDATE hotelUsers SET email_verified = 1 WHERE email = %s', [email])
        elif data['userType'] == 'developer':
            cursor.execute('UPDATE developers SET email_verified = 1 WHERE email = %s', [email])

        mysql.connection.commit()
        cursor.close()
        
        flash('Your email has been successfully verified', 'success')
        return render_template('login.html', title = 'Login')

@app.route('/home', methods=['GET', 'POST'])
def home():
    try:
        if session['logged_in'] == True:
            return render_template('index2.html', title = 'Home')
    except:
        return render_template('login.html', title = 'Login')

@app.route('/signIn', methods=['GET', 'POST'])
def index():
    return render_template('login.html', title = 'Login')

@app.route('/iataRegistration', methods=['GET', 'POST'])
@is_logged_in
def iatar():
    return render_template('users/registerIata.html', title = 'Register')


@app.route('/customerRegistrationR', methods=['GET', 'POST'])
@is_logged_in
def customerr():
    return render_template('users/rcustomer.html', title='Register')

@app.route('/customerRegistrationI', methods=['GET', 'POST'])
@is_logged_in
def customerI():
    return render_template('users/icustomer.html', title='Register')


@app.route('/customerRegistrationT', methods=['GET', 'POST'])
@is_logged_in
def customerT():
    return render_template('users/tcustomer.html', title='Register')


@app.route('/customerRegistrationC', methods=['GET', 'POST'])
@is_logged_in
def customerC():
    return render_template('users/ccustomer.html', title='Register')


@app.route('/registerI', methods = ['GET', 'POST'])
@is_logged_in
def registerI():
    if request.method == 'POST':
        fullName = request.form['fullName']
        firstName = fullName.split(' ')[0]
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        country = request.form['country']
        agencyName = request.form['agencyName']
        iataCode = request.form['iataCode']
        password = sha256_crypt.hash(password)
        hotelId = session.get('hotelId')

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * From users where email = %s', [email])
        data = cursor.fetchall()

        if len(data) == 0:
            token = generateConfirmationToken(email)
            sendMail(
                subjectv='Confirm Email',
                recipientsv=email,
                linkv='confirm_email',
                tokenv=token,
                bodyv='Confirm your email by clicking this link ',
            )
            cursor.execute('INSERT INTO users(firstName, email, password, userType, userSubType, hotelId) Values(%s, %s, %s, %s, %s, %s)',
                           (firstName, email, password, 'IATA', '', hotelId))

            cursor.execute('INSERT INTO iataUsers(fullName, email, country, phone, password, iataCode, agencyName, hotelId) Values(%s, %s, %s, %s, %s, %s, %s, %s)',
                           (fullName, email, country, phone, password, iataCode, agencyName, hotelId))

            mysql.connection.commit()
            cursor.close()
        else:
            flash('Email Already Registered', 'danger')
            return render_template('users/rcustomer.html', title="Register")

        flash('You are now registered and can log in', 'success')
        return redirect(url_for("home2"))


@app.route('/registerR', methods = ['GET', 'POST'])
@is_logged_in
def registerR():
    if request.method == 'POST':

        fullName = request.form['fullName']
        firstName = fullName.split(' ')[0]
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        country = request.form['country']
        password = sha256_crypt.hash(password)
        hotelId = session.get('hotelId')

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * From users where email = %s', [email])
        data = cursor.fetchall()

        if len(data) == 0:
            token = generateConfirmationToken(email)
            sendMail(
                subjectv='Confirm Email',
                recipientsv=email,
                linkv='confirm_email',
                tokenv=token,
                bodyv='Confirm your email by clicking this link ',
            )
            cursor.execute('INSERT INTO users(firstName, email, password, userType, userSubType, hotelId) Values(%s, %s, %s, %s, %s, %s)',
                           (firstName, email, password, 'customer', 'retail', hotelId))

            cursor.execute('INSERT INTO customers(fullName, email, country, phone, password, userType, hotelId) Values(%s, %s, %s, %s, %s, %s, %s)', (fullName, email, country, phone, password, 'retail', hotelId))
            
            mysql.connection.commit()
            cursor.close()
        else:
            flash('Email Already Registered', 'danger')
            return render_template('users/rcustomer.html', title="Register")

        flash('You are now registered and can log in', 'success')
        return redirect(url_for("home2"))

@app.route('/registerC', methods=['GET', 'POST'])
@is_logged_in
def registerC():
    if request.method == 'POST':
        fullName = request.form['fullName']
        firstName = fullName.split(' ')[0]
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        country = request.form['country']
        organizationName = request.form['organizationName']
        password = sha256_crypt.hash(password)
        hotelId = session.get('hotelId')
            

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * From users where email = %s', [email])
        data = cursor.fetchall()

        if len(data) == 0:
            token = generateConfirmationToken(email)
            sendMail(
                subjectv='Confirm Email',
                recipientsv=email,
                linkv='confirm_email',
                tokenv=token,
                bodyv='Confirm your email by clicking this link ',
            )
            cursor.execute('INSERT INTO users(firstName, email, password, userType, userSubType, hotelId) Values(%s, %s, %s, %s, %s, %s)',
                           (firstName, email, password, 'customer', 'corporate', hotelId))

            cursor.execute('INSERT INTO customers(fullName, email, country, phone, password, userType, organizationName, hotelId) Values(%s, %s, %s, %s, %s, %s, %s, %s)',
                           (fullName, email, country, phone, password, 'corporate', organizationName, hotelId))

            mysql.connection.commit()
            cursor.close()
        else:
            flash('Email Already Registered', 'danger')
            return render_template('users/rcustomer.html', title="Register")

        flash('You are now registered and can log in', 'success')
        return redirect(url_for("home2"))

@app.route('/registerT', methods=['GET', 'POST'])
@is_logged_in
def registerT():
    if request.method == 'POST':
        fullName = request.form['fullName']
        firstName = fullName.split(' ')[0]
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        country = request.form['country']
        agencyName = request.form['agencyName']
        
        password = sha256_crypt.hash(password)
        hotelId = session.get('hotelId')

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * From users where email = %s', [email])
        data = cursor.fetchall()

        if len(data) == 0:
            token = generateConfirmationToken(email)
            sendMail(
                subjectv='Confirm Email',
                recipientsv=email,
                linkv='confirm_email',
                tokenv=token,
                bodyv='Confirm your email by clicking this link ',
            )
            cursor.execute('INSERT INTO users(firstName, email, password, userType, userSubType, hotelId) Values(%s, %s, %s, %s, %s, %s)',
                           (firstName, email, password, 'customer', 'tour', hotelId))

            cursor.execute('INSERT INTO customers(fullName, email, country, phone, password, userType, agencyName, hotelId) Values(%s, %s, %s, %s, %s, %s, %s, %s)',
                           (fullName, email, country, phone, password, 'tour', agencyName, hotelId))

            mysql.connection.commit()
            cursor.close()
        else:
            flash('Email Already Registered', 'danger')
            return render_template('users/rcustomer.html', title="Register")

        flash('You are now registered and can log in', 'success')
        return redirect(url_for("home2"))


@app.route('/login', methods=['GET', 'POST'])
def login():
    #Dropdown for developers
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * From users where email = %s', [email])
        data = cursor.fetchall()

        if len(data) == 0:
            error = 'Email not registered'
            return render_template('login.html', error = error)
        else:
            data = data[0]
            password_match = data['password']
            if (sha256_crypt.verify(password, password_match)):
                session['logged_in'] = True
                session['email'] = email
                session['userType'] = data['userType']
                session['firstName'] = data['firstName']
                session['hotelId'] = data['hotelId']
                hotelId = data['hotelId']

                ''' 
                    * userType:-
                    * For Others = 'customer'
                    * For IATA = 'iatauser'
                    * For Hotel = 'hoteluser' & 
                        userSubType = 
                            1) hotelAdmin
                            2) revenue
                            3) reservation

                    * For developer = 'developer'
                '''
                
                menuParams = {}
                
                if session['userType'] == 'hoteluser':
                    menuParams = {
                    'request': True,
                    'requestCreate': True,
                    'requestManage': True,
                    'requestCreateAdhoc': True,
                    'requestCreateSeries': True,
                    'strategy': True,
                    'strategyRooms': True,
                    'strategyRate': True,
                    'strategyDiscount': True,
                    'strategyDiscountCreate': True,
                    'strategyDiscountMap': True,
                    'strategyForecast': True,
                    'settings': True,
                    'settingsRequest': True,
                    'settingsRequestCreate': True,
                    'settingsRequestMap': True,
                    'settingsContact': True,
                    'settingsContactCreate': True,
                    'settingsContactMap': True,
                    'settingsTime': True,
                    'settingsTimeCreate': True,
                    'settingsTimeMap': True,
                    'settingsNegotiation': True,
                    'settingsAutopilot': True,
                    'users': True,
                    'usersHotel': True,
                    'usersHotelAdd': True,
                    'usersHotelEdit': True,
                    'usersCustomer': True,
                    'usersCustomerAdd': True,
                    'usersCustomerEdit': True,
                    'usersCustomerUpload': True,
                    'analytics': True,
                    'analyticsDashboard': True,
                    'analyticsBehavior': True,
                    'analyticsPerformance': True,
                    'analyticsRevenue': True,
                    'analyticsTracking': True,
                    'help': True,
                    'helpUserGuide': True,
                    'helpFaq': True,
                    'helpTicketing': True,
                    'analyticsStdReport': True,
                    'strategyEvaluation': True,
                    'strategyAncillary': True,
                    'settingBusinessReward': True,
                    }
                    session['userSubType'] = data['userSubType']
                    userSubType = data['userSubType']
                    cursor.execute(
                        "SELECT * FROM hotelMenuAccess where userType = %s && hotelId = %s", [userSubType, hotelId])
                    d = cursor.fetchall()
                    cursor.execute("SELECT * FROM hotelUsers where email = %s && hotelId = %s", [email, hotelId])
                    dog = cursor.fetchall()
                    dog = dog[0]
                    if (dog['active'] == 0):
                        session.clear()
                        flash('You are de-activated. Kindly contact Super Admin!', 'danger')
                        return render_template('login.html', title = 'Login')
                    if (dog['email_verified'] == 0 or dog['email_verified'] == None):
                        session.clear()
                        flash('Please verify your email address before you login', 'danger')
                        return render_template('login.html')

                    if len(d) != 0:
                        d = d[0]
                        menuParams['request'] = getValC2(d['request'])
                        menuParams['requestCreate'] = getValC2(d['requestCreate'])
                        menuParams['requestManage'] = getValC2(d['requestManage'])
                        menuParams['requestCreateAdhoc'] = getValC2(
                            d['requestCreateAdhoc'])
                        menuParams['requestCreateSeries'] = getValC2(d['requestCreateSeries'])
                        menuParams['strategy'] = getValC2(d['strategy'])
                        menuParams['strategyRooms'] = getValC2(d['strategyRooms'])
                        menuParams['strategyRate'] = getValC2(d['strategyRate'])
                        menuParams['strategyDiscount'] = getValC2(d['strategyDiscount'])
                        menuParams['strategyDiscountCreate'] = getValC2(d['strategyDiscountCreate'])
                        menuParams['strategyDiscountMap'] = getValC2(d['strategyDiscountMap'])
                        menuParams['strategyForecast'] = getValC2(d['strategyForecast'])
                        menuParams['settingsRequest'] = getValC2(d['settingsRequest'])
                        menuParams['settingsRequestCreate'] = getValC2(d['settingsRequestCreate'])
                        menuParams['settingsRequestMap'] = getValC2(d['settingsRequestMap'])
                        menuParams['settingsContactCreate'] = getValC2(
                        d['settingsContactCreate'])
                        menuParams['settingsContactMap'] = getValC2(
                        d['settingsContactMap'])
                        menuParams['settingsTime'] = getValC2(
                        d['settingsTime'])
                        menuParams['settingsTimeCreate'] = getValC2(
                        d['settingsTimeCreate'])
                        menuParams['settingsTimeMap'] = getValC2(
                        d['settingsTimeMap'])
                        menuParams['settingsNegotiation'] = getValC2(
                        d['settingsNegotiation'])
                        menuParams['settingsAutopilot'] = getValC2(
                        d['settingsAutopilot'])
                        menuParams['usersHotel'] = getValC2(
                        d['usersHotel'])
                        menuParams['usersHotelAdd'] = getValC2(
                        d['usersHotelAdd'])
                        menuParams['usersCustomer'] = getValC2(
                        d['usersCustomer'])
                        menuParams['usersCustomerAdd'] = getValC2(
                        d['usersCustomerAdd'])
                        menuParams['usersCustomerEdit'] = getValC2(
                            d['usersCustomerEdit'])
                        menuParams['usersCustomerUpload'] = getValC2(
                        d['usersCustomerUpload'])
                        menuParams['analytics'] = getValC2(
                        d['analytics'])
                        menuParams['analyticsDashboard'] = getValC2(
                        d['analyticsDashboard'])
                        menuParams['analyticsBehavior'] = getValC2(
                        d['analyticsBehavior'])
                        menuParams['analyticsPerformance'] = getValC2(
                        d['analyticsPerformance'])
                        menuParams['analyticsRevenue'] = getValC2(
                        d['analyticsRevenue'])
                        menuParams['analyticsTracking'] = getValC2(
                        d['analyticsTracking'])
                        menuParams['help'] = getValC2(
                        d['help'])
                        menuParams['helpUserGuide'] = getValC2(
                        d['helpUserGuide'])
                        menuParams['helpFaq'] = getValC2(
                            d['helpFaq'])
                        menuParams['helpTicketing'] = getValC2(
                            d['helpTicketing'])
                        menuParams['settings'] = getValC2(
                            d['settings'])
                        menuParams['settingsContact'] = getValC2(
                            d['settingsContact'])
                        menuParams['users'] = getValC2(
                                d['users'])
                        menuParams['usersHotelEdit'] = getValC2(
                                d['usersHotelEdit'])
                        menuParams['analyticsStdReport'] = getValC2(d['analyticsStdReport'])        
                        menuParams['strategyEvaluation'] = getValC2(d['strategyEvaluation'])   
                        menuParams['settingBusinessReward'] = getValC2(d['settingBusinessReward'])
                        menuParams['strategyAncillary'] = getValC2(d['strategyAncillary'])    
                    session['menuParams'] = menuParams


                elif session['userType'] == 'iata':
                    cursor.execute(
                        "SELECT * FROM iataUsers where email = %s && hotelId = %s", [email, hotelId])
                    dog = cursor.fetchall()
                    dog = dog[0]
                    if (dog['email_verified'] == 0 or dog['email_verified'] == None):
                        session.clear()
                        flash('Please verify your email address before you login', 'danger')
                        return render_template('login.html')
                    
                    if (dog['active'] == 0):
                        session.clear()
                        flash(
                            'You are de-activated. Kindly contact Super Admin!', 'danger')
                        return render_template('login.html', title='Login')
                    menuParams = {
                    'request': True,
                    'requestCreate': True,
                    'requestManage': True,
                    'requestCreateAdhoc': True,
                    'requestCreateSeries': True,
                    'users': True,
                    'usersAdd': True,
                    'usersEdit': True,
                    'analytics': True,
                    'analyticsDashboard': True,
                    'analyticsRequest': True,
                    'analyticsPerformance': True,
                    'analyticsTracking': True,
                    'help': True,
                    'helpUserGuide': True,
                    'helpFaq': True,
                    'helpTicketing': True
                    }
                    cursor.execute("SELECT * FROM iataMenuAccess where hotelId = %s", [hotelId])
                    d = cursor.fetchall()
                    if len(d) != 0:
                        d = d[0]
                        menuParams['request'] = getValC2(d['request'])
                        menuParams['requestCreate'] = getValC2(
                            d['requestCreate'])
                        menuParams['requestManage'] = getValC2(
                            d['requestManage'])
                        menuParams['users'] = getValC2(d['users'])
                        menuParams['usersAdd'] = getValC2(d['usersAdd'])
                        menuParams['usersEdit'] = getValC2(d['usersEdit'])
                        menuParams['analytics'] = getValC2(d['analytics'])
                        menuParams['analyticsDashboard'] = getValC2(d['analyticsDashboard'])
                        menuParams['analyticsRequest'] = getValC2(d['analyticsRequest'])
                        menuParams['analyticsTracking'] = getValC2(d['analyticsTracking'])
                        menuParams['analyticsPerformance'] = getValC2(d['analyticsPerformance'])
                        
                        menuParams['requestCreateAdhoc'] = getValC2(d['requestCreateAdhoc'])
                        menuParams['requestCreateSeries'] = getValC2(d['requestCreateSeries'])
                        menuParams['help'] = getValC2(
                        d['help'])
                        menuParams['helpUserGuide'] = getValC2(
                            d['helpUserGuide'])
                        menuParams['helpFaq'] = getValC2(
                            d['helpFaq'])
                        menuParams['helpTicketing'] = getValC2(
                        d['helpTicketing'])
                    
                    session['menuParams'] = menuParams

                elif session['userType'] == 'customer':
                    cursor.execute("SELECT * FROM customers where email = %s && hotelId = %s", [email, hotelId])
                    dog = cursor.fetchall()
                    dog = dog[0]
                    if (dog['email_verified'] == 0 or dog['email_verified'] == None):
                        session.clear()
                        flash('Please verify your email address before you login', 'danger')
                        return render_template('login.html')

                    if (dog['active'] == 0):
                        session.clear()
                        flash('You are de-activated. Kindly contact Super Admin!', 'danger')
                        return render_template('login.html', title = 'Login')
                    menuParams = {
                        'request': True,
                        'requestCreate': True,
                        'requestManage': True,
                        'requestCreateAdhoc': True,
                        'requestCreateSeries': True,
                        'analytics': True,
                        'analyticsDashboard': True,
                        'analyticsRequest': True,
                        'analyticsPerformance': True,
                        'analyticsTracking': True,
                        'help': True,
                        'helpUserGuide': True,
                        'helpFaq': True,
                        'helpTicketing': True
                    }
                    cursor.execute("SELECT * FROM customerMenuAccess where hotelId = %s", [hotelid])
                    d = cursor.fetchall()
                    if len(d) != 0:
                        d = d[0]
                        menuParams['request'] = getValC2(d['request'])
                        menuParams['requestCreate'] = getValC2(
                            d['requestCreate'])
                        menuParams['requestManage'] = getValC2(
                            d['requestManage'])
                        menuParams['requestCreateAdhoc'] = getValC2(
                            d['requestCreateAdhoc'])
                        menuParams['requestCreateSeries'] = getValC2(
                            d['requestCreateSeries'])
                        menuParams['analytics'] = getValC2(d['analytics'])
                        menuParams['analyticsDashboard'] = getValC2(
                            d['analyticsDashboard'])
                        menuParams['analyticsRequest'] = getValC2(d['analyticsRequest'])
                        menuParams['analyticsPerformance'] = getValC2(d['analyticsPerformance'])
                        menuParams['analyticsTracking'] = getValC2(d['analyticsTracking'])
                        menuParams['help'] = getValC2(
                            d['help'])
                        menuParams['helpUserGuide'] = getValC2(
                            d['helpUserGuide'])
                        menuParams['helpFaq'] = getValC2(
                            d['helpFaq'])
                        menuParams['helpTicketing'] = getValC2(
                            d['helpTicketing'])

                    session['menuParams'] = menuParams

                elif session['userType'] == 'developer':
                    cursor.execute("SELECT * FROM developers where email = %s", [email])
                    dog = cursor.fetchall()
                    dog = dog[0]
                    if (dog['email_verified'] == 0 or dog['email_verified'] == None):
                        session.clear()
                        flash('Please verify your email address before you login', 'danger')
                        return render_template('login.html')
                    if (dog['active'] == 0):
                        session.clear()
                        flash('You are de-activated. Kindly contact Super Admin!', 'danger')
                        return render_template('login.html', title = 'Login')
                    
                    cursor.execute('SELECT hotelName From mapHotelId')
                    hotelName = cursor.fetchall()
                    return render_template('developer/hotelDropDown.html', hotelName = hotelName)

                flash('You are now logged in', 'success')
                return redirect(url_for('home2'))
            else:
                error = 'Passwords did not match'
                return render_template('login.html', error = error)

    return render_template('login.html', title = 'Login')

@app.route('/dropDownHotelSubmit', methods = ['GET', 'POST'])
@is_logged_in
def dropDownHotelSubmit():
    hotelName = request.form['hotelName']
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT hotelId from mapHotelId where hotelName = %s', [hotelName])
    hotelId = cursor.fetchall()
    hotelId = hotelId[0]['hotelId']
    session['hotelId'] = hotelId
    flash('You are now logged in', 'success')
    return redirect(url_for('home2'))

@app.route('/switchHotel', methods = ['GET', "POST"])
@is_logged_in
def switchHotel():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT hotelName From mapHotelId')
    hotelName = cursor.fetchall()
    selected = session.get('hotelId')
    cursor.execute('SELECT hotelName from mapHotelId where hotelId = %s', [selected])
    selected = cursor.fetchall()
    selected = selected[0]['hotelName']
    return render_template('developer/hotelDropDown.html', hotelName = hotelName, selected = selected)

@app.route('/forgotpassword', methods = ['GET', 'POST'])
def forgotpassword():
    return render_template('users/forgotpasswordreq.html', title='forgotpassword')

@app.route('/passwordupdatereq', methods = ['GET', 'POST'])
def passwordupdatereq():
    email = request.form['email']

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From users where email = %s', [email])
    data = cursor.fetchall()

    if len(data) == 0:
        flash('Email not registered', 'danger')
        return render_template('login.html', title='Login')
    else:
        token = generateConfirmationToken(email)
        sendMail(
            subjectv='Update Password',
            recipientsv=email,
            linkv='passwordupdate',
            tokenv=token,
            bodyv='Change your password by clicking this link ',
        )

        flash('Kindly Check your email', 'success')
        return redirect(url_for("home2"))


@app.route('/passwordupdate/<token>', methods = ['GET', 'POST'])
def passwordupdate(token):
    email = confirmToken(token)
    return render_template('users/forgotpassword.html', email=email)

@app.route('/passwordupdatef', methods = ['GET', 'POST'])
def passwordupdatef():
    email = request.form['email']
    password = request.form['password']
    password = sha256_crypt.hash(password)

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From users where email = %s', [email])
    data = cursor.fetchall()
    data = data[0]

    cursor.execute('UPDATE users SET password = %s where email = %s', [password, email])

    if data['userType'] == 'customer':
        cursor.execute('UPDATE customers SET password = %s where email = %s', [password, email])
    elif data['userType'] == 'IATA':
        cursor.execute('UPDATE iataUsers SET password = %s where email = %s', [password, email])
    elif data['userType'] == 'hotelUser':
        cursor.execute('UPDATE hotelUsers SET password = %s where email = %s', [password, email])
    elif data['userType'] == 'developer':
        cursor.execute('UPDATE developers SET password = %s where email = %s', [password, email])
    
    mysql.connection.commit()
    cursor.close()
    flash('Your password has been updated', 'success')
    return render_template('login.html', title = 'Login')


@app.route('/signOut', methods=['GET', 'POST'])
@is_logged_in
def signOut():
    session.clear()
    flash('You are now logged out', 'success')
    return render_template('login.html', title = 'Login')


@app.route('/hoteladduser', methods = ['GET', 'POST'])
@is_logged_in
def hoteladduser():
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    
    cursor.execute("SELECT userType FROM hotelMenuAccess where hotelId = %s", [hotelId])
    data = cursor.fetchall()
    subtypes = []

    for d in data:
        subtypes.append(d['userType'])

    if 'revenue' not in subtypes:
        subtypes.append('revenue')
    if 'reservation' not in subtypes:
        subtypes.append('reservation')
    if 'hotelAdmin' not in subtypes:
        subtypes.append('hotelAdmin')

    return render_template('users/hoteladduser.html', title='AddUser', subtypes=subtypes)



@app.route('/registerhotelusers', methods = ['GET', 'POST'])
@is_logged_in
def registerhotelusers():
    if request.method == 'POST':
        fullName = request.form['fullName']
        email = request.form['email']
        password = request.form['password']
        userType = request.form['userType']
        firstName = fullName.split(' ')[0]
        password = sha256_crypt.hash(password)
        hotelId = session.get('hotelId')

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * From users where email = %s', [email])
        data = cursor.fetchall()

        if len(data) == 0:
            token = generateConfirmationToken(email)
            sendMail(
                subjectv='Confirm Email',
                recipientsv=email,
                linkv='confirm_email',
                tokenv=token,
                bodyv='Confirm your email by clicking this link ',
            )

            cursor.execute('INSERT INTO users(firstName, email, password, userType, userSubType, hotelId) Values(%s, %s, %s, %s, %s, %s)', (firstName, email, password, "hoteluser", userType, hotelId))

            cursor.execute('INSERT INTO hotelUsers(fullName,  email, password, userType, hotelId) VALUES(%s, %s, %s, %s, %s)', (fullName,  email, password, userType, hotelId))
        else:
            flash('Email Already Registered', 'danger')
            return render_template('users/hoteladduser.html', title="Register")

        mysql.connection.commit()
        cursor.close()

        flash('New Hotel user has been added', 'success')
        return render_template('index2.html')

@app.route('/adddeveloper', methods = ['GET', 'POST'])
@is_logged_in
def adddeeloper():
    return render_template('users/adddeveloper.html', title='Add')

@app.route('/registerdeveloper', methods = ['GET', 'POST'])
@is_logged_in
def registerdeveloper():
    if request.method == 'POST':

        fullName = request.form['name']
        email = request.form['email']
        password = request.form['password']
        firstName = fullName.split(' ')[0]
        password = sha256_crypt.hash(password)
        hotelId = session.get('hotelId')
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * From users where email = %s', [email])
        data = cursor.fetchall()

        if len(data) == 0:
            token = generateConfirmationToken(email)
            sendMail(
                subjectv='Confirm Email',
                recipientsv=email,
                linkv='confirm_email',
                tokenv=token,
                bodyv='Confirm your email by clicking this link ',
            )

            cursor.execute('INSERT INTO developers(fullName, email, password, hotelId) values(%s, %s, %s, %s)',
            (fullName, email, password, hotelId))
            cursor.execute('INSERT INTO users(firstName, email, password, userType, hotelId) Values(%s, %s, %s, %s, %s)',
                           (firstName, email, password, 'developer', hotelId))
        
        else:
            flash('Email Already Registered', 'danger')
            return render_template('users/adddeveloper.html', title="Register")



        mysql.connection.commit()
        cursor.close()

        flash('You are now registered and can log in', 'success')
        return render_template('login.html', title='Login')
        
    return render_template('login.html', title='Login')

@app.route('/hoteladdusertype', methods = ["GET", "POST"])
@is_logged_in
def hoteladdusertype():
    return render_template('users/hoteladdusertype.html', title='Register')

@is_logged_in
@app.route('/addusertype', methods = ["GET", 'POST'])
def addusertype():
    requestv = getValC(request.form.get('request'))
    requestCreate = getValC(request.form.get('requestCreate'))
    requestManage = getValC(request.form.get('requestManage'))
    requestCreateAdhoc = getValC(request.form.get('requestCreateAdhoc'))
    requestCreateSeries = getValC(request.form.get('requestCreateSeries'))
    strategy = getValC(request.form.get('strategy'))
    strategyRooms = getValC(request.form.get('strategyRooms'))
    strategyRate = getValC(request.form.get('strategyRate'))
    strategyDiscount = getValC(request.form.get('strategyDiscount'))
    strategyDiscountCreate = getValC(request.form.get('strategyDiscountCreate'))
    strategyDiscountMap = getValC(request.form.get('strategyDiscountMap'))
    strategyForecast = getValC(request.form.get('strategyForecast'))
    settingsRequest = getValC(request.form.get('settingsRequest'))
    settingsRequestCreate = getValC(request.form.get('settingsRequestCreate'))
    settingsRequestMap = getValC(request.form.get('settingsRequestMap'))
    settingsContactCreate = getValC(request.form.get('settingsContactCreate'))
    settingsContactMap = getValC(request.form.get('settingsContactMap'))
    settingsTime = getValC(request.form.get('settingsTime'))
    settingsTimeCreate = getValC(request.form.get('settingsTimeCreate'))
    settingsTimeMap = getValC(request.form.get('settingsTimeMap'))
    settingsNegotiation = getValC(request.form.get('settingsNegotiation'))
    settingsAutopilot = getValC(request.form.get('settingsAutopilot'))
    usersHotel = getValC(request.form.get('usersHotel'))
    usersHotelAdd = getValC(request.form.get('usersHotelAdd'))
    usersCustomer = getValC(request.form.get('usersCustomer'))
    usersCustomerAdd = getValC(request.form.get('usersCustomerAdd'))
    usersCustomerEdit = getValC(request.form.get('usersCustomerEdit'))
    usersCustomerUpload = getValC(request.form.get('usersCustomerUpload'))
    analytics = getValC(request.form.get('analytics'))
    analyticsDashboard = getValC(request.form.get('analyticsDashboard'))
    analyticsBehavior = getValC(request.form.get('analyticsBehavior'))
    analyticsPerformance = getValC(request.form.get('analyticsPerformance'))
    analyticsRevenue = getValC(request.form.get('analyticsRevenue'))
    analyticsTracking = getValC(request.form.get('analyticsTracking'))
    settings = getValC(request.form.get('settings'))
    settingsContact = getValC(request.form.get('settingsContact'))
    users = getValC(request.form.get('users'))
    usersHotelEdit = getValC(request.form.get('usersHotelEdit'))
    userType = request.form['userType']

    hotelId = session.get('hotelId')

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From hotelMenuAccess where userType = %s && hotelId = %s', [userType, hotelId])
    data = cursor.fetchall()

    if len(data) == 0:
        cursor.execute('INSERT INTO hotelMenuAccess(userType,request, requestCreate, requestManage, strategy, strategyRooms, strategyForecast, strategyRate, strategyDiscount, settings, settingsRequest, settingsContact, settingsTime, settingsNegotiation, settingsAutopilot, users, usersHotel, usersCustomer, analytics, analyticsDashboard, analyticsBehavior, analyticsPerformance, analyticsRevenue,analyticsTracking, requestCreateAdhoc, requestCreateSeries, strategyDiscountCreate, strategyDiscountMap, settingsRequestCreate, settingsRequestMap, settingsContactCreate, settingsContactMap, settingsTimeMap, settingsTimeCreate, usersHotelAdd, usersHotelEdit, usersCustomerAdd, usersCustomerEdit, usersCustomerUpload, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                       userType, requestv, requestCreate, requestManage, strategy, strategyRooms, strategyForecast, strategyRate, strategyDiscount, settings, settingsRequest, settingsContact, settingsTime, settingsNegotiation, settingsAutopilot, users, usersHotel, usersCustomer, analytics, analyticsDashboard, analyticsBehavior, analyticsPerformance, analyticsRevenue, analyticsTracking, requestCreateAdhoc, requestCreateSeries, strategyDiscountCreate, strategyDiscountMap,  settingsRequestCreate, settingsRequestMap, settingsContactCreate, settingsContactMap, settingsTimeMap, settingsTimeCreate, usersHotelAdd, usersHotelEdit, usersCustomerAdd, usersCustomerEdit, usersCustomerUpload, hotelId])

    else:
        flash('UserType Already Registered', 'danger')
        return render_template('users/hoteladdusertype.html', title="Register")



    mysql.connection.commit()
    cursor.close()

    flash('New userType added', 'success')
    return render_template('index2.html', title='UserType')

@app.route('/managehotelusers', methods = ['GET', 'POST'])
@is_logged_in
def managehotelusers():
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT fullName, email, userType, active FROM hotelUsers where hotelId = %s', [hotelId])

    result = cursor.fetchall()
    cursor.close()
    data = []
    for res in result:
        res['firstName'] = res['fullName'].split()[0]
        data.append(res)
    
    return render_template('users/managehotelusers.html', title= 'Users', data = data)

@app.route('/showprofile/<email>', methods = ['GET', 'POST'])
@is_logged_in
def showprofile(email):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM hotelUsers where email = %s', [email])

    data = cursor.fetchall()
    cursor.close()
    data[0]['email_verified'] = "Yes" if data[0]['email_verified'] else "No"
    data[0]['fullName'] = data[0]['fullName'].split(' ')[0]
    data[0]['active'] = 'Yes' if data[0]['active'] else 'No'
    return render_template('users/showprofile.html', title='Profile', data=data[0])

@app.route('/showprofileAll/<email>', methods = ['GET', 'POST'])
@is_logged_in
def showprofileAll(email):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM users where email = %s', [email])

    data = cursor.fetchall()
    data = data[0]
    if (data['userType'] == 'developer'):
        cursor.execute('SELECT active, email_verified from developers where email = %s', [email])
        rr = cursor.fetchall()
        rr = rr[0]
    elif (data['userType'] == 'IATA'):
        cursor.execute(
             'SELECT active, email_verified from iataUsers where email = %s', [email])
        rr = cursor.fetchall()
        rr = rr[0]
    elif (data['userType'] == 'hoteluser'):
        cursor.execute('SELECT active, email_verified from hotelUsers where email = %s', [email])
        rr = cursor.fetchall()
        rr = rr[0]
    elif (data['userType'] == 'customer'):
        cursor.execute('SELECT active, email_verified from customers where email = %s', [email])
        rr = cursor.fetchall()
        rr = rr[0]
    data['email_verified'] = "Yes" if rr['email_verified'] else "No"
    data['active'] = 'Yes' if rr['active'] else 'No'    
    return render_template('users/showprofileAll.html', title='Profile', data=data)

@app.route('/editUser/<email>', methods = ["GET", "POST"])
@is_logged_in
def editUser(email):
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * FROM hotelUsers where email = %s && hotelId = %s', [email, hotelId])

    data = cursor.fetchall()
    cursor.execute("SELECT userType FROM hotelMenuAccess where hotelId = %s", [hotelId])
    data1 = cursor.fetchall()
    subtypes = []

    for d in data1:
        subtypes.append(d['userType'])

    if 'revenue' not in subtypes:
        subtypes.append('revenue')
    if 'reservation' not in subtypes:
        subtypes.append('reservation')
    if 'hotelAdmin' not in subtypes:
        subtypes.append('hotelAdmin')

    data[0]['email_verified'] = "Yes" if data[0]['email_verified'] else "No"
    return render_template('users/editUser.html', title = 'Edit', data = data[0], subtypes = subtypes)

@app.route('/editUserAll/<email>', methods = ['GET', 'POST'])
@is_logged_in
def editUserAll(email):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM users where email = %s', [email])

    data = cursor.fetchall()
    data = data[0]
    if (data['userType'] == 'developer'):
        cursor.execute(
            'SELECT fullName, active, email_verified from developers where email = %s', [email])
        rr = cursor.fetchall()
        rr = rr[0]
    elif (data['userType'] == 'IATA'):
        cursor.execute(
            'SELECT fullName, active, email_verified from iataUsers where email = %s', [email])
        rr = cursor.fetchall()
        rr = rr[0]
    elif (data['userType'] == 'hoteluser'):
        cursor.execute(
            'SELECT fullName, active, email_verified from hotelUsers where email = %s', [email])
        rr = cursor.fetchall()
        rr = rr[0]
    elif (data['userType'] == 'customer'):
        cursor.execute(
            'SELECT fullName, active, email_verified from customers where email = %s', [email])
        rr = cursor.fetchall()
        rr = rr[0]
    data['email_verified'] = "Yes" if rr['email_verified'] else "No"
    data['active'] = 'Yes' if rr['active'] else 'No'
    data['fullName'] = rr['fullName']

    return render_template('users/editUserAll.html', data=data)

@app.route('/submitEditUser', methods = ['GET', 'POST'])
@is_logged_in
def submitEditUser():
    name = request.form['name']
    userType = request.form['userType']
    email_verified = getValC(request.form.get('email_verified'))
    active = getValC(request.form.get('active'))
    firstName = name.split()[0]
    email = request.form['email']
    hotelId = session.get('hotelId')

    cursor = mysql.connection.cursor()

    cursor.execute('Update hotelUsers SET fullName = %s, userType = %s, email_verified = %s, active = %s WHERE email = %s && hotelId = %s',(name, userType, email_verified, active, email, hotelId))


    cursor.execute('Update users SET firstName = %s,  userSubType = %s WHERE email = %s && hotelId = %s', (firstName, userType, email, hotelId))

    mysql.connection.commit()
    cursor.close()

    flash('Hotel user has been edited', 'success')
    return redirect(url_for("home2"))


@app.route('/submitEditUserAll2', methods = ["GET", 'POST'])
@is_logged_in
def submitEditUserAll2():
    name = request.form['name']
    email_verified = getValC(request.form.get('email_verified'))
    active = getValC(request.form.get('active'))
    firstName = name.split()[0]
    email = request.form['email']
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM users where email = %s', [email])
    data = cursor.fetchall()
    data = data[0]
    if (data['userType'] == 'developer'):
        cursor.execute('Update developers SET fullName = %s, email_verified = %s, active = %s where email = %s', [name, email_verified, active, email])
    elif (data['userType'] == 'IATA'):
        cursor.execute('Update iataUsers SET fullName = %s, email_verified = %s, active = %s where email = %s', [
                       name, email_verified, active, email])
    elif (data['userType'] == 'hoteluser'):
        cursor.execute('Update hotelUsers SET fullName = %s, email_verified = %s, active = %s where email = %s', [
                       name, email_verified, active, email])
    elif (data['userType'] == 'customer'):
        cursor.execute('Update customers SET fullName = %s, email_verified = %s, active = %s where email = %s', [
                       name, email_verified, active, email])

    cursor.execute('Update users SET firstName = %s WHERE email = %s', (firstName, email))

    mysql.connection.commit()
    cursor.close()

    flash('User has been edited', 'success')
    return render_template('index2.html')


@is_logged_in
@app.route('/deactivateUser/<email>', methods = ['GET', 'POST'])
def deactivateUser(email):
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute("UPDATE hotelUsers SET active = 0 where email = %s && hotelId = %s", [email, hotelId])
    mysql.connection.commit()
    cursor.close()

    flash("User has been de-activated", 'success')
    return redirect(url_for("managehotelusers"))


@app.route('/deactivateUserAll/<email>', methods=['GET', 'POST'])
@is_logged_in
def deactivateUserAll(email):
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * FROM users where email = %s && hotelId = %s', [email, hotelId])
    data = cursor.fetchall()
    data = data[0]
    if (data['userType'] == 'developer'):
        cursor.execute('Update developers SET active = 0 where email = %s', [
                      email])
    elif (data['userType'] == 'IATA'):
        cursor.execute('Update iataUsers SET active = 0 where email = %s', [
                      email])
    elif (data['userType'] == 'hoteluser'):
        cursor.execute('Update hotelUsers SET active = 0 where email = %s', [
                      email])
    elif (data['userType'] == 'customer'):
        cursor.execute('Update customers SET active = 0 where email = %s', [
                      email])

    mysql.connection.commit()
    cursor.close()

    flash("User has been de-activated", 'success')
    return redirect(url_for('viewAllUsers'))

@app.route('/deactivateC/<email>', methods=['GET', 'POST'])
@is_logged_in
def deactivateC(email):
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * FROM users where email = %s && hotelId = %s', [email, hotelId])
    data = cursor.fetchall()
    data = data[0]
    if (data['userType'] == 'customer'):
        cursor.execute('Update customers SET active = 0 where email = %s', [
                      email])
    elif (data['userType'] == 'IATA'):
        cursor.execute('Update iataUsers SET active = 0 where email = %s', [
                      email])

    mysql.connection.commit()
    flash("User has been de-activated", 'success')
    return redirect(url_for('editCustomers'))

@app.route('/activateC/<email>', methods=['GET', 'POST'])
@is_logged_in
def activateC(email):
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * FROM users where email = %s && hotelId = %s', [email, hotelId])
    data = cursor.fetchall()
    data = data[0]

    if (data['userType'] == 'customer'):
        cursor.execute('Update customers SET active = 1 where email = %s', [
                      email])
    elif (data['userType'] == 'IATA'):
        cursor.execute('Update iataUsers SET active = 1 where email = %s', [
                      email])

    mysql.connection.commit()
    flash("User has been activated", 'success')
    return redirect(url_for('editCustomers'))

@app.route('/activateUser/<email>', methods=['GET', 'POST'])
@is_logged_in
def activateUser(email):
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute(
        "UPDATE hotelUsers SET active = 1 where email = %s && hotelId = %s", [email, hotelId])
    mysql.connection.commit()
    cursor.close()

    flash("User has been activated", 'success')
    return redirect(url_for("managehotelusers"))


@app.route('/activateUserAll/<email>', methods=['GET', 'POST'])
@is_logged_in
def activateUserAll(email):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM users where email = %s', [email])
    data = cursor.fetchall()
    data = data[0]
    if (data['userType'] == 'developer'):
        cursor.execute('Update developers SET active = 1 where email = %s', [
            email])
    elif (data['userType'] == 'IATA'):
        cursor.execute('Update iataUsers SET active = 1 where email = %s', [
            email])
    elif (data['userType'] == 'hoteluser'):
        cursor.execute('Update hotelUsers SET active = 1 where email = %s', [
            email])
    elif (data['userType'] == 'customer'):
        cursor.execute('Update customers SET active = 1 where email = %s', [
            email])

    
    mysql.connection.commit()
    cursor.close()

    flash("User has been activated", 'success')
    return redirect(url_for('viewAllUsers'))


@app.route('/myprofile/<email>', methods = ['GET', 'POST'])
@is_logged_in
def myprofile(email):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT userType FROM users where email = %s', [email])
    data = cursor.fetchall()
    
    data = data[0]['userType']
    result = []
    if data == 'hoteluser':
        cursor.execute('SELECT * From hotelUsers where email = %s', [email])
        result = cursor.fetchall()
    elif data == 'customer':
        cursor.execute('SELECT * From customers where email = %s', [email])
        result = cursor.fetchall()
    elif data == 'IATA':
        cursor.execute('SELECT * From iataUsers where email = %s', [email])
        result = cursor.fetchall()
    elif data == 'developer':
        cursor.execute('SELECT * From developers where email = %s', [email])
        result = cursor.fetchall()
    
    result = result[0]
    result['email_verified'] = "Yes" if result['email_verified'] else 'No'
    if 'active' in result.keys():
        result['active'] = "Yes" if result['active'] else 'No'

    result['firstName'] = result['fullName'].split(' ')[0]
    
    return render_template('users/myProfile.html', data= result)


@app.route('/submitEditUserAll', methods=['GET', 'POST'])
@is_logged_in
def submitEditUserAll():
    name = request.form['name']
    phone = request.form.get('phone')
    country = request.form.get('country')
    email = request.form['email']
    agencyName = request.form.get('agencyName')
    iataCode = request.form.get('iataCode')
    organizationName = request.form.get('organizationName')


    firstName = name.split(' ')[0]
    cursor = mysql.connection.cursor()

    cursor.execute('SELECT userType From users where email = %s', [email])
    data = cursor.fetchall()

    data = data[0]['userType']
    if data == 'hoteluser':
        cursor.execute('Update hotelUsers SET fullName = %s WHERE email = %s',
                        (name, email))
    elif data == 'customer':
        cursor.execute('Update customers SET fullName = %s, phone = %s, country = %s WHERE email = %s',
                        (name, phone, country, email))
    elif data == 'IATA':
        cursor.execute('Update iataUsers SET fullName = %s, phone = %s, country = %s WHERE email = %s',
                        (name, phone, country, email))
    elif data == 'developer':
        cursor.execute('Update developers SET fullName = %s, phone = %s WHERE email = %s',
                        (name, phone, email))

    cursor.execute('Update users SET firstName = %s WHERE email = %s',
                    (firstName, email))
    
    mysql.connection.commit()
    cursor.close()

    flash('User Details updated', 'success')
    return redirect(url_for('home2'))


@app.route('/inviteemail', methods = ['GET', 'POST'])
@is_logged_in
def inviteemail():
    email = request.form['email']
    userType = request.form['userType']
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From users where email = %s', [email])
    data = cursor.fetchall()
    hotelId = session.get('hotelId')

    if len(data) != 0:
        flash('Email already registered', 'danger')
        return render_template('login.html', title='Login')
    else:
        token = generateConfirmationToken(email)

        cursor.execute('INSERT INTO inviteEmail(email, userType, hotelId) VALUES(%s, %s, %s)', [email, userType, hotelId])
        mysql.connection.commit()
        cursor.close()
        sendMail(
            subjectv='Invite to TROMPAR',
            recipientsv=email,
            linkv='addhoteluserinv',
            tokenv=token,
            bodyv='Kindly fill the form to complete registration'
        )

        flash('Invitation sent to email', 'success')
        return render_template('index2.html', title='Login')


@app.route('/addhoteluserinv<token>', methods = ['GET', 'POST'])
@is_logged_in
def addhoteluserinv(token):
    email = confirmToken(token)
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From inviteEmail where email = %s', [email])
    data = cursor.fetchall()
    data = data[0]
    userType = data['userType']

    return render_template('users/addhoteluserinv.html', title = 'Register', email = email, userType = userType)


@app.route('/edituserType', methods = ['GET', 'POST'])
@is_logged_in
def edituserType():
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    
    cursor.execute(
        'SELECT * From hotelMenuAccess where hotelId = %s', [hotelId])
    datah = cursor.fetchall()
    if len(datah) != 0:
        datah = datah[0]
    
    cursor.execute("SELECT userType FROM hotelMenuAccess where hotelId = %s", [hotelId])
    data = cursor.fetchall()
    subtypes = []

    for d in data:
        subtypes.append(d['userType'])

    if 'revenue' not in subtypes:
        subtypes.append('revenue')
    if 'reservation' not in subtypes:
        subtypes.append('reservation')
    if 'hotelAdmin' not in subtypes:
        subtypes.append('hotelAdmin')

    return render_template('users/editusertype.html', datah=datah, subtypes=subtypes)


@app.route('/euserType', methods=['GET', 'POST'])
@is_logged_in
def euserType():
    userType = request.form.get('userType')
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute(
        'SELECT * From hotelMenuAccess where userType = %s && hotelId = %s', [userType, hotelId])
    datah = cursor.fetchall()
    if len(datah) != 0:
        datah = datah[0]
    return render_template('users/eusertype.html', datah=datah, userType=userType)


@app.route('/submiteditusertype', methods = ['GET', 'POST'])
@is_logged_in
def submiteditusertype():
    requestv = getValC(request.form.get('request'))
    requestCreate = getValC(request.form.get('requestCreate'))
    requestManage = getValC(request.form.get('requestManage'))
    requestCreateAdhoc = getValC(request.form.get('requestCreateAdhoc'))
    requestCreateSeries = getValC(request.form.get('requestCreateSeries'))
    strategy = getValC(request.form.get('strategy'))
    strategyRooms = getValC(request.form.get('strategyRooms'))
    strategyRate = getValC(request.form.get('strategyRate'))
    strategyDiscount = getValC(request.form.get('strategyDiscount'))
    strategyDiscountCreate = getValC(request.form.get('strategyDiscountCreate'))
    strategyDiscountMap = getValC(request.form.get('strategyDiscountMap'))
    strategyForecast = getValC(request.form.get('strategyForecast'))
    settingsRequest = getValC(request.form.get('settingsRequest'))
    settingsRequestCreate = getValC(request.form.get('settingsRequestCreate'))
    settingsRequestMap = getValC(request.form.get('settingsRequestMap'))
    settingsContactCreate = getValC(request.form.get('settingsContactCreate'))
    settingsContactMap = getValC(request.form.get('settingsContactMap'))
    settingsTime = getValC(request.form.get('settingsTime'))
    settingsTimeCreate = getValC(request.form.get('settingsTimeCreate'))
    settingsTimeMap = getValC(request.form.get('settingsTimeMap'))
    settingsNegotiation = getValC(request.form.get('settingsNegotiation'))
    settingsAutopilot = getValC(request.form.get('settingsAutopilot'))
    usersHotel = getValC(request.form.get('usersHotel'))
    usersHotelAdd = getValC(request.form.get('usersHotelAdd'))
    usersCustomer = getValC(request.form.get('usersCustomer'))
    usersCustomerAdd = getValC(request.form.get('usersCustomerAdd'))
    usersCustomerEdit = getValC(request.form.get('usersCustomerEdit'))
    usersCustomerUpload = getValC(request.form.get('usersCustomerUpload'))
    analytics = getValC(request.form.get('analytics'))
    analyticsDashboard = getValC(request.form.get('analyticsDashboard'))
    analyticsBehavior = getValC(request.form.get('analyticsBehavior'))
    analyticsPerformance = getValC(request.form.get('analyticsPerformance'))
    analyticsRevenue = getValC(request.form.get('analyticsRevenue'))
    analyticsTracking = getValC(request.form.get('analyticsTracking'))
    settings = getValC(request.form.get('settings'))
    settingsContact = getValC(request.form.get('settingsContact'))
    users = getValC(request.form.get('users'))
    usersHotelEdit = getValC(request.form.get('usersHotelEdit'))
    userType = request.form['userType']
    analyticsStdReport = getValC(request.form.get('analyticsStdReport'))
    strategyEvaluation = getValC(request.form.get('strategyEvaluation'))
    settingBusinessReward = getValC(request.form.get('settingBusinessReward'))
    strategyAncillary = getValC(request.form.get('strategyAncillary'))
    

    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')

    cursor.execute('SELECT * from hotelMenuAccess where userType = %s && hotelId = %s', [userType, hotelId])
    length = cursor.fetchall()
    if len(length) != 0:
        cursor.execute('Update hotelMenuAccess SET request = %s, requestCreate = %s, requestManage = %s, strategy = %s, strategyRooms = %s, strategyForecast = %s, strategyRate = %s, strategyDiscount = %s, settings = %s, settingsRequest = %s, settingsContact = %s, settingsTime = %s, settingsNegotiation = %s, settingsAutopilot = %s, users = %s, usersHotel = %s, usersCustomer = %s, analytics = %s, analyticsDashboard = %s, analyticsBehavior = %s, analyticsPerformance = %s, analyticsRevenue = %s, analyticsTracking = %s, requestCreateAdhoc = %s, requestCreateSeries = %s, strategyDiscountCreate = %s, strategyDiscountMap = %s, settingsRequestCreate = %s, settingsRequestMap = %s, settingsContactCreate = %s, settingsContactMap = %s, settingsTimeMap = %s, settingsTimeCreate = %s, usersHotelAdd = %s, usersHotelEdit = %s, usersCustomerAdd = %s, usersCustomerEdit = %s, usersCustomerUpload = %s, analyticsStdReport = %s, strategyEvaluation = %s,strategyAncillary = %s, settingBusinessReward = %s WHERE userType = %s && hotelId = %s', [
                    requestv, requestCreate, requestManage, strategy, strategyRooms, strategyForecast, strategyRate, strategyDiscount, settings, settingsRequest, settingsContact, settingsTime, settingsNegotiation, settingsAutopilot, users, usersHotel, usersCustomer, analytics, analyticsDashboard, analyticsBehavior, analyticsPerformance, analyticsRevenue, analyticsTracking, requestCreateAdhoc, requestCreateSeries, strategyDiscountCreate, strategyDiscountMap,  settingsRequestCreate, settingsRequestMap, settingsContactCreate, settingsContactMap, settingsTimeMap, settingsTimeCreate, usersHotelAdd, usersHotelEdit, usersCustomerAdd, usersCustomerEdit, usersCustomerUpload, analyticsStdReport, strategyEvaluation,strategyAncillary, settingBusinessReward, userType, hotelId])
    else:
        cursor.execute('INSERT INTO hotelMenuAccess (request, requestCreate, requestManage, strategy, strategyRooms, strategyForecast, strategyRate, strategyDiscount, settings, settingsRequest, settingsContact, settingsTime, settingsNegotiation, settingsAutopilot, users, usersHotel, usersCustomer, analytics, analyticsDashboard, analyticsBehavior, analyticsPerformance, analyticsRevenue, analyticsTracking, requestCreateAdhoc, requestCreateSeries, strategyDiscountCreate, strategyDiscountMap, settingsRequestCreate, settingsRequestMap, settingsContactCreate, settingsContactMap, settingsTimeMap, settingsTimeCreate, usersHotelAdd, usersHotelEdit, usersCustomerAdd, usersCustomerEdit, usersCustomerUpload, analyticsStdReport, strategyEvaluation,strategyAncillary, settingBusinessReward, userType, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ',[
                    requestv, requestCreate, requestManage, strategy, strategyRooms, strategyForecast, strategyRate, strategyDiscount, settings, settingsRequest, settingsContact, settingsTime, settingsNegotiation, settingsAutopilot, users, usersHotel, usersCustomer, analytics, analyticsDashboard, analyticsBehavior, analyticsPerformance, analyticsRevenue, analyticsTracking, requestCreateAdhoc, requestCreateSeries, strategyDiscountCreate, strategyDiscountMap,  settingsRequestCreate, settingsRequestMap, settingsContactCreate, settingsContactMap, settingsTimeMap, settingsTimeCreate, usersHotelAdd, usersHotelEdit, usersCustomerAdd, usersCustomerEdit, usersCustomerUpload, analyticsStdReport, strategyEvaluation,strategyAncillary, settingBusinessReward, userType, hotelId])

    mysql.connection.commit()
    cursor.close()

    flash('UserType updated!', 'success')
    return redirect(url_for('home2'))


@app.route('/viewAllUsers', methods=['GET', 'POST'])
@is_logged_in
def viewAllUsers():
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute("SELECT * FROM users where hotelId = %s", [hotelId])
    data = cursor.fetchall()

    for r in data:
        if (r['userType'] == 'developer'):
            cursor.execute(
                'SELECT active from developers where email = %s', [r['email']])
            rr = cursor.fetchall()
            if len(rr) != 0:
                rr = rr[0]
        elif (r['userType'] == 'IATA'):
            cursor.execute(
                'SELECT active from iataUsers where email = %s', [r['email']])
            rr = cursor.fetchall()
            if len(rr) != 0:
                rr = rr[0]
        elif (r['userType'] == 'hoteluser'):
            cursor.execute(
                'SELECT active from hotelUsers where email = %s', [r['email']])
            rr = cursor.fetchall()
            if len(rr) != 0:
                rr = rr[0]
        elif (r['userType'] == 'customer'):
            cursor.execute(
                'SELECT active from customers where email = %s', [r['email']])
            rr = cursor.fetchall()
            if len(rr) != 0:
                rr = rr[0]
        if len(rr) != 0:
            r['active'] = rr['active']

    cursor.close()
    return render_template('users/manageAllUsers.html', data=data)


@app.route('/editCustomers', methods = ['GET', 'POST'])
@is_logged_in
def editCustomers():
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * From users where (userType = %s or userType = %s) && hotelId = %s', ["customer", "IATA", hotelId])
    data = cursor.fetchall() 
    for r in data:
        if (r['userType'] == 'customer'):
            cursor.execute(
                'SELECT active, email_verified from customers where email = %s', [r['email']])
        elif (r['userType'] == 'IATA'):
            cursor.execute(
                'SELECT active, email_verified from iataUsers where email = %s', [r['email']])
        rr = cursor.fetchall()
        if len(rr) != 0:
            rr = rr[0]
            r['active'] = rr['active']
            r['email_verified'] = rr['email_verified']



    return render_template('users/managecustomers.html', data =data)

# Users Module Finished

@app.route('/strategyRooms', methods = ['GET', 'POST'])
@is_logged_in
def strategyRooms():
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * From room where hotelId = %s', [hotelId])
    data = cursor.fetchall()
    if len(data) == 0:
        return render_template('strategy/strategyRooms.html')
    else:
        totalRooms = 0
        for d in data:
            totalRooms += int(d['count'])

        return render_template('strategy/editstrategyRooms.html', data = data, totalRooms = totalRooms)


@app.route('/strategyRoomsSubmit', methods = ['GET', 'POST'])
@is_logged_in
def strategyRoomsSubmit():
    inp = request.json
    inp.remove(inp[0])

    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    for i in inp:
        cursor.execute("INSERT INTO room(type, count, single, doublev, triple, quad, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s)" , [i[0][0], i[1], int(i[2]), int(i[3]), int(i[4]), int(i[5]), hotelId])
    
    mysql.connection.commit()
    cursor.close()

    flash('Your Room data has been entered', 'success')
    return ('', 204)


@app.route('/editstrategyRoomsSubmit', methods = ['GET', 'POST'])
@is_logged_in
def editstrategyRoomsSubmit():
    inp = request.json
    if len(inp) == 0:
        return render_template('index2.html')
    inp.remove(inp[0])
        
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('DELETE FROM room where hotelId = %s', [hotelId])
    mysql.connection.commit()

    for i in inp:
        cursor.execute("INSERT INTO room(type, count, single, doublev, triple, quad, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s)", [
                       i[0][0], i[1], int(i[2]), int(i[3]), int(i[4]), int(i[5]), hotelId])

    mysql.connection.commit()
    cursor.close()

    flash('Your Room data has been updated', 'success')
    return ('', 204)



@app.route('/strategyRate', methods = ['GET', 'POST'])
@is_logged_in
def strategyRate():
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * From room where hotelId = %s', [hotelId])
    data = cursor.fetchall()
    if len(data) == 0:
        flash('Kindly fill types of Rooms first', 'danger')
        return render_template('strategy/strategyRooms.html')
    else:
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT * From rate where hotelId = %s', [hotelId])
            data1 = cursor.fetchall()
            if len(data1) == 0:
                return render_template('strategy/strategyRate.html', data = data)
            else:
                    cursor.execute('SELECT startDate, endDate from rate where hotelId = %s', [hotelId])
                    storedDates = cursor.fetchall()
                    for d in data1:
                        dow = ""
                        if (d['monday'] == '1'):
                            dow += " M, "    
                        if (d['tuesday'] == '1'):
                            dow += " Tu, "
                        if (d['wednesday'] == '1'):
                            dow += "W, "
                        if (d['thursday'] == '1'):
                            dow += "Th, "
                        if (d['friday'] == '1'):
                            dow += "F, "
                        if (d['saturday'] == '1'):
                            dow += "Sa, "
                        if (d['sunday'] == '1'):
                            dow += "Su"


                        try:
                            d['dow'] = dow[:dow.rindex(', ')]
                        except:
                            d['dow'] = dow

                        d['startDate'] = d['startDate'].strftime('%y-%b-%d')
                        x = d['startDate'].split('-')
                        strd = x[2] + " " + x[1] + ", " + x[0]
                        d['startDate'] = strd

                        d['endDate'] = d['endDate'].strftime('%y-%b-%d')
                        x = d['endDate'].split('-')
                        strd = x[2] + " " + x[1] + ", " + x[0]
                        d['endDate'] = strd
                    
                    return render_template('strategy/editstrategyRate.html', data=data, data1=data1, storedDates=storedDates)

        

@app.route('/strategyRateSubmit', methods = ['GET', 'POST'])
@is_logged_in
def strategyRateSubmit():
    inp = request.json
    if len(inp) == 0:
        return render_template('index2.html')
    
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('DELETE FROM rate where hotelId = %s', [hotelId])
    mysql.connection.commit()
    for i in inp:
        cursor.execute("INSERT INTO rate(startDate, endDate, monday, tuesday, wednesday, thursday, friday, saturday, sunday, type, sor, dor, tor, qor, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8], i[9][0], i[10], i[11], i[12], i[13], hotelId])
    mysql.connection.commit()
    cursor.close()

    flash('Your Rate data has been updated', 'success')
    return ('', 204)


@app.route('/requestCreateAdhoc', methods = ['GET', 'POST'])
@is_logged_in
def requestCreateAdhoc():
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * From room where hotelId = %s', [hotelId])
    data = cursor.fetchall()
    if len(data) == 0:
        flash('Kindly fill types of Rooms first', 'danger')
        return render_template('strategyRooms.html')
    
    c1 = 0
    c2 = 0
    for r in data:
        if r['type'] == '1':
            c1 = r['single'] + r['doublev'] + r['triple'] + r['quad']
        elif r['type'] == '2':
            c2 = r['single'] + r['doublev'] + r['triple'] + r['quad']

    cursor.execute('SELECT email From users where userType != %s && userType != %s && hotelId = %s', ['hoteluser', 'developer', hotelId])
    users = cursor.fetchall()
    cursor.execute('SELECT * From settingsRequest where hotelId = %s Order By submittedOn desc', [hotelId])
    result = cursor.fetchall()
    check_flag = False
    if len(result) != 0:
        check_flag = True
        result = result[0]

    return render_template('request/requestCreateAdhoc.html', data = data, users = users, check_flag = check_flag, result = result, c1 = c1, c2 = c2)


@app.route('/requestCreateAdhocSubmit', methods = ['GET', 'POST'])
@is_logged_in
def requestCreateAdhocSubmit():
    inp = request.json
    cursor = mysql.connection.cursor()
    username = session['email']
    cursor.execute('SELECT userType from users where email = %s', [inp['createdFor']])
    userType = cursor.fetchall()
    userType = userType[0]['userType']
    hotelId = session.get('hotelId')

    if inp['commissionable'] == '':
        inp['commissionable'] = 0

    inp['groupBlock'] = 1 if inp['groupBlock'] == True else 0
    inp['foc'] = 1 if inp['foc'] == True else 0

    if inp['foc1'] == '':
        inp['foc1'] = 0
    if inp['foc2'] == '':
        inp['foc2'] = 0
    


    if inp['paymentDays'] == '':
        inp['paymentDays'] = 0
    if inp['comments'] == '':
        inp['comments'] = 0
    
    cursor.execute('SELECT Count(*) from request where hotelId = %s', [hotelId])
    count = cursor.fetchall()
    count = count[0]['Count(*)'] + 1
    if (count < 10):
        id = "TR" + "00" + str(count)
    elif (count < 99):
        id = "TR" + "0" + str(count)
    today = datetime.date.today()
    d1 = datetime.datetime.strptime(inp['checkIn'], "%Y/%m/%d").date()
    lead = d1 - today
    lead = lead.days
    today = datetime.datetime.today()
    cursor.execute('INSERT INTO request(category, groupName, checkIn, checkOut, nights, commissionable, groupBlock, foc, foc1, foc2, budget, formPayment, paymentTerms, paymentDays, comments, id, createdBy, createdFor, leadTime, status, userType, createdOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                   inp['category'], inp['groupName'], inp['checkIn'], inp['checkOut'], inp['nights'], inp['commissionable'], inp['groupBlock'], inp['foc'], inp['foc1'], inp['foc2'], inp['budget'], procArr(inp['formPayment']), inp['paymentTerms'], inp['paymentDays'], inp['comments'], id, username, inp['createdFor'], lead, statusval1, userType, today, hotelId   
            ])

    table = inp['table_result']
    for t in table:
        if (t['type'] == '1'):
            cursor.execute('INSERT INTO request1Bed(date, occupancy, count, id, hotelId) VALUES(%s, %s, %s, %s, %s)', [
                t['date'], t['occupancy'], t['count'], id, hotelId])
        else:
            cursor.execute(
                'INSERT INTO request2Bed(date, occupancy, count, id, hotelId) VALUES(%s, %s, %s, %s, %s)', [t['date'],  t['occupancy'], t['count'], id, hotelId])

    mysql.connection.commit()
    cursor.close()
    flash('Your Request has been entered', 'success')
    return ('', 204)


@app.route('/', methods=['GET', 'POST'])
def home2():
    try:
        if session['logged_in'] == True:
            if session['userType'] == 'hoteluser' or session['userType'] == 'developer':
                cursor = mysql.connection.cursor()
                hotelId = session.get('hotelId')
                cursor.execute('SELECT * FROM request where hotelId = %s', [hotelId])
                data = cursor.fetchall()
                data = data[::-1]
                for d in data:
                    d['checkIn'] = d['checkIn'].strftime("%d-%b-%y")
                return render_template('index2.html', title = 'Home', data = data)
            else:
                cursor = mysql.connection.cursor()
                cursor.execute('SELECT * From request where createdFor = %s && hotelId = %s', [session['email'], hotelId])
                data = cursor.fetchall()
                data = data[::-1]
                for d in data:
                    d['checkIn'] = d['checkIn'].strftime("%d-%b-%y")
                return render_template('index2.html', title='Home', data=data)
            return render_template('index2.html', title='Home')
    except:
        #updatePasswords()
        return render_template('login.html', title='Login')

@app.route('/strategyDiscountCreate', methods = ['GET', 'POST'])
@is_logged_in
def strategyDiscountCreate():
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT count from room where hotelId = %s', [hotelId])
    data = cursor.fetchall()
    rooms = 0
    for d in data:
        rooms += int(d['count'])
    cursor.execute('SELECT * FROM discountMap where hotelId = %s', [hotelId]) 
    discountGrids = cursor.fetchall()
    cursor.execute('SELECT * FROM discountMap WHERE defaultm = TRUE && hotelId = %s', [hotelId])
    f = cursor.fetchall()
    flag = False
    defaultId = -1
    if len(f) != 0:
        flag = True
        defaultId = f[0]['discountId']

    for r in discountGrids:
        r['startDate'] = r['startDate'].strftime('%y-%b-%d')
        x = r['startDate'].split('-')
        r['startDate']= x[2] + " " + x[1] + ", " + x[0]
        r['endDate'] = r['endDate'].strftime('%y-%b-%d')
        x = r['endDate'].split('-')
        r['endDate'] = x[2] + " " + x[1] + ", " + x[0]


    cursor.execute('SELECT startDate, endDate from discountMap where defaultm = 0 && hotelId = %s', [hotelId])
    storedDates = cursor.fetchall()

    factor = rooms * 20 // 100
    halffactor = factor // 2

    return render_template('strategy/strategyDiscountCreate.html', rooms = rooms, discountGrids = discountGrids, flag = flag, defaultId = defaultId, storedDates = storedDates, factor = factor, halffactor = halffactor)


@app.route('/strategyDiscountSubmit', methods = ['GET', 'POST'])
@is_logged_in
def strategyDiscountSubmit():
    inp = request.json
    occ = inp['occ']
    hotelId = session.get('hotelId')
        
    cursor = mysql.connection.cursor()
    for o in occ:
        cursor.execute('INSERT INTO discountOcc(discountId, occ, col, hotelId) VALUES(%s, %s, %s, %s)', [inp['discountId'], o['occ'], o['col'], hotelId])

    email = session['email']
    time = datetime.datetime.utcnow()   
    cursor.execute('INSERT INTO discountMap(discountId, startDate, endDate, defaultm, createdBy, createdOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s)', [inp['discountId'], inp['startDate'], inp['endDate'], inp['defaultm'], email, time, hotelId])

    for jindex, l in enumerate(inp['leadtime']):
        lead = l.split(' - ')
        leadMin = lead[0]
        if (len(lead) == 2):
            leadMax = lead[1]
        else:
            leadMax = 730
        discountId = inp['discountId']

        for index, r in enumerate(inp['ranges']):
            range = r.split(' - ')
            roomMin = range[0]
            roomMax = range[1]
            values = inp['values']
            value = values[jindex][index]
            
            cursor.execute('INSERT INTO discount(discountId, leadMin, leadMax, roomMin, roomMax, value, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s)', [discountId, leadMin, leadMax, roomMin, roomMax, value, hotelId])


    mysql.connection.commit()
    cursor.close()

    flash('Your discount grid has been entered', 'success')
    return ('', 204)
  
@app.route('/showDiscountGrid/<id>', methods = ['GET', 'POST'])
@is_logged_in
def showDiscountGrid(id):
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * from discountMap where discountId = %s && hotelId = %s', [id, hotelId])
    data = cursor.fetchall()
    data = data[0]

    cursor.execute('SELECT * FROM discount where discountId = %s && hotelId = %s', [id, hotelId])
    grid = cursor.fetchall()

    cursor.execute('SELECT * FROM discountOcc where discountId = %s && hotelId = %s', [id, hotelId])
    occ = cursor.fetchall()

    ranges = []
    range1 = {}
    for l in grid:
        key = l['roomMin'] + " - " + l['roomMax']
        if key not in range1:
            range1[key] = 0
            ranges.append(key)
        else:
            break


    
    result = []
    tup = {}
    for d in grid:
        l = []
        min = d['leadMin']
        max = d['leadMax']
        key = str(min + " - " + max)
        dic = {}
        dic['min'] = d['roomMin']
        dic['max'] = d['roomMax']
        dic['value'] = d['value']
        if key in tup:
            tup[key].append(dic)
        else:
            tup[key] = [dic]
    
    result = tup

    cursor.execute('SELECT * From discountMap where defaultm = 1 && hotelId = %s', [hotelId])
    ffm = cursor.fetchall()
    flag = True
    if len(ffm) == 0:
        flag = False

    cursor.execute(
        'SELECT startDate, endDate from discountMap where defaultm = 0 AND discountId != %s && hotelId = %s', [id, hotelId])
    storedDates = cursor.fetchall()

    data['startDate'] = data['startDate'].strftime('%y-%b-%d')
    x = data['startDate'].split('-')
    data['startDate']= x[2] + " " + x[1] + ", " + x[0]
    data['endDate'] = data['endDate'].strftime('%y-%b-%d')
    x = data['endDate'].split('-')
    data['endDate'] = x[2] + " " + x[1] + ", " + x[0]


    return render_template('strategy/showDiscountGrid1.html', grid = grid, data = data, ranges = ranges, result = result, occ = occ, flag = flag, storedDates = storedDates)


@app.route('/unmarkDefault/<id>', methods = ['GET', 'POST'])
@is_logged_in
def unmarkDefault(id):
    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE discountMap set defaultm = 0 where discountId = %s', [id])
    mysql.connection.commit()
    cursor.close()
    flash('Grid marked as non default', 'success')
    return redirect(url_for('strategyDiscountCreate'))


@app.route('/markDefault/<id>', methods = ['GET', 'POST'])
@is_logged_in
def markDefault(id):
    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE discountMap set defaultm = 1 where discountId = %s', [id])
    mysql.connection.commit()
    cursor.close()
    flash('Grid marked as default', 'success')
    return redirect(url_for('strategyDiscountCreate'))



@app.route('/deactivateDiscount/<id>', methods = ['GET', 'POST'])
@is_logged_in
def deactivateDiscount(id):
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute(
        'UPDATE discountMap set active = 0 where discountId = %s && hotelId = %s', [id, hotelId])
    mysql.connection.commit()
    cursor.close()
    flash('Grid Deactivated', 'danger')
    return redirect(url_for('strategyDiscountCreate'))


@app.route('/activateDiscount/<id>', methods = ['GET', 'POST'])
@is_logged_in
def activateDiscount(id):
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute(
        'UPDATE discountMap set active = 1 where discountId = %s && hotelId = %s', [id, hotelId])
    mysql.connection.commit()
    cursor.close()
    flash('Grid Activated', 'success')
    return redirect(url_for('strategyDiscountCreate'))



@app.route('/editDiscountGrid', methods = ['GET', 'POST'])
@is_logged_in
def editDiscountGrid():
    inp = request.json
    cursor = mysql.connection.cursor()
    email = session['email']
    time = datetime.datetime.utcnow()
    hotelId = session.get('hotelId')


    cursor.execute('UPDATE discountMap SET startDate = %s, endDate = %s, createdBy = %s, createdOn = %s WHERE discountId = %s && hotelId = %s', [
        inp['startDate'], inp['endDate'], email, time, inp['discountId'], hotelId
    ])

    cursor.execute('DELETE FROM discount where discountId = %s && hotelId = %s', [inp['discountId'], hotelId])

    mysql.connection.commit()

    for jindex, l in enumerate(inp['leadtime']):
        lead = l.split('-')
        leadMin = lead[0]
        if (len(lead) == 2):
            leadMax = lead[1]
        else:
            leadMax = 365
        discountId = inp['discountId']

        for index, r in enumerate(inp['ranges']):
            range = r.split(' - ')
            roomMin = range[0]
            roomMax = range[1]
            values = inp['values']
            value = values[jindex][index]
            
            cursor.execute('INSERT INTO discount(discountId, leadMin, leadMax, roomMin, roomMax, value, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s)', [
                           discountId, leadMin, leadMax, roomMin, roomMax, value, hotelId])


    mysql.connection.commit()
    cursor.close()


    flash('Your discount grid has been edited', 'success')
    return ('', 204)


@app.route('/settingsAutopilot', methods = ['GET', 'POST'])
@is_logged_in
def settingsAutopilot():
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * from autopilot where hotelId = %s', [hotelId])
    data = cursor.fetchall()

    for d in data:
        if d['policy'] == 'manual':
            d['policy'] = 'Manual Calculation'

        d['startDate'] = d['startDate'].strftime('%y-%b-%d')
        x = d['startDate'].split('-')
        d['startDate']= x[2] + " " + x[1] + ", " + x[0]
        d['endDate'] = d['endDate'].strftime('%y-%b-%d')
        x = d['endDate'].split('-')
        d['endDate'] = x[2] + " " + x[1] + ", " + x[0]
        d['createdOn'] = d['createdOn'].strftime('%y-%b-%d')
        x = d['createdOn'].split('-')
        d['createdOn'] = x[2] + " " + x[1] + ", " + x[0]



    return render_template('settings/settingsAutopilot.html', data = data)


@app.route('/settingsAutopilotSubmit', methods = ['GET', 'POST'])
@is_logged_in
def settingsAutopilotSubmit():
    inp = request.json
    email = session['email']
    time = datetime.datetime.utcnow()
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('INSERT into autopilot(startDate, endDate, policy, policyName, createdBy, createdOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s)', [inp['startDate'], inp['endDate'], inp['policy'], inp['policyName'],
    email, time, hotelId
    ])

    mysql.connection.commit()
    cursor.close()


    flash('Your Autopilot setting has been added', 'success')
    return ('', 204)


@app.route('/showAutopilot/<id>', methods = ['GET', 'POST'])
@is_logged_in
def showAutopilot(id):
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * From autopilot where policyName = %s && hotelId = %s', [id, hotelId])
    data = cursor.fetchall()
    data = data[0]
    
    data['startDate'] = data['startDate'].strftime('%y-%b-%d')
    x = data['startDate'].split('-')
    data['startDate']= x[2] + " " + x[1] + ", " + x[0]
    data['endDate'] = data['endDate'].strftime('%y-%b-%d')
    x = data['endDate'].split('-')
    data['endDate'] = x[2] + " " + x[1] + ", " + x[0]

    return render_template('settings/showAutopilot.html', data = data)


@app.route('/editAutopilot', methods = ['GET', 'POST'])
@is_logged_in
def editAutopilot():
    inp = request.json
    hotelId = session.get('hotelId')
    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE autopilot SET startDate = %s, endDate = %s, policy = %s WHERE policyName = %s && hotelId = %s', [
        inp['startDate'], inp['endDate'], inp['policy'], inp['policyName'], hotelId
    ])

    mysql.connection.commit()
    cursor.close()

    flash('Your Autopilot setting has been edited', 'success')
    return ('', 204)


@app.route('/deactiveAutopilot/<id>', methods = ['GET', 'POST'])
@is_logged_in
def deactiveAutopilot(id):
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('UPDATE autopilot set active = 0 where policyName = %s && hotelId = %s', [id, hotelId])

    mysql.connection.commit()
    cursor.close()

    flash('Your Autopilot has been de-activated', 'danger')
    return redirect(url_for('settingsAutopilot'))


@app.route('/activateAutopilot/<id>', methods = ['GET', 'POST'])
@is_logged_in
def activateAutopilot(id):
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('UPDATE autopilot set active = 1 where policyName = %s && hotelId = %s', [id, hotelId])

    mysql.connection.commit()
    cursor.close()

    flash('Your Autopilot has been activated', 'success')
    return redirect(url_for('settingsAutopilot'))


@app.route('/settingsRequestCreate', methods=['GET', 'POST'])
@is_logged_in
def settingsRequestCreate():
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * from settingsRequest where hotelId = %s Order By submittedOn desc', [hotelId])
    result = cursor.fetchall()
    flag = True
    if len(result) == 0:
        flag = False
    else:
        result = result[0]
    return render_template('settings/settingsRequestCreate.html', result=result, flag=flag)


@app.route('/settingsRequestSubmit', methods=['GET', 'POST'])
@is_logged_in
def settingsRequestSubmit():
    strategy = request.form['strategy']
    count = request.form['count']
    email = session['email']
    time = datetime.datetime.utcnow()

    hotelId = session.get('hotelId')
    cursor = mysql.connection.cursor()
    cursor.execute('INSERT INTO settingsRequest(strategy, count, submittedBy, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s)', [
                   strategy, count, email, time, hotelId])
    mysql.connection.commit()
    cursor.close()
    flash('Request Settings have been updated', 'success')
    return redirect(url_for("settingsRequestCreate"))


@app.route('/settingsNegotiation', methods=['GET', 'POST'])
@is_logged_in
def settingsNegotiation():
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * from settingsNegotiation where hotelId = %s', [hotelId])
    result = cursor.fetchall()
    flag = True
    if len(result) == 0:
        flag = False
    else:
        result = result[0]
    return render_template('settings/settingsNegotiation.html', result=result, flag=flag)


@app.route('/settingsNegotiationSubmit', methods=['GET', 'POST'])
@is_logged_in
def settingsNegotiationSubmit():
    count = request.form['count']
    email = session['email']
    time = datetime.datetime.utcnow()
    hotelId = session.get('hotelId')
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From settingsNegotiation where hotelId = %s', [hotelId])
    data = cursor.fetchall()
    if len(data) == 0:
        cursor.execute('INSERT INTO settingsNegotiation(count, submittedOn, submittedBy, hotelId) VALUES(%s, %s, %s, %s)', [
                       count, time, email, hotelId])
    else:
        cursor.execute("UPDATE settingsNegotiation set count = %s, submittedOn = %s, submittedBy = %s where hotelId = %s", [
                       count, time, email, hotelId])
    mysql.connection.commit()
    cursor.close()
    flash('Negotiation settings have been updated', 'success')
    return redirect(url_for("settingsNegotiation"))


@app.route('/settingsContractCreate', methods=['GET', 'POST'])
@is_logged_in
def settingsContactCreate():
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * from contract where hotelId = %s', [hotelId])
    result = cursor.fetchall()
    for r in result:
        r['submittedOn'] = r['submittedOn'].strftime('%y-%b-%d')
        x = r['submittedOn'].split('-')
        r['submittedOn'] = x[2] + " " + x[1] + ", " + x[0]
    return render_template('settings/settingsContractCreate.html', result=result)


@app.route('/settingsContractSubmit', methods=['GET', 'POST'])
@is_logged_in
def settingsContractSubmit():
    inp = request.json
    cursor = mysql.connection.cursor()
    email = session['email']
    time = datetime.datetime.utcnow()
    hotelId = session.get('hotelId')
    cursor.execute('INSERT INTO contract(id, contract, submittedOn, submittedBy, hotelId) VALUES(%s, %s, %s, %s, %s)', [
        inp['id'], inp['contract'], time, email, hotelId
    ])
    mysql.connection.commit()

    flash('The contract has been added', 'success')
    return ('', 204)


@app.route('/settingsTimelimit', methods=['GET', 'POST'])
@is_logged_in
def settingsTimelimit():
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * From settingsTimelimit where hotelId = %s', [hotelId])
    
    result = cursor.fetchall()
    flag = True
    if len(result) == 0:
        flag = False
    else:
        result = result[0]
    return render_template('settings/settingsTimelimit.html', result=result, flag=flag)


@app.route('/settingsTimelimitSubmit', methods=['GET', 'POST'])
@is_logged_in
def settingsTimelimitSubmit():
    inp = request.json
    cursor = mysql.connection.cursor()
    email = session['email']
    time = datetime.datetime.utcnow()
    hotelId = session.get('hotelId')

    cursor.execute('SELECT * from settingsTimelimit where hotelId =%s', [hotelId])
    len1 = cursor.fetchall()

    if len(len1) == 1:
        cursor.execute('Update settingsTimelimit SET value = %s, submittedOn = %s, submittedBy = %s, days = %s where hotelId = %s', [
            inp['value'], time, email, inp['days'], hotelId
        ])
    else:
        cursor.execute('INSERT INTO settingsTimelimit(value, submittedOn, submittedBy, days, hotelId) VALUES(%s, %s, %s, %s, %s)', [
            inp['value'], time, email, inp['days'], hotelId
        ])
    mysql.connection.commit()

    flash('The time limit setting has been updated', 'success')
    return ('', 204)



# Request Actions
def reset():
    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE request set status = %s', [statusval1])
    cursor.execute('DELETE From response')
    cursor.execute('DELETE From responseDaywise')
    cursor.execute("DELETE from responseAvg")
    cursor.execute('DELETE from requestAccepted')
    cursor.execute('DELETE from review')
    cursor.execute('DELETE From DeclineRequest')
    cursor.execute('DELETE From deletedRequest')
    cursor.execute('DELETE From requestLastOpened')

    mysql.connection.commit()
    return ''

def updateIata():
    cursor = mysql.connection.cursor()
    cursor.execute("Update users set userType = %s where userType = %s", ['IATA', 'iata'])
    cursor.execute('UPDATE request set userType = %s where userType = %s', ["IATA", 'iata'])
    mysql.connection.commit()
    return ''

def updatePasswords():
    cursor = mysql.connection.cursor()
    cursor.execute("Update users set password = %s", [sha256_crypt.hash('trompar2020')])
    cursor.execute("Update iataUsers set password = %s", [sha256_crypt.hash('trompar2020')])
    cursor.execute("Update hotelUsers set password = %s", [sha256_crypt.hash('trompar2020')])
    cursor.execute("Update developers set password = %s", [sha256_crypt.hash('trompar2020')])
    cursor.execute("Update customers set password = %s", [sha256_crypt.hash('trompar2020')])
    mysql.connection.commit()

@app.route('/showRequest/<token>', methods = ['GET', 'POST'])
@is_logged_in
def showRequest(token):
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    email = session['email']
    cursor.execute('SELECT userType, userSubType from users where email = %s', [email])
    ut = cursor.fetchall()
    if len(ut) != 0:
        ut = ut[0]

    cursor.execute('SELECT status from request where id = %s && hotelId = %s', [token, hotelId])
    status = cursor.fetchall()
    status = status[0]['status']
    if (status == statusval1):
        cursor.execute('SELECT checkIn, checkOut from request where id = %s && hotelId = %s', [token, hotelId])
        dates = cursor.fetchall()
        dates = dates[0]
        checkIn = dates['checkIn']
        checkOut = dates['checkOut']
        dates = []
        day = datetime.timedelta(days=1)

        cursor.execute('SELECT startDate, endDate from autopilot where active = "1" AND policy = "manual" && hotelId = %s', [hotelId])
        excep = cursor.fetchall()

        while checkIn < checkOut:
            dates.append(checkIn)
            checkIn = checkIn + day

        newDates = []
        for d in dates:
            flag = True
            for x in excep:
                if (x['startDate'] <= d and x['endDate'] >= d):
                    flag = False
            if (flag):
                newDates.append(d)

        dates = newDates
        
        newDates = []
        for d in dates:
            day = d.strftime('%A')
            day = day.lower()
            query = 'SELECT * from rate where hotelId = %s && startDate <= %s AND endDate >= %s AND {} = 1'.format(
                day)
            cursor.execute(query, [hotelId, d, d])
            pent = cursor.fetchall()
            if len(pent) != 0:
                newDates.append(d)

        dates = newDates
        newDates = []
        for d in dates:
            y = d
            d = d.strftime('%y-%b-%d')
            x = d.split('-')
            d = x[2] + " " + x[1] + ", " + x[0]
            newDates.append({'d': y, 's' : d})


        dates = newDates

        f = True
        if len(dates) == 0:
            f = False

        return render_template('request/getOcc.html', dates = dates, token = token, flag = f)

    elif (status == statusval2 or status == statusval4 or status == statusval5 or status == statusval6 or status == statusval8 or status == statusval10 or status == statusval11 or  (status == statusval7 and ut.get('userSubType') == 'reservation') or status == statusval9):
        data5 = []
        if (status == statusval4):
            cursor.execute('SELECT * From requestAccepted where requestId = %s && hotelId = %s', [token, hotelId])
            data5 = cursor.fetchall()
            data5 = data5[0]
            temp1 = data5['time'].strftime('%y-%b-%d')
            x = temp1.split('-')
            data5['time'] = x[2] + " " + x[1] + ", " + x[0]
        
        data6 = []
        if (status == statusval5 or status == statusval8):
            cursor.execute("SELECT * From DeclineRequest where requestId = %s && hotelId = %s", [token, hotelId])
            data6 = cursor.fetchall()
            data6 = data6[0]
            temp1 = data6['time'].strftime('%y-%b-%d')
            x = temp1.split('-')
            data6['time'] = x[2] + " " + x[1] + ", " + x[0]
        
        
        data7 = []
        if (status == statusval6):
            cursor.execute("SELECT * From deletedRequest where requestId = %s && hotelId = %s", [token, hotelId])
            data7 = cursor.fetchall()
            data7 = data7[0]
            temp1 = data7['time'].strftime('%y-%b-%d')
            x = temp1.split('-')
            data7['time'] = x[2] + " " + x[1] + ", " + x[0]

        data8 = []
        if (status == statusval7):
            cursor.execute(
                "SELECT * From review where requestId = %s && hotelId = %s", [token, hotelId])
            data8 = cursor.fetchall()
            data8 = data8[0]
            temp1 = data8['time'].strftime('%y-%b-%d')
            x = temp1.split('-')
            data8['time'] = x[2] + " " + x[1] + ", " + x[0]
    
        data9 = []
        if (status == statusval10):
            cursor.execute('SELECT * From confirmRequest where requestId = %s && hotelId = %s', [token, hotelId])
            data9 = cursor.fetchall()
            data9 = data9[0]
            temp1 = data9['submittedOn'].strftime('%y-%b-%d')
            x = temp1.split('-')
            data9['submittedOn'] = x[2] + " " + x[1] + ", " + x[0]

        data10 = []
        if (status == statusval11):
            cursor.execute('SELECT * From notConfirmRequest where requestId = %s && hotelId = %s', [token, hotelId])
            data10 = cursor.fetchall()
            data10 = data10[0]
            temp1 = data10['submittedOn'].strftime('%y-%b-%d')
            x = temp1.split('-')
            data10['submittedOn'] = x[2] + " " + x[1] + ", " + x[0]

        cursor.execute('SELECT * From request where id = %s && hotelId = %s', [token, hotelId])
        data = cursor.fetchall()
        data = data[0]
        checkIn = data['checkIn']
        checkOut = data['checkOut']
        x = data['createdOn'].strftime("%y-%b-%d, %H:%M:%S")
        z = x.split(",")[0]
        y = x.split(",")[1]
        x = z.split("-")
        data['createdOn'] = x[2] + " " + x[1] + ", " + x[0] + " : " + y

        email = session['email']
        now = datetime.datetime.utcnow()

        cursor.execute('SELECT * From requestLastOpened where id = %s && hotelId = %s', [token, hotelId])
        check = cursor.fetchall()
        if len(check) != 0:
            data['lastOpenedOn'] = check[0]['time']
            data['lastOpenedBy'] = check[0]['openedBy']
            temp1 = data['lastOpenedOn'].strftime('%y-%b-%d')
            x = temp1.split('-')
            data['lastOpenedOn'] = x[2] + " " + x[1] + ", " + x[0]


        string = ''
        v = data['paymentTerms']
        if v != None:
            if v.count('pc') > 0:
                string = 'Post Checkout'
                data['paymentTerms'] = string
            elif v.count('ac') > 0:
                data['paymentTerms'] = 'At Checkout'
            elif v.count('poa') > 0:
                data['paymentTerms'] = 'Prior To Arrival'

        string = ''
        v = data['formPayment']
        if v != None:
            if v.count('cq') > 0:
                string += 'Cheque, '
            if v.count('bt') > 0:
                string += ' Bank Transfer, '
            if v.count('cc') > 0:
                string += 'Credit Card, '


        data['formPayment'] = procArr2(data['formPayment'])

        if data['comments'].isspace():
            data['comments'] = ''

        responseId = data['id'] + "R"
        cursor.execute('SELECT * From response where responseId = %s  && hotelId = %s order by submittedOn desc limit 1', [responseId, hotelId])
        data2 = cursor.fetchall()
        tfoc = False
        tcomm = False
        data3 = []
        lefttable = []
        righttable = []
        contract = ''
        contractv = ''
        declined = False
        declinedMsg = False
        nego = False
        negoInformation = ''
        canNegotiate = False

        if len(data2) != 0:
            data['groupCategory'] = data2[0]['groupCategory']
            data2 = data2[0]
            if (data2['foc'] != '0'):
                tfoc = True
            if (data2['commission'] != '0'):
                tcomm = True

            data2['formPayment'] = procArr2(data2['formPayment'])

            string = ''
            v = data2['paymentTerms']
            if v != None:
                if v.count('pc') > 0:
                    string = 'Post Checkout'
                    data2['paymentTerms'] = string
                elif v.count('ac') > 0:
                    data2['paymentTerms'] = 'At Checkout'
                elif v.count('poa') > 0:
                    data2['paymentTerms'] = 'Prior To Arrival'

            cursor.execute('SELECT submittedOn from responseAvg where responseId = %s && hotelId = %s order by submittedOn desc limit 1', [responseId, hotelId])
            submittedOn = cursor.fetchall()
            if submittedOn[0]['submittedOn'] == 'None':
                cursor.execute('SELECT * From responseAvg where responseId = %s && hotelId = %s', [responseId, hotelId])
                data3 = cursor.fetchall()
            else:
                submittedOn = submittedOn[0]['submittedOn']
                cursor.execute('SELECT * From responseAvg where responseId = %s and submittedOn = %s && hotelId = %s', [responseId, submittedOn, hotelId])
                data3 = cursor.fetchall()

            data3 = data3[0]

            cursor.execute(
                'SELECT submittedOn from responseDaywise where responseId = %s && hotelId = %s order by submittedOn desc limit 1', [responseId, hotelId])
            submittedOn = cursor.fetchall()
            if submittedOn[0]['submittedOn'] == 'None':
                cursor.execute(
                    'SELECT * From responseDaywise where responseId = %s && hotelId = %s', [responseId, hotelId])
                data4 = cursor.fetchall()
            else:
                cursor.execute('SELECT * From responseDaywise where responseId = %s and submittedOn = %s && hotelId = %s', [responseId, submittedOn[0]['submittedOn'], hotelId])
                data4 = cursor.fetchall()

            lefttable = []
            dataToCheck = []
            righttable = {}
            for d in data4:
                righttable[d['date']] = []

            for d in data4:
                if d['date'] not in dataToCheck:
                    tempArr = {}
                    tempArr['date'] = d['date']
                    tempArr['currentOcc'] = d['currentOcc']
                    tempArr['discountId'] = d['discountId']
                    tempArr['forecast'] = d['forecast']
                    tempArr['groups'] = d['groups']
                    tempArr['leadTime'] = d['leadTime']
                    lefttable.append(tempArr)
                    dataToCheck.append(d['date'])
                tArr = {}
                tArr['occupancy'] = d['occupancy']
                tArr['type'] = d['type']
                tArr['count'] = d['count']
                tArr['ratePerRoom'] = d['ratePerRoom']

                righttable[d['date']].append(tArr)


            cursor.execute(
                'SELECT contract from response where responseId = %s  && hotelId = %s order by submittedOn desc limit 1', [responseId, hotelId])
            contract = cursor.fetchall()
            contract = contract[0]

            cursor.execute('SELECT contract from contract where id = %s && hotelId = %s', [contract['contract'], hotelId])
            contractv = cursor.fetchall()
            if len(contractv) != 0:
                contractv = contractv[0]['contract']
            else:
                contractv = ''


            declined = False
            declinedMsg = ""
            if (data['status'] == statusval2):
                endline = data2['expiryTime']
                if (endline != None):
                    today = datetime.datetime.now()
                    if (today > endline):
                        cursor.execute(
                            'UPDATE request set status = %s where id = %s && hotelId = %s', [statusval9, data['id'], hotelId])

                        cursor.execute(
                                'SELECT * from response where requestId = %s  && hotelId = %s order by submittedOn desc limit 1', [data['id'], hotelId])
                        email = session['email']
                        now = datetime.datetime.utcnow()
                        prevresponse = cursor.fetchall()

                        if len(prevresponse) != 0:
                            prevresponse = prevresponse[0]
                            cursor.execute('INSERT INTO response(requestId, responseId, groupCategory, totalFare, foc, commission, commissionValue, totalQuote, cutoffDays, formPayment, paymentTerms, paymentGtd, negotiable, checkIn, checkOut, submittedBy, submittedOn, status, paymentDays, nights, comments, averageRate, contract, expectedFare, negotiationReason, timesNegotiated, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                                prevresponse['requestId'], prevresponse['responseId'], prevresponse['groupCategory'], prevresponse['totalFare'], prevresponse[
                                    'foc'], prevresponse['commission'], prevresponse['commissionValue'], prevresponse['totalQuote'], prevresponse['cutoffDays'],
                                prevresponse['formPayment'], prevresponse['paymentTerms'], prevresponse['paymentGtd'], prevresponse[
                                    'negotiable'], prevresponse['checkIn'], prevresponse['checkOut'], email, now,
                                statusval9, prevresponse['paymentDays'], prevresponse['nights'], prevresponse['comments'],
                                prevresponse['averageRate'], prevresponse['contract'], prevresponse['expectedFare'], prevresponse['negotiationReason'], prevresponse['timesNegotiated'], hotelId
                            ])

                            cursor.execute(
                                'SELECT * From responseAvg where responseId = %s && hotelId = %s order by submittedOn desc limit 1', [prevresponse['responseId'], hotelId])
                            prevAvg = cursor.fetchall()
                            if len(prevAvg) != 0:
                                prevAvg = prevAvg[0]
                                cursor.execute('INSERT INTO responseAvg(single1, single2, double1, double2, triple1, triple2, quad1, quad2, responseId, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                                    prevAvg['single1'], prevAvg['single2'], prevAvg['double1'], prevAvg['double2'], prevAvg[
                                        'triple1'], prevAvg['triple2'], prevAvg['quad1'], prevAvg['quad2'], prevAvg['responseId'], now, hotelId
                                ])

                            cursor.execute(
                                'SELECT submittedOn from responseDaywise where responseId = %s  && hotelId = %s order by submittedOn desc limit 1', [prevAvg['responseId'], hotelId])
                            submittedOn = cursor.fetchall()
                            cursor.execute('SELECT * From responseDaywise where responseId = %s and submittedOn = %s  && hotelId = %s',
                                        [prevAvg['responseId'], submittedOn[0]['submittedOn'], hotelId])

                            prevDaywise = cursor.fetchall()
                            if len(prevDaywise) != 0:
                                for p in prevDaywise:
                                    cursor.execute('INSERT INTO responseDaywise(date, currentOcc, discountId, occupancy, type, count, ratePerRoom, responseId, forecast, leadTime, groups, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                                        p['date'], p['currentOcc'], p['discountId'], p['occupancy'], p['type'], p[
                                            'count'], p['ratePerRoom'], prevAvg['responseId'], p['forecast'], p['leadTime'], p['groups'], now, hotelId
                                    ])        
                        
                        cursor.execute(
                            'UPDATE response set status = %s where requestId = %s  && hotelId = %s order by submittedOn desc limit 1', [statusval9, data['id'], hotelId])              

                        mysql.connection.commit()
                        declined = True
                        declinedMsg = "Time limit expired"
                        data['status'] = statusval9
                        data2['status'] = statusval9

            temp1 = data2['submittedOn'].strftime('%y-%b-%d, %H:%M:%S')
            x = temp1.split('-')
            data2['submittedOn'] = x[2].split(",")[0] + " " + x[1] + "," + x[0] + " " + x[2].split(",")[1]
        
        for d in lefttable:
            y = d['date']
            temp1 = d['date'].strftime('%Y-%b-%d-%A')
            x = temp1.split('-')
            x = x[3] + " : " + x[2] + " " + x[1] + "," + x[0]
            d['date'] = x
        
        for d in list(righttable):
            y = d
            temp1 = d.strftime('%Y-%b-%d-%A')
            x = temp1.split('-')
            d = x[3] + " : " + x[2] + " " + x[1] + "," + x[0]
            righttable[d] = righttable[y]
        

        for key,value in righttable.items():
            for r in value:
                if (r['type'] == 'foc'):
                    r['type'] = 'FOC'


        return render_template('request/requestQuotedView.html', data = data, data2= data2, tfoc = tfoc, tcomm = tcomm, data3 = data3, lefttable = lefttable, righttable = righttable, data5 = data5, data6 = data6, data7 = data7, data8 = data8, contract = contract, contractv = contractv, declined = declined, declinedMsg = declinedMsg, nego = nego, negoInformation = negoInformation, canNegotiate = canNegotiate, data9 = data9, data10 = data10)

    elif (status == statusval3 or ( status == statusval7 and ut.get('userSubType') != 'reservation')):
        cursor.execute('select count from settingsNegotiation where hotelId = %s', [hotelId])
        count = cursor.fetchall()
        if len(count) != 0:
            count = count[0]['count']
        else:
            count = 100 # no hard limit set so we're assuming 100 here
        
        data8 = []
        if (status == statusval7):
            cursor.execute(
                "SELECT * From review where requestId = %s  && hotelId = %s", [token, hotelId])
            data8 = cursor.fetchall()
            data8 = data8[0]
            temp1 = data8['time'].strftime('%y-%b-%d')
            x = temp1.split('-')
            data8['time'] = x[2] + " " + x[1] + ", " + x[0]

        cursor.execute('SELECT * From request where id = %s  && hotelId = %s', [token, hotelId])
        data = cursor.fetchall()
        data = data[0]
        checkIn = data['checkIn']
        checkOut = data['checkOut']
        data['createdOn'] = data['createdOn'].strftime("%y/%b/%d, %H:%M:%S")

        email = session['email']
        now = datetime.datetime.utcnow()

        cursor.execute('SELECT * From requestLastOpened where id = %s && hotelId = %s', [token, hotelId])
        check = cursor.fetchall()
        data['lastOpenedOn'] = check[0]['time']
        data['lastOpenedBy'] = check[0]['openedBy']
        temp1 = data['lastOpenedOn'].strftime('%y-%b-%d')
        x = temp1.split('-')
        data['lastOpenedOn'] = x[2] + " " + x[1] + ", " + x[0]
        string = ''
        v = data['paymentTerms']
        if v != None:
            if v.count('pc') > 0:
                string = 'Post Checkout'
                data['paymentTerms'] = string
            elif v.count('ac') > 0:
                data['paymentTerms'] = 'At Checkout'
            elif v.count('poa') > 0:
                data['paymentTerms'] = 'Prior To Arrival'

        string = ''
        

        data['formPayment'] = procArr2(data['formPayment'])

        if data['comments'].isspace():
            data['comments'] = ''

        responseId = data['id'] + "R"
        cursor.execute('SELECT * From response where responseId = %s  && hotelId = %s order by submittedOn desc limit 1', [responseId, hotelId])
        data2 = cursor.fetchall()
        tfoc = False
        tcomm = False
        data3 = []
        lefttable = []
        righttable = []
        contract = ''
        contractv = ''
        nego = False
        negoInformation = ''
        canNegotiate = False
        fop = ''
        pt = ''
        if len(data2) != 0:
            data['groupCategory'] = data2[0]['groupCategory']
            data2 = data2[0]
            if (data2['foc'] != '0'):
                tfoc = True
            if (data2['commission'] != '0'):
                tcomm = True

            string = ''
            v = data2['formPayment']
            fop = data2['formPayment']
            data2['formPayment'] = procArr2(data2['formPayment'])

            string = ''
            v = data2['paymentTerms']
            pt = data2['paymentTerms']
            if v != None:
                if v.count('pc') > 0:
                    string = 'Post Checkout'
                    data2['paymentTerms'] = string
                elif v.count('ac') > 0:
                    data2['paymentTerms'] = 'At Checkout'
                elif v.count('poa') > 0:
                    data2['paymentTerms'] = 'Prior To Arrival'

            cursor.execute('SELECT submittedOn from responseAvg where responseId = %s  && hotelId = %s order by submittedOn desc limit 1', [responseId, hotelId])
            submittedOn = cursor.fetchall()
            if submittedOn[0]['submittedOn'] == 'None':
                cursor.execute('SELECT * From responseAvg where responseId = %s && hotelId = %s', [responseId, hotelId])
                data3 = cursor.fetchall()
            else:
                submittedOn = submittedOn[0]['submittedOn']
                cursor.execute('SELECT * From responseAvg where responseId = %s and submittedOn = %s && hotelId = %s', [responseId, submittedOn, hotelId])
                data3 = cursor.fetchall()

            
            cursor.execute(
                'SELECT submittedOn from responseDaywise where responseId = %s && hotelId = %s order by submittedOn desc limit 1', [responseId, hotelId])
            submittedOn = cursor.fetchall()
            if submittedOn[0]['submittedOn'] == 'None':
                cursor.execute(
                    'SELECT * From responseDaywise where responseId = %s && hotelId = %s', [responseId, hotelId])
                data4 = cursor.fetchall()
            else:
                cursor.execute('SELECT * From responseDaywise where responseId = %s and submittedOn = %s && hotelId = %s', [responseId, submittedOn[0]['submittedOn'], hotelId])
                data4 = cursor.fetchall()

            lefttable = []
            dataToCheck = []
            righttable = {}
            for d in data4:
                righttable[d['date']] = []

            roomCount = 0
            occFlag = False
            for d in data4:
                if d['date'] not in dataToCheck:
                    tempArr = {}
                    tempArr['date'] = d['date']
                    tempArr['currentOcc'] = d['currentOcc']
                    if (d['currentOcc']) != "-":
                        occFlag = True
                    tempArr['discountId'] = d['discountId']
                    tempArr['forecast'] = d['forecast']
                    tempArr['groups'] = d['groups']
                    tempArr['leadTime'] = d['leadTime']
                    lefttable.append(tempArr)
                    dataToCheck.append(d['date'])
                tArr = {}
                tArr['occupancy'] = d['occupancy']
                tArr['type'] = d['type']
                tArr['count'] = d['count']
                roomCount += int(d['count'])
                tArr['ratePerRoom'] = d['ratePerRoom']

                righttable[d['date']].append(tArr)

            cursor.execute(
                'SELECT contract from response where responseId = %s  && hotelId = %s order by submittedOn desc limit 1', [responseId, hotelId])
            contract = cursor.fetchall()
            contract = contract[0]

            single1 = []
            single2 = []
            double1 = []
            double2 = []
            triple1 = []
            triple2 = []
            quad1 = []
            quad2 = []

            single1c = 0
            single2c = 0
            double1c = 0
            double2c = 0
            triple1c = 0
            triple2c = 0
            quad1c = 0
            quad2c = 0
            foc1c = 0
            foc2c = 0

            single1f = False
            double1f = False
            triple1f = False
            quad1f = False
            single2f = False
            double2f = False
            triple2f = False
            quad2f = False

            foc1 = 0
            foc2 = 0
            roomCount = 0

            for m in data4:
                if (m['type'] != 'foc'):
                    roomCount += int(m['count'])
                if (m['type'] == '1 Bed'):
                    if (m['occupancy'] == 'Single'):
                        if (m['ratePerRoom'] != -1):
                            s = m['ratePerRoom'].split('(')
                            v = float(s[0]) * int(m['count'])
                            single1.append(v)
                        single1c = single1c + int(m['count'])
                        single1f = True
                    elif (m['occupancy'] == 'Double'):
                        if (m['ratePerRoom'] != -1):
                            s = m['ratePerRoom'].split('(')
                            v = float(s[0]) * int(m['count'])
                            double1.append(v)
                        double1c = double1c + int(m['count'])
                        double1f = True
                    elif (m['occupancy'] == 'Triple'):
                        if (m['ratePerRoom'] != -1):
                            s = m['ratePerRoom'].split('(')
                            v = float(s[0]) * int(m['count'])
                            triple1.append(v)
                        triple1c = triple1c + int(m['count'])
                        triple1f = True
                    elif (m['occupancy'] == 'Quad'):
                        if (m['ratePerRoom'] != -1):
                            s = m['ratePerRoom'].split('(')
                            v = float(s[0]) * int(m['count'])
                            quad1.append(v)
                        quad1c = quad1c + int(m['count'])
                        quad1f = True
                elif (m['type'] == '2 Bed'):
                    if (m['occupancy'] == 'Single'):
                        if (m['ratePerRoom'] != -1):
                            s = m['ratePerRoom'].split('(')
                            v = float(s[0]) * int(m['count'])
                            single2.append(v)
                        single2c = single2c + int(m['count'])
                        single2f = True
                    elif (m['occupancy'] == 'Double'):
                        if (m['ratePerRoom'] != -1):
                            s = m['ratePerRoom'].split('(')
                            v = float(s[0]) * int(m['count'])
                            double2.append(v)
                        double2c = double2c + int(m['count'])
                        double2f = True
                    elif (m['occupancy'] == 'Triple'):
                        if (m['ratePerRoom'] != -1):
                            s = m['ratePerRoom'].split('(')
                            v = float(s[0]) * int(m['count'])
                            triple2.append(v)
                        triple2c = triple2c + int(m['count'])
                        triple2f = True
                    elif (m['occupancy'] == 'Quad'):
                        if (m['ratePerRoom'] != -1):
                            s = m['ratePerRoom'].split('(')
                            v = float(s[0]) * int(m['count'])
                            quad2.append(v)
                        quad2c = quad2c + int(m['count'])
                        quad2f = True
                elif (m['type'] == 'foc'):
                    if (m['occupancy'] == 'Single'):
                        if (m['ratePerRoom'] != -1):
                            s = m['ratePerRoom'].split('(')
                            v = float(s[0]) * int(m['count'])
                            foc1 += float(v)
                        foc1c = int(m['count'])
                    elif (m['occupancy'] == 'Double'):
                        if (m['ratePerRoom'] != -1):
                            s = m['ratePerRoom'].split('(')
                            v = float(s[0]) * int(m['count'])
                            foc2 += float(v)
                        foc2c = int(m['count'])



            cursor.execute('SELECT contract from contract where id = %s && hotelId = %s', [contract['contract'], hotelId])
            contractv = cursor.fetchall()
            if len(contractv) != 0:
                contractv = contractv[0]['contract']
            else:
                contractv = ''

            cursor.execute('SELECT * from response where responseId = %s && status = %s && hotelId = %s', [responseId, statusval3, hotelId])
            negoTime = cursor.fetchall()
            negoTimes = len(negoTime)
            nego = False
            negoInformation = {}
            canNegotiate = False
            if (int(negoTimes) < int(count)):
                canNegotiate = True
            negoInformation['expectedFare'] = data2['expectedFare']
            negoInformation['reason'] = data2['negotiationReason']

        
        email = session['email']
        cursor.execute('SELECT userType from hotelUsers where email = %s && hotelId = %s', [email, hotelId])
        ut = cursor.fetchall()
        review = True
        if len(ut) != 0:
            ut = ut[0]
            if (ut['userType'] == "hotelAdmin" or ut['userType'] == "revenue"):
                review = False

        cursor.execute('SELECT * from contract where hotelId = %s', [hotelId])
        contracts = cursor.fetchall()

        for d in lefttable:
            y = d['date']
            temp1 = d['date'].strftime('%Y-%b-%d-%A')
            x = temp1.split('-')
            x = x[3] + " : " + x[2] + " " + x[1] + "," + x[0]
            d['date'] = x
        
        for d in list(righttable):
            y = d
            temp1 = d.strftime('%Y-%b-%d-%A')
            x = temp1.split('-')
            d = x[3] + " : " + x[2] + " " + x[1] + "," + x[0]
            righttable[d] = righttable[y]

        data3 = data3[0]
        
        for key,value in righttable.items():
            for r in value:
                if (r['type'] == 'foc'):
                    r['type'] = 'FOC'



        return render_template('request/requestEditableView.html', data = data, data2= data2, tfoc = tfoc, tcomm = tcomm, data3 = data3, lefttable = lefttable, righttable = righttable, data8 = data8, contract = contract, contractv = contractv, nego = nego, negoInformation = negoInformation, canNegotiate = canNegotiate, review = review, contracts = contracts, roomCount = roomCount, fop = fop, pt = pt, single1f = single1f, double1f = double1f, triple1f = triple1f, quad1f = quad1f, single2f = single2f, double2f = double2f, triple2f = triple2f, quad2f = quad2f, single1c = single1c, double1c = double1c, triple1c = triple1c, quad1c = quad1c, single2c = single2c, double2c = double2c, triple2c = triple2c, quad2c = quad2c, foc1c = foc1c, foc2c = foc2c, occFlag = occFlag)

        

@app.route('/showRequest1', methods = ['GET', 'POST'])
@is_logged_in
def showRequest1():
    token = request.form['id']
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * FROM request where id = %s && hotelId = %s', [token, hotelId])
    data = cursor.fetchall()
    data = data[0]
    checkIn = data['checkIn']
    checkOut = data['checkOut']
    data['createdOn'] = data['createdOn'].strftime("%d %b ,%y, %H:%M:%S")

    cursor.execute('SELECT status from request where id = %s && hotelId = %s', [token, hotelId])
    status = cursor.fetchall()
    rvflag = False
    rvvv = []
    if (status[0]['status'] == statusval7):
        cursor.execute('SELECT * From review where requestId = %s && hotelId = %s', [token, hotelId])
        rvvv = cursor.fetchall()
        rvvv = rvvv[0]
        rvflag = True

    email = session['email']
    now = datetime.datetime.utcnow()

    cursor.execute('SELECT * From requestLastOpened where id = %s && hotelId = %s', [token, hotelId])
    check = cursor.fetchall()
    if len(check) == 0:
        cursor.execute('INSERT INTO requestLastOpened(id, time, openedBy, hotelId) VALUES (%s, %s, %s, %s)', [token, now ,email, hotelId]
        )   
        data['lastOpenedOn'] = now
        data['lastOpenedBy'] = email
    else:
        data['lastOpenedOn'] = check[0]['time']
        data['lastOpenedBy'] = check[0]['openedBy']
        cursor.execute('UPDATE requestLastOpened SET time = %s, openedBy = %s where id = %s && hotelId = %s', [now, email, token, hotelId])
        temp1 = data['lastOpenedOn'].strftime('%y-%b-%d')
        x = temp1.split('-')
        data['lastOpenedOn'] = x[2] + " " + x[1] + ", " + x[0]


    mysql.connection.commit()
    string = ''
    v = data['paymentTerms']
    if v != None:
        if v.count('pc') > 0:
            string = 'Post Checkout'
            data['paymentTerms'] = string
        elif v.count('ac') > 0:
            data['paymentTerms'] = 'At Checkout'
        elif v.count('poa') > 0:
            data['paymentTerms'] = 'Prior To Arrival'

    string = ''


    data['formPayment'] = procArr2(data['formPayment'])

    if data['comments'].isspace():
        data['comments'] = ''

    nights = data['nights']
    curr_date = data['checkIn']
    result = []
    dates = []
    discounts = []
    lead = int(data['leadTime'])
    occs = []

    cursor.execute('SELECT * From room where hotelId = %s', [hotelId])
    data7 = cursor.fetchall()
    totalRooms = 0
    for d in data7:
        totalRooms += int(d['count'])

    rates = []

    tfoc = False
    tfoc1 = 0
    tfoc2 = 0
    foc = []
    if (data['foc'] != 0):
        tfoc = True
        tfoc1 = data['foc1']
        tfoc2 = data['foc2']

    mmp = 1
    for i in range(0, int(nights)):
        tempResult = []
        cursor.execute('SELECT * FROM request1Bed where date = %s AND id = %s && hotelId = %s', [curr_date, token, hotelId])
        resultPerDay1 = cursor.fetchall()

        roomsToBook = 0
        for r in resultPerDay1:
            if (len(r) != 0):
                dateToCheck = curr_date.strftime('%Y-%m-%d')
                


                day = curr_date.strftime('%A')
                day = day.lower()
                query = "SELECT * FROM rate where (type = %s  AND (startDate <= %s AND endDate >= %s) AND {} = 1 AND hotelId = %s)".format(day)
                cursor.execute(query, ['1', dateToCheck, dateToCheck, hotelId])
                pent = cursor.fetchall()
                if (len(pent) == 0):
                    r['rate'] = -1
                    mmp = 0
                else:
                    if r['occupancy'] == 'Single':
                        r['rate'] = pent[0]['sor']
                    elif r['occupancy'] == 'Double':
                        r['rate'] = pent[0]['dor']
                    elif r['occupancy'] == 'Triple':
                        r['rate'] = pent[0]['tor']
                    elif r['occupancy'] == 'Quad':
                        r['rate'] = pent[0]['qor']
                
                r['type'] = '1 Bed'
                tempResult.append(r)
                roomsToBook += int(r['count'])
        
        cursor.execute(
            'SELECT * FROM request2Bed where date = %s AND id = %s  && hotelId = %s', [curr_date, token, hotelId])
        resultPerDay2 = cursor.fetchall()
        for r in resultPerDay2:
            if (len(r) != 0):
                dateToCheck = curr_date.strftime('%Y-%m-%d')
                day = curr_date.strftime('%A')
                day = day.lower()
                query = "SELECT * FROM rate where (type = %s  AND (startDate <= %s AND endDate >= %s) AND {} = 1 AND hotelId = %s)".format(
                    day)
                cursor.execute(query, ['2', dateToCheck, dateToCheck, hotelId])
                pent = cursor.fetchall()
                if (len(pent) == 0):
                    r['rate'] = -1
                    mmp = 0
                else:
                    if r['occupancy'] == 'Single':
                        r['rate'] = pent[0]['sor']
                    elif r['occupancy'] == 'Double':
                        r['rate'] = pent[0]['dor']
                    elif r['occupancy'] == 'Triple':
                        r['rate'] = pent[0]['tor']
                    elif r['occupancy'] == 'Quad':
                        r['rate'] = pent[0]['qor']
                r['type'] = '2 Bed'

                tempResult.append(r)
                roomsToBook += int(r['count'])
        
        if (tfoc):
            if (tfoc1 != '0'):
                r = {}
                dateToCheck = curr_date.strftime('%Y-%m-%d')
                day = curr_date.strftime('%A')
                day = day.lower()
                query = "SELECT * FROM rate where (type = %s  AND (startDate <= %s AND endDate >= %s) AND {} = 1 AND hotelId = %s)".format(
                    day)
                cursor.execute(query, ['1', dateToCheck, dateToCheck, hotelId])
                pent = cursor.fetchall()
                r['foc1'] = tfoc1
                r['type'] = 'FOC'
                r['occupancy'] = 'Single'
                r['count'] = tfoc1
                if (len(pent) == 0):
                    r['rate'] = -1
                else:
                    r['rate'] = pent[0]['sor']
                foc.append(r)
                tempResult.append(r)
                roomsToBook += int(tfoc1)
            if (tfoc2 != '0'):
                r = {}
                dateToCheck = curr_date.strftime('%Y-%m-%d')
                day = curr_date.strftime('%A')
                day = day.lower()
                query = "SELECT * FROM rate where (type = %s  AND (startDate <= %s AND endDate >= %s) AND {} = 1 AND hotelID = %s)".format(
                    day)
                cursor.execute(query, ['2', dateToCheck, dateToCheck, hotelId])
                pent = cursor.fetchall()
                r['foc2'] = tfoc2
                r['type'] = 'FOC'
                r['occupancy'] = 'Double'
                r['count'] = tfoc2

                if (len(pent) == 0):
                    r['rate'] = -1
                else:
                    r['rate'] = pent[0]['dor']
                
                foc.append(r)
                tempResult.append(r)
                roomsToBook += int(tfoc2)
    
            
    

        dateToCheck = curr_date.strftime('%Y-%m-%d')
        occ = request.form.get(str(curr_date))
        if occ == None:
            occs.append("-")
            cursor.execute('SELECT policyName from autopilot where startDate <= %s AND endDate >= %s AND active = 1 AND policy = "manual" && hotelId = %s', [curr_date, curr_date, hotelId])
            pn = cursor.fetchall()
            if len(pn) != 0:
                discounts.append("0" + " (AutoPilot ID: " + pn[0]['policyName'] + ")")
            else:
                discounts.append('0' + "(Not OCC)")
            for t in tempResult:
                rates.append({'val': -1, 'count': t['count'], 'type' : 'no'})
                t['rate'] = -1
        else:
            occ = int(occ)
            pam = occ * totalRooms//100
            occs.append(str(occ) + "  (" + str(pam) + " Rooms   )")
            pam = pam + 1

            minDiscountVal = 101
            glid = 0
            cursor.execute('SELECT discountId, defaultm from discountMap where startDate <= %s AND endDate >= %s AND active = 1 && hotelId = %s', [dateToCheck, dateToCheck, hotelId])
            di = cursor.fetchall()

            if len(di) == 0:
                discounts.append('0' + "(No Discount Grid)")
            else:
                if len(di) == 1:
                    id = di[0]['discountId']
                elif len(di) == 2:
                    for l in di:
                        if (l['defaultm'] == 0):
                            id = l['discountId']
                            break
                for rv in range(pam, roomsToBook + pam):
                    cursor.execute('SELECT * from discount where discountId = %s AND (leadMin <= %s && leadMax >= %s) AND (roomMin <= %s && roomMax >= %s && hotelId = %s)', [id, lead, lead, rv, rv, hotelId])
                    dd = cursor.fetchall()
                    if len(dd) == 0:
                        discounts.append('0' + "(No Grid Fits)")
                    else:
                        glid = id
                        if dd[0]['value'] == '' or dd[0]['value'] == ' ':
                            dd[0]['value'] = '0'
                        dd[0]['value'] == dd[0]['value'].strip()
                        minDiscountVal = min(minDiscountVal, float(dd[0]['value']))
                
                discounts.append(str(minDiscountVal) + " ( ID : " + str(glid) + " )")

            for t in tempResult:
                te = int(t['rate'])
                if (te == -1):
                    rates.append({'val': -1, 'count': t['count'], 'type' : 'no'})
                else:
                    if minDiscountVal == 101:
                        minDiscountVal = 0
                    val = te - (minDiscountVal * te)/100
                    rates.append({'val': val, 'count': t['count'], 'type': t['type']})
                    t['rate'] = str(val) + " (Evaluated Rate : " + str(val) + "[" + str(te) + "] )"
         

        lead = lead + 1

        dates.append(curr_date.strftime('%A : %d %b, %Y'))

    
        result.append(tempResult)
    
        curr_date = curr_date + datetime.timedelta(days = 1)


    focv = 0
    for r in rates:
        if r['type'] == 'FOC':
            focv += int(r['count']) * r['val']

    totalRate = 0
    for d in rates:
        if (d['val'] == -1 or d['type'] == 'FOC'):
            totalRate += 0
        else:
            totalRate += int(d['count']) * d['val']

    focv = float(round(focv, 2))
    totalRate = float(round(totalRate, 2))
    totalQuote = totalRate
    tcomm = False
    tcommv = 0


    comP = 0
    if (data['commissionable'] != '0'):
        vv = (totalRate * float(data['commissionable'])) / 100
        comP = data['commissionable']
        totalQuote += vv
        tcomm = True
        tcommv = vv


    tcommv = float(round(tcommv, 2))

    totalQuote += focv
    totalQuote = int(round(totalQuote))

    roomCount = 0

    single1 = []
    single2 = []
    double1 = []
    double2 = []
    triple1 = []
    triple2 = []
    quad1 = []
    quad2 = []

    single1c = 0
    single2c = 0
    double1c = 0
    double2c = 0
    triple1c = 0
    triple2c = 0
    quad1c = 0
    quad2c = 0
    foc1c = 0
    foc2c = 0
    
    single1f = False
    double1f = False
    triple1f = False
    quad1f = False 
    single2f = False
    double2f = False
    triple2f = False
    quad2f = False 
        

    foc1 = 0
    foc2 = 0


    for r in result:
        for m in r:
            if (m['type'] != 'FOC'):
                roomCount += int(m['count'])
            if (m['type'] == '1 Bed'):
                if (m['occupancy'] == 'Single'):
                    if (m['rate'] != -1):
                        s = m['rate'].split(' (')
                        v = float(s[0]) * int(m['count'])
                        single1.append(v)
                    single1c = single1c + int(m['count'])
                    single1f = True
                elif (m['occupancy'] == 'Double'):
                    if (m['rate'] != -1):
                        s = m['rate'].split(' (')
                        v = float(s[0]) * int(m['count'])
                        double1.append(v)
                    double1c = double1c + int(m['count'])
                    double1f = True
                elif (m['occupancy'] == 'Triple'):
                    if (m['rate'] != -1):
                        s = m['rate'].split(' (')
                        v = float(s[0]) * int(m['count'])
                        triple1.append(v)
                    triple1c = triple1c + int(m['count'])
                    triple1f = True
                elif (m['occupancy'] == 'Quad'):
                    if (m['rate'] != -1):
                        s = m['rate'].split(' (')
                        v = float(s[0]) * int(m['count'])
                        quad1.append(v)
                    quad1c = quad1c + int(m['count'])
                    quad1f = True
            elif (m['type'] == '2 Bed'):
                if (m['occupancy'] == 'Single'):
                    if (m['rate'] != -1):
                        s = m['rate'].split(' (')
                        v = float(s[0]) * int(m['count'])
                        single2.append(v)
                    single2c = single2c + int(m['count'])
                    single2f = True
                elif (m['occupancy'] == 'Double'):
                    if (m['rate'] != -1):
                        s = m['rate'].split(' (')
                        v = float(s[0]) * int(m['count'])
                        double2.append(v)
                    double2c = double2c + int(m['count'])
                    double2f = True
                elif (m['occupancy'] == 'Triple'):
                    if (m['rate'] != -1):
                        s = m['rate'].split(' (')
                        v = float(s[0]) * int(m['count'])
                        triple2.append(v)
                    triple2c = triple2c + int(m['count'])
                    triple2f = True
                elif (m['occupancy'] == 'Quad'):
                    if (m['rate'] != -1):
                        s = m['rate'].split(' (')
                        v = float(s[0]) * int(m['count'])
                        quad2.append(v)
                    quad2c = quad2c + int(m['count'])
                    quad2f = True
            elif (m['type'] == 'FOC'):
                if (m['occupancy'] == 'Single'):
                    if (m['rate'] != -1):
                        s = m['rate'].split(' (')
                        v = float(s[0]) * int(m['count'])
                        foc1 += float(v)
                    foc1c = int(m['count'])
                elif (m['occupancy'] == 'Double'):
                    if (m['rate'] != -1):
                        s = m['rate'].split(' (')
                        v = float(s[0]) * int(m['count'])
                        foc2 += float(v)
                    foc2c = int(m['count'])


    foc1 = foc1 / roomCount
    foc2 = foc2 / roomCount
    tcommparts = tcommv / roomCount

    le = single1c
    single1avg = 0
    if (le != 0):
        sum = 0
        for s in single1:
            sum += float(s)
        single1avg = sum / le
        single1avg = single1avg + foc1 + foc2 + tcommparts

    le = single2c
    single2avg = 0
    if (le != 0):
        sum = 0
        for s in single2:
            sum += float(s)
        single2avg = sum / le

        single2avg = single2avg + foc1 + foc2 + tcommparts
    

    le = double1c
    double1avg = 0
    if (le != 0):
        sum = 0
        for s in double1:
            sum += float(s)
        double1avg = sum / le

        double1avg = double1avg + foc1 + foc2 + tcommparts

    le = double2c
    double2avg = 0
    if (le != 0):
        sum = 0
        for s in double2:
            sum += float(s)
        double2avg = sum / le

        double2avg = double2avg + foc1 + foc2 + tcommparts

    le = triple1c
    triple1avg = 0
    if (le != 0):
        sum = 0
        for s in triple1:
            sum += float(s)
        triple1avg = sum / le

        triple1avg = triple1avg + foc1 + foc2 + tcommparts

    le = triple2c
    triple2avg = 0
    if (le != 0):
        sum = 0
        for s in triple2:
            sum += float(s)
        triple2avg = sum / le

        triple2avg = triple2avg + foc1 + foc2 + tcommparts

    le = quad1c
    quad1avg = 0
    if (le != 0):
        sum = 0
        for s in quad1:
            sum += float(s)
        quad1avg = sum / le

        quad1avg = quad1avg + foc1 + foc2 + tcommparts

    le = quad2c
    quad2avg = 0
    if (le != 0):
        sum = 0
        for s in quad2:
            sum += float(s)
        quad2avg = sum / le

        quad2avg = quad2avg + foc1 + foc2 + tcommparts

    # add foc to all equally

    

    single1avg = round(single1avg, 2)
    double1avg = round(double1avg, 2)
    triple1avg = round(triple1avg, 2)
    quad1avg = round(quad1avg, 2)
    single2avg = round(single2avg, 2)
    double2avg = round(double2avg, 2)
    triple2avg = round(triple2avg, 2)
    quad2avg = round(quad2avg, 2)

    avgRate = str(round(totalQuote/roomCount, 2))

    email = session['email']
    cursor.execute('SELECT userType from hotelUsers where email = %s && hotelId = %s', [email, hotelId])
    ut = cursor.fetchall()
    review = True
    if len(ut) != 0:
        ut = ut[0]
        if (ut['userType'] == "hotelAdmin" or ut['userType'] == "revenue"):
            review = False

    cursor.execute('SELECT * from contract where hotelId = %s', [hotelId])
    contracts = cursor.fetchall()

    cursor.execute('SELECT * From room where hotelId = %s', [hotelId])
    roomData = cursor.fetchall()

    negoF = False
    fop = ''
    pt = ''
    cursor.execute('SELECT * From response where requestId = %s  && hotelId = %s order by submittedOn desc limit 1', [token, hotelId])
    responseData = cursor.fetchall()
    if len(responseData) == 0:
        cursor.execute('SELECT count from settingsNegotiation  where hotelId = %s order by submittedOn desc', [hotelId])
        nego = cursor.fetchall()
        if len(nego) != 0:
            nego = nego[0]
            if (int(nego['count']) > 0):
                negoF = True
    else:
        cursor.execute('SELECT * from response where requestId = %s &&status = %s  && hotelId = %s', [token, statusval3, hotelId])
        negoTime = cursor.fetchall()
        negoTimes = len(negoTime)
        cursor.execute('SELECT count from settingsNegotiation  where hotelId = %s order by submittedOn desc', [hotelId])
        count = cursor.fetchall()
        if len(count) != 0:
            count = count[0]['count']
        else:
            count = 100
        if (int(negoTimes) < int(count)):
            negoF = True

        responseData = responseData[0]
        string = ''
        fop = responseData['formPayment']
        responseData['formPayment'] = procArr2(responseData['formPayment'])

        string = ''
        v = responseData['paymentTerms']
        pt = responseData['paymentTerms']
        if v != None:
            if v.count('pc') > 0:
                string = 'Post Checkout'
                responseData['paymentTerms'] = string
            elif v.count('ac') > 0:
                responseData['paymentTerms'] = 'At Checkout'
            elif v.count('poa') > 0:
                responseData['paymentTerms'] = 'Prior To Arrival'


    # get right side values

    if (mmp == 0):
        flash('No Rate Grid available (No OCC applicable as discount grid for this date range is not set)!', 'danger')
    return render_template('request/requestProcess.html', data = data, result = result, length = len(result), dates = dates, discounts = discounts, occs = occs, totalRate = totalRate, avgRate = avgRate, tcomm = tcomm, tcommv = tcommv, totalQuote = totalQuote, tfoc = tfoc, focv = focv, comP = comP, roomCount = roomCount, checkIn = checkIn, checkOut = checkOut, single1avg = single1avg, single2avg = single2avg, double1avg = double1avg, double2avg = double2avg, triple1avg = triple1avg, triple2avg = triple2avg, quad1avg = quad1avg, quad2avg = quad2avg, single1f = single1f, double1f = double1f, triple1f = triple1f, quad1f = quad1f, single2f = single2f, double2f = double2f, triple2f = triple2f, quad2f = quad2f, single1c = single1c, double1c = double1c, triple1c = triple1c, quad1c = quad1c, single2c = single2c, double2c = double2c, triple2c = triple2c, quad2c = quad2c, foc1 = foc1, foc2 = foc2, review = review, rvflag = rvflag, rvvv = rvvv, contracts = contracts, negoF = negoF, roomData = roomData, responseData = responseData, fop = fop, pt = pt)


@app.route('/requestProcessDecline', methods=['GET', 'POST'])
@is_logged_in
def requestProcessDecline():
    inp = request.json
    cursor = mysql.connection.cursor()
    responseId = inp['requestId'] + "R"
    email = session['email']
    now = datetime.datetime.utcnow()
    hotelId = session.get('hotelId')
    status = statusval8
    cursor.execute('INSERT INTO response(requestId, responseId, groupCategory, totalFare, foc, commission, commissionValue, totalQuote, cutoffDays, formPayment, paymentTerms, paymentGtd, negotiable, checkIn, checkOut, submittedBy, submittedOn, status, paymentDays, nights, comments, averageRate, contract, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
        inp['requestId'], responseId, inp['groupCategory'], inp['totalFare'], inp['foc'], str(inp['commission']), str(inp['commissionValue']), inp['totalQuote'], inp['cutoffDays'], procArr(
            inp['formPayment']), inp['paymentTerms'], inp['paymentGtd'], inp['negotiable'], inp['checkIn'], inp['checkOut'], email, now,
        status, inp['paymentDays'], inp['nights'], inp['comments'],
        inp['averageRate'], inp['contract'], hotelId
    ])

    table = inp['table_result']
    for t in table:
        cursor.execute('INSERT INTO responseDaywise(date, currentOcc, discountId, occupancy, type, count, ratePerRoom, responseId, forecast, leadTime, groups, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
            t['date'], t['currentOcc'], t['discountId'], t['occupancy'], t['type'], t[
                'count'], t['ratePerRoom'], responseId, t['forecast'], t['leadTime'], t['groups'], now, hotelId
        ])

    cursor.execute('INSERT INTO responseAvg(single1, single2, double1, double2, triple1, triple2, quad1, quad2, responseId, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
        inp['single1'], inp['single2'], inp['double1'], inp['double2'], inp['triple1'], inp['triple2'], inp['quad1'], inp['quad2'], responseId, now, hotelId
    ])

    cursor.execute(
        'UPDATE request set status = %s where id = %s && hotelId = %s', [statusval8, inp['requestId'], hotelId])
    cursor.execute(
        'UPDATE response set status = %s where requestId = %s && hotelId = %s order by submittedOn desc limit 1', [statusval8, inp['requestId'], hotelId])

    now = datetime.datetime.utcnow()
    email = session['email']
    cursor.execute("INSERT INTO DeclineRequest(requestId, time, reason, declinedBy, hotelId) VALUES(%s, %s, %s, %s, %s) ", [
        inp['requestId'], now, inp['reason'], email, hotelId])

    mysql.connection.commit()

    flash('The request has been declined', 'success')
    return ('', 204)



@app.route('/requestProcessQuote', methods = ['GET', 'POST'])
@is_logged_in
def requestProcessQuote():
    inp = request.json
    cursor = mysql.connection.cursor()
    responseId = inp['requestId'] + "R"
    email = session['email']
    now = datetime.datetime.utcnow()
    status = statusval2
    hotelId = session.get('hotelId')

    cursor.execute('SELECT days from settingsTimelimit where hotelId = %s', [hotelId])
    days = cursor.fetchall()
    endline = datetime.datetime.now().date() + datetime.timedelta(days = 99)
    if len(days) != 0:
        days = days[0]
        days = int(days['days'])
        endline = datetime.datetime.now().date() + datetime.timedelta(days = days)
        endline = datetime.datetime.combine(endline, datetime.datetime.min.time())
        endline = endline + datetime.timedelta(hours = 23, minutes = 59)

    table = inp['table_result']
    check_final = False
    for t in table:
        cursor.execute('INSERT INTO responseDaywise(date, currentOcc, discountId, occupancy, type, count, ratePerRoom, responseId, forecast, leadTime, groups, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
            t['date'], t['currentOcc'], t['discountId'], t['occupancy'], t['type'], t['count'], t['ratePerRoom'], responseId, t['forecast'], t['leadTime'], t['groups'], now, hotelId
        ])
        check = checkOverride(t['ratePerRoom'])
        if(check == True):
            check_final = True
    
    if (check_final == True):
        check_final = 1
    else:
        check_final = 0

    cursor.execute('INSERT INTO response(requestId, responseId, groupCategory, totalFare, foc, commission, commissionValue, totalQuote, cutoffDays, formPayment, paymentTerms, paymentGtd, negotiable, checkIn, checkOut, submittedBy, submittedOn, status, paymentDays, nights, comments, averageRate, contract, expiryTime, overrideReason, overrideFlag, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' , [
        inp['requestId'], responseId, inp['groupCategory'], inp['totalFare'], inp['foc'], str(inp['commission']), str(inp['commissionValue']), inp['totalQuote'], inp['cutoffDays'], procArr(inp['formPayment']), inp['paymentTerms'], inp['paymentGtd'], inp['negotiable'], inp['checkIn'], inp['checkOut'], email, now,
        status, inp['paymentDays'], inp['nights'], inp['comments'],
        inp['averageRate'], inp['contract'], endline, inp['overres'], check_final, hotelId
    ])
    
    cursor.execute("UPDATE request SET status = %s WHERE id = %s && hotelId = %s", [statusval2, inp['requestId'], hotelId])

    cursor.execute('UPDATE response set status = %s where requestId = %s && hotelId = %s order by submittedOn desc limit 1', [statusval2, inp['requestId'], hotelId]
        )

    cursor.execute('INSERT INTO responseAvg(single1, single2, double1, double2, triple1, triple2, quad1, quad2, responseId, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' , [
        inp['single1'], inp['single2'], inp['double1'], inp['double2'], inp['triple1'], inp['triple2'], inp['quad1'], inp['quad2'], responseId, now, hotelId
    ])
    
    mysql.connection.commit()
    cursor.execute('SELECT createdFor from request where id = %s && hotelId = %s', [inp['requestId'], hotelId])
    createdFor = cursor.fetchall()
    createdFor = createdFor[0]['createdFor']

    token = generateConfirmationToken(inp['requestId'])
    sendMailQ(
        subjectv = 'The Row Hotel(TR1101) - Group Rates',
        recipientsv=createdFor,
        linkv = 'showQuoteEmail',
        tokenv = token,
        bodyv = 'Please Do Not Reply to this email, \n Hello, \n\n You have recieved a response to your group rate enquiry.',
    )

    
    

    flash('The request has been quoted', 'success')
    return ('', 204)


@app.route('/showQuote/<id>', methods = ['GET', 'POST'])
@is_logged_in
def showQuote(id):
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * From request where id = %s && hotelId = %s', [id, hotelId])
    data = cursor.fetchall()
    data = data[0]

    data['createdOn'] = data['createdOn'].strftime("%d %b ,%y, %H:%M:%S")
    string = ''
    v = data['paymentTerms']
    if v != None:
        if v.count('pc') > 0:
            string = 'Post Checkout'
            data['paymentTerms'] = string
        elif v.count('ac') > 0:
            data['paymentTerms'] = 'At Checkout'
        elif v.count('poa') > 0:
            data['paymentTerms'] = 'Prior To Arrival'

    string = ''

    data['formPayment'] = procArr2(data['formPayment'])

    if data['comments'].isspace():
        data['comments'] = ''

    responseId = data['id'] + "R"
    cursor.execute(
        'SELECT * From response where responseId = %s && hotelId = %s order by submittedOn desc limit 1', [responseId, hotelId])
    data2 = cursor.fetchall()
    data2 = data2[0]
    negcheck = data2['negotiable']
    if negcheck == 0:
        negcheck = False
    else:
        negcheck = True

    string = ''
    v = data2['formPayment']
    data2['formPayment'] = procArr2(data2['formPayment'])

    string = ''
    v = data2['paymentTerms']
    if v != None:
        if v.count('pc') > 0:
            string = 'Post Checkout'
            data2['paymentTerms'] = string
        elif v.count('ac') > 0:
            data2['paymentTerms'] = 'At Checkout'
        elif v.count('poa') > 0:
            data2['paymentTerms'] = 'Prior To Arrival'
    
    cursor.execute(
        'SELECT * From responseAvg where responseId = %s && hotelId = %s order by submittedOn desc limit 1', [responseId, hotelId])
    data3 = cursor.fetchall()
    data3 = data3[0]

    result = {}
    cursor.execute('SELECT * From request1Bed where id = %s && hotelId = %s', [id, hotelId])
    temp1 = cursor.fetchall()
    for t in temp1:
        result[t['date']] = []

    cursor.execute('SELECT * From request2Bed where id = %s && hotelId = %s', [id, hotelId])
    temp2 = cursor.fetchall()
    for t in temp2:
        result[t['date']] = []

    totalRooms = 0
    for t in temp1:
        tArr = {}
        tArr['type'] = '1 Bed'
        tArr['occupancy'] = t['occupancy']
        tArr['count'] = t['count']
        totalRooms += int(t['count'])
        result[t['date']].append(tArr)
    
    for t in temp2:
        tArr = {}
        tArr['type'] = '2 Bed'
        tArr['occupancy'] = t['occupancy']
        tArr['count'] = t['count']
        totalRooms += int(t['count'])
        result[t['date']].append(tArr)

    dateButtons = result.keys()
    
    secondresult = result
    for r,v in secondresult.items():
        for row in v:
            type1 = row['type'].split(' ')[0]
            occupancy = row['occupancy'].lower()
            count = row['count']
            if data['status'] == statusval8:
                row['ratePerRoom'] = "-"
                row['total'] = "-"
            else:
                search = occupancy + type1
                query = "SELECT {} from responseAvg where responseId = %s && hotelId = %s".format(search)
                cursor.execute(query, [responseId, hotelId])
                sv = cursor.fetchall()
                row['ratePerRoom'] = sv[0][search]
                row['total'] = float(row['ratePerRoom']) * int(row['count'])

    if data['foc'] != 0:
        for key in secondresult:
            row1 = {}
            row2 = {}
            row1['type'] = 'FOC'
            if data['foc1'] != '0':
                row1['count'] = data['foc1']
                totalRooms += int(data['foc1'])
                row1['occupancy'] = 'Single'
                row1['ratePerRoom'] = "-"
                row1['total'] = "-"
                secondresult[key].append(row1)
            if data['foc2'] != '0':
                row2['count'] = data['foc2']
                totalRooms += int(data['foc1'])
                row2['occupancy'] = 'Double'
                row2['ratePerRoom'] = "-"
                row2['total'] = "-"
                secondresult[key].append(row2)


    data5 = []
    if data2['status'] == statusval4:
        cursor.execute('SELECT * from requestAccepted where requestId = %s && hotelId = %s', [id, hotelId])
        data5 = cursor.fetchall()
        data5 = data5[0]
        temp1 = data5['time'].strftime('%y-%b-%d')
        x = temp1.split('-')
        data5['time'] = x[2] + " " + x[1] + ", " + x[0]
        
    
    data6 = []
    if (data2['status'] == statusval5 or data2['status'] == statusval8):
        cursor.execute("SELECT * From DeclineRequest where requestId = %s && hotelId = %s", [id, hotelId])
        data6 = cursor.fetchall()
        data6 = data6[0]
        temp1 = data6['time'].strftime('%y-%b-%d')
        x = temp1.split('-')
        data6['time'] = x[2] + " " + x[1] + ", " + x[0]

    data9 = []
    if (data2['status'] == statusval10):
        cursor.execute('SELECT * From confirmRequest where requestId = %s && hotelId = %s', [id, hotelId])
        data9 = cursor.fetchall()
        data9 = data9[0]
        temp1 = data9['submittedOn'].strftime('%y-%b-%d')
        x = temp1.split('-')
        data9['submittedOn'] = x[2] + " " + x[1] + ", " + x[0]

    data10 = []
    if (data2['status'] == statusval11):
        cursor.execute('SELECT * From notConfirmRequest where requestId = %s && hotelId = %s', [id, hotelId])
        data10 = cursor.fetchall()
        data10 = data10[0]
        temp1 = data10['submittedOn'].strftime('%y-%b-%d')
        x = temp1.split('-')
        data10['submittedOn'] = x[2] + " " + x[1] + ", " + x[0]



    declined = False
    declinedMsg = ""
    endline = 0
    if (data['status'] == statusval2):
        endline = data2['expiryTime']
        if (endline != None):
            today = datetime.datetime.now()
            if (today > endline):
                cursor.execute(
                    'UPDATE request set status = %s where id = %s && hotelId = %s', [statusval9, data['id'], hotelId])
                cursor.execute(
                                'SELECT * from response where requestId = %s && hotelId = %s order by submittedOn desc limit 1', [data['id'], hotelId])
                email = session['email']
                now = datetime.datetime.utcnow()
                prevresponse = cursor.fetchall()

                if len(prevresponse) != 0:
                    prevresponse = prevresponse[0]
                    cursor.execute('INSERT INTO response(requestId, responseId, groupCategory, totalFare, foc, commission, commissionValue, totalQuote, cutoffDays, formPayment, paymentTerms, paymentGtd, negotiable, checkIn, checkOut, submittedBy, submittedOn, status, paymentDays, nights, comments, averageRate, contract, expectedFare, negotiationReason, timesNegotiated, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                        prevresponse['requestId'], prevresponse['responseId'], prevresponse['groupCategory'], prevresponse['totalFare'], prevresponse[
                            'foc'], prevresponse['commission'], prevresponse['commissionValue'], prevresponse['totalQuote'], prevresponse['cutoffDays'],
                        prevresponse['formPayment'], prevresponse['paymentTerms'], prevresponse['paymentGtd'], prevresponse[
                            'negotiable'], prevresponse['checkIn'], prevresponse['checkOut'], email, now,
                        statusval9, prevresponse['paymentDays'], prevresponse['nights'], prevresponse['comments'],
                        prevresponse['averageRate'], prevresponse['contract'], prevresponse['expectedFare'], prevresponse['negotiationReason'], prevresponse['timesNegotiated'], hotelId
                    ])

                    cursor.execute(
                        'SELECT * From responseAvg where responseId = %s && hotelId = %s order by submittedOn desc limit 1', [prevresponse['responseId'], hotelId])
                    prevAvg = cursor.fetchall()
                    if len(prevAvg) != 0:
                        prevAvg = prevAvg[0]
                        cursor.execute('INSERT INTO responseAvg(single1, single2, double1, double2, triple1, triple2, quad1, quad2, responseId, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                            prevAvg['single1'], prevAvg['single2'], prevAvg['double1'], prevAvg['double2'], prevAvg[
                                'triple1'], prevAvg['triple2'], prevAvg['quad1'], prevAvg['quad2'], prevAvg['responseId'], now, hotelId
                        ])

                    cursor.execute(
                        'SELECT submittedOn from responseDaywise where responseId = %s && hotelId = %s order by submittedOn desc limit 1', [prevAvg['responseId'], hotelId])
                    submittedOn = cursor.fetchall()
                    cursor.execute('SELECT * From responseDaywise where responseId = %s and submittedOn = %s && hotelId = %s',
                                [prevAvg['responseId'], submittedOn[0]['submittedOn'], hotelId])

                    prevDaywise = cursor.fetchall()
                    if len(prevDaywise) != 0:
                        for p in prevDaywise:
                            cursor.execute('INSERT INTO responseDaywise(date, currentOcc, discountId, occupancy, type, count, ratePerRoom, responseId, forecast, leadTime, groups, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                                p['date'], p['currentOcc'], p['discountId'], p['occupancy'], p['type'], p[
                                    'count'], p['ratePerRoom'], prevAvg['responseId'], p['forecast'], p['leadTime'], p['groups'], now, hotelId
                            ])        
                
                    cursor.execute(
                        'UPDATE response set status = %s where requestId = %s && hotelId = %s order by submittedOn desc limit 1', [statusval9, data['id'], hotelId])              
                mysql.connection.commit()
                declined = True
                declinedMsg = "Time limit expired"
                data['status'] = statusval9
                data2['status'] = statusval9
        

            temp1 = endline.strftime('%y-%b-%d, %H:%M:%S')
            x = temp1.split('-')
            endline = x[2].split(",")[0] + " " + x[1] + "," + x[0] + " " + x[2].split(",")[1]


    cursor.execute('select count from settingsNegotiation where hotelId = %s', [hotelId])
    count = cursor.fetchall()
    if len(count) != 0:
        count = count[0]['count']
    else:
        count = 100 # no hard limit so
    cursor.execute('SELECT * from response where responseId = %s and status = %s && hotelId = %s', [responseId, statusval3, hotelId])
    negoTime = cursor.fetchall()
    negoTimes = len(negoTime)
    nego = False
    negoInformation = {}
    canNegotiate = False
    if (int(negoTimes) <= int(count)):
        canNegotiate = True
    negoInformation['expectedFare'] = data2['expectedFare']
    negoInformation['reason'] = data2['negotiationReason']

    canNegotiate = canNegotiate and negcheck

    cursor.execute('SELECT contract, id from contract where id = %s && hotelId = %s', [
                   data2['contract'], hotelId])
    contract = cursor.fetchall()

    if (data2['cutoffDays'] != None and data2['cutoffDays'] != ''):
        cutoff = data2['submittedOn'] + datetime.timedelta(days = int(data2['cutoffDays']))
        temp1 = cutoff.strftime('%y-%b-%d, %H:%M:%S')
        x = temp1.split('-')
        cutoff = x[2].split(",")[0] + " " + x[1] + "," + x[0] + " " + x[2].split(",")[1]
        data2['cutoffDays'] = cutoff


    temp1 = data2['submittedOn'].strftime('%y-%b-%d, %H:%M:%S')
    x = temp1.split('-')
    data2['submittedOn'] = x[2].split(",")[0] + " " + x[1] + "," + x[0] + " " + x[2].split(",")[1]



    temp1 = data['checkIn'].strftime('%y-%b-%d')
    x = temp1.split('-')
    data['checkIn'] = x[2] + " " + x[1] + ", " + x[0]

    temp1 = data['checkOut'].strftime('%y-%b-%d')
    x = temp1.split('-')
    data['checkOut'] = x[2] + " " + x[1] + ", " + x[0]
    
    for d in list(dateButtons):
        y = d
        temp1 = d.strftime('%Y-%b-%d-%A')
        x = temp1.split('-')
        d = x[3] + " : " + x[2] + " " + x[1] + "," + x[0]
        result[d] = result[y]
        del result[y]
    
    dateButtons = result.keys()

    avgRate = int(data2['totalQuote']) / int(totalRooms)
    avgRate = round(avgRate, 2)



    return render_template('request/showQuote.html', data = data, data2 = data2, data3 = data3, dateButtons = dateButtons, result = result, secondresult = secondresult, data5 = data5, data6 = data6, contract = contract, declined = declined, declinedMsg = declinedMsg, canNegotiate = canNegotiate, negoInformation = negoInformation, data9 = data9, data10 = data10, endline = endline, totalRooms = totalRooms, customer = False, avgRate = avgRate)

@app.route('/showQuoteEmail/<id>', methods = ['GET', 'POST'])
def showQuoteEmail(id):
    id = confirmToken(id)
    if (id == False):
        flash('Unverified', 'danger')
        return render_template('login.html', title = 'Login')
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * From request where id = %s && hotelId = %s', [id, hotelId])
    data = cursor.fetchall()
    data = data[0]

    data['createdOn'] = data['createdOn'].strftime("%d %b ,%y, %H:%M:%S")
    string = ''
    v = data['paymentTerms']
    if v != None:
        if v.count('pc') > 0:
            string = 'Post Checkout'
            data['paymentTerms'] = string
        elif v.count('ac') > 0:
            data['paymentTerms'] = 'At Checkout'
        elif v.count('poa') > 0:
            data['paymentTerms'] = 'Prior To Arrival'

    string = ''
    data['formPayment'] = procArr2(data['formPayment'])
    if data['comments'].isspace():
        data['comments'] = ''

    responseId = data['id'] + "R"
    cursor.execute(
        'SELECT * From response where responseId = %s  && hotelId = %s order by submittedOn desc limit 1', [responseId, hotelId])
    data2 = cursor.fetchall()
    data2 = data2[0]
    negcheck = data2['negotiable']
    if negcheck == 0:
        negcheck = False
    else:
        negcheck = True

    string = ''
    data2['formPayment'] = data2['formPayment']
    string = ''
    v = data2['paymentTerms']
    if v != None:
        if v.count('pc') > 0:
            string = 'Post Checkout'
            data2['paymentTerms'] = string
        elif v.count('ac') > 0:
            data2['paymentTerms'] = 'At Checkout'
        elif v.count('poa') > 0:
            data2['paymentTerms'] = 'Prior To Arrival'
    
    cursor.execute(
        'SELECT * From responseAvg where responseId = %s  && hotelId = %s order by submittedOn desc limit 1', [responseId, hotelId])
    data3 = cursor.fetchall()
    data3 = data3[0]

    result = {}
    cursor.execute('SELECT * From request1Bed where id = %s  && hotelId = %s', [id, hotelId])
    temp1 = cursor.fetchall()
    for t in temp1:
        result[t['date']] = []

    cursor.execute('SELECT * From request2Bed where id = %s  && hotelId = %s', [id, hotelId])
    temp2 = cursor.fetchall()
    for t in temp2:
        result[t['date']] = []

    totalRooms = 0
    for t in temp1:
        tArr = {}
        tArr['type'] = '1 Bed'
        tArr['occupancy'] = t['occupancy']
        tArr['count'] = t['count']
        totalRooms += int(t['count'])
        result[t['date']].append(tArr)
    
    for t in temp2:
        tArr = {}
        tArr['type'] = '2 Bed'
        tArr['occupancy'] = t['occupancy']
        tArr['count'] = t['count']
        totalRooms += int(t['count'])
        result[t['date']].append(tArr)

    dateButtons = result.keys()
    
    secondresult = result
    for r,v in secondresult.items():
        for row in v:
            type1 = row['type'].split(' ')[0]
            occupancy = row['occupancy'].lower()
            count = row['count']
            if data['status'] == statusval8:
                row['ratePerRoom'] = "-"
                row['total'] = "-"
            else:
                search = occupancy + type1
                query = "SELECT {} from responseAvg where responseId = %s  && hotelId = %s".format(search)
                cursor.execute(query, [responseId, hotelId])
                sv = cursor.fetchall()
                row['ratePerRoom'] = sv[0][search]
                row['total'] = float(row['ratePerRoom']) * int(row['count'])

    if data['foc'] != 0:
        for key in secondresult:
            row1 = {}
            row2 = {}
            row1['type'] = 'foc'
            row2['type'] = 'foc'
            if data['foc1'] != '0':
                row1['count'] = data['foc1']
                totalRooms += int(data['foc1'])
                row1['occupancy'] = 'Single'
                row1['ratePerRoom'] = "-"
                row1['total'] = "-"
                secondresult[key].append(row1)
            if data['foc2'] != '0':
                row2['count'] = data['foc2']
                totalRooms += int(data['foc1'])
                row2['occupancy'] = 'Double'
                row2['ratePerRoom'] = "-"
                row2['total'] = "-"
                secondresult[key].append(row2)


    data5 = []
    if data2['status'] == statusval4:
        cursor.execute('SELECT * from requestAccepted where requestId = %s  && hotelId = %s', [id, hotelId])
        data5 = cursor.fetchall()
        data5 = data5[0]
        temp1 = data5['time'].strftime('%y-%b-%d')
        x = temp1.split('-')
        data5['time'] = x[2] + " " + x[1] + ", " + x[0]
        
    
    data6 = []
    if (data2['status'] == statusval5 or data2['status'] == statusval8):
        cursor.execute("SELECT * From DeclineRequest where requestId = %s  && hotelId = %s", [id, hotelId])
        data6 = cursor.fetchall()
        data6 = data6[0]
        temp1 = data6['time'].strftime('%y-%b-%d')
        x = temp1.split('-')
        data6['time'] = x[2] + " " + x[1] + ", " + x[0]

    data9 = []
    if (data2['status'] == statusval10):
        cursor.execute('SELECT * From confirmRequest where requestId = %s  && hotelId = %s', [id, hotelId])
        data9 = cursor.fetchall()
        data9 = data9[0]
        temp1 = data9['submittedOn'].strftime('%y-%b-%d')
        x = temp1.split('-')
        data9['submittedOn'] = x[2] + " " + x[1] + ", " + x[0]

    data10 = []
    if (data2['status'] == statusval11):
        cursor.execute('SELECT * From notConfirmRequest where requestId = %s  && hotelId = %s', [id, hotelId])
        data10 = cursor.fetchall()
        data10 = data10[0]
        temp1 = data10['submittedOn'].strftime('%y-%b-%d')
        x = temp1.split('-')
        data10['submittedOn'] = x[2] + " " + x[1] + ", " + x[0]



    declined = False
    declinedMsg = ""
    endline = 0
    if (data['status'] == statusval2):
        endline = data2['expiryTime']
        if (endline != None):
            today = datetime.datetime.now()
            if (today > endline):
                cursor.execute(
                    'UPDATE request set status = %s where id = %s  && hotelId = %s', [statusval9, data['id'], hotelId])
                cursor.execute(
                                'SELECT * from response where requestId = %s  && hotelId = %s order by submittedOn desc limit 1', [data['id'], hotelId])
                email = session['email']
                now = datetime.datetime.utcnow()
                prevresponse = cursor.fetchall()

                if len(prevresponse) != 0:
                    prevresponse = prevresponse[0]
                    cursor.execute('INSERT INTO response(requestId, responseId, groupCategory, totalFare, foc, commission, commissionValue, totalQuote, cutoffDays, formPayment, paymentTerms, paymentGtd, negotiable, checkIn, checkOut, submittedBy, submittedOn, status, paymentDays, nights, comments, averageRate, contract, expectedFare, negotiationReason, timesNegotiated, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                        prevresponse['requestId'], prevresponse['responseId'], prevresponse['groupCategory'], prevresponse['totalFare'], prevresponse[
                            'foc'], prevresponse['commission'], prevresponse['commissionValue'], prevresponse['totalQuote'], prevresponse['cutoffDays'],
                        prevresponse['formPayment'], prevresponse['paymentTerms'], prevresponse['paymentGtd'], prevresponse[
                            'negotiable'], prevresponse['checkIn'], prevresponse['checkOut'], email, now,
                        statusval9, prevresponse['paymentDays'], prevresponse['nights'], prevresponse['comments'],
                        prevresponse['averageRate'], prevresponse['contract'], prevresponse['expectedFare'], prevresponse['negotiationReason'], prevresponse['timesNegotiated'], hotelId
                    ])

                    cursor.execute(
                        'SELECT * From responseAvg where responseId = %s  && hotelId = %s order by submittedOn desc limit 1', [prevresponse['responseId'], hotelId])
                    prevAvg = cursor.fetchall()
                    if len(prevAvg) != 0:
                        prevAvg = prevAvg[0]
                        cursor.execute('INSERT INTO responseAvg(single1, single2, double1, double2, triple1, triple2, quad1, quad2, responseId, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                            prevAvg['single1'], prevAvg['single2'], prevAvg['double1'], prevAvg['double2'], prevAvg[
                                'triple1'], prevAvg['triple2'], prevAvg['quad1'], prevAvg['quad2'], prevAvg['responseId'], now, hotelId
                        ])

                    cursor.execute(
                        'SELECT submittedOn from responseDaywise where responseId = %s  && hotelId = %s order by submittedOn desc limit 1', [prevAvg['responseId'], hotelId])
                    submittedOn = cursor.fetchall()
                    cursor.execute('SELECT * From responseDaywise where responseId = %s and submittedOn = %s  && hotelId = %s',
                                [prevAvg['responseId'], submittedOn[0]['submittedOn'], hotelId])

                    prevDaywise = cursor.fetchall()
                    if len(prevDaywise) != 0:
                        for p in prevDaywise:
                            cursor.execute('INSERT INTO responseDaywise(date, currentOcc, discountId, occupancy, type, count, ratePerRoom, responseId, forecast, leadTime, groups, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                                p['date'], p['currentOcc'], p['discountId'], p['occupancy'], p['type'], p[
                                    'count'], p['ratePerRoom'], prevAvg['responseId'], p['forecast'], p['leadTime'], p['groups'], now, hotelId
                            ])        
                
                    cursor.execute(
                        'UPDATE response set status = %s where requestId = %s  && hotelId = %s order by submittedOn desc limit 1', [statusval9, data['id'], hotelId])              
                mysql.connection.commit()
                declined = True
                declinedMsg = "Time limit expired"
                data['status'] = statusval9
                data2['status'] = statusval9
        

            temp1 = endline.strftime('%y-%b-%d, %H:%M:%S')
            x = temp1.split('-')
            endline = x[2].split(",")[0] + " " + x[1] + "," + x[0] + " " + x[2].split(",")[1]


    cursor.execute('select count from settingsNegotiation where hotelId = %s', [hotelId])
    count = cursor.fetchall()
    if len(count) != 0:
        count = count[0]['count']
    else:
        count = 100 # no hard limit so
    cursor.execute('SELECT * from response where responseId = %s and status = %s  && hotelId = %s', [responseId, statusval3, hotelId])
    negoTime = cursor.fetchall()
    negoTimes = len(negoTime)
    nego = False
    negoInformation = {}
    canNegotiate = False
    if (int(negoTimes) <= int(count)):
        canNegotiate = True
    negoInformation['expectedFare'] = data2['expectedFare']
    negoInformation['reason'] = data2['negotiationReason']

    canNegotiate = canNegotiate and negcheck

    cursor.execute('SELECT contract, id from contract where id = %s  && hotelId = %s', [
                   data2['contract'], hotelId])
    contract = cursor.fetchall()

    cutoff = data2['submittedOn'] + datetime.timedelta(days = int(data2['cutoffDays']))
    temp1 = cutoff.strftime('%y-%b-%d, %H:%M:%S')
    x = temp1.split('-')
    cutoff = x[2].split(",")[0] + " " + x[1] + "," + x[0] + " " + x[2].split(",")[1]
    data2['cutoffDays'] = cutoff


    temp1 = data2['submittedOn'].strftime('%y-%b-%d, %H:%M:%S')
    x = temp1.split('-')
    data2['submittedOn'] = x[2].split(",")[0] + " " + x[1] + "," + x[0] + " " + x[2].split(",")[1]



    temp1 = data['checkIn'].strftime('%y-%b-%d')
    x = temp1.split('-')
    data['checkIn'] = x[2] + " " + x[1] + ", " + x[0]

    temp1 = data['checkOut'].strftime('%y-%b-%d')
    x = temp1.split('-')
    data['checkOut'] = x[2] + " " + x[1] + ", " + x[0]
    
    for d in list(dateButtons):
        y = d
        temp1 = d.strftime('%Y-%b-%d-%A')
        x = temp1.split('-')
        d = x[3] + " : " + x[2] + " " + x[1] + "," + x[0]
        result[d] = result[y]
        del result[y]
    
    dateButtons = result.keys()


    return render_template('request/showQuote.html', data = data, data2 = data2, data3 = data3, dateButtons = dateButtons, result = result, secondresult = secondresult, data5 = data5, data6 = data6, contract = contract, declined = declined, declinedMsg = declinedMsg, canNegotiate = canNegotiate, negoInformation = negoInformation, data9 = data9, data10 = data10, endline = endline, totalRooms = totalRooms, customer = True)


@app.route('/deleteRequest/<id>', methods = ['GET', 'POST'])
@is_logged_in
def deleteRequest(id):
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT status from request where id = %s && hotelId = %s', [id, hotelId])
    status = cursor.fetchall()
    if (status[0]['status'] == statusval2) or (status[0]['status'] == statusval4) or (status[0]['status'] == statusval5 or status[0]['status'] == statusval7 or status[0]['status'] == statusval3 or status[0]['status'] == statusval8 or status[0]['status'] == statusval10 or status[0]['status'] == statusval11):
        data5 = []
        if (status[0]['status'] == statusval4):
            cursor.execute(
                'SELECT * From requestAccepted where requestId = %s && hotelId = %s', [id, hotelId])
            data5 = cursor.fetchall()
            data5 = data5[0]
            temp1 = data5['time'].strftime('%y-%b-%d')
            x = temp1.split('-')
            data5['time'] = x[2] + " " + x[1] + ", " + x[0]

        data6 = []
        if (status[0]['status'] == statusval5):
            cursor.execute(
                "SELECT * From DeclineRequest where requestId = %s && hotelId = %s", [id, hotelId])
            data6 = cursor.fetchall()
            data6 = data6[0]
            temp1 = data6['time'].strftime('%y-%b-%d')
            x = temp1.split('-')
            data6['time'] = x[2] + " " + x[1] + ", " + x[0]

        data8 = []
        if (status[0]['status'] == statusval7):
            cursor.execute(
                "SELECT * From review where requestId = %s && hotelId = %s", [id, hotelId])
            data8 = cursor.fetchall()
            data8 = data8[0]
            temp1 = data8['time'].strftime('%y-%b-%d')
            x = temp1.split('-')
            data8['time'] = x[2] + " " + x[1] + ", " + x[0]

        data9 = []
        if (status[0]['status'] == statusval10):
            cursor.execute('SELECT * From confirmRequest where requestId = %s && hotelId = %s', [id, hotelId])
            data9 = cursor.fetchall()
            data9 = data9[0]
            temp1 = data9['submittedOn'].strftime('%y-%b-%d')
            x = temp1.split('-')
            data9['submittedOn'] = x[2] + " " + x[1] + ", " + x[0]

        data10 = []
        if (status[0]['status'] == statusval11):
            cursor.execute('SELECT * From notConfirmRequest where requestId = %s && hotelId = %s', [id, hotelId])
            data10 = cursor.fetchall()
            data10 = data10[0]
            temp1 = data10['submittedOn'].strftime('%y-%b-%d')
            x = temp1.split('-')
            data10['submittedOn'] = x[2] + " " + x[1] + ", " + x[0]

        cursor.execute('SELECT * From request where id = %s && hotelId = %s', [id, hotelId])
        data = cursor.fetchall()
        data = data[0]
        checkIn = data['checkIn']
        checkOut = data['checkOut']
        data['createdOn'] = data['createdOn'].strftime("%d %b ,%y, %H:%M:%S")

        email = session['email']
        now = datetime.datetime.utcnow()

        cursor.execute(
            'SELECT * From requestLastOpened where id = %s && hotelId = %s', [id, hotelId])
        check = cursor.fetchall()
        data['lastOpenedOn'] = check[0]['time']
        data['lastOpenedBy'] = check[0]['openedBy']
        temp1 = data['lastOpenedOn'].strftime('%y-%b-%d')
        x = temp1.split('-')
        data['lastOpenedOn'] = x[2] + " " + x[1] + ", " + x[0]

        string = ''
        v = data['paymentTerms']
        if v != None:
            if v.count('pc') > 0:
                string = 'Post Checkout'
                data['paymentTerms'] = string
            elif v.count('ac') > 0:
                data['paymentTerms'] = 'At Checkout'
            elif v.count('poa') > 0:
                data['paymentTerms'] = 'Prior To Arrival'

        string = ''

        data['formPayment'] = procArr2(data['formPayment'])
        if data['comments'].isspace():
            data['comments'] = ''

        responseId = data['id'] + "R"
        cursor.execute(
            'SELECT * From response where responseId = %s  && hotelId = %s order by submittedOn desc limit 1', [responseId, hotelId])
        data2 = cursor.fetchall()
        tfoc = False
        tcomm = False
        data3 = []
        lefttable = []
        righttable = []
        if len(data2) != 0:
            data['groupCategory'] = data2[0]['groupCategory']
            data2 = data2[0]
            if (data2['foc'] != '0'):
                tfoc = True
            tcomm = True
            if (data2['commission'] != '0'):
                tcomm = True

            string = ''
            data2['formPayment'] = procArr2(data2['formPayment'])

            string = ''
            v = data2['paymentTerms']
            if v != None:
                if v.count('pc') > 0:
                    string = 'Post Checkout'
                    data2['paymentTerms'] = string
                elif v.count('ac') > 0:
                    data2['paymentTerms'] = 'At Checkout'
                elif v.count('poa') > 0:
                    data2['paymentTerms'] = 'Prior To Arrival'


        cursor.execute('SELECT submittedOn from responseAvg where responseId = %s  && hotelId = %s order by submittedOn desc limit 1', [responseId, hotelId])
        submittedOn = cursor.fetchall()
        if submittedOn[0]['submittedOn'] == 'None':
            submittedOn = submittedOn[0]['submittedOn']
            cursor.execute('SELECT * From responseAvg where responseId = %s', [responseId])
            data3 = cursor.fetchall()
        else:
            cursor.execute('SELECT * From responseAvg where responseId = %s and submittedOn = %s && hotelId = %s', [responseId, submittedOn[0]['submittedOn'], hotelId])
            data3 = cursor.fetchall()

        data3 = data3[0]

        cursor.execute(
            'SELECT submittedOn from responseDaywise where responseId = %s  && hotelId = %s order by submittedOn desc limit 1', [responseId, hotelId])
        submittedOn = cursor.fetchall()
        if submittedOn[0]['submittedOn'] == 'None':
            submittedOn = submittedOn[0]['submittedOn']
            cursor.execute(
                'SELECT * From responseDaywise where responseId = %s  && hotelId = %s', [responseId, hotelId])
            data4 = cursor.fetchall()
        else:
            cursor.execute(
                'SELECT * From responseDaywise where responseId = %s  and submittedOn = %s  && hotelId = %s', [responseId, submittedOn[0]['submittedOn'], hotelId])
            data4 = cursor.fetchall()
            
        lefttable = []
        dataToCheck = []
        righttable = {}
        for d in data4:
            righttable[d['date']] = []

        for d in data4:
            if d['date'] not in dataToCheck:
                tempArr = {}
                tempArr['date'] = d['date']
                tempArr['currentOcc'] = d['currentOcc']
                tempArr['discountId'] = d['discountId']
                tempArr['forecast'] = d['forecast']
                tempArr['groups'] = d['groups']
                tempArr['leadTime'] = d['leadTime']
                lefttable.append(tempArr)
                dataToCheck.append(d['date'])
            tArr = {}
            tArr['occupancy'] = d['occupancy']
            tArr['type'] = d['type']
            tArr['count'] = d['count']
            tArr['ratePerRoom'] = d['ratePerRoom']

            righttable[d['date']].append(tArr)


        for d in lefttable:
            y = d['date']
            temp1 = d['date'].strftime('%y-%b-%d')
            x = temp1.split('-')
            x = x[2] + " " + x[1] + "," + x[0]
            d['date'] = x
        
        for d in list(righttable):
            y = d
            temp1 = d.strftime('%y-%b-%d')
            x = temp1.split('-')
            d = x[2] + " " + x[1] + "," + x[0]
            righttable[d] = righttable[y]

        deleteflag = True

        for key, value in righttable.items():
            for r in value:
                if (r['type'] == 'foc'):
                    r['type'] = "FOC"

        cursor.execute('SELECT contract from contract where id = %s  && hotelId = %s', [data2['contract'], hotelId])
        contractv = cursor.fetchall()
        if len(contractv) != 0:
            contractv = contractv[0]['contract']
        else:
            contractv = ''

        x = data2['submittedOn'].strftime('%y-%b-%d,  %H:%M:%S')
        x = x.split("-")
        data2['submittedOn'] = x[2].split(",")[0] + " " + x[1] + "," + x[0] + " " + x[2].split(",")[1]

        return render_template('request/requestQuotedView.html', data=data, data2=data2, tfoc=tfoc, tcomm=tcomm, data3=data3, lefttable=lefttable, righttable=righttable, data5=data5, data6=data6, deleteflag = deleteflag, data8 = data8, data9 = data9, data10 = data10, contractv = contractv)
    elif (status[0]['status'] == statusval1):
        cursor.execute('SELECT * From request where id = %s  && hotelId = %s', [id, hotelId])
        data = cursor.fetchall()
        data = data[0]
        checkIn = data['checkIn']
        checkOut = data['checkOut']
        data['createdOn'] = data['createdOn'].strftime("%d %b ,%y, %H:%M:%S")

        email = session['email']
        now = datetime.datetime.utcnow()

        cursor.execute(
            'SELECT * From requestLastOpened where id = %s  && hotelId = %s', [id, hotelId])
        check = cursor.fetchall()
        if len(check) != 0:
            data['lastOpenedOn'] = check[0]['time']
            data['lastOpenedBy'] = check[0]['openedBy']
            temp1 = data['lastOpenedOn'].strftime('%y-%b-%d')
            x = temp1.split('-')
            data['lastOpenedOn'] = x[2] + " " + x[1] + ", " + x[0]
        else:
            data['lastOpenedOn'] = ''
            data['lastOpenedBy'] = ''
        string = ''
        v = data['paymentTerms']
        if v != None:
            if v.count('pc') > 0:
                string = 'Post Checkout'
                data['paymentTerms'] = string
            elif v.count('ac') > 0:
                data['paymentTerms'] = 'At Checkout'
            elif v.count('poa') > 0:
                data['paymentTerms'] = 'Prior To Arrival'

        string = ''
        v = data['formPayment']

        data['formPayment'] = procArr2(data['formPayment'])


        if data['comments'].isspace():
            data['comments'] = ''
        return render_template('request/deleteRequest.html', data=data)

@app.route('/DeleteRequest2', methods = ['GET', 'POST'])
@is_logged_in
def DeleteRequest2():
    inp = request.json
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('UPDATE request set status = %s where id = %s  && hotelId = %s', [statusval6, inp['id'], hotelId])
    cursor.execute('SELECT * from response where requestId = %s  && hotelId = %s order by submittedOn desc limit 1', [inp['id'], hotelId])
    email = session['email']
    now = datetime.datetime.utcnow()
    prevresponse = cursor.fetchall()
    if len(prevresponse) != 0:
        prevresponse = prevresponse[0]
        cursor.execute('INSERT INTO response(requestId, responseId, groupCategory, totalFare, foc, commission, commissionValue, totalQuote, cutoffDays, formPayment, paymentTerms, paymentGtd, negotiable, checkIn, checkOut, submittedBy, submittedOn, status, paymentDays, nights, comments, averageRate, contract, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
            prevresponse['requestId'], prevresponse['responseId'], prevresponse['groupCategory'], prevresponse['totalFare'], prevresponse['foc'],prevresponse['commission'],prevresponse['commissionValue'], prevresponse['totalQuote'], prevresponse['cutoffDays'],
                prevresponse['formPayment'], prevresponse['paymentTerms'], prevresponse['paymentGtd'], prevresponse['negotiable'], prevresponse['checkIn'], prevresponse['checkOut'], email, now,
            statusval6, prevresponse['paymentDays'], prevresponse['nights'], prevresponse['comments'],
            prevresponse['averageRate'], prevresponse['contract'], hotelId
        ])

        cursor.execute('SELECT * From responseAvg where responseId = %s &&hotelId = %s order by submittedOn desc limit 1', [prevresponse['responseId'], hotelId])
        prevAvg = cursor.fetchall()
        if len(prevAvg) != 0:
            prevAvg = prevAvg[0]
            cursor.execute('INSERT INTO responseAvg(single1, single2, double1, double2, triple1, triple2, quad1, quad2, responseId, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
            prevAvg['single1'], prevAvg['single2'], prevAvg['double1'], prevAvg['double2'], prevAvg['triple1'], prevAvg['triple2'], prevAvg['quad1'], prevAvg['quad2'], prevAvg['responseId'], now, hotelId
            ])
        
            cursor.execute(
                'SELECT submittedOn from responseDaywise where responseId = %s  &&hotelId = %s order by submittedOn desc limit 1', [prevAvg['responseId'], hotelId])
            submittedOn = cursor.fetchall()
            cursor.execute('SELECT * From responseDaywise where responseId = %s and submittedOn = %s  &&hotelId = %s', [prevAvg['responseId'], submittedOn[0]['submittedOn'], hotelId])

            prevDaywise = cursor.fetchall()
            if len(prevDaywise) != 0:
                for p in prevDaywise:
                    cursor.execute('INSERT INTO responseDaywise(date, currentOcc, discountId, occupancy, type, count, ratePerRoom, responseId, forecast, leadTime, groups, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                p['date'], p['currentOcc'], p['discountId'], p['occupancy'], p['type'], p[
                    'count'], p['ratePerRoom'], prevAvg['responseId'], p['forecast'], p['leadTime'], p['groups'], now, hotelId
                ])


    cursor.execute("INSERT INTO deletedRequest(requestId, time, reason, deletedBy, hotelId) VALUES(%s, %s, %s, %s, %s) ", [inp['id'], now, inp['reason'], email, hotelId])

    mysql.connection.commit()
    cursor.close()

    flash('The request has been deleted', 'success')
    return ('', 204)

@app.route('/NegotiateRequest', methods = ['GET', 'POST'])
def NegotiateRequest():
    inp = request.json
    hotelId = session.get('hotelId')
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT timesNegotiated from response where requestId = %s && hotelId = %s order by submittedOn desc limit 1', [inp['id'], hotelId])
    dd = cursor.fetchall()
    dd = dd[0]
    times = int(dd['timesNegotiated']) + 1
    #here
    cursor.execute('UPDATE request set status = %s where id = %s && hotelId = %s', [statusval3, inp['id'], hotelId])

    cursor.execute(
        'SELECT * from response where requestId = %s && hotelId = %s order by submittedOn desc limit 1', [inp['id'], hotelId])

    try:
        email = session.get('email')
    except:
        cursor.execute('SELECT createdFor from request where id = %s && hotelId = %s', [inp['requestId'], hotelId])
        createdFor = cursor.fetchall()
        createdFor = createdFor[0]['createdFor']
        email = createdFor
    now = datetime.datetime.utcnow()
    prevresponse = cursor.fetchall()

    if len(prevresponse) != 0:
        prevresponse = prevresponse[0]
        cursor.execute('INSERT INTO response(requestId, responseId, groupCategory, totalFare, foc, commission, commissionValue, totalQuote, cutoffDays, formPayment, paymentTerms, paymentGtd, negotiable, checkIn, checkOut, submittedBy, submittedOn, status, paymentDays, nights, comments, averageRate, contract, expectedFare, negotiationReason, timesNegotiated, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
            prevresponse['requestId'], prevresponse['responseId'], prevresponse['groupCategory'], prevresponse['totalFare'], prevresponse[
                'foc'], prevresponse['commission'], prevresponse['commissionValue'], prevresponse['totalQuote'], prevresponse['cutoffDays'],
            prevresponse['formPayment'], prevresponse['paymentTerms'], prevresponse['paymentGtd'], prevresponse[
                'negotiable'], prevresponse['checkIn'], prevresponse['checkOut'], email, now,
            statusval3, prevresponse['paymentDays'], prevresponse['nights'], prevresponse['comments'],
            prevresponse['averageRate'], prevresponse['contract'], inp['expectedFare'], inp['reason'], times, hotelId
        ])

        cursor.execute(
            'SELECT * From responseAvg where responseId = %s && hotelId = %s order by submittedOn desc limit 1', [prevresponse['responseId'], hotelId])
        prevAvg = cursor.fetchall()
        if len(prevAvg) != 0:
            prevAvg = prevAvg[0]
            cursor.execute('INSERT INTO responseAvg(single1, single2, double1, double2, triple1, triple2, quad1, quad2, responseId, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                prevAvg['single1'], prevAvg['single2'], prevAvg['double1'], prevAvg['double2'], prevAvg[
                    'triple1'], prevAvg['triple2'], prevAvg['quad1'], prevAvg['quad2'], prevAvg['responseId'], now, hotelId
            ])

            cursor.execute(
                'SELECT submittedOn from responseDaywise where responseId = %s && hotelId = %s order by submittedOn desc limit 1', [prevAvg['responseId'], hotelId])
            submittedOn = cursor.fetchall()
            cursor.execute('SELECT * From responseDaywise where responseId = %s and submittedOn = %s  && hotelId = %s',
                           [prevAvg['responseId'], submittedOn[0]['submittedOn'], hotelId])

            prevDaywise = cursor.fetchall()
            if len(prevDaywise) != 0:
                for p in prevDaywise:
                    cursor.execute('INSERT INTO responseDaywise(date, currentOcc, discountId, occupancy, type, count, ratePerRoom, responseId, forecast, leadTime, groups, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                        p['date'], p['currentOcc'], p['discountId'], p['occupancy'], p['type'], p[
                            'count'], p['ratePerRoom'], prevAvg['responseId'], p['forecast'], p['leadTime'], p['groups'], now, hotelId
                    ])

    mysql.connection.commit()

    flash('The request is sent for negotiation', 'success')
    return ('', 204)

@app.route('/AcceptRequest', methods = ['GET', 'POST'])
def AcceptRequest():
    inp = request.json
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute(
        'SELECT * from response where requestId = %s && hotelId = %s order by submittedOn desc limit 1', [inp['id'], hotelId])
    try:
        email = session.get('email')
    except:
        cursor.execute('SELECT createdFor from request where id = %s  && hotelId = %s', [inp['requestId'], hotelId])
        createdFor = cursor.fetchall()
        createdFor = createdFor[0]['createdFor']
        email = createdFor

    now = datetime.datetime.utcnow()
    prevresponse = cursor.fetchall()

    if len(prevresponse) != 0:
        prevresponse = prevresponse[0]
        cursor.execute('INSERT INTO response(requestId, responseId, groupCategory, totalFare, foc, commission, commissionValue, totalQuote, cutoffDays, formPayment, paymentTerms, paymentGtd, negotiable, checkIn, checkOut, submittedBy, submittedOn, status, paymentDays, nights, comments, averageRate, contract, expectedFare, negotiationReason, timesNegotiated, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
            prevresponse['requestId'], prevresponse['responseId'], prevresponse['groupCategory'], prevresponse['totalFare'], prevresponse[
                'foc'], prevresponse['commission'], prevresponse['commissionValue'], prevresponse['totalQuote'], prevresponse['cutoffDays'],
            prevresponse['formPayment'], prevresponse['paymentTerms'], prevresponse['paymentGtd'], prevresponse[
                'negotiable'], prevresponse['checkIn'], prevresponse['checkOut'], email, now,
            statusval4, prevresponse['paymentDays'], prevresponse['nights'], prevresponse['comments'],
            prevresponse['averageRate'], prevresponse['contract'], prevresponse['expectedFare'], prevresponse['negotiationReason'], prevresponse['timesNegotiated'], hotelId
        ])

        cursor.execute(
            'SELECT * From responseAvg where responseId = %s && hotelId = %s order by submittedOn desc limit 1', [prevresponse['responseId'], hotelId])
        prevAvg = cursor.fetchall()
        if len(prevAvg) != 0:
            prevAvg = prevAvg[0]
            cursor.execute('INSERT INTO responseAvg(single1, single2, double1, double2, triple1, triple2, quad1, quad2, responseId, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                prevAvg['single1'], prevAvg['single2'], prevAvg['double1'], prevAvg['double2'], prevAvg[
                    'triple1'], prevAvg['triple2'], prevAvg['quad1'], prevAvg['quad2'], prevAvg['responseId'], now, hotelId
            ])

            cursor.execute(
                'SELECT submittedOn from responseDaywise where responseId = %s && hotelId = %s order by submittedOn desc limit 1', [prevAvg['responseId'], hotelId])
            submittedOn = cursor.fetchall()
            cursor.execute('SELECT * From responseDaywise where responseId = %s and submittedOn = %s && hotelId = %s',
                           [prevAvg['responseId'], submittedOn[0]['submittedOn'], hotelId])

            prevDaywise = cursor.fetchall()
            if len(prevDaywise) != 0:
                for p in prevDaywise:
                    cursor.execute('INSERT INTO responseDaywise(date, currentOcc, discountId, occupancy, type, count, ratePerRoom, responseId, forecast, leadTime, groups, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                        p['date'], p['currentOcc'], p['discountId'], p['occupancy'], p['type'], p[
                            'count'], p['ratePerRoom'], prevAvg['responseId'], p['forecast'], p['leadTime'], p['groups'], now, hotelId
                    ])

    

    cursor.execute('INSERT INTO requestAccepted(requestId, time, hotelId) VALUES(%s, %s, %s)', [inp['id'], now, hotelId])
    cursor.execute('UPDATE request set status = %s where id = %s && hotelId = %s', [statusval4, inp['id'], hotelId])
    cursor.execute('SELECT createdFor from request where id = %s && hotelId = %s', [inp['id'], hotelId])
    createdFor = cursor.fetchall()
    createdFor = createdFor[0]['createdFor']


    if prevresponse['paymentGtd'] == 1:
        with app.open_resource("static/docs/ccauth_hotels.pdf") as fp:
            msg = Message(
                'Payment Guarantee',
                sender = 'koolbhavya.epic@gmail.com',
                recipients= [createdFor],
            )
            msg.body = 'Kindly guarantee payment by filling this form'
            msg.attach(
                "PaymentGuarantee.pdf", "application/pdf", fp.read()
            )
            mail.send(msg)

    mysql.connection.commit()
    cursor.close()

    flash('The request has been accepted', 'success')
    return ('', 204)


@app.route('/DeclineRequest', methods = ['GET', 'POST'])
def DeclineRequest():
    inp = request.json
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('UPDATE request set status = %s where id = %s && hotelId = %s', [statusval5, inp['id'], hotelId])
    cursor.execute(
        'SELECT * from response where requestId = %s && hotelId = %s order by submittedOn desc limit 1', [inp['id'], hotelId])
    
    try:
        email = session.get('email')
    except:
        cursor.execute('SELECT createdFor from request where id = %s && hotelId = %s', [inp['requestId'], hotelId])
        createdFor = cursor.fetchall()
        createdFor = createdFor[0]['createdFor']
        email = createdFor
    now = datetime.datetime.utcnow()
    prevresponse = cursor.fetchall()

    if len(prevresponse) != 0:
        prevresponse = prevresponse[0]
        cursor.execute('INSERT INTO response(requestId, responseId, groupCategory, totalFare, foc, commission, commissionValue, totalQuote, cutoffDays, formPayment, paymentTerms, paymentGtd, negotiable, checkIn, checkOut, submittedBy, submittedOn, status, paymentDays, nights, comments, averageRate, contract, expectedFare, negotiationReason, timesNegotiated, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
            prevresponse['requestId'], prevresponse['responseId'], prevresponse['groupCategory'], prevresponse['totalFare'], prevresponse[
                'foc'], prevresponse['commission'], prevresponse['commissionValue'], prevresponse['totalQuote'], prevresponse['cutoffDays'],
            prevresponse['formPayment'], prevresponse['paymentTerms'], prevresponse['paymentGtd'], prevresponse[
                'negotiable'], prevresponse['checkIn'], prevresponse['checkOut'], email, now,
            statusval5, prevresponse['paymentDays'], prevresponse['nights'], prevresponse['comments'],
            prevresponse['averageRate'], prevresponse['contract'], prevresponse[
                'expectedFare'], prevresponse['negotiationReason'], prevresponse['timesNegotiated'], hotelId
        ])

        cursor.execute(
            'SELECT * From responseAvg where responseId = %s && hotelId = %s order by submittedOn desc limit 1', [prevresponse['responseId'], hotelId])
        prevAvg = cursor.fetchall()
        if len(prevAvg) != 0:
            prevAvg = prevAvg[0]
            cursor.execute('INSERT INTO responseAvg(single1, single2, double1, double2, triple1, triple2, quad1, quad2, responseId, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                prevAvg['single1'], prevAvg['single2'], prevAvg['double1'], prevAvg['double2'], prevAvg[
                    'triple1'], prevAvg['triple2'], prevAvg['quad1'], prevAvg['quad2'], prevAvg['responseId'], now, hotelId
            ])

            cursor.execute(
                'SELECT submittedOn from responseDaywise where responseId = %s  && hotelId = %s order by submittedOn desc limit 1', [prevAvg['responseId'], hotelId])
            submittedOn = cursor.fetchall()
            cursor.execute('SELECT * From responseDaywise where responseId = %s and submittedOn = %s  && hotelId = %s',
                           [prevAvg['responseId'], submittedOn[0]['submittedOn'], hotelId])

            prevDaywise = cursor.fetchall()
            if len(prevDaywise) != 0:
                for p in prevDaywise:
                    cursor.execute('INSERT INTO responseDaywise(date, currentOcc, discountId, occupancy, type, count, ratePerRoom, responseId, forecast, leadTime, groups, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                        p['date'], p['currentOcc'], p['discountId'], p['occupancy'], p['type'], p[
                            'count'], p['ratePerRoom'], prevAvg['responseId'], p['forecast'], p['leadTime'], p['groups'], now, hotelId
                    ])



    now = datetime.datetime.utcnow()
    cursor.execute("INSERT INTO DeclineRequest(requestId, time, reason, declinedBy, hotelId) VALUES(%s, %s, %s, %s, %s) ", [inp['id'], now, inp['reason'], inp['declinedBy'], hotelId])
    mysql.connection.commit()
    cursor.close()

    flash('The request has been declined', 'success')
    return ('', 204)

@app.route('/requestProcessReview', methods = ['GET', 'POST'])
@is_logged_in
def requestProcessReview():
    inp = request.json
    cursor = mysql.connection.cursor()
    responseId = inp['requestId'] + "R"
    email = session['email']
    now = datetime.datetime.utcnow()
    status = statusval7
    hotelId = session.get('hotelId')

    table = inp['table_result']
    check_final = False
    for t in table:
        cursor.execute('INSERT INTO responseDaywise(date, currentOcc, discountId, occupancy, type, count, ratePerRoom, responseId, forecast, leadTime, groups, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
            t['date'], t['currentOcc'], t['discountId'], t['occupancy'], t['type'], t['count'], t['ratePerRoom'], responseId, t['forecast'], t['leadTime'], t['groups'], now, hotelId
        ])
        check = checkOverride(t['ratePerRoom'])
        if(check == True):
            check_final = True

        
        if (check_final == True):
            check_final = 1
        else:
            check_final = 0

    cursor.execute('INSERT INTO response(requestId, responseId, groupCategory, totalFare, foc, commission, commissionValue, totalQuote, cutoffDays, formPayment, paymentTerms, paymentGtd, negotiable, checkIn, checkOut, submittedBy, submittedOn, status, paymentDays, nights, comments, averageRate, contract, overrideReason, overrideFlag, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' , [
        inp['requestId'], responseId, inp['groupCategory'], inp['totalFare'], inp['foc'], str(inp['commission']), str(inp['commissionValue']), inp['totalQuote'], inp['cutoffDays'], procArr(inp['formPayment']), inp['paymentTerms'], inp['paymentGtd'], inp['negotiable'], inp['checkIn'], inp['checkOut'], email, now,
        status, inp['paymentDays'], inp['nights'], inp['comments'],
        inp['averageRate'], inp['contract'], inp['overres'], check_final, hotelId
    ])

    
    cursor.execute("UPDATE request SET status = %s WHERE id = %s && hotelId = %s", [statusval7, inp['requestId'], hotelId])

    cursor.execute('UPDATE response set status = %s where requestId = %s  && hotelId = %s order by submittedOn desc limit 1', [statusval7, inp['requestId'], hotelId]
        )

    cursor.execute('INSERT INTO responseAvg(single1, single2, double1, double2, triple1, triple2, quad1, quad2, responseId, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' , [
        inp['single1'], inp['single2'], inp['double1'], inp['double2'], inp['triple1'], inp['triple2'], inp['quad1'], inp['quad2'], responseId, now, hotelId
    ])

    cursor.execute('INSERT INTO review(requestId, sentBy, time, hotelId) VALUES(%s, %s, %s, %s)', [inp['requestId'], email, now, hotelId])


    mysql.connection.commit()
    flash("The request has been sent for review", 'success')
    return ('', 204)


@app.route('/requestHistory/<id>', methods = ['GET', 'POST'])
@is_logged_in
def requestHistory(id):
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * From request where id = %s && hotelId = %s', [id, hotelId])
    requestData = cursor.fetchall()
    requestData = requestData[0]

    requestData['formPayment'] = procArr2(requestData['paymentTerms'])

    if requestData['comments'].isspace():
        requestData['comments'] = ''

    

    cursor.execute('SELECT * From response where requestId = %s && hotelId = %s', [id, hotelId])
    responseData = cursor.fetchall()
    data6 = []

    for r in responseData:
        v = r['paymentTerms']
        if v != None:
            if v.count('pc') > 0:
                string = 'Post Checkout'
                r['paymentTerms'] = string
            elif v.count('ac') > 0:
                r['paymentTerms'] = 'At Checkout'
            elif v.count('poa') > 0:
                r['paymentTerms'] = 'Prior To Arrival'

        print(r['overrideReason'], r['overrideFlag'])
        string = ''
        

        r['formPayment'] = procArr2(r['formPayment'])

        if r['comments'].isspace():
            r['comments'] = ''
        
        if (r['status'] == statusval5 or r['status'] == statusval8):
            cursor.execute("SELECT * From DeclineRequest where requestId = %s && hotelId = %s", [id, hotelId])
            data6 = cursor.fetchall()
            data6 = data6[0]
            r['msg'] = data6['reason']
            r['by'] = data6['declinedBy']
            r['time'] = data6['time']
            temp1 = data6['time'].strftime('%y-%b-%d')
            x = temp1.split('-')
            data6['time'] = x[2] + " " + x[1] + ", " + x[0]

    responseId = id + "R"
    cursor.execute('SELECT * From responseAvg where responseId = %s && hotelId = %s', [responseId, hotelId])

    responseAvgData = cursor.fetchall()
    cursor.execute('SELECT * From responseDaywise where responseId = %s  && hotelId = %s ', [responseId, hotelId])
    responseDaywiseData = cursor.fetchall()
    tempdict = {}
    for row in responseDaywiseData:
        tempdict[row['submittedOn']] = []


    for r in responseDaywiseData:
        tempdict[r['submittedOn']].append(r)

    responseOverReason = []
    responseDaywiseData = tempdict
    finalresult = []
    for key, value in responseDaywiseData.items():
        tdict = {}
        for r in value:
            try:
                if (r['date'] in tdict):
                    r['total'] = int(r['count']) * float(r['ratePerRoom'].split('(')[0])
                    tdict[r['date']].append(r)
                else:
                    r['total'] = int(r['count']) * float(r['ratePerRoom'].split("(")[0])
                    tdict[r['date']] = [r]
            except:
                r['total'] = "-"
                tdict[r['date']] = [r]

        finalresult.append(tdict)

    for d in finalresult:
        for m in list(d):
            y = m
            temp1 = m.strftime('%y-%b-%d')
            x = temp1.split('-')
            z = x[2] + " " + x[1] + "," + x[0]
            d[z] = d[m]
            del d[m]

    responseDaywiseData = finalresult


    return render_template('request/showHistory.html', requestData = requestData, responseData = responseData, responseAvgData = responseAvgData, responseDaywiseData = responseDaywiseData, data6 = data6, responseOverReason = responseOverReason)


@app.route('/confirmRequest/<token>', methods = ['GET', 'POST'])
@is_logged_in
def confirmRequest(token):
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * From request where id = %s && hotelId = %s', [token, hotelId])
    requestData = cursor.fetchall()
    requestData = requestData[0]

    cursor.execute('SELECT * From requestAccepted where requestId = %s && hotelId = %s', [token, hotelId])
    acceptedOn = cursor.fetchall()
    acceptedOn = acceptedOn[0]['time']

    cursor.execute('SELECT totalQuote from response where requestId = %s  && hotelId = %s order by submittedOn desc limit 1', [token, hotelId])
    totalQuote = cursor.fetchall()
    totalQuote = totalQuote[0]['totalQuote']

    requestData['checkIn'] = requestData['checkIn']
    temp1 = requestData['checkIn'].strftime('%y-%b-%d')
    x = temp1.split('-')
    requestData['checkIn'] = x[2] + " " + x[1] + ", " + x[0]

    requestData['checkOut'] = requestData['checkOut']
    temp1 = requestData['checkOut'].strftime('%y-%b-%d')
    x = temp1.split('-')
    requestData['checkOut'] = x[2] + " " + x[1] + ", " + x[0]

    return render_template('request/confirmRequest.html', requestData = requestData, acceptedOn = acceptedOn, totalQuote = totalQuote)

@app.route('/confirmRequestSubmit', methods = ['GET', 'POST'])
@is_logged_in
def confirmRequestSubmit():
    inp = request.json
    cursor = mysql.connection.cursor()
    time = datetime.datetime.utcnow()
    hotelId = session.get('hotelId')

    cursor.execute(
        'SELECT * from response where requestId = %s && hotelId = %s order by submittedOn desc limit 1', [inp['id'], hotelId])
    email = session['email']
    now = datetime.datetime.utcnow()
    prevresponse = cursor.fetchall()

    if len(prevresponse) != 0:
        prevresponse = prevresponse[0]
        cursor.execute('INSERT INTO response(requestId, responseId, groupCategory, totalFare, foc, commission, commissionValue, totalQuote, cutoffDays, formPayment, paymentTerms, paymentGtd, negotiable, checkIn, checkOut, submittedBy, submittedOn, status, paymentDays, nights, comments, averageRate, contract, expectedFare, negotiationReason, timesNegotiated, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
            prevresponse['requestId'], prevresponse['responseId'], prevresponse['groupCategory'], prevresponse['totalFare'], prevresponse[
                'foc'], prevresponse['commission'], prevresponse['commissionValue'], prevresponse['totalQuote'], prevresponse['cutoffDays'],
            prevresponse['formPayment'], prevresponse['paymentTerms'], prevresponse['paymentGtd'], prevresponse[
                'negotiable'], prevresponse['checkIn'], prevresponse['checkOut'], email, now,
            statusval10, prevresponse['paymentDays'], prevresponse['nights'], prevresponse['comments'],
            prevresponse['averageRate'], prevresponse['contract'], prevresponse['expectedFare'], prevresponse['negotiationReason'], prevresponse['timesNegotiated'], hotelId
        ])

        cursor.execute(
            'SELECT * From responseAvg where responseId = %s  && hotelId = %s order by submittedOn desc limit 1', [prevresponse['responseId'], hotelId])
        prevAvg = cursor.fetchall()
        if len(prevAvg) != 0:
            prevAvg = prevAvg[0]
            cursor.execute('INSERT INTO responseAvg(single1, single2, double1, double2, triple1, triple2, quad1, quad2, responseId, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                prevAvg['single1'], prevAvg['single2'], prevAvg['double1'], prevAvg['double2'], prevAvg[
                    'triple1'], prevAvg['triple2'], prevAvg['quad1'], prevAvg['quad2'], prevAvg['responseId'], now, hotelId
            ])

            cursor.execute(
                'SELECT submittedOn from responseDaywise where responseId = %s  && hotelId = %s order by submittedOn desc limit 1', [prevAvg['responseId'], hotelId])
            submittedOn = cursor.fetchall()
            cursor.execute('SELECT * From responseDaywise where responseId = %s and submittedOn = %s  && hotelId = %s',
                           [prevAvg['responseId'], submittedOn[0]['submittedOn'], hotelId])

            prevDaywise = cursor.fetchall()
            if len(prevDaywise) != 0:
                for p in prevDaywise:
                    cursor.execute('INSERT INTO responseDaywise(date, currentOcc, discountId, occupancy, type, count, ratePerRoom, responseId, forecast, leadTime, groups, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                        p['date'], p['currentOcc'], p['discountId'], p['occupancy'], p['type'], p[
                            'count'], p['ratePerRoom'], prevAvg['responseId'], p['forecast'], p['leadTime'], p['groups'], now, hotelId
                    ])


    cursor.execute('INSERT INTO confirmRequest(requestId, confirmationCode, comments, submittedBy, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s)', [inp['id'], inp['confirmationCode'], inp['comments'], email, time, hotelId])
    cursor.execute('UPDATE request set status = %s where id = %s && hotelId = %s', [
        statusval10, inp['id'], hotelId
    ])
    cursor.execute('UPDATE response set status = %s where requestId = %s   && hotelId = %s order by submittedOn desc limit 1', [statusval10, inp['id'], hotelId])

    cursor.execute('SELECT createdFor from request where id = %s  && hotelId = %s', [inp['id'], hotelId])
    createdFor = cursor.fetchall()
    createdFor = createdFor[0]['createdFor']
    cursor.execute('SELECT totalQuote from response where requestId = %s  && hotelId = %s order by submittedOn desc limit 1', [inp['id'], hotelId])
    totalQuote = cursor.fetchall()
    totalQuote = totalQuote[0]['totalQuote']
    mysql.connection.commit()

    msg = 'Your request with confirmationCode {} has been confirmed for totalQuote ${}'.format(inp['confirmationCode'], totalQuote)

    sendMail2(
        subjectv = 'Confirmation Email',
        recipientsv = createdFor,
        bodyv = msg,
    )


    flash('The request has been confirmed', 'success')
    return ('', 204)


@app.route('/notConfirmRequest',  methods=['GET', 'POST'])
@is_logged_in
def notConfirmRequest():
    inp = request.json
    cursor = mysql.connection.cursor()
    email = session['email']
    time = datetime.datetime.utcnow()
    hotelId = session.get('hotelId')
    cursor.execute(
        'SELECT * from response where requestId = %s && hotelId = %s order by submittedOn desc limit 1', [inp['id'], hotelId])
    email = session['email']
    now = datetime.datetime.utcnow()
    prevresponse = cursor.fetchall()

    if len(prevresponse) != 0:
        prevresponse = prevresponse[0]
        cursor.execute('INSERT INTO response(requestId, responseId, groupCategory, totalFare, foc, commission, commissionValue, totalQuote, cutoffDays, formPayment, paymentTerms, paymentGtd, negotiable, checkIn, checkOut, submittedBy, submittedOn, status, paymentDays, nights, comments, averageRate, contract, expectedFare, negotiationReason, timesNegotiated, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
            prevresponse['requestId'], prevresponse['responseId'], prevresponse['groupCategory'], prevresponse['totalFare'], prevresponse[
                'foc'], prevresponse['commission'], prevresponse['commissionValue'], prevresponse['totalQuote'], prevresponse['cutoffDays'],
            prevresponse['formPayment'], prevresponse['paymentTerms'], prevresponse['paymentGtd'], prevresponse[
                'negotiable'], prevresponse['checkIn'], prevresponse['checkOut'], email, now,
            statusval11, prevresponse['paymentDays'], prevresponse['nights'], prevresponse['comments'],
            prevresponse['averageRate'], prevresponse['contract'], prevresponse[
                'expectedFare'], prevresponse['negotiationReason'], prevresponse['timesNegotiated'], hotelId
        ])

        cursor.execute(
            'SELECT * From responseAvg where responseId = %s && hotelId = %s order by submittedOn desc limit 1', [prevresponse['responseId'], hotelId])
        prevAvg = cursor.fetchall()
        if len(prevAvg) != 0:
            prevAvg = prevAvg[0]
            cursor.execute('INSERT INTO responseAvg(single1, single2, double1, double2, triple1, triple2, quad1, quad2, responseId, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                prevAvg['single1'], prevAvg['single2'], prevAvg['double1'], prevAvg['double2'], prevAvg[
                    'triple1'], prevAvg['triple2'], prevAvg['quad1'], prevAvg['quad2'], prevAvg['responseId'], now, hotelId
            ])

            cursor.execute(
                'SELECT submittedOn from responseDaywise where responseId = %s  && hotelId = %s  order by submittedOn desc limit 1', [prevAvg['responseId'], hotelId])
            submittedOn = cursor.fetchall()
            cursor.execute('SELECT * From responseDaywise where responseId = %s and submittedOn = %s  && hotelId = %s ',
                           [prevAvg['responseId'], submittedOn[0]['submittedOn'], hotelId])

            prevDaywise = cursor.fetchall()
            if len(prevDaywise) != 0:
                for p in prevDaywise:
                    cursor.execute('INSERT INTO responseDaywise(date, currentOcc, discountId, occupancy, type, count, ratePerRoom, responseId, forecast, leadTime, groups, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                        p['date'], p['currentOcc'], p['discountId'], p['occupancy'], p['type'], p[
                            'count'], p['ratePerRoom'], prevAvg['responseId'], p['forecast'], p['leadTime'], p['groups'], now, hotelId
                    ])



    cursor.execute('INSERT INTO notConfirmRequest(requestId, confirmationCode, comments, submittedBy, submittedOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s)', [
                   inp['id'], inp['confirmationCode'], inp['comments'], email, time, hotelId])

    cursor.execute('UPDATE request set status = %s where id = %s  && hotelId = %s ', [
        statusval11, inp['id'], hotelId
    ])

    cursor.execute('UPDATE response set status = %s where requestId = %s  && hotelId = %s  order by submittedOn desc limit 1', [
                   statusval11, inp['id'], hotelId])


    mysql.connection.commit()

    cursor.execute('SELECT createdFor from request where id = %s  && hotelId = %s ', [inp['id'], hotelId])
    createdFor = cursor.fetchall()
    createdFor = createdFor[0]['createdFor']
   
    mysql.connection.commit()

    msg = 'Your request with confirmationCode {} has been declined by you for the following reason "{}"'.format(
        inp['confirmationCode'], inp['comments'])

    sendMail2(
        subjectv='Confirmation Email',
        recipientsv=createdFor,
        bodyv=msg,
    )

    flash('The request is now declined', 'danger')
    return ('', 204)

@app.route('/changeOcc/<id>', methods = ['GET', 'POST'])
@is_logged_in
def changeOcc(id):
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    responseId = id + "R"
    cursor.execute('SELECT submittedOn from responseDaywise where responseId = %s && hotelId = %s  order by submittedOn desc limit 1', [responseId, hotelId])
    submittedOn = cursor.fetchall()
    submittedOn = submittedOn[0]['submittedOn']
    

    cursor.execute('SELECT date, currentOcc from responseDaywise where responseId = %s and submittedOn = %s && hotelId = %s ', [responseId, submittedOn, hotelId])
    occ = cursor.fetchall()
    tempdict = {}
    for row in occ:
        tempdict[row['date']] = row['currentOcc'].split(" (")[0]
    
    flag = False
    for key, value in tempdict.copy().items():
        if (value != '' and value != '-'):
            flag = True
        else:
            tempdict.pop(key)
    
    for d in list(tempdict):
        y = d
        d = d.strftime('%y-%b-%d')
        x = d.split('-')
        d = x[2] + " " + x[1] + ", " + x[0]
        tempdict[d] = tempdict[y]
        del tempdict[y]


    
    return render_template('request/getOccEdit.html', occ = tempdict, flag = flag, token = id)


# Request Actions Done

@app.route('/analyticsbehavior', methods = ['GET', 'POST'])
@is_logged_in
def analyticsbehavior():
    return render_template('analytics/behavior.html', url = url)

@app.route('/analyticsbehaviorGet', methods = ['GET'])
@is_logged_in
def analyticsbehaviorGet():
    cursor = mysql.connection.cursor()
    startDate = request.args.get('startDate')
    endDate = request.args.get('endDate')
    leadtime = request.args.get('leadtime')
    category = request.args.get('category')
    customerType = request.args.get('customerType')
    status = request.args.get('status')
    hotelId = session.get('hotelId')

    result = {}
    result['leadres'] = []
    result['category'] = []
    result['customerType'] = []
    result['statusres'] = []
    if leadtime != 'Booking Lead Time':
        leadres = []
        tempres = {}
        if leadtime == "180 +":
            lead1 = 180
            cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && leadTime >= %s && hotelId = %s', [startDate, endDate, lead1, hotelId])
            leadres1 = cursor.fetchall()
        else:
            t1 = leadtime.split(' - ')
            lead1 = t1[0]
            lead2 = t1[1]
            cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && leadTime >= %s && leadTime <= %s && hotelId = %s', [startDate, endDate, int(lead1), int(lead2), hotelId])
            leadres1 = cursor.fetchall()
        

        tempres['0'] = leadtime
        tempres['1'] = len(leadres1)
        if len(leadres1) != 0:
            nights = 0
            for r in leadres1:
                nights = nights + int(r['nights'])
            
            nights = nights / len(leadres1)
            nights = round(nights, 2)
            tempres['2'] = nights
        else:
            tempres['2'] = 0
        leadres.append(tempres)
    else:
        leadres = []
        tempres1 = {}
        tempres1['0'] = "0 - 14"
        tempres2 = {}
        tempres2['0'] = "14 - 45"
        tempres3 = {}
        tempres3['0'] = "45 - 120"
        tempres4 = {}
        tempres4['0'] = "120 - 180"
        tempres5 = {}
        tempres5['0'] = "180 +"

        cursor.execute('SELECT * from request where createdOn >= %s && createdOn <= %s && leadTime >= %s && leadTime <= %s && hotelId = %s', [startDate, endDate, 0, 14, hotelId])
        leadres1 = cursor.fetchall()
        tempres1['1'] = len(leadres1)
        if len(leadres1) != 0:
            nights = 0
            for r in leadres1:
                nights = nights + int(r['nights'])
            
            nights = nights / len(leadres1)
            nights = round(nights, 2)
            tempres1['2'] = nights
        else:
            tempres1['2'] = 0
        leadres.append(tempres1)

        cursor.execute('SELECT * from request where createdOn >= %s && createdOn <= %s && leadTime > %s && leadTime <= %s && hotelId = %s', [startDate, endDate, 14, 45, hotelId])
        leadres2 = cursor.fetchall()
        tempres2['1'] = len(leadres2)
        if len(leadres2) != 0:
            nights = 0
            for r in leadres2:
                nights = nights + int(r['nights'])
            
            nights = nights / len(leadres2)
            nights = round(nights, 2)
            tempres2['2'] = nights
        else:
            tempres2['2'] = 0
        leadres.append(tempres2)  

        cursor.execute('SELECT * from request where createdOn >= %s && createdOn <= %s && leadTime > %s && leadTime <= %s && hotelId = %s', [startDate, endDate, 45, 120, hotelId])
        leadres3 = cursor.fetchall()
        tempres3['1'] = len(leadres3)
        if len(leadres3) != 0:
            nights = 0
            for r in leadres3:
                nights = nights + int(r['nights'])
            
            nights = nights / len(leadres3)
            nights = round(nights, 2)
            tempres3['2'] = nights
        else:
            tempres3['2'] = 0
        leadres.append(tempres3)    

        cursor.execute('SELECT * from request where createdOn >= %s && createdOn <= %s && leadTime > %s && leadTime <= %s && hotelId = %s', [startDate, endDate, 120, 180, hotelId])
        leadres4 = cursor.fetchall()
        tempres4['1'] = len(leadres4)
        if len(leadres4) != 0:
            nights = 0
            for r in leadres4:
                nights = nights + int(r['nights'])
            
            nights = nights / len(leadres4)
            nights = round(nights, 2)
            tempres4['2'] = nights
        else:
            tempres4['2'] = 0
        leadres.append(tempres4)    

        cursor.execute('SELECT * from request where createdOn >= %s && createdOn <= %s && leadTime > %s && hotelId = %s', [startDate, endDate, 180, hotelId])
        leadres5 = cursor.fetchall()
        tempres5['1'] = len(leadres5)
        if len(leadres5) != 0:
            nights = 0
            for r in leadres5:
                nights = nights + int(r['nights'])
            
            nights = nights / len(leadres5)
            nights = round(nights, 2)
            tempres5['2'] = nights
        else:
            tempres5['2'] = 0
        leadres.append(tempres5)           

    result['leadres'] = leadres

    if category != 'Category':
        catres = []
        tempres = {} 
        cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && category = %s && hotelId = %s', [startDate, endDate, category, hotelId])
        tempres1 = cursor.fetchall()
        tempres['0'] = category
        tempres['1'] = len(tempres1)
        if len(tempres1) != 0:
            nights = 0
            for r in tempres1:
                nights = nights + int(r['nights'])

            nights = nights / len(tempres1)
            nights = round(nights, 2)
            tempres['2'] = nights
        else:
            tempres['2'] = 0
        catres.append(tempres)
    else:
        catres = []
        cursor.execute('show columns from requestCategory')
        categories = cursor.fetchall()
        for c in categories:
            cat = c['Field']
            tempres = {}
            cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && category = %s && hotelId = %s', [startDate, endDate, cat, hotelId])
            tempres1 = cursor.fetchall()
            tempres['0'] = cat
            tempres['1'] = len(tempres1)
            if len(tempres1) != 0:
                nights = 0
                for r in tempres1:
                    nights = nights + int(r['nights'])

                nights = nights / len(tempres1)
                nights = round(nights, 2)
                tempres['2'] = nights
            else:
                tempres['2'] = 0
            catres.append(tempres)

    
    result['catres'] = catres

    if customerType != 'Customer Type':
        custres = []
        tempres = {}
        if (customerType == 'IATA'):
            cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && userType = %s && hotelId = %s', [startDate, endDate, customerType, hotelId])
            tempres1 = cursor.fetchall()
            tempres['0'] = customerType
            tempres['1'] = len(tempres1)
            if len(tempres1) != 0:
                nights = 0
                for r in tempres1:
                    nights = nights + int(r['nights'])

                nights = nights / len(tempres1)
                nights = round(nights, 2)
                tempres['2'] = nights
            else:
                tempres['2'] = 0
            catres.append(tempres)
        else:
            cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && userType = %s  && hotelId = %s',
                           [startDate, endDate, "customer", hotelId])
            tempres1 = cursor.fetchall()
            count = 0
            nights = 0
            for r in tempres1:
                cursor.execute('SELECT userSubType from users where email = %s && hotelId = %s', [r['createdFor'], hotelId])
                dd = cursor.fetchall()
                if (dd[0]['userSubType'] == customerType):
                    count = count + 1
                    nights = nights + int(r['nights'])
            
            if (count != 0):
                nights = nights / count
                nights = round(nights, 2)
            else:
                nights = 0
            
            tempres['0'] = customerType
            tempres['1'] = count
            tempres['2'] = nights
        custres.append(tempres)
    else:
        custres = []
        tempres = {}
        cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && userType = %s && hotelId = %s', [startDate, endDate, "IATA", hotelId])
        tempres1 = cursor.fetchall()
        tempres['0'] = "IATA"
        tempres['1'] = len(tempres1)
        if len(tempres1) != 0:
            nights = 0
            for r in tempres1:
                nights = nights + int(r['nights'])

            nights = nights / len(tempres1)
            nights = round(nights, 2)
            tempres['2'] = nights
        else:
            tempres['2'] = 0
        custres.append(tempres)

        cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && userType = %s && hotelId = %s', [startDate, endDate, "customer", hotelId])
        count1 = 0
        count2 = 0
        count3 = 0
        night1 = 0
        night2 = 0
        night3 = 0
        tempres1 = cursor.fetchall()
        for r in tempres1:
            cursor.execute('SELECT userSubType from users where email = %s && hotelId = %s', [r['createdFor'], hotelId])
            dd = cursor.fetchall()
            if (dd[0]['userSubType'] == 'retail'):
                count1 = count1 + 1
                night1 = night1 + int(r['nights'])
            elif (dd[0]['userSubType'] == 'corporate'):
                count2 = count2 + 1
                night2 = night2 + int(r['nights'])
            elif (dd[0]['userSubType'] == 'tour'):
                count3 = count3 + 1
                night3 = night3 + int(r['nights'])
            
        if (count1 != 0):
            night1 = night1 / count1
            night1 = round(night1, 2)
        else:
            night1 = 0

        if (count2 != 0):
            night2 = night2 / count2
            night2 = round(night2, 2)
        else:
            night2 = 0
        
        if (count3 != 0):
            night3 = night3 / count3
            night3 = round(night3, 2)
        else:
            night3 = 0

        tempres1 = {}
        tempres2 = {}
        tempres3 = {}
        tempres1['0'] = "retail"
        tempres1['1'] = count1
        tempres1['2'] = night1
        custres.append(tempres1)

        tempres2['0'] = "corporate"
        tempres2['1'] = count2
        tempres2['2'] = night2
        custres.append(tempres2)

        tempres3['0'] = "tour"
        tempres3['1'] = count3
        tempres3['2'] = night3
        custres.append(tempres3)
    
    result['custres'] = custres

    if (status != 'Status'):
        statusres = []
        tempres = {}
        cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && status = %s && hotelId = %s', [startDate, endDate, status, hotelId])
        tempres1 = cursor.fetchall()
        tempres['0'] = status
        tempres['1'] = len(tempres1)
        if len(tempres1) != 0:
            nights = 0
            for r in tempres1:
                nights = nights + int(r['nights'])
            
            nights = nights / len(tempres1)
            nights = round(nights, 2)
            tempres['2'] = nights
        else:
            tempres['2'] = 0
        statusres.append(tempres)
    else:
        statusres = []
        statuses = [statusval1, statusval2, statusval3, statusval4, statusval5, statusval6, statusval7, statusval8, statusval9, statusval10, statusval11 ]
        for s in statuses:
            tempres = {}
            cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && status = %s && hotelId = %s', [startDate, endDate, s, hotelId])
            tempres1 = cursor.fetchall()
            tempres['0'] = s
            tempres['1'] = len(tempres1)
            if len(tempres1) != 0:
                nights = 0
                for r in tempres1:
                    nights = nights + int(r['nights'])

                nights = nights / len(tempres1)
                nights = round(nights, 2)
                tempres['2'] = nights
            else:
                tempres['2'] = 0
            statusres.append(tempres)

    result['statusres'] = statusres
    return jsonify(result), 200
    

@app.route('/analyticsdashboard', methods = ['GET', 'POST'])
@is_logged_in
def analyticsdashboard():
    cursor = mysql.connection.cursor()
    endDate = datetime.datetime.today()
    startDate = endDate - datetime.timedelta(days = 31)
    hotelId = session.get('hotelId')

    startDatePass = startDate.strftime('%y-%b-%d')
    x = startDatePass.split('-')
    startDatePass = x[2] + " " + x[1] + ", " + x[0]

    endDatePass = endDate.strftime('%y-%b-%d')
    x = endDatePass.split('-')
    endDatePass = x[2] + " " + x[1] + ", " + x[0]


    result = {}
    result['leadres'] = []
    leadres = []
    tempres1 = {}
    tempres1['0'] = "0 - 14"
    tempres2 = {}
    tempres2['0'] = "14 - 45"
    tempres3 = {}
    tempres3['0'] = "45 - 120"
    tempres4 = {}
    tempres4['0'] = "120 - 180"
    tempres5 = {}
    tempres5['0'] = "180 +"

    cursor.execute('SELECT * from request where createdOn >= %s && createdOn <= %s && leadTime >= %s && leadTime <= %s && hotelId = %s', [startDate, endDate, 0, 14, hotelId])
    leadres1 = cursor.fetchall()
    tempres1['1'] = len(leadres1)
    leadres.append(tempres1)

    cursor.execute('SELECT * from request where createdOn >= %s && createdOn <= %s && leadTime > %s && leadTime <= %s && hotelId = %s', [startDate, endDate, 14, 45, hotelId])
    leadres2 = cursor.fetchall()
    tempres2['1'] = len(leadres2)
    leadres.append(tempres2)  

    cursor.execute('SELECT * from request where createdOn >= %s && createdOn <= %s && leadTime > %s && leadTime <= %s && hotelId = %s', [startDate, endDate, 45, 120, hotelId])
    leadres3 = cursor.fetchall()
    tempres3['1'] = len(leadres3)
    leadres.append(tempres3)    

    cursor.execute('SELECT * from request where createdOn >= %s && createdOn <= %s && leadTime > %s && leadTime <= %s && hotelId = %s', [startDate, endDate, 120, 180, hotelId])
    leadres4 = cursor.fetchall()
    tempres4['1'] = len(leadres4)
    leadres.append(tempres4)    

    cursor.execute('SELECT * from request where createdOn >= %s && createdOn <= %s && leadTime > %s && hotelId = %s', [startDate, endDate, 180, hotelId])
    leadres5 = cursor.fetchall()
    tempres5['1'] = len(leadres5)
    leadres.append(tempres5)           

    cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && hotelId = %s', [startDate, endDate, hotelId])
    requests = cursor.fetchall()
    table = {
        "0 - 2": 0,
        "2 - 8": 0,
        "8 - 24":0,
        "24 +":0,
    }
    notSubmitted = 0
    resHours = []
    for r in requests:
        cursor.execute('SELECT submittedOn from response where requestId = %s && (status = %s or status = %s  && hotelId = %s) order by submittedOn asc limit 1', [r['id'], statusval2, statusval8, hotelId])
        res = cursor.fetchall()
        if len(res) == 0:
            notSubmitted = notSubmitted + 1
        else:
            difference = abs(res[0]['submittedOn'] - r['createdOn'])
            difference = difference.total_seconds()
            hours = divmod(difference, 3600)[0]
            resHours.append(hours)
            if hours >= 0 and hours <= 2:
                table["0 - 2"] = table["0 - 2"] + 1
            elif hours >2 and hours <= 8:
                table["2 - 8"] = table['2 - 8'] + 1
            elif hours > 8 and hours <= 24:
                table['8 - 24'] = table['8 - 24'] + 1
            elif hours > 24:
                table["24 +"] = table["24 +"] + 1

    hotelres = {}
    hotelres['notSubmitted'] = notSubmitted
    hotelres['table'] = table


    cursor.execute('SELECT DISTINCT responseId From response where submittedOn >= %s && submittedOn <= %s && status = %s && hotelId = %s', [startDate, endDate, statusval2, hotelId])
    notSubmitted = 0
    table = {
        "0 - 2": 0,
        "2 - 8": 0,
        "8 - 24": 0,
        "24 +": 0,
    }
    responseData = cursor.fetchall()
    for r in responseData:
        cursor.execute('SELECT submittedOn From response where submittedOn >= %s && submittedOn <= %s && status = %s && responseId = %s && hotelId = %s order by submittedOn asc limit 1', [startDate, endDate, statusval2, r['responseId'], hotelId])
        tempres = cursor.fetchall()
        if len(tempres) == 0:
            notSubmitted = notSubmitted + 1
        else:
            cursor.execute('SELECT submittedOn From response where submittedOn >= %s && submittedOn <= %s && (status = %s or status = %s) && responseId = %s  && hotelId = %s order by submittedOn asc limit 1', [startDate, endDate, statusval4, statusval5, r['responseId'], hotelId])
            customerres = cursor.fetchall()
            if len(customerres) == 0:
                notSubmitted = notSubmitted + 1
            else:
                difference = customerres[0]['submittedOn'] - tempres[0]['submittedOn']
                difference = difference.total_seconds()
                hours = divmod(difference, 3600)[0]
                if hours >= 0 and hours <= 2:
                    table["0 - 2"] = table["0 - 2"] + 1
                elif hours >2 and hours <= 8:
                    table["2 - 8"] = table['2 - 8'] + 1
                elif hours > 8 and hours <= 24:
                    table['8 - 24'] = table['8 - 24'] + 1
                elif hours > 24:
                    table["24 +"] = table["24 +"] + 1

    customeres = {}
    customeres['notSubmitted'] = notSubmitted
    customeres['table'] = table

    revenueres = {}
    cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && hotelId = %s', [startDate, endDate, hotelId])
    tempres1 = cursor.fetchall()
    if len(tempres1) != 0:
        total1 = 0
        total2 = 0
        for r in tempres1:
            if (r['status'] == statusval10):
                cursor.execute('SELECT * from response where requestId = %s && status = %s  && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                res = cursor.fetchall()
                if len(res) == 0:
                    total2 = total2 + 0
                else:
                    total2 = total2 + float(res[0]['totalQuote'])
            elif (r['status'] == statusval2 or r['status'] == statusval4 or r['status'] == statusval8 or r['status'] == statusval11):
                cursor.execute('SELECT * From response where requestId = %s && status = %s && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                res = cursor.fetchall()
                if len(res) == 0:
                    total1 = total1 + 0
                else:
                    total1 = total1 + float(res[0]['totalQuote'])
            revenueres['1'] = total1
            revenueres['2'] = total2
    else:
        revenueres['1'] = 0
        revenueres['2'] = 0


    startDate = datetime.datetime.today()
    endDate = startDate + datetime.timedelta(days = 5)
    cursor.execute('SELECT * From request where checkIn >= %s && checkOut <= %s  && hotelId = %s order by checkIn', [startDate, endDate, hotelId])
    upcoming = cursor.fetchall()


    return render_template('analytics/dashboard.html', leadres = leadres, hotelres = hotelres, revenueres = [revenueres], customeres = [customeres], upcoming = upcoming, url = url, startDatePass = startDatePass, endDatePass = endDatePass)

@app.route('/analyticsperformance', methods = ['GET', 'POST'])
@is_logged_in
def analyticsperformance():
    return render_template('analytics/performance.html', url = url)

@app.route('/analyticsperformanceGet', methods = ['GET'])
@is_logged_in
def analyticsperformanceGet():
    cursor = mysql.connection.cursor()
    startDate = request.args.get('startDate')
    endDate = request.args.get('endDate')
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && hotelId = %s', [startDate, endDate, hotelId])
    requests = cursor.fetchall()
    result = {}
    result['requestsNo'] = len(requests)
    notSubmitted = 0
    resHours = []
    table = {
        "0 - 2": 0,
        "2 - 8": 0,
        "8 - 24":0,
        "24 +":0,
    }
    for r in requests:
        cursor.execute('SELECT submittedOn from response where requestId = %s && (status = %s or status = %s && hotelId = %s) order by submittedOn asc limit 1', [r['id'], statusval2, statusval8, hotelId])
        res = cursor.fetchall()
        if len(res) == 0:
            notSubmitted = notSubmitted + 1
        else:
            difference = abs(res[0]['submittedOn'] - r['createdOn'])
            difference = difference.total_seconds()
            hours = divmod(difference, 3600)[0]
            resHours.append(hours)
            if hours >= 0 and hours <= 2:
                table["0 - 2"] = table["0 - 2"] + 1
            elif hours >2 and hours <= 8:
                table["2 - 8"] = table['2 - 8'] + 1
            elif hours > 8 and hours <= 24:
                table['8 - 24'] = table['8 - 24'] + 1
            elif hours > 24:
                table["24 +"] = table["24 +"] + 1


    temp = 0
    for r in resHours:
        temp = temp + r


    if len(resHours) != 0:
        temp = temp / len(resHours)
        temp = round(temp, 2)
    result['time'] = temp
    result['notSubmitted'] = notSubmitted
    result['table'] = table

    count = 0
    cursor.execute('SELECT DISTINCT responseId From response where submittedOn >= %s && submittedOn <= %s && status = %s && hotelId = %s', [startDate, endDate, statusval2, hotelId])
    notSubmitted = 0
    resHours = []
    table = {
        "0 - 2": 0,
        "2 - 8": 0,
        "8 - 24": 0,
        "24 +": 0,
    }
    responseData = cursor.fetchall()
    for r in responseData:
        cursor.execute('SELECT submittedOn From response where submittedOn >= %s && submittedOn <= %s && status = %s && responseId = %s  && hotelId = %s order by submittedOn asc limit 1', [startDate, endDate, statusval2, r['responseId'], hotelId])
        tempres = cursor.fetchall()
        if len(tempres) == 0:
            notSubmitted = notSubmitted + 1
        else:
            count = count + 1
            cursor.execute('SELECT submittedOn From response where submittedOn >= %s && submittedOn <= %s && (status = %s or status = %s) && responseId = %s && hotelId = %s order by submittedOn asc limit 1', [startDate, endDate, statusval4, statusval5, r['responseId'], hotelId])
            customerres = cursor.fetchall()
            if len(customerres) == 0:
                notSubmitted = notSubmitted + 1
            else:
                difference = customerres[0]['submittedOn'] - tempres[0]['submittedOn']
                difference = difference.total_seconds()
                hours = divmod(difference, 3600)[0]
                resHours.append(hours)
                if hours >= 0 and hours <= 2:
                    table["0 - 2"] = table["0 - 2"] + 1
                elif hours >2 and hours <= 8:
                    table["2 - 8"] = table['2 - 8'] + 1
                elif hours > 8 and hours <= 24:
                    table['8 - 24'] = table['8 - 24'] + 1
                elif hours > 24:
                    table["24 +"] = table["24 +"] + 1

    temp = 0
    for r in resHours:
        temp = temp + r


    if len(resHours) != 0:
        temp = temp / len(resHours)
        temp = round(temp, 2)
    result['2time'] = temp
    result['2notSubmitted'] = notSubmitted
    result['2table'] = table
    result['responsesNo'] = count
        
    return jsonify(result), 200



@app.route('/analyticsrevenue', methods = ['GET', 'POST'])
@is_logged_in
def analyticsrevenue():
    return render_template('analytics/revenue.html', url = url)


@app.route('/analyticsrevenueGet', methods = ['GET', 'POST'])
@is_logged_in
def analyticsrevenueGet():
    cursor = mysql.connection.cursor()
    startDate = request.args.get('startDate')
    endDate = request.args.get('endDate')
    category = request.args.get('category')
    customerType = request.args.get('customerType')
    hotelId = session.get('hotelId')
    result = {}
    result['category'] = []
    result['customerType'] = []

    if category != 'Category':
        catres = []
        tempres = {}
        cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && category = %s && hotelId = %s', [startDate, endDate, category, hotelId])
        tempres1 = cursor.fetchall()
        tempres['0'] = category
        if len(tempres1) != 0:
            total1 = 0
            total2 = 0
            for r in tempres1:
                if (r['status'] == statusval10):
                    cursor.execute('SELECT * from response where requestId = %s && status = %s && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                    res = cursor.fetchall()
                    if len(res) == 0:
                        total2 = total2 + 0
                    else:
                        total2 = total2 + float(res[0]['totalQuote'])
                elif (r['status'] == statusval2 or r['status'] == statusval4 or r['status'] == statusval8 or r['status'] == statusval11):
                    cursor.execute('SELECT * From response where requestId = %s && status = %s && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                    res = cursor.fetchall()
                    if len(res) == 0:
                        total1 = total1 + 0
                    else:
                        total1 = total1 + float(res[0]['totalQuote'])
            tempres['1'] = total1
            tempres['2'] = total2
        else:
            tempres['1'] = 0
            tempres['2'] = 0
        catres.append(tempres)
    else:
        catres = []
        cursor.execute('show columns from requestCategory')
        categories = cursor.fetchall()
        for c in categories:
            cat = c['Field']
            tempres = {}
            cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && category = %s && hotelId = %s', [startDate, endDate, cat, hotelId])
            tempres1 = cursor.fetchall()
            tempres['0'] = cat
            if len(tempres1) != 0:
                total1 = 0
                total2 = 0
                for r in tempres1:
                    if (r['status'] == statusval10):
                        cursor.execute('SELECT * from response where requestId = %s && status = %s  && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                        res = cursor.fetchall()
                        if len(res) == 0:
                            total2 = total2 + 0
                        else:
                            total2 = total2 + float(res[0]['totalQuote'])
                    elif (r['status'] == statusval2 or r['status'] == statusval4 or r['status'] == statusval8 or r['status'] == statusval11):
                        cursor.execute('SELECT * From response where requestId = %s && status = %s && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                        res = cursor.fetchall()
                        if len(res) == 0:
                            total1 = total1 + 0
                        else:
                            total1 = total1 + float(res[0]['totalQuote'])
                tempres['1'] = total1
                tempres['2'] = total2
            else:
                tempres['1'] = 0
                tempres['2'] = 0
            
            catres.append(tempres)
    
    if customerType != 'Customer Type':
        custres = []
        tempres = {}
        if (customerType == 'IATA'):
            cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && userType = %s && hotelId = %s', [startDate, endDate, customerType, hotelId])
            tempres1 = cursor.fetchall()
            tempres['0'] = customerType
            if len(tempres1) != 0:
                total1 = 0
                total2 = 0
                for r in tempres1:
                    if (r['status'] == statusval10):
                        cursor.execute('SELECT * from response where requestId = %s && status = %s && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                        res = cursor.fetchall()
                        if len(res) == 0:
                            total2 = total2 + 0
                        else:
                            total2 = total2 + float(res[0]['totalQuote'])
                    elif (r['status'] == statusval2 or r['status'] == statusval4 or r['status'] == statusval8 or r['status'] == statusval11):
                        cursor.execute('SELECT * From response where requestId = %s && status = %s  && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                        res = cursor.fetchall()
                        if len(res) == 0:
                            total1 = total1 + 0
                        else:
                            total1 = total1 + float(res[0]['totalQuote'])
                tempres['1'] = total1
                tempres['2'] = total2
            else:
                tempres['1'] = 0
                tempres['2'] = 0
            
            custres.append(tempres)
        else:
            cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && userType = %s  && hotelId = %s',
                           [startDate, endDate, "customer", hotelId])
            tempres1 = cursor.fetchall()
            tempres['0'] = customerType
            total1 = 0
            total2 = 0
            for r in tempres1:
                cursor.execute('SELECT userSubType from users where email = %s && hotelId = %s', [r['createdFor'], hotelId])
                dd = cursor.fetchall()
                if (dd[0]['userSubType'] == customerType):
                    if (r['status'] == statusval10):
                        cursor.execute('SELECT * from response where requestId = %s && status = %s && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                        res = cursor.fetchall()
                        if len(res) == 0:
                            total2 = total2 + 0
                        else:
                            total2 = total2 + float(res[0]['totalQuote'])
                    elif (r['status'] == statusval2 or r['status'] == statusval4 or r['status'] == statusval8 or r['status'] == statusval11):
                        cursor.execute('SELECT * From response where requestId = %s && status = %s && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                        res = cursor.fetchall()
                        if len(res) == 0:
                            total1 = total1 + 0
                        else:
                            total1 = total1 + float(res[0]['totalQuote'])
            tempres['1'] = total1
            tempres['2'] = total2

        custres.append(tempres)
    else:
        custres = []
        tempres = {}
        cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && userType = %s && hotelId = %s', [startDate, endDate, "IATA", hotelId])
        tempres1 = cursor.fetchall()
        tempres['0'] = "IATA"
        if len(tempres1) != 0:
            total1 = 0
            total2 = 0
            for r in tempres1:
                if (r['status'] == statusval10):
                    cursor.execute('SELECT * from response where requestId = %s && status = %s && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                    res = cursor.fetchall()
                    if len(res) == 0:
                        total2 = total2 + 0
                    else:
                        total2 = total2 + float(res[0]['totalQuote'])
                elif (r['status'] == statusval2 or r['status'] == statusval4 or r['status'] == statusval8 or r['status'] == statusval11):
                    cursor.execute('SELECT * From response where requestId = %s && status = %s && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                    res = cursor.fetchall()
                    if len(res) == 0:
                        total1 = total1 + 0
                    else:
                        total1 = total1 + float(res[0]['totalQuote'])
            tempres['1'] = total1
            tempres['2'] = total2
        else:
            tempres['1'] = 0
            tempres['2'] = 0
            
        custres.append(tempres)

        cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && userType = %s && hotelId = %s', [startDate, endDate, "customer", hotelId])
        total1 = 0
        total2 = 0
        total3 = 0
        total4 = 0
        total5 = 0
        total6 = 0
        tempres1 = cursor.fetchall()
        for r in tempres1:
            cursor.execute('SELECT userSubType from users where email = %s && hotelId = %s', [r['createdFor'], hotelId])
            dd = cursor.fetchall()
            if (dd[0]['userSubType'] == 'retail'):
                if (r['status'] == statusval10):
                    cursor.execute('SELECT * from response where requestId = %s && status = %s && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                    res = cursor.fetchall()
                    if len(res) == 0:
                        total2 = total2 + 0
                    else:
                        total2 = total2 + float(res[0]['totalQuote'])
                elif (r['status'] == statusval2 or r['status'] == statusval4 or r['status'] == statusval8 or r['status'] == statusval11):
                    cursor.execute('SELECT * From response where requestId = %s && status = %s  && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                    res = cursor.fetchall()
                    if len(res) == 0:
                        total1 = total1 + 0
                    else:
                        total1 = total1 + float(res[0]['totalQuote'])
            elif (dd[0]['userSubType'] == 'corporate'):
                if (r['status'] == statusval10):
                    cursor.execute('SELECT * from response where requestId = %s && status = %s && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                    res = cursor.fetchall()
                    if len(res) == 0:
                        total4 = total4 + 0
                    else:
                        total4 = total4 + float(res[0]['totalQuote'])
                elif (r['status'] == statusval2 or r['status'] == statusval4 or r['status'] == statusval8 or r['status'] == statusval11):
                    cursor.execute('SELECT * From response where requestId = %s && status = %s && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                    res = cursor.fetchall()
                    if len(res) == 0:
                        total3 = total3 + 0
                    else:
                        total3 = total3 + float(res[0]['totalQuote'])
            elif (dd[0]['userSubType'] == 'tour'):
                if (r['status'] == statusval10):
                    cursor.execute('SELECT * from response where requestId = %s && status = %s && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                    res = cursor.fetchall()
                    if len(res) == 0:
                        total6 = total6 + 0
                    else:
                        total6 = total6 + float(res[0]['totalQuote'])
                elif (r['status'] == statusval2 or r['status'] == statusval4 or r['status'] == statusval8 or r['status'] == statusval11):
                    cursor.execute('SELECT * From response where requestId = %s && status = %s  && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                    res = cursor.fetchall()
                    if len(res) == 0:
                        total5 = total5 + 0
                    else:
                        total5 = total5 + float(res[0]['totalQuote'])

        tempres1 = {}
        tempres2 = {}
        tempres3 = {}
        tempres1['0'] = "retail"
        tempres1['1'] = total1
        tempres1['2'] = total2
        custres.append(tempres1)

        tempres2['0'] = "corporate"
        tempres2['1'] = total3
        tempres2['2'] = total4
        custres.append(tempres2)

        tempres3['0'] = "tour"
        tempres3['1'] = total5
        tempres3['2'] = total6
        custres.append(tempres3)


    result['category'] = catres
    result['customerType'] = custres
    return jsonify(result), 200

@app.route('/analyticstracking', methods = ['GET', 'POST'])
@is_logged_in
def analyticstracking():
    cursor = mysql.connection.cursor()
    date = datetime.date.today()
    enddate = date + datetime.timedelta(days = 31)
    enddate = datetime.datetime.combine(enddate, datetime.datetime.min.time())
    hotelId = session.get('hotelId')

    cursor.execute('SELECT * from settingsTimelimit where hotelId = %s order by submittedOn desc limit 1', [hotelId])
    expiry = cursor.fetchall()
    if len(expiry) != 0:
        expiry = expiry[0]['value']

    cursor.execute('SELECT * From request where status = %s && hotelId = %s', [statusval2, hotelId])
    requests = cursor.fetchall()
    result = []
    for r in requests:
        tempresult = {}
        cursor.execute('SELECT * From response where requestId = %s && status = %s && hotelId = %s order by submittedOn desc limit 1', [r['id'], statusval2, hotelId])
        response = cursor.fetchall()
        submittedOn = response[0]['submittedOn']
        expiration = submittedOn + datetime.timedelta(hours = float(expiry))
        if expiration < enddate:
            tempresult['id'] = r['id']
            tempresult['expiry'] = expiration
            result.append(tempresult)
    
    cursor.execute('SELECT * From request where status = %s && hotelId = %s', [statusval4, hotelId])
    requests = cursor.fetchall()
    result2 = []
    for r in requests:
        tempresult = {}
        cursor.execute('SELECT paymentGtd from response where requestId = %s && status = %s  && hotelId = %s order by submittedOn desc limit 1', [r['id'], statusval4, hotelId])
        response = cursor.fetchall()
        if len(response) != 0:
            if response[0]['paymentGtd'] == 1:
                tempresult['id'] = r['id']
                tempresult['groupName'] = r['groupName']
                tempresult['checkIn'] = r['checkIn']
                tempresult['checkOut'] = r['checkOut']
                result2.append(tempresult)
    
    cursor.execute('SELECT * from request where checkIn >= %s && checkOut <= %s && hotelId = %s', [date, enddate, hotelId])
    requests = cursor.fetchall()
    result3 = []
    for r in requests:
        tempresult = {}
        tempresult['checkIn'] = r['checkIn']
        tempresult['checkOut'] = r['checkOut']
        tempresult['status'] = r['status']
        tempresult['id'] = r['id']
        tempresult['category'] = r['category']
        tempresult['groupName'] = r['groupName']
        result3.append(tempresult)


    return render_template('analytics/tracking.html', result = result, result2 = result2, result3 = result3)


@app.route('/stdreport', methods = ['GET', 'POST'])
@is_logged_in
def stdreport():
    return render_template('analytics/stdreport.html', url = url)

@app.route('/analyticsstdreportGet', methods = ['GET', 'POST'])
@is_logged_in
def analyticsstdreportGet():
    cursor = mysql.connection.cursor()
    startDate = request.args.get('startDate')
    endDate = request.args.get('endDate')
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && hotelId = %s', [startDate, endDate, hotelId])
    requestData = cursor.fetchall()
    for r in requestData:
        cursor.execute('SELECT * From response where requestId = %s && status = %s && hotelId = %s order by submittedOn desc limit 1', [r['id'], statusval2, hotelId])
        totalQuote = cursor.fetchall()
        if len(totalQuote) == 0:
            r['totalQuote'] = 0
            r['evaluatedFare'] = 0
        else:
            r['totalQuote'] = totalQuote[0]['totalQuote']
            r['expiryTime'] = totalQuote[0]['expiryTime']
            r['negotiationReason'] = totalQuote[0]['negotiationReason']
            r['expectedFare'] = totalQuote[0]['expectedFare']
            r['overrideReason'] = totalQuote[0]['overrideReason']
            r['overrideFlag'] = totalQuote[0]['overrideFlag']
            r['timesNegotiated'] = totalQuote[0]['timesNegotiated']
            responseId = r['id'] + "R"
            submittedOn = totalQuote[0]['submittedOn']
            cursor.execute('SELECT * from responseDaywise where responseId = %s and submittedOn = %s && hotelId = %s', [responseId, submittedOn, hotelId])
            prev = cursor.fetchall()
            total = 0
            for p in prev:
                rate = p['ratePerRoom'].split('(')
                if len(rate) == 1:
                    total = total + int(p['count']) * float(rate[0])
                else:
                    rate = rate[1].split(' : ')[1].split('[')[0]
                    total = total + int(p['count']) * float(rate)
            r['evaluatedFare'] = total

    return {'response' : requestData}, 200


@app.route('/analyticsDashboardGet', methods = ['GET', 'POST'])
def analyticsDashboardGet():
    startDate = request.args.get('startDate')
    endDate = request.args.get('endDate')
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    result = {}
    result['leadres'] = []
    leadres = []
    tempres1 = {}
    tempres1['0'] = "0 - 14"
    tempres2 = {}
    tempres2['0'] = "14 - 45"
    tempres3 = {}
    tempres3['0'] = "45 - 120"
    tempres4 = {}
    tempres4['0'] = "120 - 180"
    tempres5 = {}
    tempres5['0'] = "180 +"

    cursor.execute('SELECT * from request where createdOn >= %s && createdOn <= %s && leadTime >= %s && leadTime <= %s && hotelId = %s', [startDate, endDate, 0, 14, hotelId])
    leadres1 = cursor.fetchall()
    tempres1['1'] = len(leadres1)
    leadres.append(tempres1)

    cursor.execute('SELECT * from request where createdOn >= %s && createdOn <= %s && leadTime > %s && leadTime <= %s && hotelId = %s', [startDate, endDate, 14, 45, hotelId])
    leadres2 = cursor.fetchall()
    tempres2['1'] = len(leadres2)
    leadres.append(tempres2)  

    cursor.execute('SELECT * from request where createdOn >= %s && createdOn <= %s && leadTime > %s && leadTime <= %s && hotelId = %s', [startDate, endDate, 45, 120, hotelId])
    leadres3 = cursor.fetchall()
    tempres3['1'] = len(leadres3)
    leadres.append(tempres3)    

    cursor.execute('SELECT * from request where createdOn >= %s && createdOn <= %s && leadTime > %s && leadTime <= %s && hotelId = %s', [startDate, endDate, 120, 180, hotelId])
    leadres4 = cursor.fetchall()
    tempres4['1'] = len(leadres4)
    leadres.append(tempres4)    

    cursor.execute('SELECT * from request where createdOn >= %s && createdOn <= %s && leadTime > %s && hotelId = %s', [startDate, endDate, 180, hotelId])
    leadres5 = cursor.fetchall()
    tempres5['1'] = len(leadres5)
    leadres.append(tempres5)

    result['leadres'] = leadres
    cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && hotelId = %s', [startDate, endDate, hotelId])
    requests = cursor.fetchall()
    table = {
        "0 - 2": 0,
        "2 - 8": 0,
        "8 - 24":0,
        "24 +":0,
    }
    notSubmitted = 0
    resHours = []
    for r in requests:
        cursor.execute('SELECT submittedOn from response where requestId = %s && (status = %s or status = %s && hotelId = %s) order by submittedOn asc limit 1', [r['id'], statusval2, statusval8, hotelId])
        res = cursor.fetchall()
        if len(res) == 0:
            notSubmitted = notSubmitted + 1
        else:
            difference = abs(res[0]['submittedOn'] - r['createdOn'])
            difference = difference.total_seconds()
            hours = divmod(difference, 3600)[0]
            resHours.append(hours)
            if hours >= 0 and hours <= 2:
                table["0 - 2"] = table["0 - 2"] + 1
            elif hours >2 and hours <= 8:
                table["2 - 8"] = table['2 - 8'] + 1
            elif hours > 8 and hours <= 24:
                table['8 - 24'] = table['8 - 24'] + 1
            elif hours > 24:
                table["24 +"] = table["24 +"] + 1

    hotelres = {}
    hotelres['notSubmitted'] = notSubmitted
    hotelres['table'] = table

    result['hotelres'] = hotelres

    cursor.execute('SELECT DISTINCT responseId From response where submittedOn >= %s && submittedOn <= %s && status = %s && hotelId = %s', [startDate, endDate, statusval2, hotelId])
    notSubmitted = 0
    table = {
        "0 - 2": 0,
        "2 - 8": 0,
        "8 - 24": 0,
        "24 +": 0,
    }
    responseData = cursor.fetchall()
    for r in responseData:
        cursor.execute('SELECT submittedOn From response where submittedOn >= %s && submittedOn <= %s && status = %s && responseId = %s && hotelId = %s order by submittedOn asc limit 1', [startDate, endDate, statusval2, r['responseId'], hotelId])
        tempres = cursor.fetchall()
        if len(tempres) == 0:
            notSubmitted = notSubmitted + 1
        else:
            cursor.execute('SELECT submittedOn From response where submittedOn >= %s && submittedOn <= %s && (status = %s or status = %s) && responseId = %s  && hotelId = %s order by submittedOn asc limit 1', [startDate, endDate, statusval4, statusval5, r['responseId'], hotelId])
            customerres = cursor.fetchall()
            if len(customerres) == 0:
                notSubmitted = notSubmitted + 1
            else:
                difference = customerres[0]['submittedOn'] - tempres[0]['submittedOn']
                difference = difference.total_seconds()
                hours = divmod(difference, 3600)[0]
                if hours >= 0 and hours <= 2:
                    table["0 - 2"] = table["0 - 2"] + 1
                elif hours >2 and hours <= 8:
                    table["2 - 8"] = table['2 - 8'] + 1
                elif hours > 8 and hours <= 24:
                    table['8 - 24'] = table['8 - 24'] + 1
                elif hours > 24:
                    table["24 +"] = table["24 +"] + 1

    customeres = {}
    customeres['notSubmitted'] = notSubmitted
    customeres['table'] = table

    result['customeres'] = customeres
    revenueres = {}
    cursor.execute('SELECT * From request where createdOn >= %s && createdOn <= %s && hotelId = %s', [startDate, endDate, hotelId])
    tempres1 = cursor.fetchall()
    if len(tempres1) != 0:
        total1 = 0
        total2 = 0
        for r in tempres1:
            if (r['status'] == statusval10):
                cursor.execute('SELECT * from response where requestId = %s && status = %s  && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                res = cursor.fetchall()
                if len(res) == 0:
                    total2 = total2 + 0
                else:
                    total2 = total2 + float(res[0]['totalQuote'])
            elif (r['status'] == statusval2 or r['status'] == statusval4 or r['status'] == statusval8 or r['status'] == statusval11):
                cursor.execute('SELECT * From response where requestId = %s && status = %s  && hotelId = %s order by submittedOn desc limit 1', [r['id'], r['status'], hotelId])
                res = cursor.fetchall()
                if len(res) == 0:
                    total1 = total1 + 0
                else:
                    total1 = total1 + float(res[0]['totalQuote'])
            revenueres['1'] = total1
            revenueres['2'] = total2
    else:
        revenueres['1'] = 0
        revenueres['2'] = 0

    result['revenueres'] = revenueres

    return jsonify(result), 200


@app.route('/resubmitRequest', methods = ['GET', 'POST'])
def resubmitRequest():
    inp = request.json
    username = session['email']
    cursor = mysql.connection.cursor()
    hotelId = session.get('hotelId')
    cursor.execute('SELECT * From request where id = %s && hotelId = %s', [inp['id'], hotelId])
    prevRequest = cursor.fetchall()
    cursor.execute('SELECT Count(*) from request where hotelId = %s', [hotelId])
    count = cursor.fetchall()
    count = count[0]['Count(*)'] + 1
    if (count < 10):
        id = "TR" + "00" + str(count)
    elif (count < 99):
        id = "TR" + "0" + str(count)
    today = datetime.date.today()
    d1 = prevRequest[0]['checkIn']
    lead = d1 - today
    lead = lead.days
    today = datetime.datetime.today()
    prevRequest = prevRequest[0]
    cursor.execute('INSERT INTO request(category, groupName, checkIn, checkOut, nights, commissionable, groupBlock, foc, foc1, foc2, budget, formPayment, paymentTerms, paymentDays, comments, id, createdBy, createdFor, leadTime, status, userType, createdOn, hotelId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                   prevRequest['category'], prevRequest['groupName'], prevRequest['checkIn'], prevRequest['checkOut'], prevRequest['nights'], prevRequest['commissionable'], prevRequest['groupBlock'], prevRequest['foc'], prevRequest['foc1'], prevRequest['foc2'], prevRequest['budget'], prevRequest['formPayment'], prevRequest['paymentTerms'], prevRequest['paymentDays'], prevRequest['comments'], id, username, prevRequest['createdFor'], lead, statusval1, prevRequest['userType'], today, hotelId   
            ])
    cursor.execute('SELECT * from request1Bed where id = %s  && hotelId = %s', [inp['id'], hotelId])
    table = cursor.fetchall()
    for t in table:
        cursor.execute('INSERT INTO request1Bed(date, occupancy, count, id, hotelId) VALUES(%s, %s, %s, %s, %s)', [t['date'], t['occupancy'], t['count'], id, hotelId])

    cursor.execute('SELECT * from request2Bed where id = %s && hotelId = %s', [inp['id'], hotelId])
    table = cursor.fetchall()
    for t in table:
        cursor.execute('INSERT INTO request2Bed(date, occupancy, count, id, hotelId) VALUES(%s, %s, %s, %s, %s)', [t['date'], t['occupancy'], t['count'], id, hotelId])

    mysql.connection.commit()
    flash('Your Request has been entered', 'success')
    return ('', 204)
    
# Req module ended


@app.route('/strategyForecast', methods = ['GET', 'POST'])
def strategyForecast():
    return render_template('strategy/forecast.html')


@app.route('/strategyEvaluation', methods = ['GET', 'POST'])
def strategyEvaluation():
    return render_template('strategy/evaluation.html')


@app.route('/strategyAncillary', methods = ['GET', 'POST'])
def strategyAncillary():
    return render_template('strategy/Ancillary.html')

@app.route('/settingBusinessReward', methods = ['GET', 'POST'])
def settingBusinessReward():
    return render_template('settings/BusinessReward.html')


@app.route('/addHotel', methods = ['GET', 'POST'])
def addHotel():
    return render_template('developer/addHotel.html')

@app.route('/addHotelSubmit', methods = ['GET', 'POST'])
def addHotelSubmit():
    
    if request.method == 'POST':
        hotelName = request.form['hotelName']
        email = request.form['email']
        address = request.form.get('address')
        contactName = request.form['contactName']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']
        zipv = request.form['zip']


        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * From mapHotelId where email = %s', [email])
        data = cursor.fetchall()
        if len(data) == 0:
            cursor.execute('INSERT INTO mapHotelId(hotelName, email, address, contactName, city, state, country, phone, zip) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)', [hotelName, email, address, contactName, city, state, country, phone, zipv])

            cursor.execute('SELECT hotelId from mapHotelId where hotelName = %s && email = %s', [hotelName, email])
            hotelId = cursor.fetchall()
            hotelId = hotelId[0]['hotelId']

            password = sha256_crypt.hash('trompar2020')

            firstName = contactName.split(' ')[0]
            cursor.execute('INSERT INTO users(firstName, email, password, userType, userSubType, hotelId) VALUES(%s, %s, %s, %s, %s, %s)', [firstName, email, password, "hoteluser", "hotelAdmin", hotelId])

            cursor.execute('INSERT INTO hotelUsers(fullName,  email, password, userType, hotelId, email_verified, active) VALUES(%s, %s, %s, %s, %s, %s, %s)', (contactName,  email, password, "hotelAdmin", hotelId, 1 ,1))
            
            mysql.connection.commit()
        else:
            flash('Email already registered', 'danger')
            return render_template('developer/addHotel.html')

        flash('New Hotel has been registered', 'success')
        return redirect(url_for('home2'))

@app.route('/addCustomer', methods = ['GET', 'POST'])
def addCustomer():
    return render_template('users/addCustomer.html')

@app.route('/addCustomerSubmit', methods = ['GET', 'POST'])
def addCustomerSubmit():
    customerType = request.form['customerType']
    if customerType == 'iata':
        return redirect(url_for('iatar'))
    elif customerType == 'retail':
        return redirect(url_for('customerr'))
    elif customerType == 'corporate':
        return redirect(url_for('customerC'))
    elif customerType == 'tour':
        return redirect(url_for('customerT'))

if __name__ == "__main__":
    app.run(debug = True, threaded = True)

