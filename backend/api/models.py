from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator, RegexValidator
from django.utils import timezone
import uuid


# Create your models here.
def upload_images(instance, filename):
    path = f'api/{instance.bio}' 
    extension = filename.split('.')[-1]
    if extension:
        path = path + '.' + extension
        return path


class User(models.Model):
    """
    Application profile linked to a Supabase Auth identity.
    Supabase Auth owns credentials; this model only maps public.profiles.
    """
    id = models.UUIDField(primary_key=True, editable=False)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=254)
    first_name = models.CharField(max_length=100, validators=[MinLengthValidator(2)], blank=True)
    last_name = models.CharField(max_length=100, validators=[MinLengthValidator(2)], blank=True)
    directory_status1 = models.CharField(max_length=100, blank=True, null=True)
    bio = models.CharField(max_length=500, blank=True, default="")
    profession = models.CharField(max_length=100, blank=True, default="")
    prof_initial = models.CharField(max_length=100, blank=True, default="")
    program = models.CharField(max_length=100, blank=True, default="")
    service_name = models.CharField(max_length=100, blank=True, default="")
    agreement = models.BooleanField(default=False)
    market_agreement = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    cell = models.CharField(max_length=20, blank=True, default="")
    location = models.CharField(max_length=100, blank=True, default="")
    website = models.TextField(blank=True, default="")
    profile_image = models.ImageField(upload_to=upload_images, null=True, blank=True, db_column="profile_image_path")
    coverImage = models.ImageField(upload_to=upload_images, null=True, blank=True, db_column="cover_image_path")
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)
    notification_preferences = models.JSONField(default=dict)
    privacy_settings = models.JSONField(default=dict)
    theme_preference = models.CharField(max_length=10, choices=[("light", "Light"), ("dark", "Dark"), ("auto", "Auto")], default="auto")
    language = models.CharField(max_length=10, default="en")
    timezone = models.CharField(max_length=50, default="UTC")
    total_posts = models.PositiveIntegerField(default=0)
    total_followers = models.PositiveIntegerField(default=0)
    total_following = models.PositiveIntegerField(default=0)
    reputation_score = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(blank=True, default="")
    suspension_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "profiles"
        managed = False

    def __str__(self):
        return f"{self.username} ({self.first_name} {self.last_name})"

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_suspended_now(self):
        if self.is_suspended and self.suspension_until:
            return timezone.now() < self.suspension_until
        return self.is_suspended

    def has_perm(self, perm, obj=None):
        return self.is_active and self.is_staff

    def has_module_perms(self, app_label):
        return self.is_active and self.is_staff

class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # Privacy settings
    profile_visibility = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('friends', 'Friends Only'),
            ('private', 'Private')
        ],
        default='public'
    )
    show_online_status = models.BooleanField(default=True)
    allow_messages_from = models.CharField(
        max_length=20,
        choices=[
            ('everyone', 'Everyone'),
            ('friends', 'Friends Only'),
            ('none', 'None')
        ],
        default='everyone'
    )
    
    # Content preferences
    auto_play_videos = models.BooleanField(default=True)
    show_trending_content = models.BooleanField(default=True)
    content_language = models.CharField(max_length=10, default='en')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_preferences'


class UserAnalytics(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='analytics')
    
    # Engagement metrics
    total_logins = models.PositiveIntegerField(default=0)
    last_login = models.DateTimeField(null=True, blank=True)
    total_session_time = models.PositiveIntegerField(default=0)  # in minutes
    average_session_time = models.FloatField(default=0)
    
    # Content metrics
    posts_created = models.PositiveIntegerField(default=0)
    comments_made = models.PositiveIntegerField(default=0)
    likes_given = models.PositiveIntegerField(default=0)
    likes_received = models.PositiveIntegerField(default=0)
    
    # Social metrics
    connections_made = models.PositiveIntegerField(default=0)
    messages_sent = models.PositiveIntegerField(default=0)
    messages_received = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_analytics'


class CommunityDirectory(models.Model):
    username = models.CharField(max_length=100, unique=False)
    directory_status1 = models.CharField(max_length=100)
    directory_status2 = models.CharField(max_length=100)
    directory_status3 = models.CharField(max_length=100)
    public = models.BooleanField(default=False)
    agreement = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    email = models.CharField(max_length=100)
    bio = models.TextField(max_length=500, blank=True)
    code = models.CharField(max_length=100, unique=True)
    
    # Enhanced fields
    category = models.CharField(max_length=50, blank=True)
    tags = models.JSONField(default=list)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    contact_info = models.JSONField(default=dict)
    
    # Social metrics
    member_count = models.PositiveIntegerField(default=0)
    post_count = models.PositiveIntegerField(default=0)
    engagement_rate = models.FloatField(default=0)
    
    creator = models.ForeignKey(
        User,
        related_name='created_communities',
        on_delete=models.CASCADE
    )
    followers = models.ManyToManyField(
        User,
        related_name='followed_communities',
    )
    moderators = models.ManyToManyField(
        User,
        related_name='moderated_communities',
    )
    
    profile_image = models.ImageField(
        upload_to=upload_images,
        null=True,
        blank=True
    )
    cover_image = models.ImageField(
        upload_to=upload_images,
        null=True,
        blank=True
    )
    
    # Status and visibility
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'community_directories'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['created']),
        ]
    
    def __str__(self):
        return f"{self.directory_status1} : {self.username}"
    
    @property
    def full_name(self):
        return f"{self.directory_status1} {self.directory_status2} {self.directory_status3}"


class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('file', 'File'),
        ('location', 'Location'),
        ('contact', 'Contact'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    content = models.TextField()
    media_url = models.URLField(blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    
    # Message status
    is_read = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    # Reactions
    reactions = models.JSONField(default=dict)
    
    # Reply to another message
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'messages'
        indexes = [
            models.Index(fields=['sender', 'receiver']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_read']),
        ]
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username}: {self.content[:50]}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('message', 'Message'),
        ('mention', 'Mention'),
        ('system', 'System'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Related content
    related_post_id = models.PositiveIntegerField(null=True, blank=True)
    related_comment_id = models.PositiveIntegerField(null=True, blank=True)
    related_user_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    
    # Additional data
    data = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_at']),
            models.Index(fields=['notification_type']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.recipient.username}: {self.title}"


class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_id = models.CharField(max_length=100, unique=False)
    device_info = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'user_sessions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_id']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.session_id}"
    
