from flask import Flask, render_template, flash, request, session, url_for, session, jsonify, redirect
from config import Config
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from functools import wraps
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from flask_mysqldb import MySQL
import datetime
import math

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


def sendMail(subjectv, recipientsv, linkv, tokenv, bodyv, senderv):
    msg = Message(
        subject = subjectv,
        sender = app.config['MAIL_SENDER'],
        recipients = recipientsv.split())
    link = url_for(linkv, token=tokenv, _external=True)
    msg.body = bodyv + ' ' + link
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
        elif data['userType'] == 'iatauser':
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
            return render_template('index.html', title = 'Home')
    except:
        return render_template('login.html', title = 'Login')

@app.route('/signIn', methods=['GET', 'POST'])
def index():
    return render_template('login.html', title = 'Login')

@app.route('/iataRegistration', methods=['GET', 'POST'])
def iatar():
    return render_template('registerIata.html', title = 'Register')


@app.route('/customerRegistrationR', methods=['GET', 'POST'])
def customerr():
    return render_template('rcustomer.html', title = 'Register')

@app.route('/customerRegistrationI', methods=['GET', 'POST'])
def customerI():
    return render_template('icustomer.html', title = 'Register')


@app.route('/customerRegistrationT', methods=['GET', 'POST'])
def customerT():
    return render_template('tcustomer.html', title='Register')


@app.route('/customerRegistrationC', methods=['GET', 'POST'])
def customerC():
    return render_template('ccustomer.html', title='Register')


@app.route('/registerI', methods = ['GET', 'POST'])
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
                senderv='koolbhavya.epic@gmail.com'
            )
            cursor.execute('INSERT INTO users(firstName, email, password, userType, userSubType) Values(%s, %s, %s, %s, %s)',
                           (firstName, email, password, 'iata', ''))

            cursor.execute('INSERT INTO iataUsers(fullName, email, country, phone, password, iataCode, agencyName) Values(%s, %s, %s, %s, %s, %s, %s)',
                           (fullName, email, country, phone, password, iataCode, agencyName))

            mysql.connection.commit()
            cursor.close()
        else:
            flash('Email Already Registered', 'danger')
            return render_template('rcustomer.html', title="Register")

        flash('You are now registered and can log in', 'success')
        return render_template('login.html', title='Login')


@app.route('/registerR', methods = ['GET', 'POST'])
def registerR():
    if request.method == 'POST':

        fullName = request.form['fullName']
        firstName = fullName.split(' ')[0]
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        country = request.form['country']

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
                senderv='koolbhavya.epic@gmail.com'
            )
            cursor.execute('INSERT INTO users(firstName, email, password, userType, userSubType) Values(%s, %s, %s, %s, %s)',
                           (firstName, email, password, 'customer', 'retail'))

            cursor.execute('INSERT INTO customers(fullName, email, country, phone, password, userType) Values(%s, %s, %s, %s, %s, %s)', (fullName, email, country, phone, password, 'retail'))
            
            mysql.connection.commit()
            cursor.close()
        else:
            flash('Email Already Registered', 'danger')
            return render_template('rcustomer.html', title="Register")

        flash('You are now registered and can log in', 'success')
        return render_template('login.html', title='Login')


@app.route('/registerC', methods=['GET', 'POST'])
def registerC():
    if request.method == 'POST':
        fullName = request.form['fullName']
        firstName = fullName.split(' ')[0]
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        country = request.form['country']
        organizationName = request.form['organizationName']
            

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
                senderv='koolbhavya.epic@gmail.com'
            )
            cursor.execute('INSERT INTO users(firstName, email, password, userType, userSubType) Values(%s, %s, %s, %s, %s)',
                           (firstName, email, password, 'customer', 'corporate'))

            cursor.execute('INSERT INTO customers(fullName, email, country, phone, password, userType, organizationName) Values(%s, %s, %s, %s, %s, %s, %s)',
                           (fullName, email, country, phone, password, 'corporate', organizationName))

            mysql.connection.commit()
            cursor.close()
        else:
            flash('Email Already Registered', 'danger')
            return render_template('rcustomer.html', title="Register")

        flash('You are now registered and can log in', 'success')
        return render_template('login.html', title='Login')


@app.route('/registerT', methods=['GET', 'POST'])
def registerT():
    if request.method == 'POST':
        fullName = request.form['fullName']
        firstName = fullName.split(' ')[0]
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        country = request.form['country']
        agencyName = request.form['agencyName']

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
                senderv='koolbhavya.epic@gmail.com'
            )
            cursor.execute('INSERT INTO users(firstName, email, password, userType, userSubType) Values(%s, %s, %s, %s, %s)',
                           (firstName, email, password, 'customer', 'tour'))

            cursor.execute('INSERT INTO customers(fullName, email, country, phone, password, userType, agencyName) Values(%s, %s, %s, %s, %s, %s, %s)',
                           (fullName, email, country, phone, password, 'tour', agencyName))

            mysql.connection.commit()
            cursor.close()
        else:
            flash('Email Already Registered', 'danger')
            return render_template('rcustomer.html', title="Register")

        flash('You are now registered and can log in', 'success')
        return render_template('login.html', title='Login')






@app.route('/login', methods=['GET', 'POST'])
def login():
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
            
            if (password == password_match):
                session['logged_in'] = True
                session['email'] = email
                session['userType'] = data['userType']
                session['firstName'] = data['firstName']

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
                    'helpTicketing': True
                    }
                    session['userSubType'] = data['userSubType']
                    userSubType = data['userSubType']
                    cursor.execute(
                        "SELECT * FROM hotelMenuAccess where userType = %s", [userSubType])
                    d = cursor.fetchall()
                    cursor.execute("SELECT * FROM hotelUsers where email = %s", [email])
                    dog = cursor.fetchall()
                    dog = dog[0]
                    if (dog['active'] == 0):
                        session.clear()
                        flash('You are de-activated. Kindly contact Super Admin!', 'danger')
                        return render_template('login.html', title = 'Login')

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
                                                
    

                    session['menuParams'] = menuParams


                elif session['userType'] == 'iata':
                    cursor.execute(
                        "SELECT * FROM iataUsers where email = %s", [email])
                    dog = cursor.fetchall()
                    dog = dog[0]
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
                    cursor.execute("SELECT * FROM iataMenuAccess")
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
                    cursor.execute("SELECT * FROM customers where email = %s", [email])
                    dog = cursor.fetchall()
                    dog = dog[0]
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
                    cursor.execute("SELECT * FROM customerMenuAccess")
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

                
                flash('You are now logged in', 'success')
                return redirect(url_for('home2'))
            else:
                error = 'Passwords did not match'
                return render_template('login.html', error = error)

    return render_template('login.html', title = 'Login')

