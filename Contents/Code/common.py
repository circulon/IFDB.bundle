import logging
import os
import threading

PlexRoot          = Core.app_support_path
CachePath         = os.path.join(PlexRoot, "Plug-in Support", "Data", "com.plexapp.agents.ifdb", "DataItems")

### Plex Library XML ###
PLEX_LIBRARY = {}
PLEX_LIBRARY_URL = "http://localhost:32400/library/sections/"    # Allow to get the library name to get a log per library https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token


### Get media directory ###
def GetMediaDir(media, movie, file=False):
  if movie:  return media.items[0].parts[0].file if file else os.path.dirname(media.items[0].parts[0].file)
  else:
    for s in media.seasons if media else []: # TV_Show:
      for e in media.seasons[s].episodes:
        return media.seasons[s].episodes[e].items[0].parts[0].file if file else os.path.dirname(media.seasons[s].episodes[e].items[0].parts[0].file)

### Get media root folder ###
def GetLibraryRootPath(dir, repull_libraries=True):
  roots_found, library, root, path = [], '', '', ''
  for root in [os.sep.join(dir.split(os.sep)[0:x+2]) for x in range(0, dir.count(os.sep))]:
    if root in PLEX_LIBRARY:  roots_found.append(root)
  if len(roots_found) > 0:
    root    = max(roots_found)
    library = PLEX_LIBRARY[root]
    path    = os.path.relpath(dir, root)
  else:
    if repull_libraries:
      GetPlexLibraries()  # Repull library listings as if a library was created while IFDB was already running, it would not be known
      library, root, path = GetLibraryRootPath(dir, repull_libraries=False)  # Try again but don't repull libraries as it will get stuck in an infinite loop
    else:
      path, root = '_unknown_folder', ''
  return library, root, path

