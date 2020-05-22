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
            cursor.execute('UPDATE Customers SET email_verified = 1 WHERE email = %s', [email])
        elif data['userType'] == 'iatauser':
            cursor.execute('UPDATE IATAUsers SET email_verified = 1 WHERE email = %s', [email])
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

@app.route('/iatar', methods=['GET', 'POST'])
def iatar():
    return render_template('registerIata.html', title = 'Register')


@app.route('/customerr', methods=['GET', 'POST'])
def customerr():
    return render_template('rcustomer.html', title = 'Register')

@app.route('/registerI', methods = ['GET', 'POST'])
def registerI():
    if request.method == 'POST':
        name = request.form['namev']
        email = request.form['email']
        password = request.form['password']
        agencyName = request.form['agencyName']
        phoneN = request.form['phoneN']
        country = request.form.get('country')
        firstName = name.split(' ')[0]    
        address = ''
        
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * From users where email = %s', [email])
        data = cursor.fetchall()


        if len(data) == 0:
            token = generateConfirmationToken(email)

            sendMail(
                subjectv='Confirm Email',
                recipientsv=email,
                linkv='confirm_email',
                tokenv = token,
                bodyv = 'Confirm your email by clicking this link ',
                senderv = 'koolbhavya.epic@gmail.com'
            )

            cursor.execute("INSERT INTO IATAUsers(name, email, password, agencyName, phone, country, address) VALUES(%s, %s, %s, %s, %s,  %s, %s)", (name, email, password, agencyName, phoneN, country, address))

            cursor.execute('INSERT INTO users(firstName, email, password, userType) Values(%s, %s, %s, %s)', (firstName, email, password, 'iatauser'))
        else:
            flash('Email Already Registered', 'danger')
            return render_template('registerIata.html', title = "Register")

        mysql.connection.commit()
        cursor.close()

        flash('You are now registered and can log in', 'success')
        return render_template('login.html', title = 'Login')


