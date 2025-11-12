from flask_wtf import FlaskForm
from wtforms import SelectField
from wtforms.validators import DataRequired

class DepartmentChangeForm(FlaskForm):
    target_department_id = SelectField(coerce=int, validators=[DataRequired()])

