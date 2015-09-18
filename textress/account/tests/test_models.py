import calendar
import datetime
import pytz

from django.db.models import Max, Sum
from django.test import TestCase
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group
from django.utils import timezone

from model_mommy import mommy

from account.models import (Dates, Pricing, TransType, AcctCost, AcctStmt, AcctTrans,
    CHARGE_AMOUNTS, BALANCE_AMOUNTS)
from account.tests.factory import create_acct_stmts, create_acct_trans
from concierge.tests.factory import make_guests, make_messages
from main.tests.factory import create_hotel, create_hotel_user, PASSWORD
from utils import create


class DatesTests(TestCase):

    def setUp(self):
        self.tzinfo = pytz.timezone(settings.TIME_ZONE)

    def test_tzinfo(self):
        dates = Dates()
        self.assertTrue(hasattr(dates, 'tzinfo'))

    def test_all_dates(self):
        dates = Dates()
        now = timezone.now()

        self.assertTrue(dates._now)
        self.assertEqual(dates._today, now.date())
        self.assertEqual(dates._year, now.year)
        self.assertEqual(dates._month, now.month)

    def test_first_of_month(self):
        dates = Dates()
        first_of_month = dates.first_of_month(month=1, year=1)
        self.assertEqual(
            first_of_month,
            datetime.datetime(day=1, month=1,year=1, tzinfo=self.tzinfo).date()
        )

    def test_first_of_month_defaul(self):
        dates = Dates()
        first_of_month = dates.first_of_month()
        self.assertEqual(
            first_of_month,
            datetime.datetime(day=1, month=dates._today.month,
                year=dates._today.year, tzinfo=self.tzinfo).date()
        )


class AbstractBaseTests(TestCase):

    def test_AbstractBase_properties(self):
        # auto fields work
        price = mommy.make(Pricing)
        self.assertIsInstance(price.created, datetime.datetime)
        self.assertIsInstance(price.modified, datetime.datetime)


class PricingTests(TestCase):
    # NOTE: Am skipping testing save() b/c these are static Pricing Tiers
    #   that are created once and hardly ever changed.

    fixtures = ['pricing.json']

    def test_fixtures(self):
        free_price = Pricing.objects.get(tier_name="Free")
        assert isinstance(free_price, Pricing)

    def test_get_cost(self):
        assert Pricing.objects.get_cost(units=200, units_prev=0) == 0

    def test_get_cost_two_tiers(self):
        units = 300
        tier = Pricing.objects.get(start__lte=units, end__gte=units)
        print((units - (tier.start-1)) * tier.price)
        print(Pricing.objects.get_cost(units=units, units_prev=0))
        assert (units - (tier.start-1)) * tier.price == Pricing.objects.get_cost(units=units, units_prev=0)

    def test_get_cost_three_tiers(self):
        units = 2300
        cost = 100*0.0525 + 2000*0.0550
        tier = Pricing.objects.get(start__lte=units, end__gte=units)
        print(cost)
        print(Pricing.objects.get_cost(units=units, units_prev=0))
        assert cost == Pricing.objects.get_cost(units=units, units_prev=0)


class TransTypeTests(TestCase):
    # Test contains all TransTypes
    # This Model is also static (like the `Pricing` Model) and does not change.

    fixtures = ['trans_type.json']

    def test_types(self):
        init_amt = TransType.objects.get(name='init_amt')
        recharge_amt = TransType.objects.get(name='recharge_amt')
        sms_used = TransType.objects.get(name='sms_used')
        phone_number = TransType.objects.get(name='phone_number')
        bulk_discount = TransType.objects.get(name='bulk_discount')

        self.assertIsInstance(init_amt, TransType)
        self.assertEqual(str(init_amt), init_amt.name)
        self.assertEqual(TransType.objects.count(), 5)


