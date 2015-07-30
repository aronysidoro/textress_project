import random
import os
import time
import datetime

from django.db import models
from django.conf import settings
from django.test import TestCase, LiveServerTestCase, RequestFactory
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group
from django.http import Http404
from django.utils import timezone

from model_mommy import mommy

from account.models import AcctStmt, TransType, AcctTrans, CHARGE_AMOUNTS, BALANCE_AMOUNTS, TRANS_TYPES
from main.models import Hotel
from main.tests.test_models import create_hotel
from payment.models import Customer
from utils import create


CREATE_ACCTCOST_DICT = {
    'init_amt': CHARGE_AMOUNTS[0][0],
    'balance_min': BALANCE_AMOUNTS[0][0],
    'recharge_amt': CHARGE_AMOUNTS[0][0]
    }


def _randint(a=10, b=100):
    return random.randint(a,b)


def make_trans_types():
    return [mommy.make(TransType, name=tt[0]) for tt in TRANS_TYPES]


def _acct_stmt(hotel, year, month):
    '''
    Monkey-patch save() so just generating test data and not based on actual 
    usage from Message records.
    '''
    global AcctStmt
    AcctStmt.save = models.Model.save
    return AcctStmt.objects.create(
        hotel=hotel,
        year=year,
        month=month,
        monthly_costs=_randint(),
        total_sms=_randint(),
        balance=_randint()
        )

def make_acct_stmts(hotel):
    return [_acct_stmt(hotel=hotel, year=2014, month=m)
            for m in range(1,13)]


def _acct_trans(hotel, trans_type, insert_date, amount=None):
    '''
    Monkey-patch save() for same reason as AcctStmt.
    
    'init_amt', 'recharge_amt' are 1000 Stripe Credits.

    'sms_used' are b/t -100 ... -10  (for testing purposes)
    '''
    global AcctTrans
    AcctTrans.save = models.Model.save

    # transaction
    if trans_type.name in ('init_amt', 'recharge_amt'):
        amount = _randint(1000, 1000)
    else:
        amount = _randint(-100, -10)

    return AcctTrans.objects.create(
        hotel=hotel,
        trans_type=trans_type,
        amount=amount,
        sms_used=_randint(),
        insert_date=insert_date
        )

def make_acct_trans(hotel):
    '''
    TransType: use get() b/c tests using `fixtures`.
    
    So, generate all transaction records until current date and test format.

    This factory method can be used to manually test AcctTransDetailView template
        w/ ./manage.py runserver

    '''
    # datetime
    td = datetime.timedelta(days=-30)
    next_day = datetime.timedelta(days=1)
    today = datetime.date.today()
    last_month = today + td

    # TransType
    init_amt, _ = TransType.objects.get_or_create(name='init_amt')
    recharge_amt, _ = TransType.objects.get_or_create(name='recharge_amt')
    sms_used, _ = TransType.objects.get_or_create(name='sms_used')

    # set the Hotel as Created 1 month ago
    hotel.created = last_month
    hotel.save()

    # Create `init_amt`
    _acct_trans(hotel=hotel, trans_type=init_amt, insert_date=hotel.created)

    # Daily usage until `today` (start populating based on `last_month` date)
    insert_date = hotel.created
    balance = AcctTrans.objects.filter(hotel=hotel).balance()

    # Loop thro and create. Recharge Account if Balancd < 0
    while insert_date < today:
        trans = _acct_trans(hotel=hotel, trans_type=sms_used, insert_date=insert_date)
        balance = AcctTrans.objects.filter(hotel=hotel).balance()
        if balance < 0:
            trans = _acct_trans(hotel=hotel, trans_type=recharge_amt, insert_date=insert_date)
        insert_date += next_day

    return AcctTrans.objects.all()