@app.route('/forgotpassword', methods = ['GET', 'POST'])
def forgotpassword():
    return render_template('forgotpasswordreq.html', title = 'forgotpassword')

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
            senderv='koolbhavya.epic@gmail.com'
        )

        flash('Kindly Check your email', 'success')
        return render_template('login.html', title = 'Login')


@app.route('/passwordupdate/<token>', methods = ['GET', 'POST'])
def passwordupdate(token):
    email = confirmToken(token)
    return render_template('forgotpassword.html', email = email)

@app.route('/passwordupdatef', methods = ['GET', 'POST'])
def passwordupdatef():
    email = request.form['email']
    password = request.form['password']

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From users where email = %s', [email])
    data = cursor.fetchall()
    data = data[0]

    cursor.execute('UPDATE users SET password = %s where email = %s', [password, email])

    if data['userType'] == 'customer':
        cursor.execute('UPDATE customers SET password = %s where email = %s', [password, email])
    elif data['userType'] == 'iatauser':
        cursor.execute('UPDATE iataUsers SET password = %s where email = %s', [password, email])
    elif data['userType'] == 'hotelUser':
        cursor.execute('UPDATE hotelUsers SET password = %s where email = %s', [password, email])
    elif data['userType'] == 'developer':
        cursor.execute('UPDATE developers SET password = %s where email = %s', [password, email])
    
    mysql.connection.commit()
    cursor.close()
    flash('Your password has been updated', 'success')
    return render_template('login.html', title = 'Login')

@is_logged_in
@app.route('/signOut', methods=['GET', 'POST'])
def signOut():
    session.clear()
    flash('You are now logged out', 'success')
    return render_template('login.html', title = 'Login')

@app.route('/hoteladduser', methods = ['GET', 'POST'])
def hoteladduser():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT userType FROM hotelMenuAccess")
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

    return render_template('hoteladduser.html', title = 'AddUser', subtypes = subtypes)

@app.route('/registerhotelusers', methods = ['GET', 'POST'])
def registerhotelusers():
    if request.method == 'POST':
        fullName = request.form['fullName']
        email = request.form['email']
        password = request.form['password']
        userType = request.form['userType']
        firstName = fullName.split(' ')[0]

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
                senderv='koolbhavya.epic@gmail.com'
            )

            cursor.execute('INSERT INTO users(firstName, email, password, userType, userSubType) Values(%s, %s, %s, %s, %s)', (firstName, email, password, "hoteluser", userType))

            cursor.execute('INSERT INTO hotelUsers(fullName,  email, password, userType) VALUES(%s, %s, %s, %s)', (fullName,  email, password, userType))
        else:
            flash('Email Already Registered', 'danger')
            return render_template('hoteladduser.html', title="Register")

        mysql.connection.commit()
        cursor.close()

        flash('New Hotel user has been added', 'success')
        return render_template('index.html')

@app.route('/adddeveloper', methods = ['GET', 'POST'])
def adddeeloper():
    return render_template('adddeveloper.html', title =  'Add')

@app.route('/registerdeveloper', methods = ['GET', 'POST'])
def registerdeveloper():
    if request.method == 'POST':

        fullName = request.form['name']
        email = request.form['email']
        password = request.form['password']
        firstName = fullName.split(' ')[0]

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
                senderv='koolbhavya.epic@gmail.com'
            )

            cursor.execute('INSERT INTO developers(fullName, email, password) values(%s, %s, %s)',
            (fullName, email, password))
            cursor.execute('INSERT INTO users(firstName, email, password, userType) Values(%s, %s, %s, %s)',
                           (firstName, email, password, 'developer'))
        
        else:
            flash('Email Already Registered', 'danger')
            return render_template('adddeveloper.html', title="Register")



        mysql.connection.commit()
        cursor.close()

        flash('You are now registered and can log in', 'success')
        return render_template('login.html', title='Login')
        
    return render_template('login.html', title='Login')


