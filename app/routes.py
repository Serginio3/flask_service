# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, request, session
import requests
from app import app, db
from app.forms import Service
from app.models import Payment
from hashlib import sha256
from config import Config
import json
import logging

logging.basicConfig(filename="sample.log", level=logging.INFO)
secret = Config.SECRET_KEY
currency_dict = {'EUR': '978',
                 'USD': '840',
                 'RUB': '643'}
shop_id = Config.SHOP_ID
payway = Config.PAYWAY


@app.route('/', methods=['GET', 'POST'])
def index():
    form = Service()
    if form.validate_on_submit():
        amount = request.form['sum_of_payment']
        amount = str(f"{float(amount):.{2}f}")
        description = request.form['product_description']
        currency = request.form['currency']
        new_payment = Payment(description=description, amount=amount, currency=currency)
        db.session.add(new_payment)
        db.session.commit()
        shop_order_id = Payment.query.all()[-1].id
        if currency == 'EUR':
            currency = currency_dict[currency]
            session['data'] = dict(amount=amount, currency=currency,
                                   shop_id=shop_id, shop_order_id=shop_order_id)
            keys_required = ['amount', 'currency', 'shop_id', 'shop_order_id']
            sign = make_sign(session['data'], keys_required)
            session['data']['sign'] = sign
            session['data']['description'] = description
            return redirect('/pay')
        elif currency == 'USD':
            currency = currency_dict[currency]
            session['data'] = dict(shop_amount=amount, payer_currency=currency, shop_currency=currency,
                                   shop_id=shop_id, shop_order_id=shop_order_id)
            keys_required = ['shop_amount', 'shop_currency', 'shop_id', 'shop_order_id', 'payer_currency']
            sign = make_sign(session['data'], keys_required)
            session['data']['sign'] = sign
            session['data']['description'] = description
            return redirect('/bill')
        elif currency == 'RUB':
            currency = currency_dict[currency]
            session['data'] = dict(amount=amount, currency=currency, payway=payway,
                                   shop_id=shop_id, shop_order_id=shop_order_id)
            keys_required = ['amount', 'currency', 'payway', 'shop_id',
                             'shop_order_id']
            sign = make_sign(session['data'], keys_required)
            session['data']['sign'] = sign
            session['data']['description'] = description
            return redirect('/invoice')
    logging.error(str(form.errors))
    return render_template('index.html', title='Оплата', form=form)


@app.route('/pay', methods=['POST', 'GET'])
def pay():
    return render_template('pay_form.html', data=session.get('data'))


@app.route('/bill', methods=['POST', 'GET'])
def bill():
    url = 'https://core.piastrix.com/bill/create'
    response = requests.post(url, json=session['data'])
    if response.json()['error_code']==0:
        return redirect(response.json()['data']['url'])
    else:
        logging.error(str(response.json()['message']))
        return redirect('/')

@app.route('/invoice', methods=['POST', 'GET'])
def invoice():
    url = 'https://core.piastrix.com/invoice/create'
    response = requests.post(url, json=session['data'])
    if response.json()['error_code']==0:
        return render_template('invoice_form.html', data=response.json()['data'])
    else:
        logging.error(str(response.json()['message']))
        return redirect('/')


def make_sign(dict_of_request, keys_required_tuple):
    keys_sorted = sorted(list(keys_required_tuple))
    HEX = ':'.join([str(dict_of_request[elem]) for elem in keys_sorted]) + secret
    sign = sha256(HEX.encode()).hexdigest()
    return sign
