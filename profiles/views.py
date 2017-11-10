from django.shortcuts import redirect, render
from django.views import View
from django.views.generic.edit import FormView, UpdateView, DeleteView, CreateView

from .forms import AddEmailForm, SendEmailForm, AddContactForm
from .utils import get_mailbox, get_email_body, send, delete_mails, get_folders
from .models import UserEmails, AddressBook
from . import utf

import re


class AccountDetailView(View):
    def post(self, request, account_id, folder_index):
        boxes = request.POST.getlist('boxes')
        account_row = UserEmails.objects.filter(id=account_id)
        password = account_row.values('password').get()['password']
        username = account_row.values('email').get()['email']
        imap = account_row.values('imap').get()['imap']
        folders, names = get_folders(username, password, imap)

        clicked = folders[int(folder_index)]
        to_select = names[clicked]
        headers = get_mailbox(username, password, imap, to_select)

        if 'delete' in request.POST:
            folders, names = get_folders(username, password, imap)
            clicked = folders[int(folder_index)]
            to_select = names[clicked]
            delete_mails(imap, username, password, boxes, to_select)
            headers = get_mailbox(username, password, imap, to_select)
        return render(request, 'profiles/detail.html',
                      {'headers': headers, 'account_id': account_id, 'username': username, 'folder': clicked,
                       'folders': folders, 'folder_index': folder_index})

    def get(self, request, account_id, folder_index):
        account_row = UserEmails.objects.filter(id=account_id)
        password = account_row.values('password').get()['password']
        username = account_row.values('email').get()['email']
        imap = account_row.values('imap').get()['imap']
        folders, names = get_folders(username, password, imap)
        clicked = folders[int(folder_index)]
        print(clicked)
        to_select = names[clicked]
        headers = get_mailbox(username, password, imap, to_select)
        return render(request, 'profiles/detail.html',
                      {'headers': headers, 'account_id': account_id, 'username': username, 'folder': clicked,
                       'folders': folders, 'folder_index': folder_index})


class SendEmailView(View):
    def post(self, request, account_id):
        form = SendEmailForm(request.POST, request.FILES)
        if form.is_valid():
            account_row = UserEmails.objects.filter(id=account_id)
            password = account_row.values('password').get()['password']
            username = account_row.values('email').get()['email']
            smtp = account_row.values('smtp').get()['smtp']
            to = form.cleaned_data['to'].split(',')
            for email in to:
                if not re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email):
                    error = "Not a valid email address!"
                    return render(request, 'profiles/send_email.html', {'form': form, 'error': error})
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            print("To: ", to, "Mess: ", message, "Subj: ", subject)
            files = [f for f in request.FILES.getlist('datafile')]
            result = send(smtp, username, password, to, subject, message, files)
            form = SendEmailForm()  # 4tob o4istiti posle otpravki
            if not result:
                success = 'Message successfully sent!'
                return render(request, 'profiles/send_email.html', {'form': form, 'success': success})
            return render(request, 'profiles/send_email.html', {'form': form, 'error': result})
        return render(request, 'profiles/send_email.html', {'form': form})

    def get(self, request, account_id):
        form = SendEmailForm()
        return render(request, 'profiles/send_email.html', {'form': form})


class ContactView(View):
    def get(self, request, contact_id):
        selected_contact = AddressBook.objects.get(id=contact_id)
        return render(request, 'profiles/contact_details.html',
                      {'contact': selected_contact})


class AddContactView(CreateView):
    template_name = 'profiles/add_contact.html'
    form_class = AddContactForm
    success_url = '/profile/address-book/'
    model = AddressBook

    def form_valid(self, form):
        contact = form.save(commit=False)
        contact.user_id = self.request.user.id
        contact.save()
        return redirect(self.success_url)


class EditContactView(UpdateView):
    template_name = 'profiles/contact_edit.html'
    form_class = AddContactForm
    success_url = '/profile/address-book/'
    model = AddressBook

    def get_object(self, queryset=None):
        obj = AddressBook.objects.get(id=self.kwargs['contact_id'])
        return obj


class DeleteContactView(DeleteView):
    form_class = AddContactForm
    success_url = '/profile/address-book/'
    model = AddressBook

    def get_object(self, queryset=None):
        obj = AddressBook.objects.get(id=self.kwargs['contact_id'])
        return obj


class AddressBookView(View):
    def get(self, request):
        contacts = AddressBook.objects.filter(user_id=request.user.id)
        return render(request, 'profiles/address_book.html', {'contacts': contacts})

    def post(self, request):
        contacts = AddressBook.objects.filter(user_id=request.user.id)
        return render(request, 'profiles/address_book.html', {'contacts': contacts})


class AddAccountView(FormView):
    template_name = 'profiles/add_account.html'
    form_class = AddEmailForm
    success_url = '/profile/'

    def form_valid(self, form):
        error = form.add_email(self.request.user.id)
        if error:
            return render(self.request, self.template_name, {'form': form, 'error': error})
        return redirect(self.success_url)

    def form_invalid(self, form):
        return super(AddAccountView, self).form_invalid(form)


class SettingsView(View):
    def post(self, request):
        accounts = UserEmails.objects.filter(user_id=request.user.id)
        boxes = request.POST.getlist('boxes')
        accounts_to_delete = []
        for box in boxes:
            accounts_to_delete.append(accounts[int(box)])
        for box in boxes:
            to_delete = accounts_to_delete[int(box)]
            try:
                UserEmails.objects.filter(user_id=request.user.id).filter(email=to_delete).delete()
            except Exception as ex:
                print(ex)
        accounts = UserEmails.objects.filter(user_id=request.user.id)
        return render(request, 'profiles/settings.html', {'accounts': accounts})

    def get(self, request):
        accounts = UserEmails.objects.filter(user_id=request.user.id)
        return render(request, 'profiles/settings.html', {'accounts': accounts})