@app.route('/hoteladdusertype', methods = ["GET", "POST"])
def hoteladdusertype():
    return render_template('hoteladdusertype.html', title = 'Register')


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



    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From hotelMenuAccess where userType = %s', [userType])
    data = cursor.fetchall()

    if len(data) == 0:
        cursor.execute('INSERT INTO hotelMenuAccess(userType,request, requestCreate, requestManage, strategy, strategyRooms, strategyForecast, strategyRate, strategyDiscount, settings, settingsRequest, settingsContact, settingsTime, settingsNegotiation, settingsAutopilot, users, usersHotel, usersCustomer, analytics, analyticsDashboard, analyticsBehavior, analyticsPerformance, analyticsRevenue,analyticsTracking, requestCreateAdhoc, requestCreateSeries, strategyDiscountCreate, strategyDiscountMap, settingsRequestCreate, settingsRequestMap, settingsContactCreate, settingsContactMap, settingsTimeMap, settingsTimeCreate, usersHotelAdd, usersHotelEdit, usersCustomerAdd, usersCustomerEdit, usersCustomerUpload ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                       userType, requestv, requestCreate, requestManage, strategy, strategyRooms, strategyForecast, strategyRate, strategyDiscount, settings, settingsRequest, settingsContact, settingsTime, settingsNegotiation, settingsAutopilot, users, usersHotel, usersCustomer, analytics, analyticsDashboard, analyticsBehavior, analyticsPerformance, analyticsRevenue, analyticsTracking, requestCreateAdhoc, requestCreateSeries, strategyDiscountCreate, strategyDiscountMap,  settingsRequestCreate, settingsRequestMap, settingsContactCreate, settingsContactMap, settingsTimeMap, settingsTimeCreate, usersHotelAdd, usersHotelEdit, usersCustomerAdd, usersCustomerEdit, usersCustomerUpload])

    else:
        flash('UserType Already Registered', 'danger')
        return render_template('hoteladdusertype.html', title="Register")



    mysql.connection.commit()
    cursor.close()

    flash('New userType added', 'success')
    return render_template('index.html', title='UserType')


@app.route('/managehotelusers', methods = ['GET', 'POST'])
def managehotelusers():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT fullName, email, userType, active FROM hotelUsers')

    result = cursor.fetchall()
    cursor.close()
    data = []
    for res in result:
        res['firstName'] = res['fullName'].split()[0]
        data.append(res)
    

    return render_template('managehotelusers.html', title = 'Users', data = data)


@app.route('/showprofile/<email>', methods = ['GET', 'POST'])
def showprofile(email):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM hotelUsers where email = %s', [email])

    data = cursor.fetchall()
    cursor.close()
    data[0]['email_verified'] = "Yes" if data[0]['email_verified'] else "No"
    data[0]['fullName'] = data[0]['fullName'].split(' ')[0]
    data[0]['active'] = 'Yes' if data[0]['active'] else 'No'
    return render_template('showprofile.html', title = 'Profile', data = data[0])

@app.route('/showprofileAll/<email>', methods = ['GET', 'POST'])
def showprofileAll(email):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM users where email = %s', [email])

    data = cursor.fetchall()
    data = data[0]
    if (data['userType'] == 'developer'):
        cursor.execute('SELECT active, email_verified from developers where email = %s', [email])
        rr = cursor.fetchall()
        rr = rr[0]
    elif (data['userType'] == 'iata'):
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
    return render_template('showprofileAll.html', title = 'Profile', data = data)   

@app.route('/editUser/<email>', methods = ["GET", "POST"])
def editUser(email):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM hotelUsers where email = %s', [email])

    data = cursor.fetchall()
    cursor.execute("SELECT userType FROM hotelMenuAccess")
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
    return render_template('editUser.html', title = 'Edit', data = data[0], subtypes = subtypes)

@app.route('/editUserAll/<email>', methods = ['GET', 'POST'])
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
    elif (data['userType'] == 'iata'):
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

    return render_template('editUserAll.html', data = data)



@app.route('/submitEditUser', methods = ['GET', 'POST'])
def submitEditUser():
    name = request.form['name']
    userType = request.form['userType']
    email_verified = getValC(request.form.get('email_verified'))
    active = getValC(request.form.get('active'))
    firstName = name.split()[0]
    email = request.form['email']

    cursor = mysql.connection.cursor()

    cursor.execute('Update hotelUsers SET fullName = %s, userType = %s, email_verified = %s, active = %s WHERE email = %s',(name, userType, email_verified, active, email))


    cursor.execute('Update users SET firstName = %s,  userSubType = %s WHERE email = %s', (firstName, userType, email))

    mysql.connection.commit()
    cursor.close()

    flash('Hotel user has been edited', 'success')
    return render_template('index.html')

@app.route('/submitEditUserAll2', methods = ["GET", 'POST'])
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
    elif (data['userType'] == 'iata'):
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
    return render_template('index.html')



@app.route('/deactivateUser/<email>', methods = ['GET', 'POST'])
def deactivateUser(email):
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE hotelUsers SET active = 0 where email = %s", [email])
    mysql.connection.commit()
    cursor.close()

    flash("User has been de-activated", 'success')
    return render_template('index.html')


@app.route('/deactivateUserAll/<email>', methods=['GET', 'POST'])
def deactivateUserAll(email):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM users where email = %s', [email])
    data = cursor.fetchall()
    data = data[0]
    if (data['userType'] == 'developer'):
        cursor.execute('Update developers SET active = 0 where email = %s', [
                      email])
    elif (data['userType'] == 'iata'):
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
    return render_template('index.html')


@app.route('/activateUser/<email>', methods=['GET', 'POST'])
def activateUser(email):
    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE hotelUsers SET active = 1 where email = %s", [email])
    mysql.connection.commit()
    cursor.close()

    flash("User has been activated", 'success')
    return render_template('index.html')


@app.route('/activateUserAll/<email>', methods=['GET', 'POST'])
def activateUserAll(email):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM users where email = %s', [email])
    data = cursor.fetchall()
    data = data[0]
    if (data['userType'] == 'developer'):
        cursor.execute('Update developers SET active = 1 where email = %s', [
            email])
    elif (data['userType'] == 'iata'):
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
    return render_template('index.html')



@app.route('/myprofile/<email>', methods = ['GET', 'POST'])
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
    elif data == 'iata':
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
    

    return render_template('myProfile.html', data = result)


@app.route('/submitEditUserAll', methods=['GET', 'POST'])
def submitEditUserAll():
    name = request.form['name']
    phone = request.form.get('phone')
    country = request.form.get('country')
    email = request.form['email']
    password = request.form['password']
    agencyName = request.form.get('agencyName')
    iataCode = request.form.get('iataCode')
    organizationName = request.form.get('organizationName')

    firstName = name.split(' ')[0]
    cursor = mysql.connection.cursor()

    cursor.execute('SELECT userType From users where email = %s', [email])
    data = cursor.fetchall()

    data = data[0]['userType']
    if data == 'hoteluser':
        cursor.execute('Update hotelUsers SET fullName = %s, password = %s WHERE email = %s',
                        (name, password, email))
    elif data == 'customer':
        cursor.execute('Update customers SET fullName = %s, phone = %s, country = %s, password = %s WHERE email = %s',
                        (name, phone, country, password, email))
    elif data == 'iata':
        cursor.execute('Update iataUsers SET fullName = %s, phone = %s, country = %s, password = %s WHERE email = %s',
                        (name, phone, country, password, email))
    elif data == 'developer':
        cursor.execute('Update developers SET name = %s, password = %s, phone = %s WHERE email = %s',
                        (name, password, phone, email))

    cursor.execute('Update users SET firstName = %s, password = %s WHERE email = %s',
                    (firstName, password, email))
    
    mysql.connection.commit()
    cursor.close()

    flash('Hotel user has been edited', 'success')
    return render_template('index.html')

@app.route('/inviteemail', methods = ['GET', 'POST'])
def inviteemail():
    email = request.form['email']
    userType = request.form['userType']
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From users where email = %s', [email])
    data = cursor.fetchall()

    if len(data) != 0:
        flash('Email already registered', 'danger')
        return render_template('login.html', title='Login')
    else:
        token = generateConfirmationToken(email)

        cursor.execute('INSERT INTO inviteEmail(email, userType) VALUES(%s, %s)', [email, userType])
        mysql.connection.commit()
        cursor.close()
        sendMail(
            subjectv='Invite to TROMPAR',
            recipientsv=email,
            linkv='addhoteluserinv',
            tokenv=token,
            bodyv='Kindly fill the form to complete registration',
            senderv='koolbhavya.epic@gmail.com'
        )

        flash('Invitation sent to email', 'success')
        return render_template('index.html', title='Login')


@app.route('/addhoteluserinv<token>', methods = ['GET', 'POST'])
def addhoteluserinv(token):
    email = confirmToken(token)
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From inviteEmail where email = %s', [email])
    data = cursor.fetchall()
    data = data[0]
    userType = data['userType']

    return render_template('addhoteluserinv.html', title = 'Register', email = email, userType = userType)

@app.route('/edituserType', methods = ['GET', 'POST'])
def edituserType():
    cursor = mysql.connection.cursor()
    
    cursor.execute(
        'SELECT * From hotelMenuAccess')
    datah = cursor.fetchall()
    datah = datah[0]
    
    cursor.execute("SELECT userType FROM hotelMenuAccess")
    data = cursor.fetchall()
    subtypes = []

    for d in data:
        subtypes.append(d['userType'])

    if 'revenue' not in subtypes:
        subtypes.append('revenue')
    if 'reservation' not in subtypes:
        subtypes.append('Reservation')
    if 'hotelAdmin' not in subtypes:
        subtypes.append('hotelAdmin')

    return render_template('editusertype.html', datah=datah, subtypes = subtypes)


@app.route('/euserType', methods=['GET', 'POST'])
def euserType():
    userType = request.form.get('userType')
    cursor = mysql.connection.cursor()
    cursor.execute(
        'SELECT * From hotelMenuAccess where userType = %s', [userType])
    datah = cursor.fetchall()
    datah = datah[0]
    return render_template('eusertype.html', datah=datah, userType = userType)

@app.route('/submiteditusertype', methods = ['GET', 'POST'])
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

    cursor = mysql.connection.cursor()

    cursor.execute('Update hotelMenuAccess SET request = %s, requestCreate = %s, requestManage = %s, strategy = %s, strategyRooms = %s, strategyForecast = %s, strategyRate = %s, strategyDiscount = %s, settings = %s, settingsRequest = %s, settingsContact = %s, settingsTime = %s, settingsNegotiation = %s, settingsAutopilot = %s, users = %s, usersHotel = %s, usersCustomer = %s, analytics = %s, analyticsDashboard = %s, analyticsBehavior = %s, analyticsPerformance = %s, analyticsRevenue = %s, analyticsTracking = %s, requestCreateAdhoc = %s, requestCreateSeries = %s, strategyDiscountCreate = %s, strategyDiscountMap = %s, settingsRequestCreate = %s, settingsRequestMap = %s, settingsContactCreate = %s, settingsContactMap = %s, settingsTimeMap = %s, settingsTimeCreate = %s, usersHotelAdd = %s, usersHotelEdit = %s, usersCustomerAdd = %s, usersCustomerEdit = %s, usersCustomerUpload = %s WHERE userType = %s', [
                    requestv, requestCreate, requestManage, strategy, strategyRooms, strategyForecast, strategyRate, strategyDiscount, settings, settingsRequest, settingsContact, settingsTime, settingsNegotiation, settingsAutopilot, users, usersHotel, usersCustomer, analytics, analyticsDashboard, analyticsBehavior, analyticsPerformance, analyticsRevenue, analyticsTracking, requestCreateAdhoc, requestCreateSeries, strategyDiscountCreate, strategyDiscountMap,  settingsRequestCreate, settingsRequestMap, settingsContactCreate, settingsContactMap, settingsTimeMap, settingsTimeCreate, usersHotelAdd, usersHotelEdit, usersCustomerAdd, usersCustomerEdit, usersCustomerUpload, userType])


    mysql.connection.commit()
    cursor.close()

    flash('UserType updated!', 'success')
    return render_template('index.html', title='UserType')

# Users Module Finished


@app.route('/strategyRooms', methods = ['GET', 'POST'])
def strategyRooms():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From room')
    data = cursor.fetchall()
    if len(data) == 0:
        return render_template('strategyRooms.html')
    else:
        totalRooms = 0
        for d in data:
            totalRooms += int(d['count'])

        return render_template('editstrategyRooms.html', data = data, totalRooms = totalRooms)

@app.route('/strategyRoomsSubmit', methods = ['GET', 'POST'])
def strategyRoomsSubmit():
    inp = request.json
    inp.remove(inp[0])

    cursor = mysql.connection.cursor()
    
    for i in inp:
        cursor.execute("INSERT INTO room(type, count, single, doublev, triple, quad) VALUES(%s, %s, %s, %s, %s, %s)" , [i[0][0], i[1], int(i[2]), int(i[3]), int(i[4]), int(i[5])])
    
    mysql.connection.commit()
    cursor.close()

    flash('Your Room data has been entered', 'success')
    return ('', 204)


@app.route('/editstrategyRoomsSubmit', methods = ['GET', 'POST'])
def editstrategyRoomsSubmit():
    inp = request.json
    if len(inp) == 0:
        return render_template('index.html')
    inp.remove(inp[0])
        
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM room')
    mysql.connection.commit()

    for i in inp:
        cursor.execute("INSERT INTO room(type, count, single, doublev, triple, quad) VALUES(%s, %s, %s, %s, %s, %s)", [
                       i[0][0], i[1], int(i[2]), int(i[3]), int(i[4]), int(i[5])])

    mysql.connection.commit()
    cursor.close()

    flash('Your Room data has been updated', 'success')
    return ('', 204)



@app.route('/strategyRate', methods = ['GET', 'POST'])
def strategyRate():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From room')
    data = cursor.fetchall()
    if len(data) == 0:
        flash('Kindly fill types of Rooms first', 'danger')
        return render_template('strategyRooms.html')
    else:
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT * From rate')
            data1 = cursor.fetchall()
            if len(data1) == 0:
                return render_template('strategyRate.html', data = data)
            else:
                    cursor.execute('SELECT startDate, endDate from rate')
                    storedDates = cursor.fetchall()
                    for d in data1:
                        dow = ""
                        if (d['monday'] == '1'):
                            dow += " Monday, "    
                        if (d['tuesday'] == '1'):
                            dow += " Tuesday, "
                        if (d['wednesday'] == '1'):
                            dow += "Wednesday, "
                        if (d['thursday'] == '1'):
                            dow += "Thursday, "
                        if (d['friday'] == '1'):
                            dow += "Friday, "
                        if (d['saturday'] == '1'):
                            dow += "Saturday, "
                        if (d['sunday'] == '1'):
                            dow += "Sunday"

                        d['dow'] = dow

                        d['startDate'] = d['startDate'].strftime('%Y-%m-%d')
                        x = d['startDate'].split('-')
                        strd = x[2] + "/" + x[1] + "/" + x[0]
                        d['startDate'] = strd

                        d['endDate'] = d['endDate'].strftime('%Y-%m-%d')
                        x = d['endDate'].split('-')
                        strd = x[2] + "/" + x[1] + "/" + x[0]
                        d['endDate'] = strd
                    
                    return render_template('editstrategyRate.html', data = data, data1 = data1, storedDates = storedDates)

        

@app.route('/strategyRateSubmit', methods = ['GET', 'POST'])
def strategyRateSubmit():
    inp = request.json
    if len(inp) == 0:
        return render_template('index.html')
    
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM rate')
    mysql.connection.commit()
    for i in inp:
        cursor.execute("INSERT INTO rate(startDate, endDate, monday, tuesday, wednesday, thursday, friday, saturday, sunday, type, sor, dor, tor, qor) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", [i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8], i[9][0], i[10], i[11], i[12], i[13]])
    mysql.connection.commit()
    cursor.close()

    flash('Your Rate data has been updated', 'success')
    return ('', 204)


