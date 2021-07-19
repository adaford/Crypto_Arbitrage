import flask
import waitress
app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/')
def home():
    with open('/home/ec2-user/script/flaskproject/output_webpage.log') as f:
        response = flask.jsonify(f.read())
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

waitress.serve(app, host='0.0.0.0', port=80)