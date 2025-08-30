from django.contrib import admin
from .models import VideoConversionDjango

@admin.register(VideoConversionDjango)
class VideoConversionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'original_filename', 'user', 'input_format', 
        'output_format', 'status', 'input_file_size_mb', 
        'output_file_size_mb', 'created_at'
    ]
    list_filter = ['status', 'input_format', 'output_format', 'created_at']
    search_fields = ['original_filename', 'user__username']
    readonly_fields = [
        'created_at', 'completed_at', 'input_file_size_mb', 
        'output_file_size_mb', 'duration_formatted', 'input_file_id', 'output_file_id'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('File Information', {
            'fields': ('original_filename', 'input_format', 'output_format')
        }),
        ('User & Status', {
            'fields': ('user', 'status', 'error_message')
        }),
        ('GridFS File IDs', {
            'fields': ('input_file_id', 'output_file_id'),
            'classes': ('collapse',)
        }),
        ('File Details', {
            'fields': ('file_size_input', 'file_size_output', 'duration'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
