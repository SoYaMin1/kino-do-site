from django.contrib import admin
from .models import (
    Genre, Movie, Review, Favorite, Watched, Cinema, Showtime,
    Ticket, Profile, Subscription, SubscriptionPayment
)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'rating', 'is_published', 'created_at')
    list_filter = ('is_published', 'genres', 'year')
    search_fields = ('title', 'director')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('genres',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'movie__title', 'text')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'added_at')
    search_fields = ('user__username', 'movie__title')


@admin.register(Watched)
class WatchedAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'watched_at')
    search_fields = ('user__username', 'movie__title')


@admin.register(Cinema)
class CinemaAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'address', 'phone', 'is_active')
    list_filter = ('city', 'is_active')
    search_fields = ('name', 'city', 'address')
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'city', 'address', 'phone', 'is_active')
        }),
        ('Медиа', {
            'fields': ('photo',),
            'description': 'Загрузите фотографию кинотеатра'
        }),
        ('2ГИС', {
            'fields': ('twogis_url',),
            'description': 'Вставьте ссылку на страницу кинотеатра в 2ГИС'
        }),
        ('Дополнительно', {
            'fields': ('description',)
        }),
    )

@admin.register(Showtime)
class ShowtimeAdmin(admin.ModelAdmin):
    list_display = ('movie', 'cinema', 'datetime', 'hall', 'price', 'total_seats')
    list_filter = ('cinema', 'hall', 'datetime')
    search_fields = ('movie__title',)
    date_hierarchy = 'datetime'


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'showtime', 'seat_number', 'status', 'card_last4', 'purchased_at')
    list_filter = ('status', 'purchased_at')
    search_fields = ('code', 'user__username', 'showtime__movie__title')
    readonly_fields = ('code', 'purchased_at')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'birth_date')
    search_fields = ('user__username', 'user__email', 'phone')
    list_select_related = ('user',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'started_at', 'expires_at', 'is_active')
    list_filter = ('plan', 'is_active')
    search_fields = ('user__username', 'user__email')


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'plan', 'amount', 'card_last4', 'paid_at')
    list_filter = ('plan', 'paid_at')
    search_fields = ('code', 'user__username')
    readonly_fields = ('code', 'paid_at')