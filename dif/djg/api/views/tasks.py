"""
任务管理相关视图
包含：
- TaskDetailView（任务详情）
- TaskProgressView（任务进度）
- CancelTaskView（取消任务）
"""

import logging
from rest_framework import status, views
from rest_framework.response import Response

from ..models import DirectoryScanTask
from ..serializers import DirectoryScanTaskSerializer

logger = logging.getLogger(__name__)


class TaskDetailView(views.APIView):
    """任务详情视图"""
    
    def get(self, request, task_id):
        """获取任务详情"""
        try:
            task = DirectoryScanTask.objects.get(task_id=task_id)
            serializer = DirectoryScanTaskSerializer(task)
            return Response(serializer.data)
        except DirectoryScanTask.DoesNotExist:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class TaskProgressView(views.APIView):
    """任务进度视图"""
    
    def get(self, request, task_id):
        """获取任务进度"""
        try:
            task = DirectoryScanTask.objects.get(task_id=task_id)
            return Response({
                'task_id': task_id,
                'status': task.status,
                'progress': task.progress,
                'scanned_files': task.scanned_files,
                'total_files': task.total_files,
            })
        except DirectoryScanTask.DoesNotExist:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class CancelTaskView(views.APIView):
    """取消任务视图"""
    
    def post(self, request, task_id):
        """取消任务"""
        try:
            task = DirectoryScanTask.objects.get(task_id=task_id)
            if task.status in ['pending', 'running']:
                task.status = 'cancelled'
                task.save()
                return Response({'status': 'cancelled'})
            else:
                return Response(
                    {'error': 'Cannot cancel task in current state'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except DirectoryScanTask.DoesNotExist:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )
