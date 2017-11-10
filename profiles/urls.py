from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from . import views
from profiles.views import IndexView, AddAccountView, AccountDetailView, EmailBodyView, SendEmailView, SettingsView, \
    AddressBookView, AddContactView, ContactView, EditContactView, DeleteContactView
    # , SentView, TrashView

app_name = 'profiles'
urlpatterns = [
    # url(r'^$', views.index, name='index'),
    # url(r'^add-account$', views.add_account, name='add_account'),
    # url(r'^(?P<email_id>[0-9]+)/$', views.detail, name='detail'),
    # url(r'^(?P<email_id>[0-9]+)/(?P<message_id>[0-9]+)/$', views.email_body, name='email_body'),
    # url(r'^(?P<email_id>[0-9]+)/send/$', views.send_email, name='send_email'),
    # url(r'^settings/$', views.settings, name='settings'),

    url(r'^$', login_required(IndexView.as_view()), name='index'),
    url(r'^add-account$', login_required(AddAccountView.as_view()), name='add_account'),
    url(r'^(?P<account_id>[0-9]+)/(?P<folder_index>[0-9]+)/$', login_required(AccountDetailView.as_view()), name='detail'),
    url(r'^(?P<account_id>[0-9]+)/(?P<folder_index>[0-9]+)/(?P<message_id>[0-9]+)/$', login_required(EmailBodyView.as_view()), name='email_body'),
    url(r'^(?P<account_id>[0-9]+)/send/$', login_required(SendEmailView.as_view()), name='send_email'),
    url(r'^settings/$', login_required(SettingsView.as_view()), name='settings'),
    url(r'^address-book/$', login_required(AddressBookView.as_view()), name='address_book'),
    url(r'^address-book/(?P<contact_id>[0-9]+)/$', login_required(ContactView.as_view()), name='contact_details'),
    url(r'^address-book/add-contact/$', login_required(AddContactView.as_view()), name='add_contact'),
    url(r'^address-book/edit/(?P<contact_id>[0-9]+)/$', login_required(EditContactView.as_view()), name='edit_contact'),
    url(r'^address-book/delete/(?P<contact_id>[0-9]+)/$', login_required(DeleteContactView.as_view()), name='delete_contact'),
]
