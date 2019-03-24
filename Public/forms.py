from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(max_length=255, min_length=4, required=True)
    password = forms.CharField(
        widget=forms.PasswordInput, max_length=255, min_length=8, required=True)
    remember_me = forms.CharField(widget=forms.CheckboxInput, required=False)


class PollForm(forms.Form):
    pass