@app.route('/registerC', methods = ['GET', 'POST'])
def registerC():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phoneN = request.form['phoneN']
        country = request.form.get('country')
        address = ''
        userType = request.form.get('userType')
        agencyName = request.form.get('agencyName')
        organizationName = request.form.get('organizationName')


        firstName = name.split(' ')[0]

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

            cursor.execute("INSERT INTO Customers(name, email, password, phone, country, address, userType, agencyName, organizationName) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                           (name, email, password, phoneN, country, address, userType, agencyName, organizationName))
            cursor.execute('INSERT INTO users(firstName, email, password, userType) Values(%s, %s, %s, %s)',
                           (firstName, email, password, 'customer'))
        else:
            flash('Email Already Registered', 'danger')
            return render_template('rcustomer.html', title="Register")

        mysql.connection.commit()
        cursor.close()

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
                        "SELECT * FROM hotelmenuAccess where userType = %s", [userSubType])
                    d = cursor.fetchall()
                    cursor.execute("SELECT * FROM hotelUsers where email = %s", [email])
                    dog = cursor.fetchall()
                    dog = dog[0]
                    session['active'] = getValC2(dog['active'])

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


                elif session['userType'] == 'iatauser':
                    menuParams = {
                    'request': True,
                    'requestCreate': True,
                    'requestManage': True,
                    'requestcreateadhoc': True,
                    'requestcreateseries': True,
                    'userM': True,
                    'userMadd': True,
                    'userMedit': True,
                    'analytics': True,
                    'analyticsDashboard': True,
                    'analyticsbb': True,
                    'analyticsp': True,
                    'analyticsr': True,
                    }
                    cursor.execute("SELECT * FROM iatamenuAccess")
                    d = cursor.fetchall()
                    if len(d) != 0:
                        d = d[0]
                        menuParams['request'] = getValC2(d['request'])
                        menuParams['requestCreate'] = getValC2(
                            d['requestCreate'])
                        menuParams['requestManage'] = getValC2(
                            d['requestManage'])
                        menuParams['userM'] = getValC2(d['userM'])
                        menuParams['userMadd'] = getValC2(d['userMadd'])
                        menuParams['userMedit'] = getValC2(d['userMedit'])
                        menuParams['analytics'] = getValC2(d['analytics'])
                        menuParams['analyticsDashboard'] = getValC2(d['analyticsDashboard'])
                        menuParams['analyticsbb'] = getValC2(d['analyticsbb'])
                        menuParams['analyticsp'] = getValC2(d['analyticsp'])
                        menuParams['analyticsr'] = getValC2(d['analyticsr'])
                        
                        menuParams['requestcreateadhoc'] = getValC2(d['requestcreateadhoc'])
                        menuParams['requestcreateseries'] = getValC2(d['requestcreateseries'])
                    
                    session['menuParams'] = menuParams

                elif session['userType'] == 'customer':
                    menuParams = {
                        'request': True,
                        'requestCreate': True,
                        'requestManage': True,
                        'requestcreateadhoc': True,
                        'requestcreateseries': True,
                        'analytics': True,
                        'analyticsDashboard': True,
                        'analyticsbb': True,
                        'analyticsp': True,
                        'analyticsr': True,
                    }
                    cursor.execute("SELECT * FROM iatamenuAccess")
                    d = cursor.fetchall()
                    if len(d) != 0:
                        d = d[0]
                        menuParams['request'] = getValC2(d['request'])
                        menuParams['requestCreate'] = getValC2(
                            d['requestCreate'])
                        menuParams['requestManage'] = getValC2(
                            d['requestManage'])
                        menuParams['analytics'] = getValC2(d['analytics'])
                        menuParams['analyticsDashboard'] = getValC2(
                            d['analyticsDashboard'])
                        menuParams['analyticsbb'] = getValC2(d['analyticsbb'])
                        menuParams['analyticsp'] = getValC2(d['analyticsp'])
                        menuParams['analyticsr'] = getValC2(d['analyticsr'])

                        menuParams['requestcreateadhoc'] = getValC2(
                            d['requestcreateadhoc'])
                        menuParams['requestcreateseries'] = getValC2(
                            d['requestcreateseries'])

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
        cursor.execute('UPDATE Customers SET password = %s where email = %s', [password, email])
    elif data['userType'] == 'iatauser':
        cursor.execute('UPDATE IATAUsers SET password = %s where email = %s', [password, email])
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
    cursor.execute("SELECT userType FROM hotelmenuAccess")
    data = cursor.fetchall()
    subtypes = []

    for d in data:
        subtypes.append(d['userType'])

    if 'Revenue Management' not in subtypes:
        subtypes.append('Revenue Management')
    if 'Reservations' not in subtypes:
        subtypes.append('Reservation')

    return render_template('hoteladduser.html', title = 'AddUser', subtypes = subtypes)

