from django.contrib import messages
from datetime import datetime
from django.db.models import Q
# from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect
from .models import Candidate, Interview, Interviewer, Slot
from .forms import InterviewScheduleForm, SlotForm

# check availability
def check_availability(slot_obj, interviewers, candidates):
    flag = False
    message_text = ""
    for i in interviewers:
        i_obj = Interviewer.objects.get(id=i)
        for j in i_obj.scheduled_slots.all():
            if slot_obj.is_overlapping(j):
                message_text += i_obj.interviewer_name + " "
                flag = True
    for i in candidates:
        i_obj = Candidate.objects.get(id=i)
        for j in i_obj.scheduled_slots.all():
            if slot_obj.is_overlapping(j):
                message_text += i_obj.candidate_name + " "
                flag = True
    return flag, message_text

# adding slot for the interview
def add_slot(slot_obj, interview_obj, interviewers, candidates):
    for i in interviewers:
        i_obj = Interviewer.objects.get(id=i)
        interview_obj.interviewers.add(i_obj)
        i_obj.scheduled_slots.add(slot_obj)
    for i in candidates:
        i_obj = Candidate.objects.get(id=i)
        interview_obj.candidates.add(i_obj)
        i_obj.scheduled_slots.add(slot_obj)

# interviews list function 
def interview_list(request):
    curr_date_obj = datetime.now().date()
    curr_time_obj = datetime.now().time()
    interviews = Interview.objects.filter(Q(slot__date__gt=curr_date_obj) | (Q(slot__date=curr_date_obj) & Q(slot__start_time__gte=curr_time_obj)))
    interviews = interviews.order_by('slot__date', 'slot__start_time')
    context = {"interviews": interviews}
    return render(request, 'task/interview_list.html', context=context)

# updating the interview slots of candidates and interviewers
def remove_slot(prev_slot_obj, interview_obj):
    for i in interview_obj.interviewers.all():
        i.scheduled_slots.remove(prev_slot_obj)
    for i in interview_obj.candidates.all():
        i.scheduled_slots.remove(prev_slot_obj)
    interview_obj.interviewers.clear()
    interview_obj.candidates.clear()


# scheduling the interview
def schedule_interview(request):
    if request.method == "POST":
        title = request.POST['title']
        interviewers = dict(request.POST)['interviewers']
        candidates = dict(request.POST)['candidates']
        date = request.POST['date']
        start_time = request.POST['start_time']
        end_time = request.POST['end_time']
        print(request.FILES, request.POST)
        interview_form = InterviewScheduleForm(request.POST, request.FILES)
        slot_form = SlotForm(request.POST, request.FILES)
        date_obj = datetime.strptime(request.POST['date'], "%Y-%m-%d").date()
        try:
            start_time_obj = datetime.strptime(start_time, "%H:%M").time()
        except:
            start_time_obj = datetime.strptime(start_time, "%H:%M:%S").time()
        try:
            end_time_obj = datetime.strptime(end_time, "%H:%M").time()
        except:
            end_time_obj = datetime.strptime(end_time, "%H:%M:%S").time()
        curr_date_obj = datetime.now().date()
        curr_time_obj = datetime.now().time()
        if not (start_time_obj <= end_time_obj and 
        (date_obj > curr_date_obj or (date_obj == curr_date_obj and start_time_obj >= curr_time_obj))):
            messages.error(request, 'Invalid Date, Start time or End time')
        else:
            slot_obj = Slot.objects.get_or_create(date=date, start_time=start_time, end_time=end_time)[0]
            flag, message_text = check_availability(slot_obj, interviewers, candidates)
            if flag:
                messages.error(request, message_text + 'are not available at this slot')
            else:
                try:
                    resume = request.FILES['resume']
                    interview_obj = Interview.objects.create(title=title, slot=slot_obj, resume=resume)
                except:    
                    interview_obj = Interview.objects.create(title=title, slot=slot_obj)
                add_slot(slot_obj, interview_obj, interviewers, candidates)
                interview_obj.save()
                return redirect('task:interview-scheduled')
    else:
        interview_form = InterviewScheduleForm()
        slot_form = SlotForm()
    return render(request, 'task/index.html', {'interview_form': interview_form, 'slot_form': slot_form})

#rescheduling the interview
def reschedule_interview(request, pk):
    interview_obj = Interview.objects.get(id=pk)
    prev_slot_obj = interview_obj.slot
    if request.method == "POST":
        title = request.POST['title']
        interviewers = dict(request.POST)['interviewers']
        candidates = dict(request.POST)['candidates']
        date = request.POST['date']
        start_time = request.POST['start_time']
        end_time = request.POST['end_time']
        interview_form = InterviewScheduleForm(request.POST, request.FILES)
        slot_form = SlotForm(request.POST, request.FILES)
        date_obj = datetime.strptime(request.POST['date'], "%Y-%m-%d").date()
        try:
            start_time_obj = datetime.strptime(start_time, "%H:%M").time()
        except:
            start_time_obj = datetime.strptime(start_time, "%H:%M:%S").time()
        try:
            end_time_obj = datetime.strptime(end_time, "%H:%M").time()
        except:
            end_time_obj = datetime.strptime(end_time, "%H:%M:%S").time()
        curr_date_obj = datetime.now().date()
        curr_time_obj = datetime.now().time()
        if not (start_time_obj <= end_time_obj and 
        (date_obj > curr_date_obj or (date_obj == curr_date_obj and start_time_obj >= curr_time_obj))):
            messages.error(request, 'Invalid Date, Start time or End time')
        else:
            slot_obj = Slot.objects.get_or_create(date=date, start_time=start_time, end_time=end_time)[0]
            remove_slot(prev_slot_obj, interview_obj)
            flag, message_text = check_availability(slot_obj, interviewers, candidates)
            if flag:
                messages.error(request, message_text + 'are not available at this slot')
            else:
                try:
                    resume = request.FILES['resume']
                    interview_obj.resume = resume
                except:
                    pass
                interview_obj.title = title
                interview_obj.slot = slot_obj
                add_slot(slot_obj, interview_obj, interviewers, candidates)
                interview_obj.save()
                return redirect('task:interview-rescheduled')
    else:
        interview_form = InterviewScheduleForm(instance=interview_obj)
        slot_form = SlotForm(instance=prev_slot_obj)
    return render(request, 'task/interview_update.html', {'interview_form': interview_form, 'slot_form': slot_form})    


# interview scheduled function
def interview_scheduled(request):
    return render(request, 'task/interview_scheduled.html')


# interview rescheduled function
def interview_rescheduled(request):
    return render(request, 'task/interview_rescheduled.html')

 