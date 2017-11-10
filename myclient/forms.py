from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from registration import validators
from registration.forms import RegistrationForm

User = get_user_model()


# There exists RegistrationFormUniqueEmail in django-registration
class MyUniqueEmailRegistrationForm(RegistrationForm):
    def clean(self):
        username_value = self.cleaned_data.get(User.USERNAME_FIELD)
        email = self.cleaned_data.get('email')
        if username_value is not None:
            try:
                if hasattr(self, 'reserved_names'):
                    reserved_names = self.reserved_names
                else:
                    reserved_names = validators.DEFAULT_RESERVED_NAMES
                validator = validators.ReservedNameValidator(
                    reserved_names=reserved_names
                )
                validator(username_value)
                if email:
                    if User.objects.filter(email=email).exists():
                        raise forms.ValidationError('This email is already used.')
            except ValidationError as v:
                self.add_error(User.USERNAME_FIELD, v)
        super(RegistrationForm, self).clean()
