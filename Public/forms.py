from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(max_length=255, min_length=4, required=True)
    password = forms.CharField(
        widget=forms.PasswordInput, max_length=255, min_length=8, required=True)
    remember_me = forms.CharField(widget=forms.CheckboxInput, required=False)


class JsonGeneratorForm(forms.Form):
    poll_id = forms.IntegerField(required=True)
    question_id = forms.IntegerField(required=True)
