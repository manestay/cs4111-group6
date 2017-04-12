from wtforms import Form, RadioField, StringField, PasswordField, SelectField, \
                    BooleanField, validators
from wtforms.fields.html5 import IntegerRangeField

schools = [('1','Columbia'),('2','NYU'), ('3','Fordham'),
      ('4','Hunter'), ('5','Brooklyn'), ('6','Baruch'), ('7','Pace'), (8,'Queens'),
      (9,'Juilliard'), (10,'Parsons')]
years = [('UG1', 'Freshman'), ('UG2', 'Sophomore'), ('UG3', 'Junior'),
      ('UG4','Senior'), ('G', 'Graduate'), ('PROF', 'Professor')]
    
class LoginForm(Form):
  email = StringField('Email Address', [validators.DataRequired(), validators.Email()])
  password = PasswordField('Password', [validators.DataRequired()])
  
  def validate(self):
    from server import engine
    conn = engine.connect()
    if not super(LoginForm, self).validate():
      return False
    res = conn.execute("SELECT U.email FROM users_belong_to U WHERE U.email = '{}' AND U.password"
                       "='{}'".format(self.email.data, self.password.data))
    if res.rowcount == 0: # given email and password not in database
      self.email.errors.append('email and/or password not found')
      conn.close()
      return False
    conn.close()
    return True

class AccountForm(Form):
  email = StringField('Email Address', [validators.Length(max=30)])
  name = StringField('Name', [validators.Length(max=25)])
  school_id = SelectField('School')
  year = RadioField('Year', choices=years)
  user_id = StringField('User ID', [validators.Length(min=1, max=10)])
  password = PasswordField('Password (plaintext, not secure)', [
      validators.DataRequired(),
      validators.EqualTo('confirm', message='Passwords must match')
  ])
  confirm = PasswordField('Repeat Password')
  
  def validate(self):
    from server import engine
    conn = engine.connect()
    if not super(AccountForm, self).validate():
        return False
    res = conn.execute("SELECT U.email FROM users_belong_to U WHERE U.email = '{}'".format(self.email.data))
    if res.rowcount == 1:
        self.email.errors.append('email already exists')          
        conn.close()
        return False

    res1 = conn.execute("SELECT U.uid FROM users_belong_to U WHERE U.uid = '{}'".format(self.user_id.data))
    if res1.rowcount == 1:
        self.user_id.errors.append('user id taken')
        conn.close()
        return False
    conn.close()
    return True


class UpdateAccountForm(Form): #like previous, but data not required
  email = StringField('Email Address')
  name = StringField('Name')
  school_id = SelectField('School')
  year = SelectField('Year', choices=years)
  user_id = StringField('User ID')
  password = PasswordField('Password (plaintext, not secure)', [
      validators.EqualTo('confirm', message='Passwords must match')
  ])
  confirm = PasswordField('Repeat Password')
  
  new_password = PasswordField('Password (plaintext, not secure)', [
      validators.EqualTo('new_confirm', message='Passwords must match')
  ])
  new_confirm = PasswordField('Repeat Password')
  
  def validate(self):
    from server import engine
    conn = engine.connect()
    if not super(UpdateAccountForm, self).validate():
        return False
    res = conn.execute("SELECT U.email FROM users_belong_to U WHERE U.email = '{}'".format(self.email.data))
    if res.rowcount == 1:
        self.email.errors.append('email already exists')          
        conn.close()
        return False

    res1 = conn.execute("SELECT U.uid FROM users_belong_to U WHERE U.uid = '{}'".format(self.user_id.data))
    if res1.rowcount == 1:
        self.user_id.errors.append('user id taken')
        conn.close()
        return False
    conn.close()
    return True


class SearchForm(Form): #for advanced search
  school_id = SelectField('School')
  category = SelectField('Category')
  show = BooleanField('Also show establishments without active discounts')
  check = BooleanField('Free discounts only')
  def validate(self):
    from server import engine
    conn = engine.connect()
    if not super(SearchForm, self).validate():
      return False
    res = conn.execute("SELECT U.email FROM users_belong_to U WHERE U.email = '{}' AND U.password"
                       "='{}'".format(self.email.data, self.password.data))
    if res.rowcount == 0: # given email and password not in database
      self.email.errors.append('email and/or password not found')
      conn.close()
      return False
    conn.close()
    return True
    

