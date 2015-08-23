from rest_framework import serializers
from django.contrib.auth.models import User

from concierge.models import Guest, Message


### MESSAGE

MESSAGE_FIELDS = ('id', 'guest', 'user', 'sid', 'received', 'status',
    'to_ph', 'from_ph', 'body', 'reason', 'cost', 'read',
    'created', 'modified', 'hidden')


class MessageGuestUserSerializer(serializers.ModelSerializer):
    '''
    For the GuestListView - to filter on 'read' / 'unread' messages
    '''
    class Meta:
        model = Message
        fields = ('id', 'guest', 'user', 'read',)


# class MessageBasicSerializer(serializers.ModelSerializer):
#     '''
#     Message info for GuestDetailView API.
#     '''
#     class Meta:
#         model = Message
#         fields = MESSAGE_FIELDS
#         read_only_fields = ('created', 'modified',)


class MessageBasicSerializer(serializers.ModelSerializer):
    '''
    ``user`` field isn't required b/c if Message is from the Guest, 
    then it doesn't have a ``user`` attr. 
    '''
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Message
        fields = MESSAGE_FIELDS
        read_only_fields = ('created', 'modified',)


class MessageSerializer(serializers.ModelSerializer):
    '''
    Used for AngularJs to post to List API to create new Messages.
    '''
    guest = serializers.PrimaryKeyRelatedField(
        queryset=Guest.objects.all(),
        required=False
        )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False
        )

    class Meta:
        model = Message
        fields = MESSAGE_FIELDS + ('insert_date',)
        read_only_fields = ('created', 'modified',)


### GUEST

class GuestBaseSerizer(serializers.ModelSerializer):
    '''
    Base Serializer for the 2 serializers below. The only difference for 
    the below is how they serialize related ``messages``.
    '''
    class Meta:
        model = Guest
        fields = ('id', 'name', 'room_number', 'phone_number', 'thumbnail',
            'check_in', 'check_out', 'created', 'modified', 'hidden',
            'messages',)
        read_only_fields = ('created', 'modified',)


class GuestBasicSerializer(GuestBaseSerizer):
    '''
    Guest List Create API Serializer
    '''
    messages = MessageGuestUserSerializer(many=True, source='message_set')


class GuestMessageSerializer(GuestBaseSerizer):
    '''
    GuestDetailView main Serializer
    '''
    messages = MessageBasicSerializer(many=True, source='message_set')