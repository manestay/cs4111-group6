from wtforms import Form, BooleanField, StringField, PasswordField, validators

class LoginForm(Form):
    email = StringField('Email Address', [validators.DataRequired(), validators.Email()])
    password = PasswordField('Password', [validators.DataRequired()])
    
    def validate(self):
        from server import engine
        conn = engine.connect()
        if not super(LoginForm, self).validate():
            return False
        res = conn.execute("SELECT U.email FROM users_belong_to U "
                           "WHERE U.email = '{}' AND U.password="
                           "'{}'".format(self.email.data, self.password.data))
        if res.rowcount == 0: # given email and password not in database
            self.email.errors.append('email and/or password not found')
            return False
                          
        return True
