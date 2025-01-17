import time
import urlparse

import requests
import common
from common import Log
from urlparse import urlparse
from datetime import datetime

# URLS
IFDB_BASE_URL = 'https://fanedit.org/'
IFDB_BASE_SEARCH_URL = IFDB_BASE_URL + 'fanedit-search/search-results/'
IFDB_SEARCH_URL = IFDB_BASE_SEARCH_URL + '?query={}&scope=title&keywords={}&order=rdate'
IFDB_SEARCH_YEAR = '&jr_faneditreleasedate={}'
COMMON_HEADERS    = {
  'User-agent': 'Plex/IFDB',
}


class IFDB:
  def fetch_search_result(self, keywords, year):
    Log.Info("##### IFDB.fetch_search_result() #####")
    search_url = IFDB_SEARCH_URL.format(
      Prefs["match_type"],
      String.Quote((keywords).encode('utf-8'), usePlus=True)
    )
    if year:
      search_url = search_url + IFDB_SEARCH_YEAR.format(year)

    Log.Info("###########  Fetch Search Results ###########")
    Log.Info("With Url: {}".format(search_url))

    matches = []
    try:
      resp = requests.get(search_url, headers=COMMON_HEADERS)
      Log.Info("Actual Search url: {}".format(resp.url))
      resp.raise_for_status()
      root_node = HTML.ElementFromString(resp.content)
    except Exception as e:
      Log.Error("==== Error type: {}".format(type(e)))
      Log.Error("######### IFDB Loading search XML failed, Exception: '{}'".format(str(e)), exc_info=True)
    else:
      # check if we got a search resuls page
      if "search-results" in resp.url:
        matches = self.entries_from_search_result(root_node)
      # if there is an exact match the page will be redirected
      # to that actual entry listing
      elif root_node.xpath('//*[@id="primary"]//div[contains(@class,"jrCustomFields")]'):
        match  = self.entry_from_page_listing(root_node)
        if match:
          matches.append(match)

    return matches

  def fetch_entry_with_id(self, ifdb_id):
    """
    Get an entry based on the IFDB id.

    NOTE: as redirects based on the number id used for entry comparison
        we have opted instead for the url path that denotes the actual
        entry page itself as it is also unique
    """
    Log.Info("#### IFDB.fetch_entry_with_id()")
    Log.Info("entry id: {}".format(ifdb_id))
    entry = {}
    try:
      url = "{}/{}/".format(IFDB_BASE_URL, ifdb_id)
      resp = requests.get(url, headers=COMMON_HEADERS)
      resp.raise_for_status()
      Log.Info("Using Entry url: {}".format(resp.url))
      root_node = HTML.ElementFromString(resp.content)
    except Exception as e:
      Log.Error("==== Error type: {}".format(type(e)))
      Log.Error("IFDB Loading Entry Listing failed, Exception: '{}'".format(str(e)), exc_info=True)
    else:
      # get extra info so we can populate the Plex entry
      entry = self.entry_from_page_listing(root_node, True)

    return entry

  # entry extractors
  def entries_from_search_result(self, root_node):
      Log.Info("###### IFDB.entries_from_search_result()  ###########")
      results = []
      entry_nodes = root_node.xpath('//*[@id="jr-pagenav-ajax"]/div[3]//div[contains(@class,"jrListingTitle")]/../..')
      Log.Info("### Search Found: {} entries ###".format(len(entry_nodes)))
      for entry in entry_nodes:
        title = self.get_string_content_from_xpath(entry, './/div[contains(@class,"jrListingTitle")]//a/text()')
        # ifdb_id = self.get_string_content_from_xpath(entry, './/div[contains(@class,"jrCompareButton")]/input/@value')
        page_url = self.get_string_content_from_xpath(entry, './/div[contains(@class,"jrListingTitle")]/a/@href')
        parsed_url = urlparse(page_url)
        ifdb_id = parsed_url.path.replace('/', '')
        thumb = self.get_string_content_from_xpath(entry, './/div[contains(@class,"jrListingThumbnail")]//img/@data-jr-src')
        full_release_date = self.get_field_link_value(entry, "jrFaneditreleasedate")
        release_date = datetime.strptime(full_release_date, "%B %Y").date()
        entry = {
          "id": ifdb_id,
          "name": title,
          "year": release_date.year,
          "thumb": thumb,
        }
        results.append(entry)
        Log.Info(("search entry: {}".format(entry)))

      return results

  def entry_from_page_listing(self, root_node, extra_info=False):
    Log.Info("##### IFDB.entry_from_page_listing #####")
    Log.Info("### Extra Info: {}".format(extra_info))
    banner_node = root_node.xpath('.//div[@id="primary"]/div')[0]
    title = self.get_string_content_from_xpath(banner_node, './/div[contains(@class,"jrDetailHeader")]//h1/span/text()')
    Log.Info("### Title: {}".format(title))
    # get the page id from the link
    page_url = self.get_string_content_from_xpath(root_node, '//link[@rel="canonical"][contains(@href, "fanedit.org")]/@href')
    parsed_url = urlparse(page_url)
    ifdb_id = parsed_url.path.replace('/', '')
    Log.Info("### IFDB id: {}".format(ifdb_id))
    thumbnail_url = self.get_string_content_from_xpath(banner_node, '//div[contains(@class,"jrListingMainImage")]/a//img/@data-jr-src')
    Log.Info("### Thumbnail Url: {}".format(thumbnail_url))
    fields_node = banner_node.xpath('.//div[contains(@class,"jrCustomFields")]//div[contains(@class,"jrFaneditorname")]/../..')[0]
    full_release_date = self.get_string_content_from_xpath(fields_node, './/div[contains(@class,"jrFaneditreleasedate")]//a/text()')
    Log.Info("### Fanedit release date: {}".format(full_release_date))
    release_date = datetime.strptime(full_release_date, "%B %Y").date()
    entry = {
      "id": str(ifdb_id),
      "name": title,
      "year": release_date.year,
      "thumb": thumbnail_url,
    }

    if extra_info:
      entry.update(self.extra_info_from_page_entry(banner_node))

    return entry

  def extra_info_from_page_entry(self, root_node):
    Log.Info("########### Extra Info From Page Entry ###########")
    info = {}
    fields_node = root_node.xpath('.//div[contains(@class,"jrCustomFields")]//div[contains(@class,"jrFaneditorname")]/../..')[0]

    # Faneditor Name
    fan_editors = self.get_field_value_list(fields_node, "jrFaneditorname")
    Log.Info("### Fan Editors: {}".format(fan_editors))
    info["fan_editors"] = fan_editors

    # Original Movie Titles
    original_titles = self.get_field_value_list(fields_node, 'jrOriginalmovietitle')
    Log.Info("### Original Title: {}".format(original_titles))
    info["original_titles"] = original_titles

    # Genres
    genres = self.get_field_value_list(fields_node, 'jrGenre')
    Log.Info("### Genres: {}".format(genres))
    info["genres"] = genres

    # Tag line
    tag_line = self.get_field_value(fields_node, 'jrTagline')
    Log.Info("### Tag line: {}".format(tag_line))
    info["tag_line"] = tag_line

    # Franchises
    franchises = self.get_field_value_list(fields_node, 'jrFranchise')
    Log.Info("### Franchises: {}".format(franchises))
    info["franchises"] = franchises

    # Fanedit Type
    fanedit_type = self.get_field_link_value(fields_node, 'jrFanedittype')
    Log.Info("### Fanedit Type: {}".format(fanedit_type))
    info["fanedit_type"] = fanedit_type

    # Fanedit release year
    release_date_str = self.get_field_link_value(fields_node, "jrFaneditreleasedate")
    release_date = datetime.strptime(release_date_str, "%B %Y").date()
    Log.Info("### Fanedit Release Date: {}".format(str(release_date)))
    info["fanedit_release_date"] = release_date

    # Original movie Release Date
    original_release_date_str = self.get_field_value(fields_node, "jrOriginalreleasedate")
    Log.Info("### Original Release Year: {}".format(original_release_date_str))
    original_release_date = datetime.strptime(original_release_date_str, "%Y").date()
    info["original_release_date"] = original_release_date

    reviews_node = root_node.xpath('//div[@id="editorReviews"]')[0]
    # Rating
    rating = self.get_string_content_from_xpath(reviews_node, '//div[@itemprop="ratingValue"]')
    Log.Info("### Rating: {}".format(rating))
    info["rating"] = float(rating) if rating else 0.0

    fanedit_info_node = root_node.xpath('//div[@id="fanedit-info"]')[0]
    # Brief Synopsis
    summary = self.get_field_value(fanedit_info_node, "jrBriefsynopsis")
    Log.Info("### Summary: {}".format(summary))
    info["summary"] = summary

    # Poster
    poster_url = self.get_string_content_from_xpath(root_node, '//div[contains(@class,"jrListingMainImage")]//a/@href')
    Log.Info("### Poster url: {}".format(poster_url))
    info["poster_url"] = poster_url

    return info

  # content extraction helpers
  def get_string_content_from_xpath(self, source, query):
    return source.xpath('string(' + query + ')')

  def get_field_link_value(self, source, field_name):
    return self.get_string_content_from_xpath(source, './/div[contains(@class,"' +
                                              field_name + '")]//div[contains(@class,"jrFieldValue")]//a/text()')

  def get_field_value(self, source, field_name):
    return self.get_string_content_from_xpath(source, './/div[contains(@class,"' +
                                              field_name + '")]//div[contains(@class,"jrFieldValue")]/text()')

  # Retrieve all values of a Field that is a list
  def get_field_value_list(self, source, field_name):
    return source.xpath('.//div[contains(@class,"' +
                        field_name + '")]//div[contains(@class,"jrFieldValue")]//li//text()')
