import os
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.files.base import ContentFile
from .models import VideoConversion
from .utils import video_converter
from .mongodb_storage import mongodb_storage
from .srt_converter import srt_converter
import logging
        # Save uploaded file to GridFS
import uuid
logger = logging.getLogger(__name__)

@login_required
def converter_dashboard(request):
    """Main converter dashboard"""
    try:
        user_conversions = VideoConversion.objects.filter(user_id=request.user.id).order_by('-created_at')[:10]
    except Exception as e:
        logger.error(f"Error fetching conversions: {e}")
        user_conversions = []
    
    context = {
        'conversions': user_conversions,
        'supported_formats': video_converter.supported_video_formats,
    }
    return render(request, 'converter/dashboard.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def upload_video(request):
    """Handle video file upload and start conversion"""
    try:
        if 'video_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No video file provided'
            }, status=400)
        
        video_file = request.FILES['video_file']
        filename = video_file.name
        
        # Validate file format
        if not video_converter.is_video_file(filename):
            return JsonResponse({
                'success': False,
                'error': f'Unsupported file format. Supported formats: {", ".join(video_converter.supported_video_formats)}'
            }, status=400)
        
        # Validate file size (max 100MB)
        max_size = 100 * 1024 * 1024  # 100MB
        if video_file.size > max_size:
            return JsonResponse({
                'success': False,
                'error': 'File size too large. Maximum size is 100MB.'
            }, status=400)
        


