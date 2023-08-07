from rest_framework import serializers
from .models import *

class TgNotifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = TgNotifier
        fields = '__all__'

class AdvertSerialaizer(serializers.ModelSerializer):
    post_time = serializers.DateTimeField(format="%Y-%m-%d-%H-%M-%S", input_formats=["%Y-%m-%d-%H-%M-%S"])

    class Meta:
        model = Advert
        fields = '__all__'

class CallerSerialaizer(serializers.ModelSerializer):
    class Meta:
        model = Caller
        fields = '__all__'

class CallSerialaizer(serializers.ModelSerializer):

    from_user = CallerSerialaizer()
    to_user = CallerSerialaizer()

    task = serializers.PrimaryKeyRelatedField(many=False, read_only=True)

    class Meta:
        model = Call
        fields = '__all__'
        depth = 1
    
    def create(self, validated_data):
        from_user = validated_data.pop('from_user')
        to_user = validated_data.pop('to_user')
        from_user_id = Caller.objects.create(**from_user)
        to_user_id = Caller.objects.create(**to_user)
        call = Call.objects.create(from_user=from_user_id, to_user=to_user_id, **validated_data)
        return call

    def to_internal_value(self, data):
        new_data = {(key + '_user' if key == 'from' or key == 'to' else key):value for (key,value) in data.items()}
        return super().to_internal_value(new_data)

# class SimpleSaveTaskSerializer(serializers.Serializer):
#     save_request = serializers.CharField()
#     create_time = serializers.DateTimeField(auto_now_add=True)
#     call_initiator = CallerSerialaizer()

#     def create(self, validated_data):
#         profile_data = validated_data.pop('profile')
#         user = User.objects.create(**validated_data)
#         Profile.objects.create(user=user, **profile_data)
#         return user
