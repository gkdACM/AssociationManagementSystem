from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, DecimalField, FileField
from wtforms.validators import DataRequired, Optional

class ExamForm(FlaskForm):
    title = StringField(validators=[DataRequired()])
    description = TextAreaField(validators=[Optional()])
    department_id = SelectField(coerce=int, validators=[Optional()])
    exam_date = DateField(validators=[DataRequired()])
    pass_threshold = DecimalField(places=2, rounding=None, validators=[Optional()])

class ExamResultForm(FlaskForm):
    student_id = StringField(validators=[DataRequired()])
    score = DecimalField(places=2, rounding=None, validators=[DataRequired()])
    remark = StringField(validators=[Optional()])

class ExamImportForm(FlaskForm):
    file = FileField(validators=[DataRequired()])

