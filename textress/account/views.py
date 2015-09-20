from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.http import Http404, HttpResponseRedirect
from django.conf import settings
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required

from django.views.generic import View, ListView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView, CreateView, UpdateView
from django.views.generic.edit import ModelFormMixin

from rest_framework import generics
from rest_framework.response import Response

from braces.views import (LoginRequiredMixin, GroupRequiredMixin, SetHeadlineMixin,
    StaticContextMixin, FormValidMessageMixin)

from account.forms import (AuthenticationForm, CloseAccountForm,
    CloseAcctConfirmForm, AcctCostForm, AcctCostUpdateForm)
from account.mixins import alert_messages
from account.models import Dates, AcctCost, AcctStmt, AcctTrans, Pricing
from account.serializers import PricingSerializer
from main.mixins import RegistrationContextMixin, AdminOnlyMixin, HotelUserMixin
from payment.mixins import BillingSummaryContextMixin
from utils import email, login_messages
from utils.mixins import FormUpdateMessageMixin


### ACCOUNT ERROR / REDIRCT ROUTING VIEWS ###

@login_required(login_url=reverse_lazy('login'))
def private(request):
    messages.info(request, login_messages['now_logged_in'])
    return HttpResponseRedirect(reverse('account'))


def login_error(request):
    messages.warning(request, login_messages['login_error'])
    return HttpResponseRedirect(reverse('login'))


@login_required(login_url=reverse_lazy('login'))
def logout(request):
    auth.logout(request)
    messages.warning(request, 'You are now logged out')
    return HttpResponseRedirect(reverse('login'))


@login_required(login_url=reverse_lazy('login'))
def verify_logout(request):
    return render(request, 'cpanel/form-success/verify_logout.html')


### ACCOUNT VIEWS ###

class AccountView(LoginRequiredMixin, HotelUserMixin, SetHeadlineMixin,
    StaticContextMixin, TemplateView):
    """
    Account Dashboard ~ User Home Page
    """
    headline = 'Dashboard'
    static_context = {'headline_small': 'guest list & quick links'}
    template_name = 'cpanel/account.html'

    def get_context_data(self, **kwargs):
        """Show alert messages for pending actions needed before the 
        Account will be fully functional."""
        context = super(AccountView, self).get_context_data(**kwargs)
        if not self.hotel.twilio_ph_sid:
            alert = {
                'type': 'warning',
                'link': reverse('sms:ph_num_add'),
                'strong_message': 'Alert!',
                'message': 'You need to purchase a phone number before you are able to send SMS.'
            }
            context['alerts'] = alert_messages(messages=[alert])
        return context


### REGISTRATION VIEWS ###

class RegisterAcctCostBaseView(GroupRequiredMixin, RegistrationContextMixin, View):
    """
    Step #3 of Registration

    Pick a Plan, and save the Plan as a `session cookie` before creating
    the Stipe Customer/Subscription using the Plan Choice.
    """
    group_required = ["hotel_admin"]
    model = AcctCost
    form_class = AcctCostForm
    template_name = 'frontend/register/register.html'
    success_url = reverse_lazy('payment:register_step4')

    def get_context_data(self, **kwargs):
        context = super(RegisterAcctCostBaseView, self).get_context_data(**kwargs)
        context['step_number'] = 2
        context['step'] = context['steps'][context['step_number']]
        return context


class RegisterAcctCostCreateView(RegisterAcctCostBaseView, CreateView):
    '''
    If AcctCost already exists for the Hotel, re-route to the UpdateView.
    '''
    def dispatch(self, request, *args, **kwargs):
        try:
            acct_cost = self.request.user.profile.hotel.acct_cost
        except AttributeError:
            return super(RegisterAcctCostCreateView, self).dispatch(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('register_step3_update', kwargs={'pk': acct_cost.pk}))

    def form_valid(self, form):
        '''Add the Hotel Obj to the AcctCost instance b/4 saving.'''

        self.object, created = self.model.objects.get_or_create(
            hotel=self.request.user.profile.hotel, **form.cleaned_data)

        return super(ModelFormMixin, self).form_valid(form)


class RegisterAcctCostUpdateView(RegisterAcctCostBaseView, UpdateView):    
    '''
    AcctCost must belong to the Admin User's Hotel.
    '''
    def dispatch(self, request, *args, **kwargs):
        try:
            # must call this or else the "object" instance of the Model
            # will not be available
            self.object = self.get_object()
            acct_cost = self.object.hotel == self.request.user.profile.hotel
        except AttributeError:
            acct_cost = None

        if not acct_cost:
            raise Http404

        return super(RegisterAcctCostUpdateView, self).dispatch(request, *args, **kwargs)


#############
# ACCT COST #
#############

class AcctCostUpdateView(AdminOnlyMixin, BillingSummaryContextMixin,
    SetHeadlineMixin, FormUpdateMessageMixin, UpdateView):

    headline = "Payment Refill Settings"
    template_name = "cpanel/form.html"
    model = AcctCost
    form_class = AcctCostUpdateForm
    success_url = reverse_lazy('payment:summary')


#############
# ACCT STMT #
#############

