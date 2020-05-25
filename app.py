from flask import Flask, render_template, flash, request, session, url_for, session
from config import Config
from functools import wraps
from flask_mysqldb import MySQL
from functions import *


app = Flask(__name__)
app.config.from_object(Config)

mail = Mail(app)
mysql = MySQL(app)

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


@app.route('/', methods = ['GET', 'POST'])
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

                print(session)
                
                flash('You are now logged in', 'success')
                return render_template('index.html')
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
    
    print(data)

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

@app.route('/deactivateUser/<email>', methods = ['GET', 'POST'])
def deactivateUser(email):
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE hotelUsers SET active = 0 where email = %s", [email])
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




if __name__ == "__main__":
    app.run(debug = True)
