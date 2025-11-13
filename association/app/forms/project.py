from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, URLField
from wtforms.validators import DataRequired, Optional, URL

class ProjectForm(FlaskForm):
    name = StringField(validators=[DataRequired()])
    description = TextAreaField(validators=[Optional()])
    department_id = SelectField(coerce=int, validators=[Optional()])
    github_url = URLField(validators=[Optional(), URL(require_tld=False)])
    start_date = DateField(validators=[Optional()])
    end_date = DateField(validators=[Optional()])

class ParticipationDecisionForm(FlaskForm):
    remark = StringField(validators=[Optional()])