@app.route('/requestCreateAdhoc', methods = ['GET', 'POST'])
def requestCreateAdhoc():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From room')
    data = cursor.fetchall()
    cursor.execute('SELECT email From users where userType != %s', ['hoteluser'])
    users = cursor.fetchall()

    return render_template('requestCreateAdhoc.html', data = data, users = users)


@app.route('/requestCreateAdhocSubmit', methods = ['GET', 'POST'])
def requestCreateAdhocSubmit():
    inp = request.json
    cursor = mysql.connection.cursor()
    username = session['email']
    cursor.execute('SELECT userType from users where email = %s', [inp['createdFor']])
    userType = cursor.fetchall()
    userType = userType[0]['userType']

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
    
    
    cursor.execute('SELECT Count(*) from request')
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
    cursor.execute('INSERT INTO request(category, groupName, checkIn, checkOut, nights, commissionable, groupBlock, foc, foc1, foc2, budget, formPayment, paymentTerms, paymentDays, comments, id, createdBy, createdFor, leadTime, status, userType, createdOn) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                   inp['category'], inp['groupName'], inp['checkIn'], inp['checkOut'], inp['nights'], inp['commissionable'], inp['groupBlock'], inp['foc'], inp['foc1'], inp['foc2'], inp['budget'], procArr(inp['formPayment']), inp['paymentTerms'], inp['paymentDays'], inp['comments'], id, username, inp['createdFor'], lead, 'NEW', userType, today   
            ])

    table = inp['table_result']
    for t in table:
        if (t['type'] == '1'):
            cursor.execute('INSERT INTO request1Bed(date, occupancy, count, id) VALUES(%s, %s, %s, %s)', [
                t['date'], t['occupancy'], t['count'], id])
        else:
            cursor.execute(
                'INSERT INTO request2Bed(date, occupancy, count, id) VALUES(%s, %s, %s, %s)', [t['date'],  t['occupancy'], t['count'], id])

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
                cursor.execute('SELECT * FROM request')
                data = cursor.fetchall()
                data = data[::-1]
                return render_template('index2.html', title = 'Home', data = data)
            else:
                cursor = mysql.connection.cursor()
                cursor.execute('SELECT * From request where createdFor = %s', [session['email']])
                data = cursor.fetchall()
                data = data[::-1]
                return render_template('index2.html', title='Home', data=data)
            return render_template('index.html', title='Home')
    except:
        return render_template('login.html', title='Login')


