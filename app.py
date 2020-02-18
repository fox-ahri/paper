import json
import os
import time
from bson.objectid import ObjectId
import pymongo
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app, supports_credentials=True)

# mongo = "mongodb://root:Aa12345.@127.0.0.1:27017/"
mongo = "mongodb://root:Aa12345.@127.0.0.1:11001/"


@app.route('/')
@app.route('/index')
def hello_world():
    return render_template("index.html")


@app.route('/login')
def login_view():
    return render_template("login.html")


@app.route('/tagging')
def tagging_view():
    return render_template("tagging.html")


@app.route('/inspect')
def inspect_view():
    return render_template("inspect.html")


@app.route('/user')
def user_view():
    return render_template("user.html")


@app.route('/api/login', methods=['POST'])
def login():
    userdata = json.loads(request.get_data().decode('utf-8'))
    conn = pymongo.MongoClient(mongo)
    user = conn['paper']['user'].find_one({'username': userdata['username'], 'password': userdata['password']})
    if user:
        user['_id'] = str(user['_id'])
        if user['username'] == 'admin':
            return jsonify({
                'code': 100,
                'msg': '',
                'data': user
            })
        return jsonify({
            'code': 200,
            'msg': '',
            'data': user
        })
    else:
        return jsonify({
            'code': 400,
            'msg': '用户名或密码错误！',
            'data': {}
        })


@app.route('/api/user', methods=['GET', 'POST', 'DELETE'])
def user():
    if request.method == 'GET':
        conn = pymongo.MongoClient(mongo)
        users = conn['paper']['user'].find({'username': {'$ne': 'admin'}})
        res = []
        for i in users:
            i['_id'] = str(i['_id'])
            res.append(i)
        return jsonify({
            'code': 200,
            'msg': '',
            'data': res
        })
    elif request.method == 'POST':
        userdata = json.loads(request.get_data().decode('utf-8'))
        conn = pymongo.MongoClient(mongo)
        old_user = conn['paper']['user'].find_one({'username': userdata['username']})
        if userdata['username'] == 'nobody' or old_user:
            return jsonify({
                'code': 400,
                'msg': '用户名重复',
                'data': {}
            })
        else:
            conn['paper']['user'].insert_one(
                {'username': userdata['username'], 'password': userdata['password'], 'role': userdata['role'],
                 'date': time.strftime("%Y-%m-%d %H:%M", time.localtime())})
            return jsonify({
                'code': 200,
                'msg': '',
                'data': {}
            })
    elif request.method == 'DELETE':
        conn = pymongo.MongoClient(mongo)
        conn['paper']['user'].delete_one({'_id': ObjectId(request.args['_id'])})
        return jsonify({
            'code': 200,
            'msg': '',
            'data': {}
        })