class AcctCostTests(TestCase):
    '''
    Hotel can only have 1 AcctCost record. Can be updated.
    '''

    def setUp(self):
        self.password = PASSWORD
        self.hotel = create_hotel()

        # "other_hotel" has no affect on this one
        self.hotel_2 = create_hotel()
        AcctCost.objects.get_or_create(hotel=self.hotel_2)

    def test_create(self):
        # Dave starts with the "Default Amounts" when creating his ``AcctCost``
        acct_cost, created = AcctCost.objects.get_or_create(hotel=self.hotel)
        self.assertTrue(created)
        self.assertIsInstance(acct_cost, AcctCost)
        self.assertEqual(acct_cost.init_amt, CHARGE_AMOUNTS[0][0])
        self.assertEqual(acct_cost.balance_min, BALANCE_AMOUNTS[0][0])
        self.assertEqual(acct_cost.recharge_amt, CHARGE_AMOUNTS[0][0])

        # create new actually modifies original b/c p/ Hotel, singleton obj
        new_acct_cost, created = AcctCost.objects.get_or_create(
            hotel=self.hotel,
            balance_min=BALANCE_AMOUNTS[2][0],
            recharge_amt=CHARGE_AMOUNTS[2][0]
            )
        self.assertFalse(created)
        self.assertEqual(acct_cost, new_acct_cost)
        self.assertEqual(AcctCost.objects.filter(hotel=self.hotel).count(), 1)
        self.assertEqual(new_acct_cost.balance_min, BALANCE_AMOUNTS[2][0])
        self.assertEqual(new_acct_cost.recharge_amt, CHARGE_AMOUNTS[2][0])

        # If a ``get_or_create`` is called w/ no kwargs, it returns the current
        # ``acct_cost`` as is
        acct_cost, created = AcctCost.objects.get_or_create(hotel=self.hotel)
        self.assertFalse(created)
        self.assertEqual(acct_cost, new_acct_cost)
        self.assertEqual(AcctCost.objects.filter(hotel=self.hotel).count(), 1)
        self.assertEqual(acct_cost.balance_min, BALANCE_AMOUNTS[2][0])
        self.assertEqual(acct_cost.recharge_amt, CHARGE_AMOUNTS[2][0])


class AcctStmtTests(TestCase):

    fixtures = ['pricing.json', 'trans_type.json']

    def setUp(self):
        self.password = PASSWORD
        self.today = timezone.now().date()
        create._get_groups_and_perms()
        self.hotel = create_hotel()
        self.admin = create_hotel_user(self.hotel, 'admin')
        
        # Guests (makes 10)
        self.guest = make_guests(hotel=self.hotel, number=1)[0] #b/c returns a list
        # Messages (makes 10)
        self.messages = make_messages(
            hotel=self.hotel,
            user=self.admin,
            guest=self.guest
            )

        # AcctStmt
        self.acct_stmts = create_acct_stmts(hotel=self.hotel)
        # Single AcctStmt
        self.acct_stmt = self.acct_stmts[0]
        # Supporting Models
        self.acct_cost = AcctCost.objects.get_or_create(hotel=self.hotel)
        self.acct_trans = create_acct_trans(hotel=self.hotel)

    ### MODEL TESTS

    def test_get_absolute_url(self):
        self.assertEqual(
            self.acct_stmt.get_absolute_url(),
            reverse('acct_stmt_detail', kwargs={'year':self.acct_stmt.year,
                'month':self.acct_stmt.month})
        )

    def test_str(self):
        self.assertEqual(
            str(self.acct_stmt),
            "{} {}".format(calendar.month_name[self.acct_stmt.month], self.acct_stmt.year)
        )

    def test_month_abbr(self):
        self.assertEqual(
            self.acct_stmt.month_abbr,
            "{} {}".format(calendar.month_abbr[self.acct_stmt.month], self.acct_stmt.year)
        )

    ### MANAGER TESTS

    def test_get_or_create_current_month(self):
        # Should already exist
        acct_stmt, created = AcctStmt.objects.get_or_create(
            hotel=self.hotel,
            month=self.today.month,
            year=self.today.year
            )
        self.assertIsInstance(acct_stmt, AcctStmt)
        self.assertTrue(created)

        acct_stmt, created = AcctStmt.objects.get_or_create(
            hotel=self.hotel,
            month=self.today.month,
            year=self.today.year
            )
        self.assertIsInstance(acct_stmt, AcctStmt)
        self.assertFalse(created)