@app.route('/showRequest/<token>', methods = ['GET', 'POST'])
def showRequest(token):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT status from request where id = %s', [token])
    status = cursor.fetchall()
    if (status[0]['status'] == 'QUOTED'):
        cursor.execute('SELECT * From request where id = %s', [token])
        data = cursor.fetchall()
        data = data[0]
        checkIn = data['checkIn']
        checkOut = data['checkOut']
        data['createdOn'] = data['createdOn'].strftime("%d/%B/%Y, %H:%M:%S")

        email = session['email']
        now = datetime.datetime.utcnow()

        cursor.execute('SELECT * From requestLastOpened where id = %s', [token])
        check = cursor.fetchall()
        data['lastOpenedOn'] = check[0]['time']
        data['lastOpenedBy'] = check[0]['openedBy']
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
                string += '(Cheque),'
            if v.count('bt') > 0:
                string += ' (Bank Transfer),'
            if v.count('cc') > 0:
                string += '(Credit Card)'

        data['formPayment'] = string

        if data['comments'].isspace():
            data['comments'] = ''

        responseId = data['id'] + "R"
        cursor.execute('SELECT * From response where responseId = %s', [responseId])
        data2 = cursor.fetchall()
        data['groupCategory'] = data2[0]['groupCategory']
        data2 = data2[0]
        tfoc = True
        if (data2['foc'] == '0'):
            tfoc = False
        tcomm = True
        if (data2['commission'] == '0'):
            tcomm = False

        string = ''
        v = data2['formPayment']
        if v != None:
            if v.count('cq') > 0:
                string += '(Cheque),'
            if v.count('bt') > 0:
                string += ' (Bank Transfer),'
            if v.count('cc') > 0:
                string += '(Credit Card)'

        data2['formPayment'] = string

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
        
        cursor.execute('SELECT * From responseAvg where responseId = %s', [responseId])
        data3 = cursor.fetchall()
        data3 = data3[0]
        
        cursor.execute('SELECT * From responseDaywise where responseId = %s', [responseId])
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


        return render_template('requestQuotedView.html', data = data, data2= data2, tfoc = tfoc, tcomm = tcomm, data3 = data3, lefttable = lefttable, righttable = righttable)


    cursor.execute('SELECT checkIn, checkOut from request where id = %s', [token])
    dates = cursor.fetchall()
    dates = dates[0]
    checkIn = dates['checkIn']
    checkOut = dates['checkOut']
    dates = []
    day = datetime.timedelta(days=1)

    cursor.execute('SELECT startDate, endDate from autopilot where active = "1" AND policy = "manual"')
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
        query = 'SELECT * from rate where startDate <= %s AND endDate >= %s AND {} = 1'.format(
            day)
        cursor.execute(query, [d, d])
        pent = cursor.fetchall()
        if len(pent) != 0:
            newDates.append(d)

    dates = newDates
    
    f = True
    if len(dates) == 0:
        f = False

    return render_template('getOcc.html', dates = dates, token = token, flag = f)

