from flask import Flask, render_template, flash, request, session, url_for, session, jsonify, redirect
from config import Config
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from functools import wraps
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from flask_mysqldb import MySQL
import datetime

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
    cursor.execute('SELECT * FROM request where id = %s', [token])
    data = cursor.fetchall()
    data = data[0]
    data['createdOn'] = data['createdOn'].strftime("%d/%B/%Y, %H:%M:%S")
    string = ''
    v = data['paymentTerms']
    if v != None:
        if v.count('pc') > 0:
            string = 'Post Checkout'
            data['paymentTerms'] = string

    string = ''
    v = data['formPayment']
    if v != None:
        if v.count('cq') > 0:
            string = 'Cheque'
            data['formPayment'] = string

    if data['comments'].isspace():
        data['comments'] = ''

    nights = data['nights']
    curr_date = data['checkIn']
    result = []
    dates = []

    mmp = 1
    for i in range(0, int(nights)):
        tempResult = []
        cursor.execute('SELECT * FROM request1Bed where date = %s AND id = %s', [curr_date, token])
        resultPerDay1 = cursor.fetchall()
        #print(resultPerDay1)
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
        
        cursor.execute(
            'SELECT * FROM request2Bed where date = %s AND id = %s', [curr_date, token])
        resultPerDay2 = cursor.fetchall()
        #print(resultPerDay2)
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
                # print(pent)
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

        dates.append(curr_date.strftime('%B %d'))


        result.append(tempResult)
    
        curr_date = curr_date + datetime.timedelta(days = 1)
    
    print(result)
    if (mmp == 0):
        flash('No Rate Grid available!', 'danger')
    return render_template('requestProcess.html', data = data, result = result, length = len(result), dates = dates)


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
    print(inp)
    occ = inp['occ']
    print(occ)
        
    cursor = mysql.connection.cursor()
    for o in occ:
        cursor.execute('INSERT INTO discountOcc(discountId, occ, col) VALUES(%s, %s, %s)', [inp['discountId'], o['occ'], o['col']])
    
    cursor.execute('INSERT INTO discountMap(discountId, startDate, endDate, defaultm) VALUES(%s, %s, %s, %s)', [inp['discountId'], inp['startDate'], inp['endDate'], inp['defaultm']])

    for jindex, l in enumerate(inp['leadtime']):
        lead = l.split(' - ')
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
    print(occ)

    ranges = []
    range1 = {}
    for l in grid:
        key = l['roomMin'] + " - " + l['roomMax']
        if key not in range1:
            range1[key] = 0
            ranges.append(key)
        else:
            break

    print(ranges)

    
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

    return render_template('showDiscountGrid1.html', grid = grid, data = data, ranges = ranges, result = result, occ = occ, flag = flag)

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



if __name__ == "__main__":
    app.run(debug = True)
