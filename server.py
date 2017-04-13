import os
from forms import *
from flask import Flask, request, session, render_template, g, redirect, Response, flash, url_for
from sqlalchemy import *

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__,template_folder=tmpl_dir)
app.secret_key = "i love db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://bl2557:sealion6@104.196.135.151/proj1part2'
engine = create_engine('postgresql://bl2557:sealion6@104.196.135.151/proj1part2')
#session = {} # store logged in user credentials

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
  global session
  if 'email' in session:
    flash('You are already logged in.')
    return redirect(url_for('index'))

  form = LoginForm(request.form)
    
  if request.method == 'POST' and form.validate():
    email = form.email.data
    
    u_query = g.conn.execute("SELECT * FROM users_belong_to U "
                           "WHERE U.email = '{}'".format(email))
    u = u_query.first()
    s_query = g.conn.execute("SELECT S.sname, S.sid "
                           "FROM schools S, users_belong_to U "
                           "WHERE U.sid = S.sid AND "
                           "U.uid='{}'".format(u[0]))
    s = s_query.first()
                           
    session.update({'uid': u[0], 'name': u[1], 'year': u[2], 'sid': u[3].strip(),
                  'email': u[4], 'school': s[0], 'password': u[5]})
    flash('you have successfully logged in')
    return redirect(url_for('index'))
  return render_template('login.html', form=form)
        

@app.route('/logout')
def logout():
  global session
  if 'email' in session:
    flash('You have logged out.')
    removed_keys = ('uid', 'year', 'sid', 'email', 'school')
    for k in removed_keys: session.pop(k, None)
  else:
    flash('Not logged in yet.')
  return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
  global session
  if 'email' in session:
    flash('You are already logged in. Please log out before registering another account.')
    return redirect(url_for('index'))

  form = AccountForm(request.form)
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
                           
    session.update({'uid':user_id, 'name':name, 'year': year,
                  'sid': school_id, 'email': email, 'password': password})
    flash('you have succesfully registered, and are logged in')
    return redirect(url_for('/'))
  return render_template('registration.html', form=form)

@app.route('/establishment')
def establishment():
    eid = request.args.get('eid')
    ename = g.conn.execute("SELECT E.ename FROM Establishments E WHERE E.eid='{}'".format(eid)).first()[0]
    print ename
    l, f, p = [], [], []
    res = g.conn.execute("SELECT L.address, L.url FROM locations_situated_in L "
                         "JOIN establishments E USING (eid) WHERE (E.eid = '{}')".format(eid))
    for i in res: l.append(i[0])
    q = process_query(
        "SELECT original_price, student_price, ongoing, notes, sname "
        "FROM discounts_offered D JOIN fixed_val_discounts F USING (did) "
        "JOIN benefit_from B using(did) JOIN schools S using (sid) WHERE D.eid = '{}'".format(eid))
    q1 = process_query(
        "SELECT percent, ongoing, notes, sname "
        "FROM discounts_offered D JOIN percentage_discounts P USING (did) "
        "JOIN benefit_from B using(did) JOIN schools S using (sid) WHERE D.eid = '{}'".format(eid))
    res1 = g.conn.execute(q)
    res2 = g.conn.execute(q1)
    for i in res1: f.append("$" + str(i[0]) + "0 Off")
    for i in res2: p.append(str(i[0]) + "% Off")
    
    return render_template("establishment.html", locations=l, f_discounts=f,p_discounts=p, ename=ename)

@app.route('/list')
def list():
  cursor = g.conn.execute("SELECT eid, ename, cname FROM establishments E LEFT OUTER JOIN fall_under using (eid)")
  est = []
  for result in cursor:
    eid = result[0]
    q = process_query("SELECT * FROM discounts_offered D WHERE D.eid = '{}'".format(eid))
    discounts = g.conn.execute(q)
    available = discounts.rowcount
    est.append([result[0].strip(), result[1], result[2], available])
    
  cursor.close()
  return render_template('list.html',est=est)
  
@app.route('/search', methods=['GET', 'POST'])
def search():
  if 'sid' in session:
    form = SearchForm(request.form, school_id = session['sid'])
  else:
    form = SearchForm(request.form)
  res = g.conn.execute("SELECT S.sid, S.sname FROM schools S")
  res1 = g.conn.execute("SELECT C.cname FROM categories C")
  form.school_id.choices = [('','any school')] + [(s[0].strip(),s[1]) for s in res]
  form.category.choices = [('','all categories')] + [(s[0],s[0]) for s in res1]
  if request.method == 'POST' and form.validate():
    return redirect(url_for('results',sid = form.school_id.data.strip(), cid = form.category.data.strip(), free=form.check.data))
  return render_template('search.html', form=form)

