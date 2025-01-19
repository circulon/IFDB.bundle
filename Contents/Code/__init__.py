from datetime import datetime

import common

INITIAL_SCORE = 100  # Starting value for score before deductions are taken.
GOOD_SCORE = 98  # Score required to short-circuit matching and stop searching.
IGNORE_SCORE = 45  # Any score lower than this will be ignored.

VERSION = '2.0.0-beta1'


def Start():
  Log.Info("Internet Fanedit Database Agent by Circulon (Forked from tomfin46's v{}) - CPU: {}, OS: {}".format(VERSION, Platform.CPU, Platform.OS))
  # common.GetPlexLibraries()

class IFDBAgent(Agent.Movies):
  name = 'IFDB Movies'
  fallback_agent = False
  languages = [Locale.Language.English]
  primary_provider = True
  accepts_from = ['com.plexapp.agents.localmedia']
  contributes_to = None

  ##############################
  ##### Main Search Method #####
  ##############################
  def search(self, results,  media, lang, manual):
    from common import Log  #Import here for startup logging to go to the plex pms log
    Log.Info('=== search() ==='.ljust(157, '='))
    orig_title = media.name
    Log.Open(media=media, search=True, movie=True)
    # if media.filename is not None: filename = String.Unquote(media.filename) #auto match only
    Log.Info("title: '{}', name: '{}', filename: '{}', manual: '{}', year: '{}'".format(orig_title, media.name, media.filename, str(manual), media.year))
    Log.Info("start: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")))
    Log.Info("".ljust(157, '='))
    if not orig_title:
      return

    year = None
    if media.year and int(media.year) > 1900:
      year = media.year

    # Strip Diacritics from media name
    stripped_name = String.StripDiacritics(orig_title)
    if len(stripped_name) == 0:
      stripped_name = media.name

    # Do the Search
    from ifdb import IFDB
    found_results = IFDB().fetch_search_result(stripped_name, year)
    if not found_results:
      Log.Info('No results found for query "{}" {}'.format(stripped_name, year))
      Log.Info("end: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")))
      Log.Close()
      return

    scored_matches = []
    # For each result:
    # calculate Levenshtein Distance from our query
    # add the lang key
    for entry in found_results:
      score = INITIAL_SCORE - abs(String.LevenshteinDistance(entry['name'].lower(), media.name.lower()))
      entry['score'] = score
      entry['lang'] = lang
      should_ignore = score < IGNORE_SCORE
      Log.Info("Search result - name: {} score: {} year: {} should ignore result: {}".format(entry["name"], score, entry["year"], should_ignore))
      if should_ignore:
        continue

      scored_matches.append(entry)

    # Reverse sort by score so most likely match is at the top
    scored_matches = sorted(scored_matches, key=lambda item: item['score'], reverse=True)

    for entry in scored_matches:
      Log.Info("Adding Search result: id: {} score: {} title: {}".format(entry["id"], entry["score"], entry["name"]))
      results.Append(MetadataSearchResult(**entry))
      # If more than one result but current match is considered a good score use this and move on
      if not manual and len(scored_matches) > 1 and entry['score'] >= GOOD_SCORE:
        break

    Log.Info("end: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")))
    Log.Close()

  #############################
  ##### Main Update Methd #####
  #############################
  def update(self, metadata, media, lang, force):
    from common import Log  #Import here for startup logging to go to the plex pms log
    Log.Info("########### update() ###########")
    Log.Info("start: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")))
    from ifdb import IFDB
    entry_info = IFDB().fetch_entry_with_id(metadata.id)
    if not entry_info:
      Log.Error("No IFDB entry foir id: {}".format(metadata.id))
      Log.Info("end: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")))
      Log.Close()
      return

    try:
      metadata.title = entry_info["name"]
      metadata.rating = entry_info["rating"]
      metadata.tagline = entry_info["tag_line"]
      metadata.tags.add(entry_info["fanedit_type"])
      metadata.original_title = ', '.join(entry_info["original_titles"])

      try:
        metadata.originally_available_at = entry_info["original_release_date"]
        metadata.year = entry_info["fanedit_release_date"].year
      except:
        pass

      metadata.summary = entry_info["summary"]

      metadata.directors.clear()
      for editor in entry_info["fan_editors"]:
        metadata.directors.new().name = editor

      for genre in entry_info["genres"]:
        metadata.genres.add(genre)

      for franchise in entry_info["franchises"]:
        metadata.collections.add(franchise)

      poster_url = entry_info["poster_url"]
      if poster_url not in metadata.posters:
        try:
          metadata.posters[poster_url] = Proxy.Media(HTTP.Request(poster_url).content)
        except:
          pass

    except Exception as e:
      Log.Error('Error updating data for item with id {} [{}] '.format(metadata.id, str(e)))

    Log.Info("end: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")))
    Log.Close()
