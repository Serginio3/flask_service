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
currency_code = {'EUR': '978',
                 'USD': '840',
                 'RUB': '643'}
shop_id = Config.SHOP_ID
payway = Config.PAYWAY


@app.route('/', methods=['GET', 'POST'])
def index():
    depending_of_endpoint_on_currency = {'978': '/pay',
                                         '840': '/bill',
                                         '643': '/invoice'}
    form = Service()
    if form.validate_on_submit():
        amount = request.form['sum_of_payment']
        amount = str(f"{float(amount):.{2}f}")
        currency = currency_code[request.form['currency']]
        shop_order_id = db_add_order(amount=amount, currency=currency,
                                     description=request.form['product_description'])
        session['data'] = dict(amount=amount, currency=currency,
                               description=request.form['product_description'], shop_order_id=shop_order_id)
        endpoint = depending_of_endpoint_on_currency[currency]
        return redirect(endpoint)
    logging.error(str(form.errors))
    return render_template('index.html', title='Оплата', form=form)


@app.route('/pay', methods=['POST', 'GET'])
def pay():
    keys_required = ['amount', 'currency', 'shop_id', 'shop_order_id']
    required_values = dict(amount=session['data']['amount'], currency=session['data']['currency'], shop_id=shop_id,
                           shop_order_id=session['data']['shop_order_id'], description=session['data']['description'])
    required_values_with_sign = make_sign(required_values, keys_required)
    return render_template('pay_form.html', data=required_values_with_sign)


@app.route('/bill', methods=['POST', 'GET'])
def bill():
    keys_required = ['shop_amount', 'shop_currency', 'shop_id', 'shop_order_id', 'payer_currency']
    required_values = dict(shop_amount=session['data']['amount'], payer_currency=session['data']['currency'],
                           shop_currency=session['data']['currency'], shop_id=shop_id,
                           shop_order_id=session['data']['shop_order_id'], description=session['data']['description'])
    required_values_with_sign = make_sign(required_values, keys_required)
    url = 'https://core.piastrix.com/bill/create'
    response = requests.post(url, json=required_values_with_sign)
    if response.json()['error_code'] == 0:
        return redirect(response.json()['data']['url'])
    else:
        logging.error(str(response.json()['message']))
        return redirect('/')


@app.route('/invoice', methods=['POST', 'GET'])
def invoice():
    keys_required = ['amount', 'currency', 'payway', 'shop_id',
                     'shop_order_id']
    required_values = dict(amount=session['data']['amount'], currency=session['data']['currency'], payway=payway,
                           shop_id=shop_id, shop_order_id=session['data']['shop_order_id'],
                           description=session['data']['description'])
    required_values_with_sign = make_sign(required_values, keys_required)
    url = 'https://core.piastrix.com/invoice/create'
    response = requests.post(url, json=required_values_with_sign)
    if response.json()['error_code'] == 0:
        return render_template('invoice_form.html', data=response.json()['data'])
    else:
        logging.error(str(response.json()['message']))
        return redirect('/')


def db_add_order(amount, currency, description):
    """add order to database"""
    new_payment = Payment(description=description, amount=amount, currency=currency)
    db.session.add(new_payment)
    db.session.commit()
    shop_order_id = Payment.query.all()[-1].id
    return shop_order_id


def make_sign(required_values, keys_required_tuple):
    """make sign and return required values with sign (dict)"""
    keys_sorted = sorted(list(keys_required_tuple))
    HEX = ':'.join([str(required_values[elem]) for elem in keys_sorted]) + secret
    sign = sha256(HEX.encode()).hexdigest()
    dict_of_request_with_sign = required_values.copy()
    dict_of_request_with_sign['sign'] = sign
    return dict_of_request_with_sign