@app.route('/registerhotelusers', methods = ['GET', 'POST'])
def registerhotelusers():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phoneN = request.form['phoneN']
        address = request.form.get('address')
        country = request.form.get('country')
        city = request.form.get('city')
        userType = request.form['userType']
        firstName = name.split(' ')[0]

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

            cursor.execute('INSERT INTO hotelUsers(name,  email, password, phone, address, country, city, userType) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)', (name,  email, password, phoneN, address, country, city, userType))
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

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        firstName = name.split(' ')[0]

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

            cursor.execute('INSERT INTO developers(name, email, password) values(%s, %s, %s)',
            (name, email, password))
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
    requestc = getValC(request.form.get('requestc'))
    requestcr = getValC(request.form.get('requestcreate'))
    requestm = getValC(request.form.get('requestmanage'))
    
    yieldc = getValC(request.form.get('yield'))
    yieldr = getValC(request.form.get('yieldr'))
    yieldd = getValC(request.form.get('yieldd'))

    business = getValC(request.form.get('business'))
    businessr = getValC(request.form.get('businessr'))
    businessc = getValC(request.form.get('businessc'))
    businesst = getValC(request.form.get('businesst'))
    businessn = getValC(request.form.get('businessn'))
    businessa = getValC(request.form.get('businessa'))

    user = getValC(request.form.get('user'))
    userc = getValC(request.form.get('userc'))
    userh = getValC(request.form.get('userh'))
    
    analytics = getValC(request.form.get('analytics'))
    analyticsd = getValC(request.form.get('analyticsd'))
    analyticsbb = getValC(request.form.get('analyticsbb'))
    analyticsp = getValC(request.form.get('analyticsp'))
    analyticsr = getValC(request.form.get('analyticsr'))

    userType = request.form['usertype']
    developers = getValC(request.form.get('developers'))


    requestcreateadhoc = getValC(request.form.get('requestcreateadhoc'))
    requestcreateseries = getValC(request.form.get('requestcreateseries'))
    yielddiscountcreate = getValC(request.form.get('yielddiscountcreate'))
    yielddiscountmap = getValC(request.form.get('yielddiscountmap'))

    businessRequestcreate = getValC(request.form.get('businessRequestcreate'))
    businessRequestmap = getValC(request.form.get('businessRequestmap'))
    businesscontactcreate = getValC(request.form.get('businesscontactcreate'))
    businesscontactmap = getValC(request.form.get('businesscontactmap'))
    businessTimemap = getValC(request.form.get('businessTimemap'))

    businessRooms = getValC(request.form.get('businessRooms'))
    businessTimecreate = getValC(request.form.get('businessTimecreate'))
    userMHoteladd = getValC(request.form.get('userMHoteladd'))
    userMHoteledit = getValC(request.form.get('userMHoteledit'))
    userMCustomeradd = getValC(request.form.get('userMCustomeradd'))
    userMCustomeredit = getValC(request.form.get('userMCustomeredit'))
    userMCustomerupload = getValC(request.form.get('userMCustomerupload'))


    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From hotelmenuAccess where userType = %s', [userType])
    data = cursor.fetchall()

    if len(data) == 0:
        cursor.execute('INSERT INTO hotelmenuAccess(userType,request, requestCreate, requestManage, yield, yieldRate, yieldDiscount, business, businessRequest, businessContact, businessTime, businessNegotiation, businessAuto, userM, userMHotel, userMCustomer, developers, analytics, analyticsDashboard, analyticsbb, analyticsp, analyticsr, requestcreateadhoc, requestcreateseries, yielddiscountcreate, yielddiscountmap, businessRequestcreate, businessRequestmap, businesscontactcreate, businesscontactmap, businessTimemap, businessRooms, businessTimecreate, userMHoteladd, userMHoteledit, userMCustomeradd, userMCustomeredit, userMCustomerupload ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                       userType, requestc, requestcr, requestm, yieldc, yieldr, yieldd, business, businessr, businessc, businesst, businessn, businessa, user, userh, userc, developers, analytics, analyticsd, analyticsbb, analyticsp, analyticsr, requestcreateadhoc, requestcreateseries, yielddiscountcreate, yielddiscountmap, businessRequestcreate, businessRequestmap,  businesscontactcreate, businesscontactmap,  businessTimemap, businessRooms, businessTimecreate, userMHoteladd, userMHoteledit, userMCustomeradd, userMCustomeredit, userMCustomerupload])

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
    cursor.execute('SELECT name, email, userType, active FROM hotelUsers')

    result = cursor.fetchall()
    cursor.close()
    data = []
    for res in result:
        res['firstName'] = res['name'].split()[0]
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
    data[0]['firstName'] = data[0]['name'].split(' ')[0]
    data[0]['active'] = 'Yes' if data[0]['active'] else 'No'
    return render_template('showprofile.html', title = 'Profile', data = data[0])

@app.route('/editUser/<email>', methods = ["GET", "POST"])
def editUser(email):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM hotelUsers where email = %s', [email])

    data = cursor.fetchall()
    cursor.execute("SELECT userType FROM hotelmenuAccess")
    data1 = cursor.fetchall()
    subtypes = []

    for d in data1:
        subtypes.append(d['userType'])

    if 'Revenue Management' not in subtypes:
        subtypes.append('Revenue Management')
    if 'Reservations' not in subtypes:
        subtypes.append('Reservation')

    data[0]['email_verified'] = "Yes" if data[0]['email_verified'] else "No"
    return render_template('editUser.html', title = 'Edit', data = data[0], subtypes = subtypes)

@app.route('/submitEditUser', methods = ['GET', 'POST'])
def submitEditUser():
    name = request.form['name']
    phone = request.form['phoneN']
    address = request.form.get('address')
    country = request.form.get('country')
    city = request.form.get('city')
    userType = request.form['userType']
    email_verified = getValC(request.form.get('email_verified'))
    oldemail = request.form['oldemail']
    active = getValC(request.form.get('active'))
    firstName = name.split()[0]

    cursor = mysql.connection.cursor()

    cursor.execute('Update hotelUsers SET name = %s,  phone = %s, address = %s, country = %s, city = %s, userType = %s, email_verified = %s, active = %s WHERE email = %s',(name, phone, address, country, city, userType, email_verified, active, oldemail))


    cursor.execute('Update users SET firstName = %s,  userSubType = %s WHERE email = %s', (firstName, userType, oldemail))

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
        cursor.execute('SELECT * From Customers where email = %s', [email])
        result = cursor.fetchall()
    elif data == 'iatauser':
        cursor.execute('SELECT * From IATAUsers where email = %s', [email])
        result = cursor.fetchall()
    elif data == 'developer':
        cursor.execute('SELECT * From developers where email = %s', [email])
        result = cursor.fetchall()
    
    result = result[0]
    result['email_verified'] = "Yes" if result['email_verified'] else 'No'
    if 'active' in result.keys():
        result['active'] = "Yes" if result['active'] else 'No'

    result['firstName'] = result['name'].split(' ')[0]
    

    return render_template('myProfile.html', data = result)


@app.route('/submitEditUserAll', methods=['GET', 'POST'])
def submitEditUserAll():
    name = request.form['name']
    phone = request.form['phoneN']
    address = request.form.get('address')
    country = request.form.get('country')
    oldemail = request.form['oldemail']
    password = request.form['password']
    agencyName = request.form.get('agencyName')
    organizationName = request.form.get('organizationName')

    firstName = name.split(' ')[0]
    cursor = mysql.connection.cursor()

    cursor.execute('SELECT userType From users where email = %s', [oldemail])
    data = cursor.fetchall()

    data = data[0]['userType']
    if data == 'hoteluser':
        cursor.execute('Update hotelUsers SET name = %s, phone = %s, address = %s, country = %s, password = %s WHERE email = %s',
                        (name, phone, address, country, password, oldemail))
    elif data == 'customer':
        cursor.execute('Update Customers SET name = %s, phone = %s, address = %s, country = %s, password = %s, organizationName = %s WHERE email = %s',
                        (name, phone, address, country,password, organizationName, oldemail))
    elif data == 'iatauser':
        cursor.execute('Update IATAUsers SET name = %s, phone = %s, address = %s, country = %s, password = %s, agencyName = %s WHERE email = %s',
                        (name, phone, address, country, password, agencyName, oldemail))
    elif data == 'developer':
        cursor.execute('Update developers SET name = %s, password = %s, phone = %s, address = %s WHERE email = %s',
                        (name, password, phone, address, oldemail))

    cursor.execute('Update users SET firstName = %s, password = %s WHERE email = %s',
                    (firstName, password, oldemail))
    
    mysql.connection.commit()
    cursor.close()

    flash('Hotel user has been edited', 'success')
    return render_template('index.html')

@app.route('/inviteemail', methods = ['GET', 'POST'])
def inviteemail():
    email = request.form['email']
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From users where email = %s', [email])
    data = cursor.fetchall()

    if len(data) != 0:
        flash('Email already registered', 'danger')
        return render_template('login.html', title='Login')
    else:
        token = generateConfirmationToken(email)

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
    cursor.execute("SELECT userType FROM hotelmenuAccess")
    data = cursor.fetchall()
    subtypes = []

    for d in data:
        subtypes.append(d['userType'])

    if 'Revenue Management' not in subtypes:
        subtypes.append('Revenue Management')
    if 'Reservations' not in subtypes:
        subtypes.append('Reservation')
    return render_template('addhoteluserinv.html', title = 'Register', email = email, subtypes = subtypes)


@app.route('/iatanav', methods = ['GET', 'POST'])
def iatanav():
    requestc = getValC(request.form.get('requestc'))
    requestcr = getValC(request.form.get('requestcreate'))
    requestm = getValC(request.form.get('requestmanage'))

    user = getValC(request.form.get('user'))
    useredit = getValC(request.form.get('userc'))
    useradd = getValC(request.form.get('userh'))

    analytics = getValC(request.form.get('analytics'))
    analyticsd = getValC(request.form.get('analyticsd'))
    analyticsbb = getValC(request.form.get('analyticsbb'))
    analyticsp = getValC(request.form.get('analyticsp'))
    analyticsr = getValC(request.form.get('analyticsr'))

    requestcreateadhoc = getValC(request.form.get('requestcreateadhoc'))
    requestcreateseries = getValC(request.form.get('requestcreateseries'))
    
    cursor = mysql.connection.cursor()
    cursor.execute(
        'SELECT * From iatamenuAccess')
    data = cursor.fetchall()
    if len(data) == 0:
        cursor.execute('INSERT INTO iatamenuAccess(request, requestCreate, requestManage, userM, userMadd, userMedit, requestcreateadhoc, requestcreateseries, analytics, analyticsr, analyticsbb, analyticsDashboard, analyticsp) VALUES( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
            requestc, requestcr, requestm, user, useradd, useredit, requestcreateadhoc, requestcreateseries, analytics, analyticsr, analyticsbb, analyticsd, analyticsp
        ])
    else:
        flash('UserType Already Registered', 'danger')
        return render_template('hoteladdusertype.html', title="Register")

    mysql.connection.commit()
    cursor.close()

    flash('New userType added', 'success')
    return render_template('index.html', title='UserType')


