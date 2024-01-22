from rest_framework import serializers, exceptions
from django.contrib.auth import authenticate
from billing.models import *
from user.models import *
from billing.business_logic.validators import *
from billing.business_logic.services import EventServices


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(username=attrs['username'],
                            password=attrs['password'])
        if not user:
            raise serializers.ValidationError(
                'Incorrect username or password.')
        if not user.is_active:
            raise serializers.ValidationError('User is disabled.')
        return {'user': user}


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ("__all__")


class CashOutflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashOutflow
        fields = ("__all__")


class TeamMemberBillSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMemberBill
        fields = ("__all__")


class AddOnSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddOn
        fields = ("__all__")


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ("__all__")

    def update(self, instance, validated_data):
        # Extract the 'add_ons' data from the validated data
        add_ons_data = validated_data.pop('add_ons', None)
        lead_photographers_data = validated_data.pop('lead_photographers', None)

        # Update the fields of the 'Event' model instance with the validated data
        for key, value in validated_data.items():
            setattr(instance, key, value)

        # Add the new 'add_ons' from the validated data to the instance
        if add_ons_data is not None:
            instance.add_ons.clear()
            instance.add_ons.add(*add_ons_data)

        if lead_photographers_data is not None:
            instance.lead_photographers.clear()
            instance.lead_photographers.add(*lead_photographers_data)

        EventServices(instance, add_ons_data)
        # Save the updated instance
        instance.save()
        return instance

    def validate(self, data):
        try:
            EventValidator(data, self.instance)
        except ValueError as e:
            raise serializers.ValidationError(str(e))
        return data


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ("__all__")


class CashInflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashInflow
        fields = ("__all__")

    def validate(self, data):
        try:
            CashInflowValidator(data, self.instance)
        except ValueError as e:
            raise serializers.ValidationError(str(e))
        return data


class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = ("__all__")
