from __future__ import unicode_literals

import datetime
import os

import djcelery
from celery.schedules import crontab

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from .utils import *  # noqa


djcelery.setup_loader()

PROJECT_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    os.pardir,
    os.pardir,
))

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': '127.0.0.1:6379:10',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'tracpro',
        'CONN_MAX_AGE': 60,
        'ATOMIC_REQUESTS': True,
        'OPTIONS': {},
    },
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',

    'compressor',
    'djcelery',
    'guardian',
    'mptt',
    'sorl.thumbnail',
    'smart_selects',

    'smartmin',
    'smartmin.csv_imports',
    'smartmin.users',

    'tracpro.orgs_ext.apps.DashOrgConfig',
    'dash.utils',

    'tracpro.baseline',
    'tracpro.charts',
    'tracpro.contacts',
    'tracpro.groups',
    'tracpro.home',
    'tracpro.msgs',
    'tracpro.orgs_ext',
    'tracpro.polls',
    'tracpro.profiles',
    'tracpro.trackers',
]

LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('en', _("English")),
    ('fr', _("French")),
    ('es', _("Spanish")),
    ('ps', _("Pashto")),
    ('fa', _("Persian")),
]

LOCALE_PATHS = [
    os.path.join(PROJECT_ROOT, 'locale'),
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'celery': {
            'level': 'ERROR'
        },
        'django': {
            'level': 'ERROR',
            'propagate': True,
        },
        'django.request': {
            'level': 'ERROR',
            'propagate': True,
        },
        'django.db.backends': {
            'level': 'ERROR',
        },
        'tracpro': {
            'level': 'INFO',
        },
    },
    'root': {
        'handlers': ['console', 'mail_admins'],
    }
}

LOGIN_REDIRECT_URL = reverse_lazy('home.home')

LOGIN_URL = reverse_lazy('users.user_login')

LOGOUT_REDIRECT_URL = reverse_lazy('home.home')

LOGOUT_URL = reverse_lazy('users.user_logout')

MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'public', 'media')

MEDIA_URL = "/media/"

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'smartmin.middleware.AjaxRedirect',
    'tracpro.orgs_ext.middleware.TracproOrgMiddleware',
    'tracpro.profiles.middleware.ForcePasswordChangeMiddleware',
    'tracpro.groups.middleware.UserRegionsMiddleware',
    'tracpro.orgs_ext.middleware.HandleTembaAPIError',
)

ROOT_URLCONF = 'tracpro.urls'

SESSION_COOKIE_NAME = 'tracpro'

SITE_DATE_FORMAT = r'%b %d, %Y'

SITE_ID = 1

STATICFILES_DIRS = [
    os.path.join(PROJECT_ROOT, 'tracpro', 'static'),
]

STATIC_ROOT = os.path.join(PROJECT_ROOT, 'public', 'static')

STATIC_URL = '/sitestatic/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
    'dash.orgs.context_processors.user_group_perms_processor',
    'dash.orgs.context_processors.set_org_processor',
    'dash.context_processors.lang_direction',
    'tracpro.orgs_ext.context_processors.user_is_admin',
    'tracpro.orgs_ext.context_processors.available_languages',
    'tracpro.groups.context_processors.show_subregions_toggle_form',
)

TEMPLATE_DIRS = [
    os.path.join(PROJECT_ROOT, 'tracpro', 'templates'),
]

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TIME_ZONE = 'GMT'

USER_TIME_ZONE = 'GMT'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# === Third-party settings. === #

ANONYMOUS_USER_ID = -1

BROKER_URL = CELERY_RESULT_BACKEND = 'redis://localhost:6379/4'

CELERYD_HIJACK_ROOT_LOGGER = False

CELERYD_PREFETCH_MULTIPLIER = 1

CELERY_SEND_TASK_ERROR_EMAILS = True

CELERY_TIMEZONE = 'UTC'

ORG_TASK_TIMEOUT = datetime.timedelta(minutes=10)


def _org_scheduler_task(task_name):
    return {
        'task': 'tracpro.orgs_ext.tasks.ScheduleTaskForActiveOrgs',
        'schedule': ORG_TASK_TIMEOUT,
        'kwargs': {
            'task_name': task_name,
        },
    }


def _org_scheduler_report_task(period, schedule):
    return {
        'task': 'tracpro.orgs_ext.tasks.ScheduleTaskForActiveOrgs',
        'schedule': schedule,
        'kwargs': {
            'task_name': 'tracpro.trackers.tasks.ReportEmails',
            'period': period
        },
    }