@app.route('/customernav', methods = ['GET', 'POST'])
def customernav():
    requestc = getValC(request.form.get('requestc'))
    requestcr = getValC(request.form.get('requestcreate'))
    requestm = getValC(request.form.get('requestmanage'))
    
    analytics = getValC(request.form.get('analytics'))
    analyticsd = getValC(request.form.get('analyticsd'))
    analyticsbb = getValC(request.form.get('analyticsbb'))
    analyticsp = getValC(request.form.get('analyticsp'))
    analyticsr = getValC(request.form.get('analyticsr'))

    requestcreateadhoc = getValC(request.form.get('requestcreateadhoc'))
    requestcreateseries = getValC(request.form.get('requestcreateseries'))

    cursor = mysql.connection.cursor()
    cursor.execute(
        'SELECT * From customermenuAccess')
    data = cursor.fetchall()
    if len(data) == 0:
        cursor.execute('INSERT INTO customermenuAccess(request, requestCreate, requestManage,  requestcreateadhoc, requestcreateseries, analytics, analyticsr, analyticsbb, analyticsDashboard, analyticsp) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
        requestc, requestcr, requestm,  requestcreateadhoc, requestcreateseries, analytics, analyticsr, analyticsbb, analyticsd, analyticsp
        ])
    else:
        flash('UserType Already Registered', 'danger')
        return render_template('hoteladdusertype.html', title="Register")

    mysql.connection.commit()
    cursor.close()

    flash('New userType added', 'success')
    return render_template('index.html', title='UserType')


@app.route('/edituserType', methods = ['GET', 'POST'])
def edituserType():
    cursor = mysql.connection.cursor()
    cursor.execute(
        'SELECT * From customermenuAccess')
    datac = cursor.fetchall()
    datac = datac[0]
    
    cursor.execute(
        'SELECT * From iatamenuAccess')
    datai = cursor.fetchall()
    datai = datai[0]

    cursor.execute(
        'SELECT * From hotelmenuAccess')
    datah = cursor.fetchall()
    datah = datah[0]

    return render_template('editusertype.html', datac= datac, datai = datai, datah=datah)

@app.route('/customernavupdate', methods = ['GET', 'POST'])
def customernavupdate():
    return 'h'  



if __name__ == "__main__":
    app.run(debug = True)


'''

    TODOS

    marked on top
    country madatory

    invite usertype param

'''