@app.route('/showRequest1', methods = ['GET', 'POST'])
def showRequest1():


    token = request.form['id']
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM request where id = %s', [token])
    data = cursor.fetchall()
    data = data[0]
    checkIn = data['checkIn']
    checkOut = data['checkOut']
    data['createdOn'] = data['createdOn'].strftime("%d/%B/%Y, %H:%M:%S")

    email = session['email']
    now = datetime.datetime.utcnow()

    cursor.execute('SELECT * From requestLastOpened where id = %s', [token])
    check = cursor.fetchall()
    if len(check) == 0:
        cursor.execute('INSERT INTO requestLastOpened(id, time, openedBy) VALUES (%s, %s, %s)', [token, now ,email]
        )   
        data['lastOpenedOn'] = now
        data['lastOpenedBy'] = email
    else:
        data['lastOpenedOn'] = check[0]['time']
        data['lastOpenedBy'] = check[0]['openedBy']
        cursor.execute('UPDATE requestLastOpened SET time = %s, openedBy = %s where id = %s', [now, email, token])


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
    v = data['formPayment']
    if v != None:
        if v.count('cq') > 0:
            string += '(Cheque),'
        if v.count('bt') > 0:
            string += ' (Bank Transfer),'
        if v.count('cc') > 0:
            string += '(Credit Card)'

    data['formPayment'] = string

    if data['comments'].isspace():
        data['comments'] = ''

    nights = data['nights']
    curr_date = data['checkIn']
    result = []
    dates = []
    discounts = []
    lead = int(data['leadTime'])
    occs = []

    cursor.execute('SELECT * From room')
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
        cursor.execute('SELECT * FROM request1Bed where date = %s AND id = %s', [curr_date, token])
        resultPerDay1 = cursor.fetchall()

        roomsToBook = 0
        for r in resultPerDay1:
            if (len(r) != 0):
                dateToCheck = curr_date.strftime('%Y-%m-%d')
                


                day = curr_date.strftime('%A')
                day = day.lower()
                query = "SELECT * FROM rate where (type = %s  AND (startDate <= %s AND endDate >= %s) AND {} = 1)".format(day)
                cursor.execute(query, ['1', dateToCheck, dateToCheck])
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
            'SELECT * FROM request2Bed where date = %s AND id = %s', [curr_date, token])
        resultPerDay2 = cursor.fetchall()
        for r in resultPerDay2:
            if (len(r) != 0):
                dateToCheck = curr_date.strftime('%Y-%m-%d')
                day = curr_date.strftime('%A')
                day = day.lower()
                query = "SELECT * FROM rate where (type = %s  AND (startDate <= %s AND endDate >= %s) AND {} = 1)".format(
                    day)
                cursor.execute(query, ['2', dateToCheck, dateToCheck])
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
                query = "SELECT * FROM rate where (type = %s  AND (startDate <= %s AND endDate >= %s) AND {} = 1)".format(
                    day)
                cursor.execute(query, ['1', dateToCheck, dateToCheck])
                pent = cursor.fetchall()
                r['foc1'] = tfoc1
                r['type'] = 'foc'
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
                query = "SELECT * FROM rate where (type = %s  AND (startDate <= %s AND endDate >= %s) AND {} = 1)".format(
                    day)
                cursor.execute(query, ['2', dateToCheck, dateToCheck])
                pent = cursor.fetchall()
                r['foc2'] = tfoc2
                r['type'] = 'foc'
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
            cursor.execute('SELECT policyName from autopilot where startDate <= %s AND endDate >= %s AND active = 1 AND policy = "manual"', [curr_date, curr_date])
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
            cursor.execute('SELECT discountId, defaultm from discountMap where startDate <= %s AND endDate >= %s AND active = 1', [dateToCheck, dateToCheck])
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
                    cursor.execute('SELECT * from discount where discountId = %s AND (leadMin <= %s && leadMax >= %s) AND (roomMin <= %s && roomMax >= %s)', [id, lead, lead, rv, rv])
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
                    t['rate'] = str(val) + " ( Rate Grid Value : " + str(te) + ")"
         

        lead = lead + 1

        dates.append(curr_date.strftime('%B %d'))

    
        result.append(tempResult)
    
        curr_date = curr_date + datetime.timedelta(days = 1)


    focv = 0
    for r in rates:
        if r['type'] == 'foc':
            focv += int(r['count']) * r['val']

    totalRate = 0
    for d in rates:
        if (d['val'] == -1 or d['type'] == 'foc'):
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
            if (m['type'] != 'foc'):
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
            elif (m['type'] == 'foc'):
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


    if (mmp == 0):
        flash('No Rate Grid available!', 'danger')
    return render_template('requestProcess.html', data = data, result = result, length = len(result), dates = dates, discounts = discounts, occs = occs, totalRate = totalRate, avgRate = avgRate, tcomm = tcomm, tcommv = tcommv, totalQuote = totalQuote, tfoc = tfoc, focv = focv, comP = comP, roomCount = roomCount, checkIn = checkIn, checkOut = checkOut, single1avg = single1avg, single2avg = single2avg, double1avg = double1avg, double2avg = double2avg, triple1avg = triple1avg, triple2avg = triple2avg, quad1avg = quad1avg, quad2avg = quad2avg, single1f = single1f, double1f = double1f, triple1f = triple1f, quad1f = quad1f, single2f = single2f, double2f = double2f, triple2f = triple2f, quad2f = quad2f, single1c = single1c, double1c = double1c, triple1c = triple1c, quad1c = quad1c, single2c = single2c, double2c = double2c, triple2c = triple2c, quad2c = quad2c, foc1 = foc1, foc2 = foc2)


