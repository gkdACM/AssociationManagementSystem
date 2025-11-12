from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional

class ProfileChangeForm(FlaskForm):
    name = StringField(validators=[Optional(), Length(max=64)])
    class_name = StringField(validators=[Optional(), Length(max=64)])
    gender = SelectField(choices=[('男','男'),('女','女'),('其他','其他')], validators=[Optional()])
    grade = StringField(validators=[Optional(), Length(max=16)])
    phone = StringField(validators=[Optional(), Length(max=32)])
    email = StringField(validators=[Optional(), Email(), Length(max=128)])
