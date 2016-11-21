#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.contrib.auth import login
from sistemaDeCalificaciones.models import *

class LoginForm(forms.Form):
    username = forms.CharField(label="Usuario", max_length=64)
    password = forms.CharField(label='Clave', widget=forms.PasswordInput, max_length=64)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        try:
            user = User.objects.get(username=username)
            if not check_password(password, user.password):
                raise forms.ValidationError('Password incorrecto')
        except User.DoesNotExist:
            raise forms.ValidationError("No existe el usuario")
        return user


    def is_valid(self):
        valid = super(LoginForm, self).is_valid()
        if not valid:
            return valid
        return True


class ChangePasswordForm(forms.Form):
    password_1 = forms.CharField(label='Clave 1', widget=forms.PasswordInput, max_length=64)
    password_2 = forms.CharField(label='Clave 2', widget=forms.PasswordInput, max_length=64)

    def clean(self):
        password_1 = self.cleaned_data.get('password_1')
        password_2 = self.cleaned_data.get('password_2')
        if password_1 != password_2:
            raise forms.ValidationError('No coinciden las contraseñas')
        return password_1


    def is_valid(self):
        valid = super(ChangePasswordForm, self).is_valid()
        if not valid:
            return valid
        return True