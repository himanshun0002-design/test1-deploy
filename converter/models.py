from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import mongoengine as me
from mongoengine import Document, StringField, IntField, FloatField, DateTimeField, ReferenceField, BooleanField
import os

class VideoConversion(Document):
    """MongoDB model to track video to audio conversions"""
    
    CONVERSION_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # User reference (using Django User model ID)
    user_id = IntField(null=True, blank=True)
    
    # File information
    original_filename = StringField(required=True, max_length=255)
    input_file_id = StringField(required=True)  # GridFS file ID
    output_file_id = StringField(null=True, blank=True)  # GridFS file ID
    srt_file_id = StringField(null=True, blank=True)  # GridFS file ID for SRT
    language = StringField(null=True, blank=True, max_length=50)  # Detected language
    
    # Format information
    input_format = StringField(required=True, max_length=10)
    output_format = StringField(default='mp3', max_length=10)
    
    # Status and metadata
    status = StringField(choices=CONVERSION_STATUS, default='pending', max_length=20)
    error_message = StringField(null=True, blank=True)
    
    # File sizes in bytes
    file_size_input = IntField(null=True, blank=True)
    file_size_output = IntField(null=True, blank=True)
    
    # Duration in seconds
    duration = FloatField(null=True, blank=True)
    
    # Timestamps
    created_at = DateTimeField(default=timezone.now)
    completed_at = DateTimeField(null=True, blank=True)
    
    # MongoDB collection name
    meta = {
        'collection': 'video_conversions',
        'indexes': [
            'user_id',
            'status',
            'created_at',
            ('user_id', 'created_at')
        ]
    }
    
    def __str__(self):
        return f"{self.original_filename} -> {self.output_format}"
    
    @property
    def input_file_size_mb(self):
        """Return input file size in MB"""
        if self.file_size_input:
            return round(self.file_size_input / (1024 * 1024), 2)
        return 0
    
    @property
    def output_file_size_mb(self):
        """Return output file size in MB"""
        if self.file_size_output:
            return round(self.file_size_output / (1024 * 1024), 2)
        return 0
    
    @property
    def duration_formatted(self):
        """Return duration in HH:MM:SS format"""
        if self.duration:
            hours = int(self.duration // 3600)
            minutes = int((self.duration % 3600) // 60)
            seconds = int(self.duration % 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "00:00:00"
    
    def mark_completed(self, output_file_id=None, file_size=None, srt_file_id=None, language=None):
        """Mark conversion as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if output_file_id:
            self.output_file_id = output_file_id
        if file_size:
            self.file_size_output = file_size
        if srt_file_id:
            self.srt_file_id = srt_file_id
        if language:
            self.language = language
        self.save()
    
    def mark_failed(self, error_message):
        """Mark conversion as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.save()

# Django model for admin interface compatibility (using SQLite)
class VideoConversionDjango(models.Model):
    """Django model wrapper for admin interface"""
    
    CONVERSION_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    input_file_id = models.CharField(max_length=255)
    output_file_id = models.CharField(max_length=255, null=True, blank=True)
    input_format = models.CharField(max_length=10)
    output_format = models.CharField(max_length=10, default='mp3')
    status = models.CharField(max_length=20, choices=CONVERSION_STATUS, default='pending')
    error_message = models.TextField(null=True, blank=True)
    file_size_input = models.BigIntegerField(null=True, blank=True)
    file_size_output = models.BigIntegerField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        managed = False
        db_table = 'video_conversions'
    
    def __str__(self):
        return f"{self.original_filename} -> {self.output_format}"
    
    @property
    def input_file_size_mb(self):
        if self.file_size_input:
            return round(self.file_size_input / (1024 * 1024), 2)
        return 0
    
    @property
    def output_file_size_mb(self):
        if self.file_size_output:
            return round(self.file_size_output / (1024 * 1024), 2)
        return 0
    
    @property
    def duration_formatted(self):
        if self.duration:
            hours = int(self.duration // 3600)
            minutes = int((self.duration % 3600) // 60)
            seconds = int(self.duration % 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "00:00:00"
