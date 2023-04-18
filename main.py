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


app.config['MONGO_URI'] = 'mongodb://localhost:27017/historycount'
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

def gen(camera):
    while True:
        frame,A = camera.get_frame()
        #print("a ",get_count())
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        
def geta(camera):
    while True:
        frame,A = camera.get_frame()
        return A


@app.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/history')
def history():
    
    # num = int(request.args.get('num', 5))
    session['graph'] = int(request.args.get('graph', 2023))
    month = int(request.args.get('month', -1))
    year = int(request.args.get('year', -1))
    if month == -1 and year == -1:
        cursor = collection.aggregate([{"$project":{"_id":1,"count":1,"Date":{"$dateToString":{"format":"%d/%m/%Y %H:%M:%S","date":"$Date"}}}},{"$sort":{"Date":-1}}])
    elif month != -1 and year == -1:
        cursor = collection.aggregate([{"$match": {"$expr": {"$eq": [{ "$month": "$Date" }, month]}}},{"$project":{"_id":1,"count":1,"Date":{"$dateToString":{"format":"%d/%m/%Y %H:%M:%S","date":"$Date"}}}}])
    elif month == -1 and year != -1:
        cursor = collection.aggregate([{"$match": {"$expr": {"$eq": [{ "$year": "$Date" }, year]}}},{"$project":{"_id":1,"count":1,"Date":{"$dateToString":{"format":"%d/%m/%Y %H:%M:%S","date":"$Date"}}}}])
    else:
        cursor = collection.aggregate([{"$match": {"$and":[ {"$expr": {"$eq": [{ "$year": "$Date" }, year]}} , {"$expr": {"$eq": [{ "$month": "$Date" }, month]}}]}  },{"$project":{"_id":1,"count":1,"Date":{"$dateToString":{"format":"%d/%m/%Y %H:%M:%S","date":"$Date"}}}}])
    
    data = []
    for doc in cursor:
        data.append({
            'count': doc['count'],
            'Date': doc['Date'],
        })
    return render_template('history.html', data=data)

@app.route('/parse')
def parse():
    graph = session.get('graph', 2023)
    print(graph)
    month = [0,"January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    datasplit = collection.aggregate([{"$match": {"$expr": {"$eq": [{ "$year": "$Date" }, graph]}}},{"$group" : {"_id": {"year":{"$year":"$Date"},"month":{"$month":"$Date"}},"average": { "$avg": "$count" }}},{"$sort":{"_id":1}}])
    datasplitarray = []
    for doc in datasplit:
        datasplitarray.append({
            '_id': month[doc["_id"]["month"]]+" "+str(doc["_id"]["year"]),
            'average': doc['average'],
        })
    return jsonify(datasplitarray)


if __name__ == '__main__':
    app.run(port=5000, debug=False)

#-----------------------------