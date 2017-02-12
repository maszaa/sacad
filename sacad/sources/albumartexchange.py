import collections
import random

import lxml.cssselect
import lxml.etree

from sacad.cover import CoverImageFormat, CoverSourceQuality, CoverSourceResult
from sacad.sources.base import CoverSource


class AlbumArtExchangeCoverSourceResult(CoverSourceResult):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, source_quality=CoverSourceQuality.NORMAL, **kwargs)


class AlbumArtExchangeCoverSource(CoverSource):

  """ Cover source scraping www.albumartexchange.com. """

  BASE_URL = "http://www.albumartexchange.com"

  def __init__(self, *args, **kwargs):
    super().__init__(*args, min_delay_between_accesses=2, **kwargs)

  def updateHttpHeaders(self, headers):
    """ See CoverSource.updateHttpHeaders. """
    headers["User-Agent"] = "Mozilla/5.0 Firefox/%u.0" % (random.randint(4, 51))

  def getSearchUrl(self, album, artist):
    """ See CoverSource.getSearchUrl. """
    params = collections.OrderedDict()
    params["q"] = " ".join(map(__class__.unaccentuate,
                               map(str.lower,
                                   (artist, album))))
    params["fltr"] = "ALL"
    params["sort"] = "RATING"
    params["status"] = "RDY"
    size = (100 + self.size_tolerance_prct) * self.target_size // 100
    if size > 1000:
      params["size"] = "1001+"
    elif size > 800:
      params["size"] = "801-1000"
    elif size > 600:
      params["size"] = "601-800"
    return __class__.assembleUrl(__class__.BASE_URL + "/covers", params)

  def parseResults(self, api_data):
    """ See CoverSource.parseResults. """
    results = []
    parser = lxml.etree.HTMLParser()
    html = lxml.etree.XML(api_data.decode("utf-8", "ignore"), parser)
    results_selector = lxml.cssselect.CSSSelector(".grid-container .cover")
    box_selector = lxml.cssselect.CSSSelector(".img-box")
    info_selector = lxml.cssselect.CSSSelector(".image-info .dimensions")
    for i, result in enumerate(results_selector(html)):
      box = box_selector(result)[0]
      thumbnail_url = box.get("style").split("(", 1)[1].split(")", 1)[0]
      thumbnail_url = __class__.BASE_URL + thumbnail_url
      url_parts = thumbnail_url.split("/")
      url_parts[4] = "gallery"
      img_url = "/".join(url_parts)
      info_div = info_selector(result)[0]
      size = tuple(map(int,
                       lxml.etree.tostring(info_div,
                                           encoding="unicode",
                                           method="text").split("×")))
      results.append(AlbumArtExchangeCoverSourceResult(img_url,
                                                       size,
                                                       CoverImageFormat.JPEG,
                                                       thumbnail_url=thumbnail_url,
                                                       source=self,
                                                       rank=i))
    return results
