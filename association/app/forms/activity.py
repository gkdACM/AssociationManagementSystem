from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Optional

class ActivityForm(FlaskForm):
    name = StringField(validators=[DataRequired()])
    description = TextAreaField(validators=[Optional()])
    department_id = SelectField(coerce=int, validators=[Optional()])
    event_date = DateField(validators=[DataRequired()])