CELERYBEAT_SCHEDULE = {
    'sync-polls': _org_scheduler_task('tracpro.polls.tasks.SyncOrgPolls'),
    'sync-contacts': _org_scheduler_task('tracpro.contacts.tasks.SyncOrgContacts'),
    'sync-data-fields': _org_scheduler_task('tracpro.contacts.tasks.SyncOrgDataFields'),
    'sync-boundaries': _org_scheduler_task('tracpro.groups.tasks.SyncOrgBoundaries'),
    'fetch-runs': _org_scheduler_task('tracpro.polls.tasks.FetchOrgRuns'),
    'fetch-inbox-messages': _org_scheduler_task('tracpro.msgs.tasks.FetchOrgInboxMessages'),
    'snapshots': {  # Executes every day at 2:00 A.M
        'task': 'tracpro.orgs_ext.tasks.ScheduleTaskForActiveOrgs',
        'schedule': crontab(hour=2, minute=0),
        'kwargs': {
            'task_name': 'tracpro.trackers.tasks.CreateSnapshots',
        },
    },
    'apply-group-rules': {  # Executes every day at 8:00 A.M
        'task': 'tracpro.orgs_ext.tasks.ScheduleTaskForActiveOrgs',
        'schedule': crontab(hour=8, minute=0),
        'kwargs': {
            'task_name': 'tracpro.trackers.tasks.ApplyGroupRules',
        },
    },
    'send-alert-threshold-emails': {  # Executes every day at 8:00 A.M
        'task': 'tracpro.orgs_ext.tasks.ScheduleTaskForActiveOrgs',
        'schedule': crontab(hour=8, minute=0),
        'kwargs': {
            'task_name': 'tracpro.trackers.tasks.SendAlertThresholdEmails',
        },
    },
    'tracker-report-daily': _org_scheduler_report_task(datetime.timedelta(days=1), crontab(hour=10, minute=0)),
    'tracker-report-weekly': _org_scheduler_report_task(datetime.timedelta(days=7),
                                                        crontab(hour=10, minute=0, day_of_week='monday')),
    'tracker-report-fortnightly-first': _org_scheduler_report_task(datetime.timedelta(days=14),
                                                                   crontab(10, 0, day_of_month='1')),
    'tracker-report-fortnightly-second': _org_scheduler_report_task(datetime.timedelta(days=14),
                                                                    crontab(10, 0, day_of_month='15')),
    'tracker-report-monthly': _org_scheduler_report_task(datetime.timedelta(days=30), crontab(10, 0, day_of_month='1')),
    'tracker-report-quarterly': _org_scheduler_report_task(datetime.timedelta(days=90),
                                                           crontab(10, 0, month_of_year='*/3')),
}

COMPRESS_PRECOMPILERS = (
    ('text/coffeescript', 'coffee --compile --stdio'),
    ('text/less', 'tracpro.compress.LessFilter'),
)

DEFAULT_LANGUAGE = 'en'

GROUP_PERMISSIONS = {
    "Administrators": (
        'orgs.org_home',
        'orgs.org_edit',
        'baseline.baselineterm.*',
        'contacts.contact.*',
        'groups.boundary.*',
        'groups.group.*',
        'groups.region.*',
        'msgs.message.*',
        'msgs.inboxmessage.*',
        'polls.poll.*',
        'polls.pollrun.*',
        'polls.response.*',
        'profiles.profile.*',
        'trackers.tracker.*',
    ),
    "Editors": (
        'baseline.baselineterm.*',
        'contacts.contact.*',
        'groups.boundary.*',
        'groups.group_most_active',
        'groups.region_most_active',
        'msgs.inboxmessage.*',
        'msgs.message_send',
        'msgs.message_by_contact',
        'polls.poll_read',
        'polls.pollrun_create',
        'polls.pollrun_restart',
        'polls.pollrun_read',
        'polls.pollrun_participation',
        'polls.pollrun_latest',
        'polls.pollrun_list',
        'polls.pollrun_by_poll',
        'polls.response_by_contact',
        'polls.response_by_pollrun',
        'profiles.profile_user_read',
    ),
    "Viewers": (),
}

ORG_CONFIG_FIELDS = [
    {
        'name': 'available_languages',
        'field': {
            'help_text': _("The languages used by administrators in your organization"),
            'required': True,
        },
    },
    {
        'name': 'show_spoof_data',
        'field': {
            'help_text': _("Whether to show spoof data for this organization"),
            'required': False,
        },
    },
]

PERMISSIONS = {
    '*': (
        'create',  # can create an object
        'read',  # can view an object's details
        'update',  # can update an object
        'delete',  # can delete an object
        'list',  # can view a list of the objects
    ),
    'orgs.org': ('create', 'update', 'list', 'edit', 'home'),
    'baseline.baselineterm': ('create', 'read', 'update', 'delete', 'list', 'data_spoof', 'clear_spoof'),
    'contacts.contact': ('create', 'read', 'update', 'delete', 'list'),
    'groups.group': ('list', 'most_active', 'select'),
    'groups.region': ('list', 'most_active', 'select', 'update_all'),
    'msgs.message': ('list', 'send', 'by_contact'),
    'msgs.inboxmessage': ('read', 'list', 'conversation'),
    'polls.poll': ('read', 'update', 'list', 'select'),
    'polls.pollrun': ('create', 'restart', 'read', 'participation', 'list', 'by_poll', 'latest'),
    'polls.response': ('by_pollrun', 'by_contact'),
    # can't create profiles.user.* permissions because we don't own User
    'profiles.profile': ('user_create', 'user_read', 'user_update', 'user_list'),
    'trackers.tracker': ('create', 'update', 'list'),
}

RTL_LANGUAGES = ['ps', 'fa']

SITE_ALLOW_NO_ORG = (
    'orgs_ext.org_create',
    'orgs_ext.org_update',
    'orgs_ext.org_list',
    'profiles.admin_create',
    'profiles.admin_update',
    'profiles.admin_list',
    'set_language',
)

SITE_API_HOST = 'rapidpro.io'

SITE_API_USER_AGENT = 'tracpro/1.0'

SITE_CHOOSER_URL_NAME = 'orgs_ext.org_chooser'

SITE_CHOOSER_TEMPLATE = 'org_chooser.html'

SITE_HOST_PATTERN = 'http://%s.localhost:8000'

SITE_USER_HOME = '/'