# Save uploaded file to GridFS
        try:
    # Generate unique filename
            base, ext = os.path.splitext(filename)
            unique_filename = f"uploads/{base}_{uuid.uuid4().hex}{ext}"

    # Prepare file for GridFS
            content = ContentFile(video_file.read())
            content.name = unique_filename
            content.content_type = video_file.content_type

    # Save to GridFS
            input_file_id = mongodb_storage._save(content.name, content)

            # Create conversion record
            conversion = VideoConversion(
                user_id=request.user.id if request.user.is_authenticated else None,
                original_filename=filename,
                input_file_id=input_file_id,
                input_format=os.path.splitext(filename)[1][1:].lower(),
                file_size_input=video_file.size,
                status='pending'
            )
            conversion.save()
            
            # Start conversion process
            try:
                conversion.status = 'processing'
                conversion.save()
                
                # Convert video to MP3 and generate SRT
                output_file_id = video_converter.convert_video_to_mp3(input_file_id)
                
                if output_file_id:
                    # Get output file size
                    output_size = mongodb_storage.size(output_file_id)
                    
                    # Generate SRT with language detection
                    srt_result = srt_converter.process_video_to_srt(input_file_id)
                    
                    if srt_result['success']:
                        # Mark as completed with SRT info
                        conversion.mark_completed(
                            output_file_id=output_file_id,
                            file_size=output_size,
                            srt_file_id=srt_result['srt_file_id'],
                            language=srt_result['language']
                        )
                    else:
                        # Mark as completed without SRT (SRT generation failed)
                        conversion.mark_completed(
                            output_file_id=output_file_id,
                            file_size=output_size
                        )
                        logger.warning(f"SRT generation failed: {srt_result['error']}")
                    
                    return JsonResponse({
                        'success': True,
                        'conversion_id': str(conversion.id),
                        'output_file_id': output_file_id,
                        'filename': os.path.basename(filename).replace('.mp4', '.mp3'),
                        'file_size': output_size
                    })
                else:
                    conversion.mark_failed('Conversion failed - no output file generated')
                    return JsonResponse({
                        'success': False,
                        'error': 'Conversion failed'
                    }, status=500)
                    
            except Exception as e:
                logger.error(f"Conversion error: {e}")
                conversion.mark_failed(str(e))
                return JsonResponse({
                    'success': False,
                    'error': f'Conversion failed: {str(e)}'
                }, status=500)
                
        except Exception as e:
            logger.error(f"GridFS save error: {e}")
            return JsonResponse({
                'success': False,
                'error': f'File upload failed: {str(e)}'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
def download_audio(request, conversion_id):
    """Download converted audio file from GridFS"""
    try:
        # Handle MongoDB ObjectId
        from bson import ObjectId
        try:
            obj_id = ObjectId(conversion_id)
            conversion = VideoConversion.objects.get(id=obj_id)
        except:
            # Fallback to string comparison
            conversion = VideoConversion.objects.get(id=conversion_id)
        
        # Check if user owns this conversion or is admin
        if not request.user.is_authenticated or (conversion.user_id and conversion.user_id != request.user.id):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        if conversion.status != 'completed' or not conversion.output_file_id:
            return JsonResponse({'error': 'Conversion not completed'}, status=404)
        
        # Get file content from GridFS
        file_content = mongodb_storage.get_file_content(conversion.output_file_id)
        if not file_content:
            return JsonResponse({'error': 'File not found in GridFS'}, status=404)
        
        # Serve file for download
        response = HttpResponse(file_content, content_type='audio/mpeg')
        response['Content-Disposition'] = f'attachment; filename="{conversion.original_filename.replace(".mp4", ".mp3")}"'
        return response
        
    except VideoConversion.DoesNotExist:
        return JsonResponse({'error': 'Conversion not found'}, status=404)
    except Exception as e:
        logger.error(f"Download error: {e}")
        return JsonResponse({'error': 'Download failed'}, status=500)

@require_http_methods(["GET"])
def download_srt(request, conversion_id):
    """Download SRT subtitle file from GridFS"""
    try:
        # Handle MongoDB ObjectId
        from bson import ObjectId
        try:
            obj_id = ObjectId(conversion_id)
            conversion = VideoConversion.objects.get(id=obj_id)
        except:
            # Fallback to string comparison
            conversion = VideoConversion.objects.get(id=conversion_id)
        
        # Check if user owns this conversion or is admin
        if not request.user.is_authenticated or (conversion.user_id and conversion.user_id != request.user.id):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        if conversion.status != 'completed' or not conversion.srt_file_id:
            return JsonResponse({'error': 'SRT file not available'}, status=404)
        
        # Get file content from GridFS
        file_content = mongodb_storage.get_file_content(conversion.srt_file_id)
        if not file_content:
            return JsonResponse({'error': 'SRT file not found in GridFS'}, status=404)
        
        # Serve file for download
        response = HttpResponse(file_content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{conversion.original_filename.replace(".mp4", ".srt")}"'
        return response
        
    except VideoConversion.DoesNotExist:
        return JsonResponse({'error': 'Conversion not found'}, status=404)
    except Exception as e:
        logger.error(f"SRT download error: {e}")
        return JsonResponse({'error': 'SRT download failed'}, status=500)

@require_http_methods(["GET"])
def conversion_status(request, conversion_id):
    """Get conversion status"""
    try:
        # Handle MongoDB ObjectId
        from bson import ObjectId
        try:
            obj_id = ObjectId(conversion_id)
            conversion = VideoConversion.objects.get(id=obj_id)
        except:
            # Fallback to string comparison
            conversion = VideoConversion.objects.get(id=conversion_id)
        
        # Check if user owns this conversion
        if not request.user.is_authenticated or (conversion.user_id and conversion.user_id != request.user.id):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        return JsonResponse({
            'id': str(conversion.id),
            'status': conversion.status,
            'original_filename': conversion.original_filename,
            'input_file_size_mb': conversion.input_file_size_mb,
            'output_file_size_mb': conversion.output_file_size_mb,
            'duration_formatted': conversion.duration_formatted,
            'created_at': conversion.created_at.isoformat(),
            'completed_at': conversion.completed_at.isoformat() if conversion.completed_at else None,
            'error_message': conversion.error_message
        })
        
    except VideoConversion.DoesNotExist:
        return JsonResponse({'error': 'Conversion not found'}, status=404)

@require_http_methods(["DELETE"])
def delete_conversion(request, conversion_id):
    """Delete conversion and associated files from GridFS"""
    try:
        # Handle MongoDB ObjectId
        from bson import ObjectId
        try:
            obj_id = ObjectId(conversion_id)
            conversion = VideoConversion.objects.get(id=obj_id)
        except:
            # Fallback to string comparison
            conversion = VideoConversion.objects.get(id=conversion_id)
        
        # Check if user owns this conversion
        if not request.user.is_authenticated or (conversion.user_id and conversion.user_id != request.user.id):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Delete files from GridFS
        if conversion.input_file_id:
            mongodb_storage.delete(conversion.input_file_id)
        if conversion.output_file_id:
            mongodb_storage.delete(conversion.output_file_id)
        
        # Delete database record
        conversion.delete()
        
        return JsonResponse({'success': True})
        
    except VideoConversion.DoesNotExist:
        return JsonResponse({'error': 'Conversion not found'}, status=404)
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return JsonResponse({'error': 'Delete failed'}, status=500)

@require_http_methods(["GET"])
def conversion_history(request):
    """Get user's conversion history"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        conversions = VideoConversion.objects.filter(user_id=request.user.id).order_by('-created_at')[:20]
        
        history = []
        for conversion in conversions:
            history.append({
                'id': str(conversion.id),
                'original_filename': conversion.original_filename,
                'status': conversion.status,
                'input_format': conversion.input_format,
                'output_format': conversion.output_format,
                'input_file_size_mb': conversion.input_file_size_mb,
                'output_file_size_mb': conversion.output_file_size_mb,
                'duration_formatted': conversion.duration_formatted,
                'created_at': conversion.created_at.isoformat(),
                'completed_at': conversion.completed_at.isoformat() if conversion.completed_at else None,
            })
        
        return JsonResponse({'conversions': history})
    except Exception as e:
        logger.error(f"Error fetching conversion history: {e}")
        return JsonResponse({'error': 'Failed to fetch history'}, status=500)
