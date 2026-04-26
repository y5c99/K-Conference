from django.urls import path
from . import views

app_name = 'submissions'

urlpatterns = [
    # Author pages
    path('mine/',                      views.my_submissions,        name='my_submissions'),
    path('new/',                       views.submission_create,     name='create'),
    path('<int:pk>/',                  views.submission_detail,     name='detail'),
    path('<int:pk>/edit/',             views.submission_edit,       name='edit'),
    path('<int:pk>/upload/',           views.submission_upload_file, name='upload_file'),
    path('<int:pk>/submit/',           views.submission_finalise,   name='finalise'),
    path('<int:pk>/withdraw/',         views.submission_withdraw,   name='withdraw'),

    # Secure file download
    path('files/<int:file_pk>/download/', views.download_file,      name='download_file'),

    # Organiser views
    path('conference/<int:conference_pk>/all/',
         views.organiser_submission_list, name='organiser_list'),
    path('conference/<int:conference_pk>/decisions/',
         views.decisions_dashboard, name='decisions_dashboard'),
    path('<int:pk>/decide/',
         views.make_decision, name='make_decision'),
]