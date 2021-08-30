import hmac
import sqlite3
import cloudinary
import cloudinary.uploader
import re
import rsaidnumber
from datetime import timedelta

from flask_cors import CORS
from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from flask_jwt import JWT, jwt_required, current_identity


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def users():
    conn = sqlite3.connect('final.db')
    print("Database Ready")

    conn.execute("CREATE TABLE IF NOT EXISTS users("
                 "name TEXT NOT NULL,"
                 "surname TEXT NOT NULL,"
                 "id_number INTEGER NOT NULL,"
                 "email TEXT NOT NULL,"
                 "username TEXT NOT NULL PRIMARY KEY,"
                 "password TEXT NOT NULL)")
    print('User Table Active')
    conn.close()


def products():
    conn = sqlite3.connect('final.db')
    conn.execute("CREATE TABLE IF NOT EXISTS product(id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "title TEXT NOT NULL,"
                 "image TEXT NOT NULL,"
                 "price TEXT NOT NULL,"
                 "type TEXT NOT NULL)")
    print('Product Table Ready')
    conn.close()


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def fetch_users():
    with sqlite3.connect('final.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        customer = cursor.fetchall()

        all_data = []

        for data in customer:
            all_data.append(User(data[2], data[4], data[5]))
    return all_data


customers = fetch_users()
users()
products()


# function to take image uploads and convert them into urls
def upload_file():
    app.logger.info('in upload route')
    cloudinary.config(cloud_name = "dbcczql4w",
                      api_key = "138784466689969",
                      api_secret = "Nw8Wv4yVQaFk7I8gu1PHt2OcPxQ"
                      )
    upload_result = None
    if request.method == 'POST' or request.method == 'PUT':
        image = request.json['image']
        app.logger.info('%s file_to_upload', image)
        if image:
            upload_result = cloudinary.uploader.upload(image)
            app.logger.info(upload_result)
            return upload_result['url']


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return user_id.get(user_id, None)


username_table = {u.username: u for u in customers}
userid_table = {u.id: u for u in customers}


# Flask application
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})           # allows you to use api
app.debug = True                                         # when finds a bug, it continues to run
app.config['SECRET_KEY'] = 'super-secret'                # a random key used to encrypt your web app
app.config["JWT_EXPIRATION_DELTA"] = timedelta(days=1)   # allows token to last a day
app.config['MAIL_SERVER'] = 'smtp.gmail.com'             # Code For Sending Emails Through Flask
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = '081698work@gmail.com'
app.config['MAIL_PASSWORD'] = 'open@123'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)                                         # Code For Sending Emails Ends
app.config['TESTING'] = True
app.config['CORS_HEADERS'] = ['Content-Type']

jwt = JWT(app, authenticate, identity)


@app.route('/login/', methods=['PATCH'])
def login():
    response = {}

    if request.method == 'PATCH':
        username = request.json['username']
        password = request.json['password']

        with sqlite3.connect('final.db') as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? and password=?", (username, password))
            user = cursor.fetchone()

            response['message'] = 'User ' + str(username) + ' retrieved'
            response['status_code'] = 201
            response['data'] = user
        return response


@app.route('/register/', methods=['POST'])
def register():
    response = {}

    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        id_number = request.form['id_number']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        try:
            regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
            if re.search(regex, email) and rsaidnumber.parse(id_number):
                with sqlite3.connect('final.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO users('
                                   'name,'
                                   'surname,'
                                   'id_number,'
                                   'email,'
                                   'username,'
                                   'password) VALUES(?,?,?,?,?,?)', (name, surname, id_number, email, username, password))
                    conn.commit()
                    msg = Message('Welcome To Tech Town', sender='081698work@gmail.com', recipients=[email])
                    msg.subject = 'New User'
                    msg.body = "Thank You For Registering with us " + name + "."
                    msg.body = "Don't forget your Username: " + username + " and Password: " + password + "."
                    mail.send(msg)

                    response['message'] = 'Registration Successful'
                    response['status_code'] = 201
            else:
                response['message'] = 'Invalid Email Address'
                response['status_code'] = 401
        except ValueError:
            response['message'] = 'ID Number Invalid'
            response['status_code'] = 400
        except sqlite3.IntegrityError:
            response['message'] = 'This username has been taken'
            response['status_code'] = 400
    return response


@app.route('/reset-password/<username>', methods=["PUT"])
def reset(username):
    response = {}

    if request.method == 'PUT':
        with sqlite3.connect('final.db') as conn:
            password = request.json['password']
            put_data = {}

            if password is not None:
                put_data['password'] = password
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET password =? WHERE username=?', (put_data['password'], username))
                conn.commit()
                response['message'] = 'Password Reset Successfully'
                response['status_code'] = 200
            return response


@app.route('/show-users/', methods=["GET"])
def show_users():
    response = {}

    with sqlite3.connect("final.db") as conn:
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")

        people = cursor.fetchall()

    response['message'] = 'All Users Found'
    response['status_code'] = 201
    response['data'] = people
    return jsonify(response)


