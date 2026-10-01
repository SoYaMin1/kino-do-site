from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import (
    Movie, Genre, Review, Favorite, Watched, Cinema, Showtime,
    Ticket, Profile, Subscription, SubscriptionPayment
)
from .forms import (
    ReviewForm, RegisterForm, LoginForm, UserForm, ProfileForm,
    TicketPaymentForm, SubscriptionForm
)


# ============ АВТОРИЗАЦИЯ ============

def register_view(request):
    if request.user.is_authenticated:
        return redirect('movies:movie_list')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('movies:movie_list')
    else:
        form = RegisterForm()
    return render(request, 'movies/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('movies:movie_list')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f'С возвращением, {user.username}!')
                next_url = request.GET.get('next') or 'movies:movie_list'
                return redirect(next_url)
    else:
        form = LoginForm()
    return render(request, 'movies/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из аккаунта')
    return redirect('movies:movie_list')


# ============ КАТАЛОГ ============

def movie_list(request):
    movies = Movie.objects.filter(is_published=True)

    query = request.GET.get('q')
    if query:
        movies = movies.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(director__icontains=query)
        )

    genre_slug = request.GET.get('genre')
    if genre_slug:
        movies = movies.filter(genres__slug=genre_slug)

    sort = request.GET.get('sort', '-created_at')
    sort_options = {
        '-created_at': 'Новые',
        'title': 'А-Я',
        '-title': 'Я-А',
        '-rating': 'Рейтинг ↓',
        'rating': 'Рейтинг ↑',
        '-year': 'Год ↓',
        'year': 'Год ↑',
    }
    if sort not in sort_options:
        sort = '-created_at'
    movies = movies.order_by(sort)

    featured = Movie.objects.filter(is_published=True).order_by('-created_at')[:5]

    paginator = Paginator(movies, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'genres': Genre.objects.all(),
        'query': query or '',
        'current_genre': genre_slug or '',
        'current_sort': sort,
        'sort_options': sort_options,
        'featured_movies': featured,
    }
    return render(request, 'movies/movie_list.html', context)


def movie_detail(request, slug):
    movie = get_object_or_404(Movie, slug=slug, is_published=True)
    reviews = movie.reviews.select_related('user', 'user__profile').all()
    form = ReviewForm()

    can_review = (
        request.user.is_authenticated and
        not Review.objects.filter(movie=movie, user=request.user).exists()
    )

    is_favorite = False
    is_watched = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, movie=movie).exists()
        is_watched = Watched.objects.filter(user=request.user, movie=movie).exists()

    similar = Movie.objects.filter(
        genres__in=movie.genres.all()
    ).exclude(id=movie.id).distinct()[:6]

    showtimes = movie.showtimes.filter(
        datetime__gte=timezone.now(),
        cinema__is_active=True
    ).select_related('cinema').order_by('datetime')

    # Группируем сеансы по кинотеатрам
    showtimes_by_cinema = {}
    for st in showtimes:
        showtimes_by_cinema.setdefault(st.cinema, []).append(st)

    context = {
        'movie': movie,
        'reviews': reviews,
        'form': form,
        'can_review': can_review,
        'similar_movies': similar,
        'is_favorite': is_favorite,
        'is_watched': is_watched,
        'showtimes_by_cinema': showtimes_by_cinema,
    }
    return render(request, 'movies/movie_detail.html', context)


