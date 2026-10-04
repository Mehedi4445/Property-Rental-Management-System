from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class StyledFormMixin:
    def style_fields(self):
        for f in self.fields.values():
            w = f.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs["class"] = "form-check-input"
            elif isinstance(w, (forms.Select, forms.SelectMultiple)):
                w.attrs["class"] = "form-select"
            elif not isinstance(w, forms.FileInput):
                w.attrs["class"] = "form-control"
            else:
                w.attrs["class"] = "form-control"


class RegisterForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.Role.choices, label="I am a", widget=forms.RadioSelect, initial="tenant")

    class Meta:
        model = User
        fields = ("username", "email", "role", "phone", "password1", "password2")

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.style_fields()
        self.fields["role"].widget.attrs["class"] = "role-input"
        self.fields["username"].widget.attrs["placeholder"] = "Choose a username"
        self.fields["email"].widget.attrs["placeholder"] = "you@example.com"


class LoginForm(StyledFormMixin, AuthenticationForm):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.style_fields()
        self.fields["username"].widget.attrs.update(placeholder="Your username", autofocus=True)
        self.fields["password"].widget.attrs["placeholder"] = "Your password"


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "bio", "profile_image")
        widgets = {"bio": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.style_fields()
