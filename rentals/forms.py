from django import forms

from accounts.forms import StyledFormMixin

from .models import Property, RentalRequest, Review


class PropertyForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Property
        exclude = ("owner", "created_at", "updated_at")
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.style_fields()

    def clean_monthly_rent(self):
        rent = self.cleaned_data["monthly_rent"]
        if rent <= 0:
            raise forms.ValidationError("Rent must be greater than zero.")
        return rent

    def clean(self):
        data = super().clean()
        if data.get("property_type") == Property.Type.OFFICE and data.get("bedrooms", 0) > 20:
            self.add_error("bedrooms", "That seems too many for an office.")
        return data


class PropertySearchForm(StyledFormMixin, forms.Form):
    q = forms.CharField(required=False, label="Location", widget=forms.TextInput(attrs={"placeholder": "City or area"}))
    property_type = forms.ChoiceField(required=False, choices=[("", "All types")] + Property.Type.choices)
    min_rent = forms.DecimalField(required=False, min_value=0)
    max_rent = forms.DecimalField(required=False, min_value=0)

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.style_fields()

    def clean(self):
        data = super().clean()
        lo, hi = data.get("min_rent"), data.get("max_rent")
        if lo is not None and hi is not None and lo > hi:
            raise forms.ValidationError("Minimum rent cannot exceed maximum rent.")
        return data


class RentalRequestForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = RentalRequest
        fields = ("message",)
        widgets = {"message": forms.Textarea(attrs={"rows": 4, "placeholder": "Introduce yourself and say when you'd like to move in."})}

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.style_fields()

    def clean_message(self):
        msg = self.cleaned_data["message"].strip()
        if len(msg) < 10:
            raise forms.ValidationError("Please write at least 10 characters.")
        return msg


class ReviewForm(StyledFormMixin, forms.ModelForm):
    rating = forms.TypedChoiceField(choices=[(i, f"{i} / 5") for i in range(5, 0, -1)], coerce=int)

    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {"comment": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.style_fields()
