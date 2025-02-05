
from wsgid.loaders import IAppLoader
from wsgid.core import Plugin, get_main_logger
try:
  from django.conf import settings
except ImportError:
  pass # Without django its unlikely anyone intends on using the DjangoAppLoader

import os
import sys
import simplejson

log = get_main_logger()

class DjangoAppLoader(Plugin):
  implements = [IAppLoader]

  def _not_hidden_folder(self, name):
    return not name.startswith('.')

  def _valid_dirs(self, app_path):
    return sorted(filter(self._not_hidden_folder, os.listdir(app_path)))

  def _first_djangoproject_dir(self, app_path):
    dirs = self._valid_dirs(app_path)
    log.debug("{0} Possible valid djangoapp folders: {1}".format(len(dirs), dirs))
    for d in dirs:
      settings_path = os.path.join(app_path, d, 'settings')
      init_path = os.path.join(app_path, d, '__init__.py')
      if os.path.exists(settings_path) and os.path.exists(init_path):
        return d
    return None

  def can_load(self, app_path):
    return self._first_djangoproject_dir(app_path) is not None

  def _load_django_extra_options(self, path):
      parsed = {}
      conf_file = os.path.join(path, 'django.json')
      log.debug("Reading {0}".format(conf_file))
      if os.path.exists(conf_file):
          try:
            parsed = simplejson.load(open(conf_file))
          except:
              log.exception("Error parsing {file}".format(file=conf_file))
      return parsed

  def load_app(self, app_path, app_full_name = None):
    logger = get_main_logger()
    # Since we receive here --app-path + app/, we need to remove the last part
    # because django.json lives in --app-path
    wsgidapp_path = os.path.dirname(app_path)

    site_name = self._first_djangoproject_dir(app_path)
    os.environ['DJANGO_SETTINGS_MODULE'] = '{0}.settings'.format(site_name)
    logger.debug("Using DJANGO_SETTINGS_MODULE = {0}".format(os.environ['DJANGO_SETTINGS_MODULE']))

    new_syspath = os.path.join(app_path, site_name)

    logger.debug("Adding {0} to sys.path".format(app_path))
    sys.path.append(app_path)
    logger.debug("Adding {0} to sys.path".format(new_syspath))
    sys.path.append(new_syspath)

    import django.core.handlers.wsgi
    return django.core.handlers.wsgi.WSGIHandler()

  '''
   Check if isinstance(args[0], instance_of) returns True for *all*
   members of *args
  '''
  def _is_all_instance(self, instance_of, *args):
    for a in args:
      if not isinstance(a, instance_of):
        return False
    return True

