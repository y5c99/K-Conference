from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    # Reviewer
    path('mine/',                           views.my_assigned_reviews, name='my_assigned'),
    path('<int:pk>/edit/',                  views.review_form,         name='edit'),
    path('<int:pk>/view/',                  views.view_review,         name='view_review'),
    path('<int:pk>/recuse/',                views.declare_conflict,    name='declare_conflict'),

    # Organiser
    path('submission/<int:submission_pk>/', views.submission_reviews,  name='submission_reviews'),
    path('submission/<int:submission_pk>/assign/',
         views.assign_reviewer, name='assign'),
    path('<int:pk>/remove/',                views.remove_assignment,   name='remove_assignment'),
]