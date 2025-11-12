from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional

class LoginForm(FlaskForm):
    student_id = StringField(validators=[DataRequired(), Length(max=32)])
    password = PasswordField(validators=[DataRequired(), Length(min=6, max=64)])

class RegisterForm(FlaskForm):
    name = StringField(validators=[DataRequired(), Length(max=64)])
    class_name = StringField(validators=[DataRequired(), Length(max=64)])
    student_id = StringField(validators=[DataRequired(), Length(max=32)])
    gender = SelectField(choices=[('男','男'),('女','女'),('其他','其他')], validators=[DataRequired()])
    grade = StringField(validators=[DataRequired(), Length(max=16)])
    phone = StringField(validators=[Optional(), Length(max=32)])
    email = StringField(validators=[Optional(), Email(), Length(max=128)])
    department_id = SelectField(coerce=int, validators=[Optional()])
    password = PasswordField(validators=[DataRequired(), Length(min=6, max=64)])

