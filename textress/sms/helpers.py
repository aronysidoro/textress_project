#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import requests
import xmltodict

import twilio
from twilio.rest import TwilioRestClient

from django import forms
from django.conf import settings
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.timezone import now 


sms_messages = {
    "limit_reached": "Daily text message limit reached. Please try again tomorrow.",
    "sent": "SMS message successfully sent.",
    "send_failed": "SMS failed to send. Please check that is a valid U.S. phone number.",
    "enter_valid_ph": "Please enter a valid phone number."
}


def _to(text):
    try:
        to = text.to
    except AttributeError:
        raise forms.ValidationError("Invalid Phone Number")
    else:
        return to


def send_text(text):
    """
    `text` == sms.models.Text

    Send SMS or print exception for the time being only "print"

    Uses default Twilio settings b/c this is for the Demo Yahoo! Weather View.
    """
    account = settings.TWILIO_ACCOUNT_SID
    token = settings.TWILIO_AUTH_TOKEN
    client = TwilioRestClient(account, token)

    try:
        message = client.messages.create(
            to=_to(text),
            from_=text.frm,
            body=text.body
            )
    except twilio.TwilioRestException as e:
        raise
    else:
        text.sent = True
        text.save()
        return text


def send_message(hotel, to, body):
    """
    Send Message for Concierge App.

    Use `hotel` to connect the correct Twilio Client.
    """
    client = TwilioRestClient(hotel.twilio_sid, hotel.twilio_auth_token)

    try:
        message = client.messages.create(
            to=to,
            from_=hotel.twilio_phone_number,
            body=body
            )
    except twilio.TwilioRestException as e:
        raise e
    else:
        return message


def get_weather(url="http://weather.yahooapis.com/forecastrss?w=12795483&u=f"):
    try:
        r = requests.get(url)
        # parse bytes into a text string
        text = r.content.decode("utf-8")
        #convert xml text to OrderedDict
        doc = xmltodict.parse(text)
        # item contains all the main temp info
        title = doc['rss']['channel']['title']
        condition = doc['rss']['channel']['item']['yweather:condition']
        weather = condition['@text']
        temp = condition['@temp']
        return "{0}. {1}. {2}°F.".format(title, weather, temp)
    except requests.ConnectionError:
        return "Sorry, the weather connection failed. Weather currently unavailable."
    except KeyError:
        return "Weather currently unavailable."


def bad_ph_error(to):
    return "'{}' is not a valid phone #.\
            Please enter a 10 digit phone #.".format(to)


def clean_to(obj, cleaned_data):
    """
    Check that it's a valid ph.
    Use *regex* to clean DEFAULT testing ph#'s from settings.py.
    """
    to = cleaned_data.get('to')
    try:
        pattern = re.compile(r'(?:\+1){0,1}(\d{10})')
        match = re.search(pattern, to)
        new_to = match.group(1)
    except AttributeError:
        raise forms.ValidationError(bad_ph_error(to))
    else:
        to = "+1" + new_to
        cleaned_data['to'] = to
    return obj, cleaned_data