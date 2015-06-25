from django.conf.urls import *

urlpatterns = patterns('tasks.views',
    (r'^(?P<task_id>[\w\-]+)/json$', 'task_details'),
    (r'^(?P<task_id>[\w\-]+)/*$', 'tasks'),
    (r'^(?P<task_id>[\w\-]+)/kpoints$', 'download_kpts')
)
