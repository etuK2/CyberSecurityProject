from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('login/', auth_views.LoginView.as_view(template_name='notes/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('edit/<int:note_id>/', views.edit_note, name='edit_note'),  # Broken access control flaw
    path('delete/<int:note_id>/', views.delete_note, name='delete_note'),  # CSRF flaw
]
