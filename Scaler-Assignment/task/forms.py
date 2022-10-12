from .models import *
from django.contrib.admin.widgets import AdminDateWidget, AdminTimeWidget
from django import forms
from django.db.models.fields import DateField

class InterviewScheduleForm(forms.ModelForm):

    class Meta:
        model = Interview
        fields = ('title', 'interviewers', 'candidates', 'resume')

    def __init__(self, *args, **kwargs):
        super(InterviewScheduleForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['resume'].label = 'Resume'

class DateInput(forms.DateInput):
    input_type = 'date'

class TimeInput(forms.TimeInput):
    input_type = 'time'

class SlotForm(forms.ModelForm):

    class Meta:
        model = Slot
        fields = ('date', 'start_time', 'end_time')
        widgets = {
            'date': DateInput(),
            'start_time': TimeInput(),
            'end_time': TimeInput(),
        }
    