from flask_wtf import FlaskForm
from wtforms import StringField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, Email

# 실제로 사용자가 입력할건 이름, 메일뿐임
class ReservationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    date = DateTimeField('Date', format='%Y-%m-%d %H:%M:%s', validators=[
        DataRequired()])
    submit = SubmitField('Reservation')
