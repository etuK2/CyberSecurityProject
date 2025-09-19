from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from .models import Note
from .forms import NoteForm, RegisterForm


@login_required
def main_page(request):
    query = request.GET.get('q', '')
    notes = Note.objects.filter(user=request.user)

    if query:
        # OWASP A03:2021 - Injection (FLAW)
        # Flaw: Raw SQL with unsanitized user input
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT id FROM notes_note WHERE content LIKE '%{query}%'")
            note_ids = [row[0] for row in cursor.fetchall()]
        notes = Note.objects.filter(id__in=note_ids)
        # FIX: Uncomment the next line to restrict to user's own notes even when searching
        #notes = notes.filter(user=request.user)
        # FIX: Uncomment the next lines to use parameterized queries
        #with connection.cursor() as cursor:
        #     cursor.execute("SELECT id FROM notes_note WHERE content LIKE %s", [f'%{query}%'])
        #     note_ids = [row[0] for row in cursor.fetchall()]
        #notes = Note.objects.filter(id__in=note_ids, user=request.user)

    notes = notes.order_by('-created_at')

    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            return redirect('main_page')
    else:
        form = NoteForm()

    return render(request, 'notes/main_page.html', {
        'form': form, 'notes': notes, 'query': query
    })

@login_required
def search_notes(request):
    q = request.GET.get('q', '')

    sql = f"SELECT id, content FROM notes_note WHERE content LIKE '%{q}%'"
    with connection.cursor() as cursor:
        cursor.execute(sql)
        rows = cursor.fetchall()

    return render(request, 'notes/search_results.html', {
        'results': rows, 'query': q
    })

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'notes/register.html', {'form': form})


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        print("Attempting login for user:", username)

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('main_page')
        else:
            return render(request, 'notes/login.html', {'error': 'Invalid credentials'})

    return render(request, 'notes/login.html')
    

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def edit_note(request, note_id):
    # OWASP A01:2021 - Broken Access Control (FLAW)
    # Flaw: Any logged-in user can edit any note by ID
    note = get_object_or_404(Note, id=note_id)  # <-- FLAW: No user check
    # Fix: Uncomment the next lines to restrict editing to the note owner
    # if note.user != request.user:
    #     return redirect('main_page')
    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            return redirect('main_page')
    else:
        form = NoteForm(instance=note)
    return render(request, 'notes/edit_note.html', {'form': form, 'note': note})

@login_required
@csrf_exempt  # This disables CSRF protection (FLAW)
def delete_note(request, note_id):
    note = get_object_or_404(Note, id=note_id, user=request.user)
    if request.method == 'POST':
        note.delete()
        return redirect('main_page')
    return redirect('main_page')