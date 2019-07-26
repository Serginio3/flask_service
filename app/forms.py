from flask_wtf import FlaskForm
from wtforms import DecimalField, TextAreaField, SubmitField, SelectField, TextField
from wtforms.validators import DataRequired


class Service(FlaskForm):
    sum_of_payment = DecimalField('Сумма оплаты', validators=[DataRequired()])
    product_description = TextAreaField('Описание товара')
    currency = SelectField('Валюта', choices=[('EUR','EUR'), ('USD', 'USD'), ('RUB','RUB')])
    submit = SubmitField('Оплатить')
