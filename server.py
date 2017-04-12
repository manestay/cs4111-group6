import os
from forms import LoginForm, RegistrationForm, SearchForm
from flask import Flask, request, render_template, g, redirect, Response, flash, url_for
from sqlalchemy import *

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__,template_folder=tmpl_dir)
app.secret_key = "i love db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://bl2557:sealion6@104.196.135.151/proj1part2'
engine = create_engine('postgresql://bl2557:sealion6@104.196.135.151/proj1part2')
cache = {} # store logged in user credentials

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

@app.route('/login', methods=['GET', 'POST'])
def login():
  global cache
  if 'email' in cache:
    flash('You are already logged in.')
    return redirect(url_for('index'))

  form = LoginForm(request.form)
    
  if request.method == 'POST' and form.validate():
    email = form.email.data
    
    u_query = g.conn.execute("SELECT * FROM users_belong_to U "
                           "WHERE U.email = '{}'".format(email))
    u = u_query.first()
    '''s_query = g.conn.execute("SELECT S.sname, S.sid "
                           "FROM schools S, users_belong_to U "
                           "WHERE U.sid = S.sid AND "
                           "U.uid='{}'".format(u[0]))
    s = s_query.first()'''
                           
    cache.update({'uid': u[0], 'name': u[1], 'year': u[2], 'sid': u[3],
                  'email': u[4]}) #'school': s[0]})
    flash('you have successfully logged in')
    return redirect(url_for('index'))
  return render_template('login.html', form=form)
        

@app.route('/logout')
def logout():
  global cache
  if 'email' in cache:
    flash('You have logged out.')
    removed_keys = ('uid', 'year', 'sid', 'email', 'school')
    for k in removed_keys: cache.pop(k, None)
  else:
    flash('Not logged in yet.')
  return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
  global cache
  if 'email' in cache:
    flash('You are already logged in. Please log out before registering another account.')
    return redirect(url_for('index'))

  form = RegistrationForm(request.form)
  res = g.conn.execute("SELECT S.sid, S.sname FROM schools S")
  form.school_id.choices = [(s[0],s[1]) for s in res]
  if request.method == 'POST' and form.validate():
    email = form.email.data
    user_id = form.user_id.data
    name = form.name.data
    year = form.year.data
    password = form.password.data
    school_id = form.school_id.data
    
    u_query = g.conn.execute("INSERT INTO users_belong_to "
        "VALUES ('{}','{}','{}','{}','{}','{}')".format(
        user_id, name, year, school_id, email, password))
                           
    cache.update({'uid':user_id, 'name':name, 'year': year,
                  'sid': school_id, 'email': email})
    flash('you have succesfully registered, and are logged in')
    return redirect(url_for('/'))
  return render_template('registration.html', form=form)


@app.route('/search', methods=['GET', 'POST'])
def search():
  form = SearchForm()
  res = g.conn.execute("SELECT S.sid, S.sname FROM schools S")
  res1 = g.conn.execute("SELECT C.cname FROM categories C")
  form.school_id.choices = [('','any school')] + [(s[0],s[1]) for s in res]
  form.category.choices = [('','all categories')] + [(s[0],s[0]) for s in res1]
  return render_template('search.html', form=form)
  
    
  if request.method == 'POST' and form.validate():
    pass
  

@app.route('/')
def index():
  cursor = g.conn.execute("SELECT * FROM users_belong_to")
  users = []
  ''''for result in cursor:
    users.append(result)  # can also be accessed using result[0]
  cursor.close()'''
  
  context = dict(data = users)
  
  return render_template("index.html", cache=cache, **context)

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
