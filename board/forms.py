from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Post, Category, POST_MAX_LENGTH


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Used for sign-in and, if needed, contacting you about a post.")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class PostForm(forms.ModelForm):
    body = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6, "maxlength": POST_MAX_LENGTH}),
        max_length=POST_MAX_LENGTH,
        help_text=f"Up to {POST_MAX_LENGTH} characters.",
    )

    class Meta:
        model = Post
        fields = ("category", "body")
