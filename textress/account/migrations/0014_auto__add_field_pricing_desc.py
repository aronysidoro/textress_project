# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Pricing.desc'
        db.add_column('account_pricing', 'desc',
                      self.gf('django.db.models.fields.CharField')(max_length=255, blank=True, default=''),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Pricing.desc'
        db.delete_column('account_pricing', 'desc')


    models = {
        'account.acctcost': {
            'Meta': {'object_name': 'AcctCost'},
            'balance_min': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'hotel': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'acct_cost'", 'to': "orm['main.Hotel']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'init_amt': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1000'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'per_sms': ('django.db.models.fields.FloatField', [], {'blank': 'True', 'default': '5.5'}),
            'recharge_amt': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1000'})
        },
        'account.acctstmt': {
            'Meta': {'object_name': 'AcctStmt'},
            'balance': ('django.db.models.fields.FloatField', [], {'blank': 'True', 'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'hotel': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'acct_stmt'", 'to': "orm['main.Hotel']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'month': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            'monthly_costs': ('django.db.models.fields.FloatField', [], {'blank': 'True', 'default': '500.0'}),
            'total_sms': ('django.db.models.fields.IntegerField', [], {'blank': 'True', 'default': '0'}),
            'year': ('django.db.models.fields.IntegerField', [], {'blank': 'True'})
        },
        'account.accttrans': {
            'Meta': {'object_name': 'AcctTrans'},
            'amount': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'credit': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'debit': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hotel': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'acct_trans'", 'to': "orm['main.Hotel']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'insert_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'sms_used': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True', 'default': '0'}),
            'trans_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['account.TransType']"})
        },
        'account.pricing': {
            'Meta': {'object_name': 'Pricing', 'ordering': "('tier',)"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'desc': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'end': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '5', 'decimal_places': '4'}),
            'start': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'tier': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'tier_name': ('django.db.models.fields.CharField', [], {'max_length': '55', 'blank': 'True'})
        },
        'account.transtype': {
            'Meta': {'object_name': 'TransType', 'ordering': "['id']"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'desc': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True'})
        },
        'main.hotel': {
            'Meta': {'object_name': 'Hotel', 'ordering': "['-created']"},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'address_city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'address_line1': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'address_line2': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'address_phone': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'address_state': ('django.db.models.fields.CharField', [], {'max_length': '25', 'default': "'Alabama'"}),
            'address_zip': ('django.db.models.fields.IntegerField', [], {'max_length': '5'}),
            'admin_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True', 'unique': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'customer': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'to': "orm['payment.Customer']"}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hotel_type': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True', 'default': "''"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'unique': 'True'}),
            'rooms': ('django.db.models.fields.IntegerField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '125', 'blank': 'True', 'unique': 'True'}),
            'twilio_auth_token': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'twilio_ph_sid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'twilio_phone_number': ('django.db.models.fields.CharField', [], {'max_length': '12', 'blank': 'True'}),
            'twilio_sid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        'payment.customer': {
            'Meta': {'object_name': 'Customer', 'ordering': "['-created']"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now': 'True'}),
            'short_pk': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        }
    }

    complete_apps = ['account']