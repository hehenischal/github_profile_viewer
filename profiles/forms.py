from django import forms
from .models import BookmarkedProfile


class BookmarkNoteForm(forms.ModelForm):
    class Meta:
        model = BookmarkedProfile
        fields = ["note"]
        widgets = {
            "note": forms.Textarea(attrs={
                "class": "form-control form-control-sm gh-input",
                "rows": 2,
                "placeholder": "Add personal note about this profile...",
            }),
        }
        labels = {
            "note": "",
        }
