from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, DecimalField, FileField
from wtforms.validators import DataRequired, Optional

class CompetitionForm(FlaskForm):
    name = StringField(validators=[DataRequired()])
    description = TextAreaField(validators=[Optional()])
    category = SelectField(choices=[('internal','内部赛'),('external','外部赛')], validators=[DataRequired()])
    level = SelectField(choices=[('国际级','国际级'),('国家级','国家级'),('区域级','区域级'),('省级','省级'),('市级','市级'),('校级','校级'),('联合赛','联合赛'),('企业赛','企业赛'),('邀请赛','邀请赛')], validators=[DataRequired()])
    department_id = SelectField(coerce=int, validators=[Optional()])
    event_date = DateField(validators=[DataRequired()])

class CompetitionResultForm(FlaskForm):
    student_id = StringField(validators=[DataRequired()])
    score = DecimalField(places=2, rounding=None, validators=[Optional()])
    award = StringField(validators=[Optional()])
    remark = StringField(validators=[Optional()])

class CompetitionImportForm(FlaskForm):
    file = FileField(validators=[DataRequired()])

