from django.urls import path
from . import views

app_name = 'conference'

urlpatterns = [
    # Public
    path('',                             views.conference_list,    name='list'),
    path('<int:pk>/',                    views.conference_detail,  name='detail'),

    # Organiser CRUD on conferences
    path('create/',                      views.conference_create,  name='create'),
    path('<int:pk>/edit/',               views.conference_edit,    name='edit'),
    path('<int:pk>/delete/',             views.conference_delete,  name='delete'),
    path('mine/',                        views.my_conferences,     name='mine'),

    # Tracks
    path('<int:conference_pk>/tracks/add/', views.track_create,    name='track_create'),
    path('tracks/<int:pk>/delete/',         views.track_delete,    name='track_delete'),

    # Sessions
    path('<int:conference_pk>/sessions/add/', views.session_create, name='session_create'),
    path('sessions/<int:pk>/delete/',         views.session_delete, name='session_delete'),

    # Participant registration
    path('<int:pk>/register/',           views.register_for_conference,
         name='register'),
    path('<int:pk>/unregister/',         views.unregister_from_conference,
         name='unregister'),
]