class AcctStmtNewHotelTests(TestCase):
    # Test Hotels that have only signed up, and don't have 
    # any SMS sent yet

    fixtures = ['trans_type.json']

    def setUp(self):
        self.password = PASSWORD
        self.today = timezone.now().date()
        create._get_groups_and_perms()
        self.hotel = create_hotel()
        self.admin = create_hotel_user(self.hotel, 'admin')
        # Supporting Models
        self.acct_cost = AcctCost.objects.get_or_create(hotel=self.hotel)

    def test_sms_used_mtd(self):
        acct_stmt, created = AcctStmt.objects.get_or_create(hotel=self.hotel)
        self.assertIsInstance(acct_stmt,AcctStmt)
        self.assertEqual(AcctTrans.objects.sms_used_mtd(self.hotel, self.today), 0)


class AcctTransTests(TestCase):

    fixtures = ['pricing.json', 'trans_type.json']

    def setUp(self):
        self.password = PASSWORD
        self.today = timezone.now().date()
        self.yesterday = self.today - datetime.timedelta(days=1)

        # Hotel / Admin User
        create._get_groups_and_perms()
        self.hotel = create_hotel()
        self.admin = create_hotel_user(hotel=self.hotel, group='hotel_admin')

        # Guest
        self.guest = make_guests(hotel=self.hotel, number=1)[0] #b/c returns a list
        # Messages
        self.messages = make_messages(
            hotel=self.hotel,
            user=self.admin,
            guest=self.guest
            )

        # TransTypes
        self.init_amt = TransType.objects.get(name='init_amt')
        self.recharge_amt = TransType.objects.get(name='recharge_amt')
        self.sms_used = TransType.objects.get(name='sms_used')
        self.bulk_discount = TransType.objects.get(name='bulk_discount')
        self.phone_number = TransType.objects.get(name='phone_number')

        # AcctStmt
        self.acct_stmts = create_acct_stmts(hotel=self.hotel)
        self.acct_stmt = self.acct_stmts[0]

        # AcctCost
        self.acct_cost, created = AcctCost.objects.get_or_create(hotel=self.hotel)

        # AcctTrans
        self.acct_trans = create_acct_trans(hotel=self.hotel)
        self.acct_tran = self.acct_trans[0]

    ### CREATE TESTS ###

    def test_create_acct_cost(self):
        assert self.acct_cost.recharge_amt

    ### MANAGER TESTS ###

    def test_monthly_trans(self):
        monthly_trans = AcctTrans.objects.filter(
            hotel=self.hotel, 
            insert_date__month=self.today.month,
            insert_date__year=self.today.year
            )
        monthly_trans_mgr = AcctTrans.objects.monthly_trans(
            hotel=self.hotel
            )
        assert len(monthly_trans) == len(monthly_trans_mgr)

    def test_balance(self):
        assert (AcctTrans.objects.balance() ==
                AcctTrans.objects.aggregate(Sum('amount'))['amount__sum'])

    def test_init_amt_mgr(self):
        acct_cost = AcctCost.objects.get(hotel=self.hotel)
        acct_tran, created = AcctTrans.objects.get_or_create(
            hotel=self.hotel, trans_type=self.init_amt)
        assert acct_cost.init_amt == acct_tran.amount

    def test_recharge_amt_mgr(self):
        acct_cost = AcctCost.objects.get(hotel=self.hotel)
        acct_tran, created = AcctTrans.objects.get_or_create(
            hotel=self.hotel, trans_type=self.recharge_amt)
        assert acct_cost.recharge_amt == acct_tran.amount

    ### SMS_USED

    def test_sms_used_validate_insert_date(self):
        with self.assertRaises(ValidationError):
            AcctTrans.objects.sms_used_validate_insert_date(self.today)

        self.assertIsNone(AcctTrans.objects.sms_used_validate_insert_date(
            self.yesterday))

    def test_sms_used_validate_single_date_record(self):
        # test for "yesterday" b/c `sms_used` can only be calculated
        # for completed days, so it is a final # of SMS sent
        for ea in AcctTrans.objects.filter(hotel=self.hotel, insert_date__gte=self.yesterday):
            ea.delete()

        self.assertIsNone(AcctTrans.objects.sms_used_validate_single_date_record(
            hotel=self.hotel, insert_date=self.yesterday))

        AcctTrans.objects.sms_used(hotel=self.hotel, insert_date=self.yesterday)

    def test_sms_used_daily_message_count(self):
        self.assertEqual(self.hotel.messages.filter(
            insert_date=self.yesterday).count(), 10)

    def test_sms_used_mtd(self):
        for ea in AcctTrans.objects.filter(hotel=self.hotel, trans_type=self.sms_used):
            ea.delete()

        self.assertEqual(AcctTrans.objects.sms_used_mtd(hotel=self.hotel,
            insert_date=self.yesterday), 0)

        AcctTrans.objects.sms_used(hotel=self.hotel, insert_date=self.yesterday)
        self.assertEqual(AcctTrans.objects.sms_used_mtd(hotel=self.hotel,
            insert_date=self.yesterday), 10)

    ### PHONE_NUMBER

    def test_phone_number_charge(self):
        # set the ``desc`` as an arbitrary ph num string
        acct_tran = AcctTrans.objects.phone_number_charge(self.hotel,
            phone_number=settings.DEFAULT_TO_PH)
        self.assertIsInstance(acct_tran, AcctTrans)
        self.assertEqual(acct_tran.amount, -settings.PHONE_NUMBER_MONTHLY_COST)

    def test_recharge(self):
        # ``recharge()`` returns None if it is not triggered
        old_balance = AcctTrans.objects.filter(hotel=self.hotel).balance()
        print('old_balance:', old_balance)
        recharge_amt, created = AcctTrans.objects.recharge(self.hotel, old_balance)
        self.assertIsNone(recharge_amt)

        # Create a fake charge to cause a call to ``.recharge()``
        AcctTrans.objects.phone_number_charge(hotel=self.hotel, phone_number=settings.DEFAULT_TO_PH)
        AcctTrans.objects.phone_number_charge(hotel=self.hotel, phone_number=settings.DEFAULT_TO_PH)
        AcctTrans.objects.phone_number_charge(hotel=self.hotel, phone_number=settings.DEFAULT_TO_PH)
        AcctTrans.objects.phone_number_charge(hotel=self.hotel, phone_number=settings.DEFAULT_TO_PH)

        # the balance of credits is higher than the acct_cost.balance_min, so no recharge occurs
        # set balance=0 b/c min balance is 100, so this will trigger a recharge
        current_balance = AcctTrans.objects.filter(hotel=self.hotel).balance()
        print "current_balance:", current_balance
        recharge_amt, created = AcctTrans.objects.recharge(self.hotel, balance=current_balance)
        print('recharge w/ balance=0:', recharge_amt.amount)
        assert recharge_amt.amount
        assert recharge_amt
        assert recharge_amt.trans_type == self.recharge_amt

        new_balance = AcctTrans.objects.filter(hotel=self.hotel).balance()

        print('self.hotel.acct_cost.recharge_amt:', self.hotel.acct_cost.recharge_amt)
        print('recharge_amt.amount:', recharge_amt.amount)
        print('old_balance:', old_balance, 'new_balance:', new_balance)
        print('balance_min:', self.hotel.acct_cost.balance_min)
        print('new_balance:', new_balance)
        self.assertTrue(new_balance >= self.hotel.acct_cost.balance_min)

    ### BALANCE