@app.route('/api/select', methods=['POST'])
def select():
    form = json.loads(request.get_data().decode('utf-8'))
    conn = pymongo.MongoClient(mongo)
    if form['opera'] == 'select':
        user = conn['paper']['user'].find_one({'_id': ObjectId(form['user_id'])})
        tmp = conn['paper']['paper'].find_one({'status': {'$lt': 1}, 'u1': user['username']})
        if tmp:
            tmp['_id'] = str(tmp['_id'])
            if tmp['_id'] == form['_id']:
                return jsonify({
                    'code': 402,
                    'msg': '继续标注...',
                    'data': tmp
                })
            else:
                return jsonify({
                    'code': 401,
                    'msg': '有任务未完成,请继续标注...',
                    'data': tmp
                })
        if int(user['role']) > 1 or conn['paper']['paper'].find_one({'_id': ObjectId(form['_id']), 'status': 1}):
            conn['paper']['paper'].update_one({'_id': ObjectId(form['_id'])},
                                              {'$set': {'status': 0, 'u1': user['username']}})
            paper = conn['paper']['paper'].find_one({'_id': ObjectId(form['_id'])})
            paper['_id'] = str(paper['_id'])
            return jsonify({
                'code': 200,
                'msg': '',
                'data': paper
            })
        else:
            return jsonify({
                'code': 400,
                'msg': '该辩题已被选取',
                'data': {}
            })
    elif form['opera'] == 'save':
        conn['paper']['paper'].update_one({'_id': ObjectId(form['_id'])}, {
            '$set': {'content': form['content'], 'name': form['name'],
                     'date': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}})
        return jsonify({
            'code': 200,
            'msg': '',
            'data': {}
        })
    elif form['opera'] == 'inspect':
        paper = conn['paper']['paper'].find_one({'_id': ObjectId(form['_id'])})
        paper['_id'] = str(paper['_id'])
        return jsonify({
            'code': 200,
            'msg': '',
            'data': paper
        })
    elif form['opera'] == 'pass':
        user = conn['paper']['user'].find_one({'_id': ObjectId(form['user_id'])})
        conn['paper']['paper'].update_one({'_id': ObjectId(form['_id'])}, {
            '$set': {'status': 3, 'u2': user['username'], 'content': form['content'], 'name': form['name'],
                     'date': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}})
        return jsonify({
            'code': 200,
            'msg': '',
            'data': {}
        })
    elif form['opera'] == 'redo':
        user = conn['paper']['user'].find_one({'_id': ObjectId(form['user_id'])})
        conn['paper']['paper'].update_one({'_id': ObjectId(form['_id'])}, {
            '$set': {'status': -1, 'u2': user['username'], 'content': form['content'], 'name': form['name'],
                     'date': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}})
        return jsonify({
            'code': 200,
            'msg': '',
            'data': {}
        })
    else:
        conn['paper']['paper'].update_one({'_id': ObjectId(form['_id'])},
                                          {'$set': {'content': form['content'], 'name': form['name'], 'status': 2,
                                                    'date': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}})
        return jsonify({
            'code': 200,
            'msg': '',
            'data': {}
        })


@app.route('/api/upload', methods=['GET', 'POST', 'DELETE'])
def upload():
    if request.method == 'GET':
        _id = request.args['_id']
        conn = pymongo.MongoClient(mongo)
        current_user = conn['paper']['user'].find_one({'_id': ObjectId(_id)})
        if int(current_user['role']) > 1:
            papers = conn['paper']['paper'].find()
        # elif int(current_user['role']) > 1:
        #     papers = conn['paper']['paper'].find({
        #         '$or': [
        #             {'status': {'$lt': 3}, 'u2': ''},
        #             {'status': {'$lt': 3}, 'u2': current_user['username']}
        #         ]
        #     })
        else:
            papers = conn['paper']['paper'].find({
                '$or': [
                    {'u1': ''},
                    {'u1': current_user['username']}
                ]
            })
        res = []
        for i in papers:
            i['_id'] = str(i['_id'])
            res.append(i)
        return jsonify({
            'code': 200,
            'msg': '',
            'data': res
        })
    elif request.method == 'POST':
        f = request.files.get('file')
        name = f.filename
        conn = pymongo.MongoClient(mongo)
        if conn['paper']['paper'].find_one({'title': name}):
            return jsonify({'code': 400, 'msg': name})
        s = f.read()
        content = s.decode('utf8').split('\n')
        result = []
        for i in content:
            t = i.split('\t')
            tmp = {
                'num': t[0],
                'text': "" if len(t) < 2 else t[1],
                'argument': "",
                'position': "",
                'type': []
            }
            result.append(tmp)
        conn['paper']['paper'].insert_one({
            'date': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            'title': name,
            'content': result,
            'status': 1,
            'u1': '',
            'u2': '',
            'name': os.path.splitext(name)[0]
        })
        return jsonify({'code': '200'})
    elif request.method == 'DELETE':
        conn = pymongo.MongoClient(mongo)
        conn['paper']['paper'].delete_one({'_id': ObjectId(request.args['_id'])})
        return jsonify({
            'code': 200,
            'msg': '',
            'data': {}
        })


if __name__ == '__main__':
    app.run()
