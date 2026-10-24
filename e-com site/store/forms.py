import re

from django import forms


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=200)
    phone = forms.CharField(max_length=20)
    email = forms.EmailField()
    address = forms.CharField(widget=forms.Textarea, max_length=500)
    city = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100)
    pin_code = forms.CharField(max_length=10)
    payment_method = forms.ChoiceField(choices=(('cod', 'Cash on Delivery'), ('demo', 'Mock payment (testing only)')))
    checkout_key = forms.UUIDField(widget=forms.HiddenInput)

    def clean_phone(self):
        value = re.sub(r'[\s()+-]', '', self.cleaned_data['phone'])
        if not value.isdigit() or not 10 <= len(value) <= 15:
            raise forms.ValidationError('Enter a valid phone number.')
        return value

    def clean_pin_code(self):
        value = self.cleaned_data['pin_code'].strip()
        if not re.fullmatch(r'\d{6}', value):
            raise forms.ValidationError('Enter a valid 6-digit PIN code.')
        return value


class NewsletterForm(forms.Form):
    email = forms.EmailField(max_length=254)
