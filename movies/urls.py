from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    # Каталог
    path('', views.movie_list, name='movie_list'),
    path('movie/<slug:slug>/', views.movie_detail, name='movie_detail'),
    path('genre/<slug:slug>/', views.genre_detail, name='genre_detail'),
    path('search/', views.movie_search, name='movie_search'),
    path('showtimes/', views.showtimes_list, name='showtimes'),

    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Профиль
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('my/reviews/', views.my_reviews, name='my_reviews'),
    path('my/favorites/', views.favorites_list, name='favorites'),
    path('my/watched/', views.watched_list, name='watched'),

    # Отзывы
    path('movie/<slug:slug>/review/', views.add_review, name='add_review'),
    path('review/<int:pk>/delete/', views.delete_review, name='delete_review'),

    # Избранное / Просмотренные
    path('movie/<slug:slug>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('movie/<slug:slug>/watched/', views.toggle_watched, name='toggle_watched'),

    # Кинотеатры
    path('cinemas/', views.cinema_list, name='cinema_list'),
    path('cinema/<int:pk>/', views.cinema_detail, name='cinema_detail'),

    # Билеты
    path('movie/<slug:slug>/buy/', views.movie_buy_ticket, name='movie_buy_ticket'),
    path('buy/<int:showtime_id>/', views.buy_ticket, name='buy_ticket'),
    path('my/tickets/', views.my_tickets, name='my_tickets'),
    path('ticket/<int:pk>/cancel/', views.cancel_ticket, name='cancel_ticket'),

    # Подписка
    path('subscription/', views.subscription_view, name='subscription'),
    path('subscription/pay/', views.subscription_pay, name='subscription_pay'),
]