class PlexLog(object):
    ''' Logging class to join scanner and agent logging per serie
        Usage Agent:
         - log = common.PlexLog(file='mytest.log', isAgent=True )
         - log.debug('some debug message: %s', 'test123')
    '''

    def Logger(self):
        logger = logging.getLogger(hex(threading.currentThread().ident))
        return logger if logger.handlers else logging.getLogger('com.plexapp.agents.ifdb')

    def Root(self, msg, *args, **kwargs):
        logging.getLogger('com.plexapp.agents.ifdb').debug(msg, *args, **kwargs)

    def Debug(self, msg, *args, **kwargs):
        self.Logger().debug(msg, *args, **kwargs)

    def Info(self, msg, *args, **kwargs):
        self.Logger().info(msg, *args, **kwargs)

    def Warning(self, msg, *args, **kwargs):
        self.Logger().warning(msg, *args, **kwargs)

    def Error(self, msg, *args, **kwargs):
        self.Logger().error("ERROR: {}".format(msg), *args, **kwargs); self.Root("ERROR: {}".format(msg))

    def Critical(self, msg, *args, **kwargs):
        self.Logger().critical("FATAL: {}".format(msg), *args, **kwargs); self.Root("FATAL: {}".format(msg))

    def Open(self, media=None, movie=False, search=False, isAgent=True, log_format='%(message)s', file="", mode='w',
             maxBytes=4 * 1024 * 1024, backupCount=5, encoding=None, delay=False, enable_debug=True):
        if not file:
            library, root, path = GetLibraryRootPath(
                GetMediaDir(media, movie))  # Get movie or serie episode folder location
            mode = 'a' if path in ('_unknown_folder', '_root_') else 'w'

            # Logs folder
            for char in list("\\/:*?<>|~;"):  # remove leftover parenthesis (work with code a bit above)
                if char in library:  library = library.replace(char,
                                                               '-')  # translate anidb apostrophes into normal ones
            LOGS_PATH = os.path.join(CachePath, '_Logs', library)
            if not os.path.exists(LOGS_PATH):  os.makedirs(LOGS_PATH);  self.Debug(
                "[!] folder: '{}'created".format(LOGS_PATH))

            if path == '' and root:  path = '_root_'
            filename = path.split(os.sep, 1)[0] + '.agent-search.log' if search else path.split(os.sep, 1)[
                                                                                         0] + '.agent-update.log'
            file = os.path.join(LOGS_PATH, filename)
        try:
            log = logging.getLogger(hex(threading.currentThread().ident))  # update thread's logging handler
            for handler in log.handlers:  log.removeHandler(handler)  # remove all old handlers
            handler_new = logging.FileHandler(file, mode=mode or 'w', encoding=encoding, delay=delay)
            handler_new.setFormatter(logging.Formatter(log_format))  # Set log format
            log.addHandler(handler_new)
            log.setLevel(logging.DEBUG if enable_debug else logging.INFO)  # update level

            log = logging.getLogger('com.plexapp.agents.ifdb')  # update ifdb root's logging handler
            library_log = os.path.join(LOGS_PATH, '_root_.agent.log')
            if library_log not in [handler.baseFilename for handler in log.handlers if
                                   hasattr(handler, 'baseFilename')]:
                for handler in log.handlers:
                    if hasattr(handler, 'baseFilename') and os.path.join(CachePath,
                                                                         '_Logs') in handler.baseFilename:  log.removeHandler(
                        handler)
                handler_new = logging.handlers.RotatingFileHandler(library_log, mode='a', maxBytes=4 * 1024 * 1024,
                                                                   backupCount=1, encoding=encoding, delay=delay)
                # handler_new = logging.FileHandler(library_log, mode='w', encoding=encoding, delay=delay)
                handler_new.setFormatter(
                    logging.Formatter('%(asctime)-15s - %(thread)x - %(message)s'))  # Set log format
                log.addHandler(handler_new)
            log.info('==== common.PlexLog(file="{}")'.format(file))

        except IOError as e:
            self.isAgent = isAgent;  logging.getLogger('com.plexapp.agents.ifdb').info(
                'updateLoggingConfig: failed to set logfile: {}'.format(e))
        self.Info("".ljust(157, '='))
        self.Info('common.PlexLog(file="{}", movie={})'.format(file, movie))
        self.Info('[!] file:       "{}"'.format(GetMediaDir(media, movie, True)))
        self.Info('[ ] library:    "{}"'.format(library))
        self.Info('[ ] root:       "{}"'.format(root))
        self.Info('[ ] path:       "{}"'.format(path))
        self.Info('[ ] Plex root:  "{}"'.format(PlexRoot))
        self.Info('[ ] Log folder: "{}"'.format(os.path.relpath(LOGS_PATH, PlexRoot)))
        self.Info('[ ] Log file:   "{}"'.format(filename))
        self.Info('[ ] Logger:     "{}"'.format(hex(threading.currentThread().ident)))
        self.Info('[ ] mode:       "{}"'.format(mode))
        self.isAgent = isAgent

    def Close(self):
        log = logging.getLogger(hex(threading.currentThread().ident))  # update root logging's handler
        for handler in log.handlers:  log.removeHandler(handler)

Log = PlexLog()

def GetPlexLibraries():
  try:
    library_xml = XML.ElementFromURL(PLEX_LIBRARY_URL, cacheTime=0, timeout=float(30), headers={"X-Plex-Token": os.environ['PLEXTOKEN']})
    PLEX_LIBRARY.clear()
    Log.Root('Libraries: ')
    for directory in library_xml.iterchildren('Directory'):
      for location in directory:
        if directory.get("agent") == "com.plexapp.agents.ifdb":
          PLEX_LIBRARY[location.get("path")] = directory.get("title")  # Only pull libraries that use IFDB to prevent miss identification
        Log.Root('[{}] id: {:>2}, type: {:<6}, agent: {:<30}, scanner: {:<30}, library: {:<24}, path: {}'.format('x' if directory.get("agent") == "com.plexapp.agents.ifdb" else ' ', directory.get("key"), directory.get('type'), directory.get("agent"), directory.get("scanner"), directory.get('title'), location.get("path")))
  except Exception as e:
    Log.Root("PLEX_LIBRARY_URL - Exception: '{}'".format(e))