@app.route('/view-user/<username>', methods=["GET"])
def view_user(username):
    response = {}
    with sqlite3.connect('final.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE username='" + str(username) + "'")
        response["status_code"] = 200
        response["description"] = "User retrieved successfully"
        response["data"] = cursor.fetchone()
    return jsonify(response)


# A Route To Add A New Product
@app.route('/add-product/', methods=['POST'])
def add_product():
    response = {}

    if request.method == 'POST':
        title = request.json['title']
        image = upload_file()
        price = request.json['price']
        type = request.json['type']

        with sqlite3.connect('final.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO product(title,'
                           'image,'
                           'price,'
                           'type) VALUES(?,?,?,?)', (title, image, price, type))
            conn.commit()
            response['status_code'] = 201
            response['description'] = 'New Product Has Been Added'
    return response


# A Route To View All Products
@app.route('/show-products/', methods=['GET'])
def view_products():
    response = {}

    with sqlite3.connect('final.db') as conn:
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM product')

        product = cursor.fetchall()

    response['data'] = product
    return jsonify(response)


# A Route to View A Specific Products
@app.route('/view-product/<int:id>', methods=['GET'])
def view_product(id):
    response = {}

    with sqlite3.connect('final.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM product WHERE id=' + str(id))

        response['status_code'] = 200
        response['description'] = 'Product Successfully Retrieved'
        response['data'] = cursor.fetchone()
    return jsonify(response)


# A Route To Edit A Specific user
@app.route('/edit-user/<user>', methods=['PUT'])
def edit_user(user):
    response = {}

    if request.method == 'PUT':
        with sqlite3.connect('final.db') as conn:
            name = request.json['name']
            surname = request.json['surname']
            email = request.json['email']
            username = request.json['username']
            password = request.json['password']
            put_data = {}

            if name is not None:
                put_data['name'] = name
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET name=? WHERE username=?', (put_data['name'], user))
                conn.commit()

                response['message'] = 'User Name Updated Successfully'
                response['status_code'] = 200

            if surname is not None:
                put_data['surname'] = surname
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET surname=? WHERE username=?', (put_data['surname'], user))
                conn.commit()
                response['message'] = 'User Surname Updated Successfully'
                response['status_code'] = 200

            if email is not None:
                put_data['email'] = email
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET email=? WHERE username=?',(put_data['email'], user))
                conn.commit()
                response['message'] = 'User Email Address Updated Successfully'
                response['status_code'] = 200

            if username is not None:
                put_data['username'] = username
                cursor = conn.cursor()
                cursor.execute('UPDATE product SET username=? WHERE username=?',(put_data['username'], user))
                conn.commit()
                response['message'] = 'User Username Updated Successfully'
                response['status_code'] = 200

            if password is not None:
                put_data['password'] = password
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET password =? WHERE username=?',(put_data['password'], user))
                conn.commit()
                response['message'] = 'User Password Updated Successfully'
                response['status_code'] = 200
        return response


# A Route To Edit A Specific Product
@app.route('/edit-product/<int:id>', methods=['PUT'])
def edit_product(id):
    response = {}
    try:
        if request.method == 'PUT':
            with sqlite3.connect('final.db') as conn:
                incoming_data = dict(request.json)
                put_data = {}

                if incoming_data.get('title') is not None:
                    put_data['title'] = incoming_data.get('title')
                    cursor = conn.cursor()
                    cursor.execute('UPDATE product SET title=? WHERE id=?', (put_data['title'], id))
                    conn.commit()

                    response['message'] = 'Product Title Updated Successfully'
                    response['status_code'] = 200

                if incoming_data.get('image') is not None:
                    put_data['image'] = upload_file()
                    cursor = conn.cursor()
                    cursor.execute('UPDATE product SET image=? WHERE id=?',(put_data['image'], id))
                    conn.commit()
                    response['message'] = 'Product Image Updated Successfully'
                    response['status_code'] = 200

                if incoming_data.get('price') is not None:
                    put_data['price'] = incoming_data.get('price')
                    cursor = conn.cursor()
                    cursor.execute('UPDATE product SET price=? WHERE id=?', (put_data['price'], id))
                    conn.commit()
                    response['message'] = 'Product Price Updated Successfully'
                    response['status_code'] = 200

                if incoming_data.get('type') is not None:
                    put_data['type'] = incoming_data.get('type')
                    cursor = conn.cursor()
                    cursor.execute('UPDATE product SET type=? WHERE id=?',(put_data['type'], id))
                    conn.commit()
                    response['message'] = 'Product Type Updated Successfully'
                    response['status_code'] = 200
    except ValueError:
        if request.method != "PUT":
            response['message'] = 'error method is in correct'
            response['status_code'] = 400
    finally:
        return response


# A Route to delete products
@app.route('/delete-product/<int:id>')
def delete_product(id):
    response = {}

    with sqlite3.connect('final.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM product WHERE id=' + str(id))
        conn.commit()
        response['status_code'] = 204
        response['message'] = 'Product Has Been Deleted'
    return response


@app.route('/delete-user/<username>')
def delete_user(username):
    response = {}

    with sqlite3.connect('final.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username='" + str(username) +"'")
        conn.commit()
        response['status_code'] = 200
        response['message'] = 'User Has Been Deleted'
    return response


if __name__ == '__main__':
    app.run()
