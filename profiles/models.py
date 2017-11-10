from django.db import models
from django.conf import settings
from django.urls import reverse


class UserEmails(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=32)
    imap = models.CharField(max_length=100)
    smtp = models.CharField(max_length=100)

    def __str__(self):
        return self.email


class AddressBook(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=32)
    surname = models.CharField(max_length=32)
    email = models.EmailField(max_length=100)
    phone = models.CharField(max_length=32)
    other_info = models.TextField(max_length=2000)

    def __str__(self):
        return self. name