def genre_detail(request, slug):
    genre = get_object_or_404(Genre, slug=slug)
    movies = genre.movies.filter(is_published=True)
    paginator = Paginator(movies, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = {
        'genre': genre,
        'page_obj': page_obj,
        'genres': Genre.objects.all(),
    }
    return render(request, 'movies/genre_detail.html', context)


def movie_search(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        results = Movie.objects.filter(title__icontains=query, is_published=True)[:10]
    return render(request, 'movies/search_results.html', {'results': results, 'query': query})


# ============ ОТЗЫВЫ ============

@login_required
def add_review(request, slug):
    movie = get_object_or_404(Movie, slug=slug, is_published=True)
    if request.method == 'POST':
        if Review.objects.filter(movie=movie, user=request.user).exists():
            messages.warning(request, 'Вы уже оставляли отзыв к этому фильму')
            return redirect('movies:movie_detail', slug=movie.slug)
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.movie = movie
            review.user = request.user
            review.save()
            avg = movie.reviews.aggregate(Avg('rating'))['rating__avg']
            movie.rating = round(avg, 1)
            movie.save()
            messages.success(request, 'Спасибо за отзыв!')
    return redirect('movies:movie_detail', slug=movie.slug)


@login_required
def delete_review(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)
    movie = review.movie
    review.delete()
    avg = movie.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    movie.rating = round(avg, 1)
    movie.save()
    messages.info(request, 'Отзыв удалён')
    return redirect('movies:my_reviews')


# ============ ИЗБРАННОЕ / ПРОСМОТРЕННОЕ ============

@login_required
def toggle_favorite(request, slug):
    movie = get_object_or_404(Movie, slug=slug)
    fav, created = Favorite.objects.get_or_create(user=request.user, movie=movie)
    if not created:
        fav.delete()
        messages.info(request, f'«{movie.title}» удалён из избранного')
    else:
        messages.success(request, f'«{movie.title}» добавлен в избранное ❤')
    return redirect(request.META.get('HTTP_REFERER', movie.get_absolute_url()))


@login_required
def toggle_watched(request, slug):
    movie = get_object_or_404(Movie, slug=slug)
    w, created = Watched.objects.get_or_create(user=request.user, movie=movie)
    if not created:
        w.delete()
        messages.info(request, f'«{movie.title}» убран из просмотренных')
    else:
        messages.success(request, f'«{movie.title}» отмечен как просмотренный 👁')
    return redirect(request.META.get('HTTP_REFERER', movie.get_absolute_url()))


@login_required
def favorites_list(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('movie')
    return render(request, 'movies/favorites.html', {'favorites': favorites})


@login_required
def watched_list(request):
    watched = Watched.objects.filter(user=request.user).select_related('movie')
    return render(request, 'movies/watched.html', {'watched': watched})


@login_required
def my_reviews(request):
    reviews = Review.objects.filter(user=request.user).select_related('movie')
    return render(request, 'movies/my_reviews.html', {'reviews': reviews})


# ============ ПРОФИЛЬ ============

@login_required
def profile(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)
    subscription, _ = Subscription.objects.get_or_create(user=request.user)

    reviews_count = Review.objects.filter(user=request.user).count()
    favorites_count = Favorite.objects.filter(user=request.user).count()
    watched_count = Watched.objects.filter(user=request.user).count()
    tickets_count = Ticket.objects.filter(user=request.user).exclude(status='cancelled').count()

    context = {
        'profile_obj': profile_obj,
        'subscription': subscription,
        'reviews_count': reviews_count,
        'favorites_count': favorites_count,
        'watched_count': watched_count,
        'tickets_count': tickets_count,
        'recent_reviews': Review.objects.filter(user=request.user).select_related('movie')[:5],
        'recent_favorites': Favorite.objects.filter(user=request.user).select_related('movie')[:6],
    }
    return render(request, 'movies/profile.html', context)


@login_required
def edit_profile(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile_obj)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Профиль обновлён ✅')
            return redirect('movies:profile')
        else:
            messages.error(request, 'Исправьте ошибки в форме')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=profile_obj)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile_obj': profile_obj,
    }
    return render(request, 'movies/edit_profile.html', context)


# ============ КИНОТЕАТРЫ ============

def cinema_list(request):
    cinemas = Cinema.objects.filter(is_active=True)
    city = request.GET.get('city')
    if city:
        cinemas = cinemas.filter(city=city)

    cities = Cinema.objects.filter(is_active=True).values_list('city', flat=True).distinct()

    context = {
        'cinemas': cinemas,
        'cities': cities,
        'current_city': city or '',
    }
    return render(request, 'movies/cinema_list.html', context)


def cinema_detail(request, pk):
    cinema = get_object_or_404(Cinema, pk=pk, is_active=True)
    showtimes = cinema.showtimes.filter(
        datetime__gte=timezone.now()
    ).select_related('movie').order_by('datetime')

    # Группируем по датам
    showtimes_by_date = {}
    for st in showtimes:
        key = st.datetime.date()
        showtimes_by_date.setdefault(key, []).append(st)

    context = {
        'cinema': cinema,
        'showtimes_by_date': showtimes_by_date,
    }
    return render(request, 'movies/cinema_detail.html', context)


def showtimes_list(request):
    showtimes = Showtime.objects.filter(
        datetime__gte=timezone.now(),
        cinema__is_active=True
    ).select_related('movie', 'cinema').order_by('datetime')
    return render(request, 'movies/showtimes.html', {'showtimes': showtimes})


# ============ ПОКУПКА БИЛЕТА (с оплатой) ============

@login_required
def buy_ticket(request, showtime_id):
    showtime = get_object_or_404(Showtime, pk=showtime_id)

    if request.method == 'POST':
        form = TicketPaymentForm(request.POST)
        seat_number = request.POST.get('seat_number')

        # Валидация места
        seat_error = None
        try:
            seat = int(seat_number)
            if seat < 1 or seat > showtime.total_seats:
                seat_error = f'Место должно быть от 1 до {showtime.total_seats}'
            elif seat in showtime.booked_seats:
                seat_error = 'Это место уже занято'
        except (TypeError, ValueError):
            seat_error = 'Выберите место'

        if seat_error:
            messages.error(request, seat_error)
        elif form.is_valid():
            ticket = Ticket.objects.create(
                user=request.user,
                showtime=showtime,
                seat_number=seat,
                status='paid',
                card_last4=form.last4,
            )
            messages.success(
                request,
                f'🎟️ Билет куплен! Код: {ticket.code}. '
                f'Место {seat}, карта ****{form.last4}'
            )
            return redirect('movies:my_tickets')
    else:
        form = TicketPaymentForm()

    context = {
        'showtime': showtime,
        'form': form,
        'booked_seats': showtime.booked_seats,
    }
    return render(request, 'movies/buy_ticket.html', context)


@login_required
def movie_buy_ticket(request, slug):
    """Страница покупки билета на конкретный фильм — список сеансов"""
    movie = get_object_or_404(Movie, slug=slug, is_published=True)
    showtimes = movie.showtimes.filter(
        datetime__gte=timezone.now(),
        cinema__is_active=True
    ).select_related('cinema').order_by('datetime')

    # Группировка по кинотеатрам
    by_cinema = {}
    for st in showtimes:
        by_cinema.setdefault(st.cinema, []).append(st)

    context = {
        'movie': movie,
        'by_cinema': by_cinema,
    }
    return render(request, 'movies/movie_buy_ticket.html', context)


@login_required
def my_tickets(request):
    tickets = Ticket.objects.filter(user=request.user).select_related(
        'showtime', 'showtime__movie', 'showtime__cinema'
    )
    return render(request, 'movies/my_tickets.html', {'tickets': tickets})


@login_required
def cancel_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk, user=request.user)
    if ticket.status != 'cancelled':
        ticket.status = 'cancelled'
        ticket.save()
        messages.info(request, f'Билет на «{ticket.showtime.movie.title}» отменён')
    return redirect('movies:my_tickets')


