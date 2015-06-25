# Maps URL patterns to functions in views.py
#
# For example, visiting https://materialsproject.org/tasks/mp-24850 will
# trigger a call to views.tasks with keyword arg task_id="mp-24850".
#
# This file assumes a urls.py file at the project level with a pattern like
# (r'^tasks/', include('tasks.urls')) so that this file is for the "tasks/" URL
# namespace.

from django.conf.urls import *

urlpatterns = patterns('tasks.views',
    (r'^(?P<task_id>[\w\-]+)/json$', 'task_details'),
    (r'^(?P<task_id>[\w\-]+)/*$', 'tasks'),
    (r'^(?P<task_id>[\w\-]+)/kpoints$', 'download_kpts')
)
