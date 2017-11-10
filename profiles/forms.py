from django import forms
from .models import UserEmails, AddressBook
from .utils import validate_input


class AddEmailForm(forms.Form):
    email = forms.EmailField(max_length=100)
    password = forms.CharField(max_length=32, widget=forms.PasswordInput)
    imap = forms.CharField(max_length=100)
    smtp = forms.CharField(max_length=100)

    def add_email(self, user_id):
        self.email = self.cleaned_data['email']
        self.password = self.cleaned_data['password']
        self.imap = self.cleaned_data['imap']
        self.smtp = self.cleaned_data['smtp']
        error = validate_input(self.email, self.password, self.imap, self.smtp)
        if error:
            return error
        else:
            row = UserEmails(user_id=user_id, email=self.email, password=self.password, imap=self.imap, smtp=self.smtp)
            row.save()


class SendEmailForm(forms.Form):
    to = forms.CharField(required=True)
    subject = forms.CharField(max_length=100)
    message = forms.Field(widget=forms.Textarea)


class AddContactForm(forms.ModelForm):
    class Meta:
        model = AddressBook
        fields = ['name', 'surname', 'email', 'phone', 'other_info']
