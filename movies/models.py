from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import uuid


class Genre(models.Model):
    name = models.CharField('Название', max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('movies:genre_detail', args=[self.slug])


class Movie(models.Model):
    title = models.CharField('Название', max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField('Описание')
    poster = models.ImageField('Постер', upload_to='posters/')
    year = models.PositiveIntegerField('Год выпуска')
    country = models.CharField('Страна', max_length=100)
    director = models.CharField('Режиссёр', max_length=255)
    duration = models.PositiveIntegerField('Длительность (мин)', default=0)
    video_url = models.URLField('Ссылка на видео', blank=True)
    genres = models.ManyToManyField(Genre, related_name='movies', verbose_name='Жанры')
    rating = models.DecimalField('Рейтинг', max_digits=3, decimal_places=1, default=0)
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)
    is_published = models.BooleanField('Опубликовано', default=True)

    class Meta:
        verbose_name = 'Фильм'
        verbose_name_plural = 'Фильмы'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.year})'

    def get_absolute_url(self):
        return reverse('movies:movie_detail', args=[self.slug])


class Review(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    text = models.TextField('Отзыв')
    rating = models.PositiveIntegerField(
        'Оценка',
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
        unique_together = ('movie', 'user')

    def __str__(self):
        name = self.user.username if self.user else 'Гость'
        return f'{name} — {self.movie.title} ({self.rating}/10)'


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='favorited_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ('user', 'movie')
        ordering = ['-added_at']

    def __str__(self):
        return f'{self.user.username} ❤ {self.movie.title}'


class Watched(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watched')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='watched_by')
    watched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Просмотренный фильм'
        verbose_name_plural = 'Просмотренные фильмы'
        unique_together = ('user', 'movie')
        ordering = ['-watched_at']

    def __str__(self):
        return f'{self.user.username} 👁 {self.movie.title}'


# ============ КИНОТЕАТРЫ ============

class Cinema(models.Model):
    name = models.CharField('Название', max_length=255)
    city = models.CharField('Город', max_length=100)
    address = models.CharField('Адрес', max_length=255)
    phone = models.CharField('Телефон', max_length=30, blank=True)
    photo = models.ImageField(
        'Фото кинотеатра',
        upload_to='cinemas/',
        blank=True,
        null=True,
        help_text='Загрузите фотографию здания или зала'
    )
    twogis_url = models.URLField(
        'Ссылка на 2ГИС',
        blank=True,
        help_text='Вставьте ссылку на кинотеатр в 2ГИС (например: https://2gis.kg/bishkek/firm/...)'
    )
    description = models.TextField('Описание', blank=True)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Кинотеатр'
        verbose_name_plural = 'Кинотеатры'
        ordering = ['city', 'name']

    def __str__(self):
        return f'{self.name} ({self.city})'


class Showtime(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='showtimes')
    cinema = models.ForeignKey(Cinema, on_delete=models.CASCADE, related_name='showtimes')
    datetime = models.DateTimeField('Дата и время')
    price = models.DecimalField('Цена', max_digits=8, decimal_places=2, default=500)
    hall = models.CharField('Зал', max_length=50, default='Зал 1')
    total_seats = models.PositiveIntegerField('Всего мест', default=50)

    class Meta:
        verbose_name = 'Сеанс'
        verbose_name_plural = 'Сеансы'
        ordering = ['datetime']

    def __str__(self):
        return f'{self.movie.title} — {self.cinema.name} ({self.datetime:%d.%m %H:%M})'

    @property
    def booked_seats(self):
        return list(self.tickets.exclude(status='cancelled').values_list('seat_number', flat=True))

    @property
    def available_seats(self):
        return self.total_seats - len(self.booked_seats)


# ============ ПОДПИСКА ============

class Subscription(models.Model):
    PLAN_CHOICES = [
        ('basic', 'Базовая — 500 сом/мес'),
        ('premium', 'Премиум — 1200 сом/мес'),
        ('vip', 'VIP — 2500 сом/мес'),
    ]
    PLAN_PRICES = {
        'basic': 500,
        'premium': 1200,
        'vip': 2500,
    }
    PLAN_DAYS = {
        'basic': 30,
        'premium': 30,
        'vip': 30,
    }

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField('Тариф', max_length=20, choices=PLAN_CHOICES, default='basic')
    started_at = models.DateTimeField('Начало', auto_now_add=True)
    expires_at = models.DateTimeField('Истекает', null=True, blank=True)
    is_active = models.BooleanField('Активна', default=True)

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user.username} — {self.get_plan_display()}'

    @property
    def is_valid(self):
        return self.is_active and self.expires_at and self.expires_at > timezone.now()

    @property
    def days_left(self):
        if self.expires_at:
            delta = self.expires_at - timezone.now()
            return max(0, delta.days)
        return 0

    def activate(self, plan):
        """Активировать или продлить подписку"""
        self.plan = plan
        days = self.PLAN_DAYS.get(plan, 30)
        now = timezone.now()
        # Если подписка ещё активна — продлеваем от текущей даты окончания
        if self.expires_at and self.expires_at > now:
            self.expires_at = self.expires_at + timedelta(days=days)
        else:
            self.expires_at = now + timedelta(days=days)
            self.started_at = now
        self.is_active = True
        self.save()


class SubscriptionPayment(models.Model):
    """История оплат подписок (симуляция)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscription_payments')
    plan = models.CharField('Тариф', max_length=20)
    amount = models.DecimalField('Сумма', max_digits=8, decimal_places=2)
    card_last4 = models.CharField('Последние 4 цифры', max_length=4)
    paid_at = models.DateTimeField(auto_now_add=True)
    code = models.CharField('Код транзакции', max_length=20, unique=True, blank=True)

    class Meta:
        verbose_name = 'Оплата подписки'
        verbose_name_plural = 'Оплаты подписок'
        ordering = ['-paid_at']

    def __str__(self):
        return f'{self.user.username} — {self.plan} — {self.amount} сом'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = 'SUB-' + uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)


# ============ БИЛЕТЫ ============

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('booked', 'Забронирован'),
        ('paid', 'Оплачен'),
        ('cancelled', 'Отменён'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    showtime = models.ForeignKey(Showtime, on_delete=models.CASCADE, related_name='tickets')
    seat_number = models.PositiveIntegerField('Место')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='booked')
    code = models.CharField('Код билета', max_length=20, unique=True, blank=True)
    card_last4 = models.CharField('Последние 4 цифры карты', max_length=4, blank=True)
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Билет'
        verbose_name_plural = 'Билеты'
        unique_together = ('showtime', 'seat_number')
        ordering = ['-purchased_at']

    def __str__(self):
        return f'Билет #{self.seat_number} — {self.showtime}'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = uuid.uuid4().hex[:10].upper()
        super().save(*args, **kwargs)


# ============ ПРОФИЛЬ ============

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    birth_date = models.DateField('Дата рождения', blank=True, null=True)
    bio = models.TextField('О себе', max_length=500, blank=True)

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'Профиль {self.user.username}'


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()