class EmailBodyView(View):
    def get(self, request, account_id, message_id, folder_index):
        try:
            account_row = UserEmails.objects.filter(id=account_id)
            password = account_row.values('password').get()['password']
            username = account_row.values('email').get()['email']
            imap = account_row.values('imap').get()['imap']
            folders, names = get_folders(username, password, imap)
            clicked = folders[int(folder_index)]
            print(clicked)
            to_select = names[clicked]
            # print(username, password, imap)
            email_text = get_email_body(username, password, imap, message_id, to_select)
        except Exception as ex:
            print(ex)
            return redirect('/profile')
        return render(request, 'profiles/email_body.html', {'email_body': email_text})


class IndexView(View):
    def get(self, request):
        accounts = UserEmails.objects.filter(user_id=request.user.id)
        return render(request, 'profiles/main.html', {'accounts': accounts})


        # In this, and others below i should've used login_required decorator.

        # def index(request):
        # username = request.user.get_username()
        # accounts = UserEmails.objects.filter(user_id=request.user.id)
        # return render(request, 'profiles/main.html', {'username': username, 'accounts': accounts})

        # def add_account(request):
        #     if request.method == 'POST':
        #         username = request.user.get_username()
        #         user_id = request.user.id
        #         form = AddEmailForm(request.POST)
        #         if form.is_valid():
        #             email = form.cleaned_data['email']
        #             password = form.cleaned_data['password']
        #             imap = form.cleaned_data['imap']
        #             smtp = form.cleaned_data['smtp']
        #             error = validate_input(email, password, imap, smtp)
        #             if error:
        #                 print(error)
        #                 return render(request, 'profiles/add_account.html', {'form': form, 'error': error})
        #             row = UserEmails(user_id=user_id, email=email, password=password, imap=imap, smtp=smtp)
        #             row.save()
        #             return redirect('/profile/')
        #     else:
        #         form = AddEmailForm()
        #     return render(request, 'profiles/add_account.html', {'form': form})

        # def detail(request, email_id):
        #     accounts = UserEmails.objects.filter(user_id=request.user.id)
        #     email = accounts[int(email_id)]
        #     account_row = UserEmails.objects.filter(email=email)
        #     password = account_row.values('password').get()['password']
        #     username = account_row.values('email').get()['email']
        #     imap = account_row.values('imap').get()['imap']
        #     if request.method == 'POST':
        #         boxes = request.POST.getlist('boxes')
        #         delete_mails(imap, username, password, boxes)
        #         headers = get_mailbox(username, password, imap)
        #         return render(request, 'profiles/detail.html', {'headers': headers, 'email_id': email_id})
        #     headers = get_mailbox(username, password, imap)
        #     return render(request, 'profiles/detail.html', {'headers': headers, 'email_id': email_id})

        # def email_body(request, email_id, message_id):
        #     try:
        #         accounts = UserEmails.objects.filter(user_id=request.user.id)
        #         email = accounts[int(email_id)]
        #         account_row = UserEmails.objects.filter(email=email)
        #         password = account_row.values('password').get()['password']
        #         username = account_row.values('email').get()['email']
        #         imap = account_row.values('imap').get()['imap']
        #         # print(username, password, imap)
        #         email_text = get_email_body(username, password, imap, message_id)
        #     except Exception as ex:
        #         print(ex)
        #         return redirect('/profile')
        #     return render(request, 'profiles/email_body.html', {'email_body': email_text})

        # def send_email(request, email_id):
        #     if request.method == 'POST':
        #         form = SendEmailForm(request.POST)
        #         if form.is_valid():
        #             accounts = UserEmails.objects.filter(user_id=request.user.id)
        #             email = accounts[int(email_id)]
        #             account_row = UserEmails.objects.filter(email=email)
        #             password = account_row.values('password').get()['password']
        #             username = account_row.values('email').get()['email']
        #             smtp = account_row.values('smtp').get()['smtp']
        #             to = [form.cleaned_data['to']]
        #             subject = form.cleaned_data['subject']
        #             message = form.cleaned_data['message']
        #             print(username, password)
        #             result = send(smtp, username, password, to, subject, message)
        #             form = SendEmailForm()
        #             if not result:
        #                 result = 'Message successfully sent!'
        #                 return render(request, 'profiles/send_email.html', {'form': form, 'result': result})
        #             return render(request, 'profiles/send_email.html', {'form': form, 'result': result})
        #     form = SendEmailForm()
        #     return render(request, 'profiles/send_email.html', {'form': form})

        # def settings(request):
        #     accounts = UserEmails.objects.filter(user_id=request.user.id)
        #     if request.method == 'POST':
        #         boxes = request.POST.getlist('boxes')
        #         for box in boxes:
        #             to_delete = accounts[int(box)]
        #             try:
        #                 UserEmails.objects.filter(user_id=request.user.id).filter(email=to_delete).delete()
        #             except Exception as ex:
        #                 print(ex)
        #         accounts = UserEmails.objects.filter(user_id=request.user.id)
        #         return render(request, 'profiles/settings.html', {'accounts': accounts})
        #     return render(request, 'profiles/settings.html', {'accounts': accounts})
