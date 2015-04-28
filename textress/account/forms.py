from django import forms 
from django.contrib.auth.models import User
from django.contrib import auth
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import forms as auth_forms

from djangular.forms import NgFormValidationMixin
from djangular.styling.bootstrap3.forms import (Bootstrap3Form,
    Bootstrap3ModelForm)

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div, HTML

from .helpers import login_messages, salt
from utils import email


# Forms use `djangular` client side validation w/ django native contrib.forms logic

class AuthenticationForm(NgFormValidationMixin, auth_forms.AuthenticationForm, Bootstrap3Form):
    form_name = 'login_form'


class PasswordResetForm(NgFormValidationMixin, auth_forms.PasswordResetForm, Bootstrap3Form):
    form_name = 'pw_reset_form'


class SetPasswordForm(NgFormValidationMixin, auth_forms.SetPasswordForm, Bootstrap3Form):
    form_name = 'set_pw_form'


class PasswordChangeForm(NgFormValidationMixin, auth_forms.PasswordChangeForm, Bootstrap3Form):
    form_name = 'pw_change_form'


##############
# CLOSE ACCT #
##############

class CloseAccountForm(forms.Form):
    pass 


class CloseAcctConfirmForm(forms.Form):
    pass