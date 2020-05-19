from flask import Flask, render_template, flash, request, session, url_for, session
from config import Config
from functools import wraps
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Mail, Message
from wtforms import Form, StringField, TextAreaField, BooleanField, PasswordField, validators
from wtforms.fields.html5 import EmailField
from wtforms.widgets import TextArea
from flask_mysqldb import MySQL

app = Flask(__name__)
app.config.from_object(Config)

mail = Mail(app)
mysql = MySQL(app)


# Email Confirmations
def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

def confirm_token(token, expiration=3600):
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


@app.route('/confirm_email/<token>', methods=['GET', 'POST'])
def confirm_email(token):
    email = confirm_token(token)

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

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized, Please Login", 'danger')
            return render_template('login.html', title = 'Login')
    return wrap










@app.route('/', methods = ['GET', 'POST'])
def f():
    try:
        if session['logged_in'] == True:
            return render_template('index.html', title = 'Home')
    except:
        return render_template('login.html', title = 'Login')


@app.route('/signIn', methods=['GET', 'POST'])
def index():
    return render_template('login.html', title = 'Login')

@app.route('/home', methods = ['GET', 'POST'])
def home():
    try:
        if session['logged_in'] == True:
            return render_template('index.html', title = 'Home')
    except:
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
            token = generate_confirmation_token(email)
            msg = Message(
            'Confirm Email',
            sender='koolbhavya.epic@gmail.com',
            recipients=[email])
            link = url_for('confirm_email', token=token, _external=True)
            msg.body = 'Confirm your email by clicking this link:- {}'.format(link)
            mail.send(msg)

            cursor.execute("INSERT INTO IATAUsers(name, email, password, agencyName, phone, country) VALUES(%s, %s, %s, %s, %s,  %s, %s)", (name, email, password, agencyName, phoneN, country, address))
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
            token = generate_confirmation_token(email)
            msg = Message(
            'Confirm Email',
            sender='koolbhavya.epic@gmail.com',
            recipients=[email])
            link = url_for('confirm_email', token=token, _external=True)
            msg.body = 'Confirm your email by clicking this link:- {}'.format(link)
            mail.send(msg)
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
                menuParams = {
                    'request': True,
                    'requestCreate': True,
                    'requestManage': True,
                    'yield': True,
                    'yieldRate': True,
                    'yieldDiscount': True,
                    'business': True,
                    'businessRequest': True,
                    'businessContact': True,
                    'businessTime': True,
                    'businessNegotiation': True,
                    'businessAuto': True,
                    'userM': True,
                    'userMHotel': True,
                    'userMCustomer': True,
                    'developers': True,
                    'analytics': True,
                    'analyticsDashboard': True,
                    'analyticsbb': True,
                    'analyticsp': True,
                    'analyticsr': True,
                }

                
                if session['userType'] == 'hoteluser':
                    session['userSubType'] = data['userSubType']
                    userSubType = data['userSubType']
                    cursor.execute("SELECT * FROM menuAccess where userType = %s", [userSubType])
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
                        menuParams['yield'] = getValC2(d['yield'])
                        menuParams['yieldRate'] = getValC2(d['yieldRate'])
                        menuParams['yieldDiscount'] = getValC2(d['yieldDiscount'])
                        menuParams['business'] = getValC2(d['business'])
                        menuParams['businessRequest'] = getValC2(d['businessRequest'])
                        menuParams['businessContact'] = getValC2(d['businessContact'])
                        menuParams['businessTime'] = getValC2(d['businessTime'])
                        menuParams['businessNegotiation'] = getValC2(d['businessNegotiation'])
                        menuParams['businessAuto'] = getValC2(d['businessAuto'])
                        menuParams['userM'] = getValC2(d['userM'])
                        menuParams['userMHotel'] = getValC2(d['userMHotel'])
                        menuParams['userMCustomer'] = getValC2(d['userMCustomer'])
                        menuParams['userMCustomer'] = getValC2(d['userMCustomer'])
                        menuParams['developers'] = getValC2(d['developers'])
                        menuParams['analytics'] = getValC2(d['analytics'])
                        menuParams['analyticsDashboard'] = getValC2(d['analyticsDashboard'])
                        menuParams['analyticsbb'] = getValC2(d['analyticsbb'])
                        menuParams['analyticsp'] = getValC2(d['analyticsp'])
                        menuParams['analyticsr'] = getValC2(d['analyticsr'])

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
        token = generate_confirmation_token(email)
        msg = Message(
            'Update Password',
            sender = 'koolbhavya.epic@gmail.com',
            recipients = [email])
        link = url_for('passwordupdate', token = token, _external=True)
        msg.body = 'Change your password by clicking this link:- {}'.format(link)
        mail.send(msg)

        flash('Kindly Check your email', 'success')
        return render_template('login.html', title = 'Login')


@app.route('/passwordupdate/<token>', methods = ['GET', 'POST'])
def passwordupdate(token):
    email = confirm_token(token)
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
    cursor.execute("SELECT userType FROM menuAccess")
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
            token = generate_confirmation_token(email)
            msg = Message(
                'Confirm Email',
                sender='koolbhavya.epic@gmail.com',
                recipients=[email])
            link = url_for('confirm_email', token=token, _external=True)
            msg.body = 'Confirm your email by clicking this link:- {}'.format(
                link)
            mail.send(msg)
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

            token = generate_confirmation_token(email)
            msg = Message(
                    'Confirm Email',
                    sender='koolbhavya.epic@gmail.com',
                    recipients=[email])
            link = url_for('confirm_email', token=token, _external=True)
            msg.body = 'Confirm your email by clicking this link:- {}'.format(
                    link)
            mail.send(msg)

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


    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * From menuAccess where userType = %s', [userType])
    data = cursor.fetchall()

    if len(data) == 0:
        cursor.execute('INSERT INTO menuAccess(userType,request, requestCreate, requestManage, yield, yieldRate, yieldDiscount, business, businessRequest, businessContact, businessTime, businessNegotiation, businessAuto, userM, userMHotel, userMCustomer, developers, analytics, analyticsDashboard, analyticsbb, analyticsp, analyticsr) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                       userType, requestc, requestcr, requestm, yieldc, yieldr, yieldd, business, businessr, businessc, businesst, businessn, businessa, user, userh, userc, developers, analytics, analyticsd, analyticsbb, analyticsp, analyticsr])

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
    cursor.execute("SELECT userType FROM menuAccess")
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



if __name__ == "__main__":
    app.run(debug = True)


'''

    TODOS

        invite email option
        edit usertype
        navbar db

'''