@app.route('/results')
def results():
    sid = request.args.get('sid') 
    cid = request.args.get('cid') 
    free = request.args.get('free')
    r,r1,e1,e2 = [], [], [], []
    query = "SELECT DISTINCT * FROM Establishments E2 NATURAL JOIN Discounts_Offered D  NATURAL JOIN benefit_from B NATURAL JOIN Schools S"
    if (sid):
      sid = "'" + sid + "'"
    if (cid):
      query += " NATURAL JOIN categories C NATURAL JOIN fall_under F"
      cid = "'" + cid + "'"
    query += " NATURAL JOIN fixed_val_discounts FV WHERE"
    
    if(free):
      query += " FV.free = 't'"
    if(sid):
      if query[-5:] != 'WHERE': query += ' AND'
      query += " S.sid=" + sid
    if(cid):
      if query[-5:] != 'WHERE': query += ' AND'
      query += " C.cname=" + cid
    if query[-5:] == 'WHERE': query = query.replace('WHERE', '')
    
    if free !='True':
        query1 = "SELECT DISTINCT * FROM Establishments E2 NATURAL JOIN Discounts_Offered D NATURAL JOIN benefit_from B NATURAL JOIN Schools S"
        if (cid):
          query1 += " NATURAL JOIN categories C NATURAL JOIN fall_under F"
        query1 += " NATURAL JOIN percentage_discounts P WHERE"
        
        if(sid):
          if query1[-5:] != 'WHERE': query1 += ' AND'
          query1 += " S.sid=" + sid
        if(cid):
          if query1[-5:] != 'WHERE': query1 += ' AND'
          query1 += " C.cname=" + cid
        if query1[-5:] == 'WHERE': query1 = query1.replace('WHERE', '')
        per = g.conn.execute(query1)
        for i in per: 
          r1.append("{} {}% Off, Notes: {}, for {}".format(i['ename'], i['percent'], i['notes'] or 'None', i['sname']))
    fv = g.conn.execute(query)
    # for row in ename:
    #   print row
    
    for i in fv: 
      if i['student_price']==0:
        student = 'free'
      else:
        student = '${}'.format(i['student_price'])
      r.append("{} Student Price: {}, Notes: {}, for {}".format(i['ename'], student, i['notes'] or 'None', i['sname']))
    return render_template("results.html", fval = r, pval = r1)


@app.route('/account', methods=['GET', 'POST'])
def account():
  if not 'email' in session:
    flash('You must be logged in to manage your account.')
    return redirect(url_for('index'))
    
  form = UpdateAccountForm(request.form, school_id = session['sid'], year= session['year'])
  res = g.conn.execute("SELECT S.sid, S.sname FROM schools S")
  form.school_id.choices = [(s[0].strip(),s[1]) for s in res]
  
  if request.method == 'POST' and form.validate():
    print form.year.data
    email = form.email.data or session['email']
    name = form.name.data or session['name']
    year = form.year.data
    password = form.new_password.data or session['password']
    school_id = form.school_id.data
    
    for pair in form.school_id.choices:
      if pair[0] == school_id: session['school'] = pair[1]
    g.conn.execute("UPDATE users_belong_to SET (uname, email, year, sid, password) = "
        "('{}','{}','{}','{}','{}') WHERE uid='{}'".format(name, email, year, school_id, password,session['uid']))
    session.update({'name':name, 'year': year,
                  'sid': school_id, 'email': email, 'password':password})
    flash('successfully updated account information')
    return redirect(url_for('account'))
  return render_template('account.html', session=session, form=form)

@app.route('/')
def index():
  cursor = g.conn.execute("SELECT * FROM users_belong_to")
  
  return render_template("index.html", session=session)

def process_query(string): # for logged in users, restrict to only their schools
    if not 'email' in session: return string
    s = string.replace('WHERE ', "WHERE B.sid = '{}' AND ".format(session['sid']))
    if 'join schools s' not in s.lower():
        s = s.replace(' WHERE', " JOIN benefit_from B using(did) JOIN schools S using (sid) WHERE")
    return s
    
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