class AcctStmtListView(AdminOnlyMixin, SetHeadlineMixin, ListView):
    '''AcctStmt by Month.'''

    headline = _("Account Statements")
    template_name = 'list.html'

    def get_queryset(self):
        return AcctStmt.objects.filter(hotel=self.hotel)

    def get(self, request, *args, **kwargs):
        '''Ensure the current month's AcctStmt is up to date.

        TODO: Make this a daiy job, and not in the View.get()
        '''
        # acct_stmt = update_current_acct_stmt(hotel=self.hotel)
        return super(AcctStmtListView, self).get(request, *args, **kwargs)


class AcctStmtDetailView(AdminOnlyMixin, SetHeadlineMixin, BillingSummaryContextMixin, TemplateView):
    '''
    All AcctTrans for a single Month.
    '''
    headline = "Account Statement Detail"
    template_name = 'account/acct_trans_detail.html'

    def get_context_data(self, **kwargs):
        context = super(AcctStmtDetailView, self).get_context_data(**kwargs)
        # Use All Time Hotel Transactions to get the Balance
        _date = Dates().first_of_month(int(kwargs['month']), int(kwargs['year']))
        all_trans = AcctTrans.objects.filter(hotel=self.hotel)
        monthly_trans = AcctTrans.objects.monthly_trans(self.hotel, _date).order_by('-created')
        # Table Context
        context['monthly_trans'] = monthly_trans
        context['init_balance'] = monthly_trans.balance()
        # Normal Context
        context['acct_stmt'] = (AcctStmt.objects.filter(hotel=self.hotel)
                                                .get(month=kwargs['month'], year=kwargs['year']))
        context['acct_stmts'] = AcctStmt.objects.filter(hotel=self.hotel)
        context['balance'] = all_trans.balance()
        return context


class AcctPmtHistoryView(AdminOnlyMixin, SetHeadlineMixin, BillingSummaryContextMixin, ListView):
    '''
    Simple table view of payments that uses pagination.
    '''
    headline = "Account Payments"
    model = AcctTrans
    template_name = "account/acct_pmt_history.html"
    paginate_by = 2 if settings.DEBUG else 10

    def get_queryset(self):
        queryset = AcctTrans.objects.filter(hotel=self.hotel,
            trans_type__name__in=['init_amt', 'recharge_amt']).order_by('-insert_date')
        return queryset


##############
# CLOSE ACCT #
##############

class CloseAcctView(AdminOnlyMixin, SetHeadlineMixin, FormView):
    '''
    Steps
    -----
    Release Twilio Ph(s)
    Suspend Twilio Subaccount
    Refund and Account Credits via Stripe Refund
    Deactivate Hotel
    Deactivate Users
    Delete Stripe Cards

    Notes
    -----
    Will be done via Celery daily per Hotel request. So as not to slow down
        request/response cycle of normal web activity.
    Email CloseAcct confirmation to AdminUser w/ refund details, etc...

    '''
    headline = _("Close Account")
    form_class = CloseAccountForm
    template_name = 'account/account_form.html'

    def get_success_url(self):
        return reverse('close_acct_confirm',
            kwargs={'slug': self.hotel.customer.short_pk})


class CloseAcctConfirmView(AdminOnlyMixin, SetHeadlineMixin, FormView):
    '''
    Expl
    ----
    Cannot be reversed, ph #(s) released
    If you want to use the services in the future, please go through
        the normal signup process.
    Will recieve email with confirmation of "close acct" request
    Takes 24 hours to process request
    Payment refund take 5-7 business days
    Any questions, please contact: billing@textress.com
    PH # for questions, 775-419-4000
    '''

    headline = _("Confirm Close Account")
    form_class = CloseAcctConfirmForm
    template_name = 'account/account_form.html'
    success_url = reverse_lazy('close_acct_success')

    def form_valid(self, form):
        '''
        TODO: dispatch request to Celery
            - Send email that "request has been submitted"
        '''
        msg = email.close_account_email(self.request.user)
        msg.send()
        return super(CloseAcctConfirmView, self).form_valid(form)


class CloseAcctSuccessView(AdminOnlyMixin, SetHeadlineMixin, TemplateView):
    '''
    TODO
    ----
    `context`: 
        submitted, takes: 
            Takes 24 hours to process request
            Payment refund take 5-7 business days
        msg:
            "thank you and we hope that we can do Biz again in future."

    '''
    headline = _("Close Account Request Submitted")
    template_name = 'template.html'

    def get_context_data(self, **kwargs):
        context = super(CloseAcctSuccessView, self).get_context_data(**kwargs)
        context['message'] = "Thank you and we hope that we can do Biz again in future."
        return context


### REINSTATE ACCT: Not in use ###

class ReinstateAcctView(View):
    '''
    Steps
    -----
    AdminUser reactivates his User
    Reactivate Hotel
    Confirm Pmt details. ex- $10 refills at $0 balance
    Make Pmt
    Activate Twilio Subaccount
    AdminUser chooses new Twilio Ph #
    Activate Users

    Notes
    -----
    Will use similar steps to "Signup Process"

    '''
    pass


########
# REST #
########

class PricingListAPIView(generics.ListAPIView):
    '''No permissions needed b/c read only list view, and will be used 
    on the Biz Site.'''

    queryset = Pricing.objects.all()
    serializer_class = PricingSerializer

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)


class PricingRetrieveAPIView(generics.RetrieveAPIView):

    queryset = Pricing.objects.all()
    serializer_class = PricingSerializer