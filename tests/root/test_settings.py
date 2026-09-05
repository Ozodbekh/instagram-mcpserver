from django.conf import settings


def test_no_admin_and_no_sessions():
    assert 'django.contrib.admin' not in settings.INSTALLED_APPS
    assert 'django.contrib.sessions' not in settings.INSTALLED_APPS
    assert 'django.contrib.staticfiles' not in settings.INSTALLED_APPS


def test_no_append_slash_middleware():
    assert 'django.middleware.common.CommonMiddleware' not in settings.MIDDLEWARE


def test_templates_are_empty_of_everything_but_app_dirs():
    template = settings.TEMPLATES[0]

    assert template['DIRS'] == []
    assert template['APP_DIRS'] is True
    assert template['OPTIONS']['context_processors'] == []


def test_json_is_the_only_renderer_and_parser():
    assert settings.REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] == [
        'rest_framework.renderers.JSONRenderer',
    ]
    assert settings.REST_FRAMEWORK['DEFAULT_PARSER_CLASSES'] == [
        'rest_framework.parsers.JSONParser',
    ]
