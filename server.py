import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__,template_folder=tmpl_dir)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://bl2557:sealion6@104.196.135.151/proj1part2'
db = SQLAlchemy(app)
engine = create_engine('postgresql://bl2557:sealion6@104.196.135.151/proj1part2')

engine.execute("""SELECT * FROM Establishments""")

@app.before_request
def before_request():

  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):

  try:
    g.conn.close()
  except Exception as e:
    pass


@app.route('/')
def index():
  print request.args