# ============ ПОДПИСКА ============

@login_required
def subscription_view(request):
    subscription, _ = Subscription.objects.get_or_create(user=request.user)
    payments = SubscriptionPayment.objects.filter(user=request.user)[:10]

    context = {
        'subscription': subscription,
        'plans': Subscription.PLAN_CHOICES,
        'prices': Subscription.PLAN_PRICES,
        'payments': payments,
    }
    return render(request, 'movies/subscription.html', context)


@login_required
def subscription_pay(request):
    """Симуляция оплаты подписки"""
    subscription, _ = Subscription.objects.get_or_create(user=request.user)
    plan = request.GET.get('plan') or request.POST.get('plan') or 'basic'

    if plan not in Subscription.PLAN_PRICES:
        plan = 'basic'

    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            selected_plan = form.cleaned_data['plan']
            amount = Subscription.PLAN_PRICES.get(selected_plan, 500)

            # Симуляция успешной оплаты — просто сохраняем запись
            payment = SubscriptionPayment.objects.create(
                user=request.user,
                plan=selected_plan,
                amount=amount,
                card_last4=form.last4,
            )

            # Активируем / продлеваем подписку
            subscription.activate(selected_plan)

            messages.success(
                request,
                f'✅ Подписка «{subscription.get_plan_display()}» активирована! '
                f'Транзакция: {payment.code}. Действует до {subscription.expires_at:%d.%m.%Y}'
            )
            return redirect('movies:subscription')
    else:
        form = SubscriptionForm(initial={'plan': plan})

    context = {
        'form': form,
        'plan': plan,
        'plan_label': dict(Subscription.PLAN_CHOICES).get(plan, 'Базовая'),
        'price': Subscription.PLAN_PRICES.get(plan, 500),
        'subscription': subscription,
    }
    return render(request, 'movies/subscription_pay.html', context)