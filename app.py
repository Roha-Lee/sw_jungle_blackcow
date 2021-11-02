import threading
from gather_items import gather_hellomarket, gather_bunjang, gather_joongna
from utils import _generate_product_response
from pymongo import MongoClient
from flask import Flask, render_template, jsonify, request
import jwt, hashlib, datetime

app = Flask(__name__)
SECRET_KEY = 'black_cow'

client = MongoClient('localhost', 27017)
db = client.dbjungle_black_cow


@app.route('/')
def home():
    return render_template('index.html')


### 회원 가입 기능 구현 ###
@app.route('/sign_up', methods=['GET'])
def sing_up():
    return render_template('signup.html', title = '회원가입')


@app.route('/sign_up', methods=['POST'])
def sign_up_save():
    # 회원 가입 시 받을 정보 3가지 
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    email_receive = request.form['email_give']

    # password의 경우 보안을 위해 hash 처리
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    user_data = {
        'username': username_receive,
        'password': password_hash,
        'email': email_receive
    }

    db.users.insert_one(user_data)
    return jsonify({'result': 'success'})


@app.route('/check_up', methods=['POST'])
def check_up():
    email_receive = request.form['email_give']
    duplicate = bool(db.users.find_one({'email': email_receive}))
    return jsonify({'result': 'success', 'duplicate':duplicate})


### 로그인 기능 구현 ###
@app.route('/sign_in', methods=['GET'])
def sign_in():
    return render_template('signin.html', title = '로그인')


@app.route('/sign_in', methods=['POST'])
def sign_in_user():
    email_receive = request.form['email_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'email': email_receive, 'password': password_hash})
    
    if result is not None :
        payload = {
            'ID': email_receive,
            'NAME': result['username'],
            'EXP': str(datetime.datetime.utcnow() + datetime.timedelta(seconds = 60 * 60 * 24))
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        
        return jsonify({'result': 'success', 'token': str(token)})
    else :
        return jsonify({'result': 'fail', 'message': 'E-mail/Password가 정확하지 않습니다.'})

@app.route('/my_page', methods=['GET'])
def my_page():
    return render_template('mypage.html', title = '마이페이지')


# 상품 정보 가져오기 기능 구현 
@app.route('/products', methods=['POST'])
def get_products():
    query = request.form['user_query']
    user_token = request.form['user_token']
    
    user_token = bytes(user_token[2:-1].encode('ascii'))
    payload= jwt.decode(user_token, SECRET_KEY, algorithms=['HS256'])
    user_id = payload['ID']
    
    user_favorites = db.favorites.find({"user_id": user_id})
    user_favorites_pid = set()
    for user_favorite in user_favorites:
        user_favorites_pid.add(user_favorite['pid'])

    threads = []
    result_dict = {}
    search_functions = [gather_bunjang, gather_joongna, gather_hellomarket]
    args = (query, result_dict)
    for fn in search_functions:
        th = threading.Thread(target = fn, args = args)
        threads.append(th)
    
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    response = _generate_product_response(result_dict, user_favorites_pid)
    return jsonify(response)

if __name__ == '__main__':  
    app.run('0.0.0.0',port=5000,debug=True)