@app.route('/strategyDiscountCreate', methods = ['GET', 'POST'])
def strategyDiscountCreate():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT count from room')
    data = cursor.fetchall()
    rooms = 0
    for d in data:
        rooms += int(d['count'])
    cursor.execute('SELECT * FROM discountMap') 
    discountGrids = cursor.fetchall()
    cursor.execute('SELECT * FROM discountMap WHERE defaultm = TRUE')
    f = cursor.fetchall()
    flag = False
    defaultId = -1
    if len(f) != 0:
        flag = True
        defaultId = f[0]['discountId']

    cursor.execute('SELECT startDate, endDate from discountMap where defaultm = 0')
    storedDates = cursor.fetchall()

    return render_template('strategyDiscountCreate.html', rooms = rooms, discountGrids = discountGrids, flag = flag, defaultId = defaultId, storedDates = storedDates)

@app.route('/viewAllUsers', methods = ['GET', 'POST'])
def viewAllUsers():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users")
    data = cursor.fetchall()

    for r in data:
        if (r['userType'] == 'developer'):
            cursor.execute(
                'SELECT active from developers where email = %s', [r['email']])
            rr = cursor.fetchall()
            rr = rr[0]
        elif (r['userType'] == 'iata'):
            cursor.execute(
                'SELECT active from iataUsers where email = %s', [r['email']])
            rr = cursor.fetchall()
            rr = rr[0]
        elif (r['userType'] == 'hoteluser'):
            cursor.execute(
                'SELECT active from hotelUsers where email = %s', [r['email']])
            rr = cursor.fetchall()
            rr = rr[0]
        elif (r['userType'] == 'customer'):
            cursor.execute(
                'SELECT active from customers where email = %s', [r['email']])
            rr = cursor.fetchall()
            rr = rr[0]
        r['active'] = rr['active']    
    

    cursor.close()
    return render_template('manageAllUsers.html', data = data)

@app.route('/strategyDiscountSubmit', methods = ['GET', 'POST'])
def strategyDiscountSubmit():
    inp = request.json
    occ = inp['occ']
        
    cursor = mysql.connection.cursor()
    for o in occ:
        cursor.execute('INSERT INTO discountOcc(discountId, occ, col) VALUES(%s, %s, %s)', [inp['discountId'], o['occ'], o['col']])

    email = session['email']
    time = datetime.datetime.utcnow()   
    cursor.execute('INSERT INTO discountMap(discountId, startDate, endDate, defaultm, createdBy, createdOn) VALUES(%s, %s, %s, %s, %s, %s)', [inp['discountId'], inp['startDate'], inp['endDate'], inp['defaultm'], email, time])

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
            
            cursor.execute('INSERT INTO discount(discountId, leadMin, leadMax, roomMin, roomMax, value) VALUES(%s, %s, %s, %s, %s, %s)', [discountId, leadMin, leadMax, roomMin, roomMax, value])


    mysql.connection.commit()
    cursor.close()

    flash('Your discount grid has been entered', 'success')
    return ('', 204)
  


@app.route('/showDiscountGrid/<id>', methods = ['GET', 'POST'])
def showDiscountGrid(id):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * from discountMap where discountId = %s', [id])
    data = cursor.fetchall()
    data = data[0]

    cursor.execute('SELECT * FROM discount where discountId = %s', [id])
    grid = cursor.fetchall()

    cursor.execute('SELECT * FROM discountOcc where discountId = %s', [id])
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

    cursor.execute('SELECT * From discountMap where defaultm = 1')
    ffm = cursor.fetchall()
    flag = True
    if len(ffm) == 0:
        flag = False

    cursor.execute(
        'SELECT startDate, endDate from discountMap where defaultm = 0 AND discountId != %s', [id])
    storedDates = cursor.fetchall()

    return render_template('showDiscountGrid1.html', grid = grid, data = data, ranges = ranges, result = result, occ = occ, flag = flag, storedDates = storedDates)

@app.route('/unmarkDefault/<id>', methods = ['GET', 'POST'])
def unmarkDefault(id):
    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE discountMap set defaultm = 0 where discountId = %s', [id])
    mysql.connection.commit()
    cursor.close()
    flash('Grid marked as non default', 'success')
    return redirect(url_for('strategyDiscountCreate'))

@app.route('/markDefault/<id>', methods = ['GET', 'POST'])
def markDefault(id):
    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE discountMap set defaultm = 1 where discountId = %s', [id])
    mysql.connection.commit()
    cursor.close()
    flash('Grid marked as default', 'success')
    return redirect(url_for('strategyDiscountCreate'))


