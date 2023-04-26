from flask import Flask, render_template, Response, request, jsonify, session
from camera import VideoCamera
from server import create_count
from pymongo import MongoClient
from flask_pymongo import PyMongo


app = Flask(__name__)
#-----------------------

client = MongoClient('mongodb+srv://fishdb:fishdb@cluster0.6jeeb1j.mongodb.net/?retryWrites=true&w=majority')
db = client['historycount']
collection = db['count']
app.config['MONGO_URI'] = 'mongodb+srv://fishdb:fishdb@cluster0.6jeeb1j.mongodb.net/?retryWrites=true&w=majority/historycount'
mongo = PyMongo(app)

app.config['SECRET_KEY'] = 'some random string'

#-----------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/', methods=['POST'])
def button():
    create_count(geta(VideoCamera()))
    return render_template('index.html')

def geta(camera):
    while True:
        frame,A = camera.get_frame()
        return A

def gen(camera):
    while True:
        frame,A = camera.get_frame()
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        
@app.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/history')
def history():
    
    session['yearDayChart'] = int(request.args.get('yearDayChart', 2023))
    session['monthDayChart'] = int(request.args.get('monthDayChart', 4))
    session['dayDayChart'] = int(request.args.get('dayDayChart', 20))
    session['yearMonthChart'] = int(request.args.get('yearMonthChart', 2023))
    day = int(request.args.get('day', 20))
    month = int(request.args.get('month', 4))
    year = int(request.args.get('year', 2023))
    if day == -1 and month == -1 and year == -1:
        cursor = collection.aggregate([
            {"$project":{"_id":1,"count":1,"Date":{"$dateToString":{"format":"%d/%m/%Y %H:%M:%S","date":"$Date"}}}}
            ,{"$sort":{"Date":-1}}])
    elif day == -1 and month != -1 and year == -1:
        cursor = collection.aggregate([
            {"$match": {"$expr": {"$eq": [{ "$month": "$Date" }, month]}}}
            ,{"$project":{"_id":1,"count":1,"Date":{"$dateToString":{"format":"%d/%m/%Y %H:%M:%S","date":"$Date"}}}}])
    elif day == -1 and month == -1 and year != -1:
        cursor = collection.aggregate([
            {"$match": {"$expr": {"$eq": [{ "$year": "$Date" }, year]}}}
            ,{"$project":{"_id":1,"count":1,"Date":{"$dateToString":{"format":"%d/%m/%Y %H:%M:%S","date":"$Date"}}}}])
    elif day == -1 and month != -1 and year != -1:
        cursor = collection.aggregate([
            {"$match": {"$and":[ {"$expr": {"$eq": [{ "$year": "$Date" }, year]}}
                                ,{"$expr": {"$eq": [{ "$month": "$Date"}, month]}}]}}
            ,{"$project":{"_id":1,"count":1,"Date":{"$dateToString":{"format":"%d/%m/%Y %H:%M:%S","date":"$Date"}}}}])
    elif day != -1 and month == -1 and year == -1:
        cursor = collection.aggregate([
            {"$match": {"$expr": {"$eq": [{ "$dayOfMonth": "$Date" }, day]}}}
            ,{"$project":{"_id":1,"count":1,"Date":{"$dateToString":{"format":"%d/%m/%Y %H:%M:%S","date":"$Date"}}}}])
    elif day != -1 and month == -1 and year != -1:
        cursor = collection.aggregate([
            {"$match": {"$and":[ {"$expr": {"$eq": [{ "$year": "$Date" }, year]}} 
                                , {"$expr": {"$eq": [{ "$dayOfMonth": "$Date"}, day]}}]}}
            ,{"$project":{"_id":1,"count":1,"Date":{"$dateToString":{"format":"%d/%m/%Y %H:%M:%S","date":"$Date"}}}}])
    elif day != -1 and month != -1 and year == -1:
        cursor = collection.aggregate([
            {"$match": {"$and":[ {"$expr": {"$eq": [{ "$month": "$Date" }, month]}} 
                                        , {"$expr": {"$eq": [{ "$dayOfMonth": "$Date"}, day]}}]}}
            ,{"$project":{"_id":1,"count":1,"Date":{"$dateToString":{"format":"%d/%m/%Y %H:%M:%S","date":"$Date"}}}}])
    else:
        cursor = collection.aggregate([
            {"$match": {"$and":[ {"$expr": {"$eq": [{ "$year": "$Date" }, year]}}
                                ,{"$expr": {"$eq": [{ "$month": "$Date"}, month]}}
                                ,{"$expr": {"$eq": [{ "$dayOfMonth": "$Date" }, day]}}]}}
            ,{"$project":{"_id":1,"count":1,"Date":{"$dateToString":{"format":"%d/%m/%Y %H:%M:%S","date":"$Date"}}}}])

    data = []
    for doc in cursor:
        data.append({
            'count': doc['count'],
            'Date': doc['Date'],
        })
    return render_template('history.html', data=data)

@app.route('/parseDay')
def parseDay():
    selectyear = session.get('yearDayChart', 2023)
    selectmonth = session.get('monthDayChart', 4)
    selectday = session.get('dayDayChart', 20)
    datasplit3 = collection.aggregate([
        {"$match": {"$and":[ {"$expr": {"$eq": [{ "$year": "$Date" }, selectyear]}} 
                            , {"$expr": {"$eq": [{ "$month": "$Date" }, selectmonth]}}
                            , {"$expr": {"$eq": [{ "$dayOfMonth": "$Date" }, selectday]}} ]}  }
        ,{"$project":{"_id":1,"count":1,"Date":{"$dateToString":{"format":"%d/%m/%Y %H:%M:%S","date":"$Date"}}}}])
    datasplitarray3 = []
    for doc in datasplit3:
        datasplitarray3.append({
            'count': doc["count"],
            'Date': doc['Date'],
        })
    return jsonify(datasplitarray3)


@app.route('/parseMonth')
def parseMonth():
    selectyear = session.get('yearMonthChart', 2023)
    print(selectyear)
    month = [0,"January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    datasplit = collection.aggregate([
        {"$match": {"$expr": {"$eq": [{ "$year": "$Date" }, selectyear]}}}
        ,{"$group" : {"_id": {"year":{"$year":"$Date"},"month":{"$month":"$Date"}},"average": { "$avg": "$count" }}}
        ,{"$sort":{"_id":1}}])
    datasplitarray = []
    for doc in datasplit:
        datasplitarray.append({
            '_id': month[doc["_id"]["month"]]+" "+str(doc["_id"]["year"]),
            'average': doc['average'],
        })
    return jsonify(datasplitarray)


@app.route('/parseYear')
def parseYear():

    datasplit2 = collection.aggregate([{"$group" : {"_id": {"$year":"$Date"},"average": { "$avg": "$count" }}}
                                       ,{"$sort":{"_id":1}}])
    datasplitarray2 = []
    for doc in datasplit2:
        datasplitarray2.append({
            '_id': doc["_id"],
            'average': doc['average'],
        })
    return jsonify(datasplitarray2)

if __name__ == '__main__':
    app.run(port=5000, debug=False)

#-----------------------------