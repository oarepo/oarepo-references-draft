from flask import current_app
from jsonresolver import hookimpl
from werkzeug.routing import Rule


@hookimpl
def jsonresolver_loader(url_map):
    url_map.add(Rule(
        '/drafts/records/<string:pid_value>',
        endpoint=get_draft_object,
        host=current_app.config.get('SERVER_NAME')
    ))
    url_map.add(Rule(
        '/records/<string:pid_value>',
        endpoint=get_published_object,
        host=current_app.config.get('SERVER_NAME')
    ))
    url_map.add(Rule(
        '/api/drafts/records/<string:pid_value>',
        endpoint=get_draft_object,
        host=current_app.config.get('SERVER_NAME')
    ))
    url_map.add(Rule(
        '/api/records/<string:pid_value>',
        endpoint=get_published_object,
        host=current_app.config.get('SERVER_NAME')
    ))


def get_draft_object(pid_value):
    return {
        'draft': pid_value
    }


def get_published_object(pid_value):
    return {
        'published': pid_value
    }