@app.route('/deactivateDiscount/<id>', methods = ['GET', 'POST'])
def deactivateDiscount(id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        'UPDATE discountMap set active = 0 where discountId = %s', [id])
    mysql.connection.commit()
    cursor.close()
    flash('Grid Deactivated', 'danger')
    return redirect(url_for('strategyDiscountCreate'))

@app.route('/activateDiscount/<id>', methods = ['GET', 'POST'])
def activateDiscount(id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        'UPDATE discountMap set active = 1 where discountId = %s', [id])
    mysql.connection.commit()
    cursor.close()
    flash('Grid Activated', 'success')
    return redirect(url_for('strategyDiscountCreate'))


@app.route('/editDiscountGrid', methods = ['GET', 'POST'])
def editDiscountGrid():
    inp = request.json
    cursor = mysql.connection.cursor()
    email = session['email']
    time = datetime.datetime.utcnow()

    cursor.execute('UPDATE discountMap SET startDate = %s, endDate = %s, createdBy = %s, createdOn = %s WHERE discountId = %s', [
        inp['startDate'], inp['endDate'], email, time, inp['discountId']
    ])

    cursor.execute('DELETE FROM discount where discountId = %s', [inp['discountId']])

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
            
            cursor.execute('INSERT INTO discount(discountId, leadMin, leadMax, roomMin, roomMax, value) VALUES(%s, %s, %s, %s, %s, %s)', [
                           discountId, leadMin, leadMax, roomMin, roomMax, value])


    mysql.connection.commit()
    cursor.close()


    flash('Your discount grid has been edited', 'success')
    return ('', 204)


@app.route('/settingsAutopilot', methods = ['GET', 'POST'])
def settingsAutopilot():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * from autopilot')
    data = cursor.fetchall()

    for d in data:
        if d['policy'] == 'manual':
            d['policy'] = 'Manual Calculation'

    return render_template('settingsAutopilot.html', data = data)


@app.route('/settingsAutopilotSubmit', methods = ['GET', 'POST'])
def settingsAutopilotSubmit():
    inp = request.json
    email = session['email']
    time = datetime.datetime.utcnow()
    cursor = mysql.connection.cursor()
    cursor.execute('INSERT into autopilot(startDate, endDate, policy, policyName, createdBy, createdOn) VALUES(%s, %s, %s, %s, %s, %s)', [inp['startDate'], inp['endDate'], inp['policy'], inp['policyName'],
    email, time
    ])

    mysql.connection.commit()
    cursor.close()


    flash('Your Autopilot setting has been added', 'success')
    return ('', 204)


@app.route('/showAutopilot/<id>', methods = ['GET', 'POST'])
def showAutopilot(id):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From autopilot where policyName = %s', [id])
    data = cursor.fetchall()
    return render_template('showAutopilot.html', data = data[0])

@app.route('/editAutopilot', methods = ['GET', 'POST'])
def editAutopilot():
    inp = request.json

    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE autopilot SET startDate = %s, endDate = %s, policy = %s WHERE policyName = %s', [
        inp['startDate'], inp['endDate'], inp['policy'], inp['policyName']
    ])

    mysql.connection.commit()
    cursor.close()

    flash('Your Autopilot setting has been edited', 'success')
    return ('', 204)


@app.route('/deactiveAutopilot/<id>', methods = ['GET', 'POST'])
def deactiveAutopilot(id):
    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE autopilot set active = 0 where policyName = %s', [id])

    mysql.connection.commit()
    cursor.close()

    flash('Your Autopilot has been de-activated', 'danger')
    return redirect(url_for('settingsAutopilot'))

@app.route('/activateAutopilot/<id>', methods = ['GET', 'POST'])
def activateAutopilot(id):
    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE autopilot set active = 1 where policyName = %s', [id])

    mysql.connection.commit()
    cursor.close()

    flash('Your Autopilot has been activated', 'success')
    return redirect(url_for('settingsAutopilot'))


@app.route('/requestProcessQuote', methods = ['GET', 'POST'])
def requestProcessQuote():
    inp = request.json
    cursor = mysql.connection.cursor()
    responseId = inp['requestId'] + "R"
    email = session['email']
    now = datetime.datetime.utcnow()
    status = 'QUOTED'

    cursor.execute('INSERT INTO response(requestId, responseId, groupCategory, totalFare, foc, commission, commissionValue, totalQuote, cutoffDays, formPayment, paymentTerms, paymentGtd, negotiable, checkIn, checkOut, submittedBy, submittedOn, status, paymentDays, nights, comments, averageRate) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' , [
        inp['requestId'], responseId, inp['groupCategory'], inp['totalFare'], inp['foc'], str(inp['commission']), str(inp['commissionValue']), inp['totalQuote'], inp['cutoffDays'], procArr(inp['formPayment']), inp['paymentTerms'], inp['paymentGtd'], inp['negotiable'], inp['checkIn'], inp['checkOut'], email, now,
        status, inp['paymentDays'], inp['nights'], inp['comments'],
        inp['averageRate']
    ])

    table = inp['table_result']
    for t in table:
        cursor.execute('INSERT INTO responseDaywise(date, currentOcc, discountId, occupancy, type, count, ratePerRoom, responseId, forecast, leadTime, groups) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
            t['date'], t['currentOcc'], t['discountId'], t['occupancy'], t['type'], t['count'], t['ratePerRoom'], responseId, t['forecast'], t['leadTime'], t['groups']
        ])
    
    cursor.execute("UPDATE request SET status = 'QUOTED' WHERE id = %s", [inp['requestId']])

    cursor.execute('INSERT INTO responseAvg(single1, single2, double1, double2, triple1, triple2, quad1, quad2, responseId) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)' , [
        inp['single1'], inp['single2'], inp['double1'], inp['double2'], inp['triple1'], inp['triple2'], inp['quad1'], inp['quad2'], responseId
    ])

    mysql.connection.commit()

    # dynamic => db

    flash('The request has been quoted', 'success')
    return ('', 204)


if __name__ == "__main__":
    app.run(debug = True)

