#!/usr/bin/env python

from utils import utils, inspector
from bs4 import BeautifulSoup
from datetime import datetime
import urlparse

# options:
#   component: limit to a specific component. See COMPONENTS dict at bottom.
#   limit: only download X number of reports (per component)


def run(options):
  component = options.get('component', None)
  if component:
    components = [component]
  else:
    components = COMPONENTS.keys()

  limit = int(options.get('limit', 0))

  for component in components:
    print "## Fetching reports for component %s" % component
    url = url_for(options, component)
    body = utils.download(url)

    doc = BeautifulSoup(body)

    results = doc.select("table.contentpaneopen table[border=1] tr")
    # accept only trs that look like body tr's (no 'align' attribute)
    #   note: HTML is very inconsistent. cannot rely on thead or tbody
    results = filter(lambda x: x.get('align', None) is None, results)

    count = 0
    for result in results:
      report = report_from(result, component, url)
      inspector.save_report(report)

      count += 1
      if limit and (count >= limit):
        break

    print "## Fetched %i reports for component %s\n\n" % (count, component)


def report_from(result, component, url):
  report = {
    'inspector': 'dhs',
    'type': 'report' # can't seem to find any easy distinctions
  }

  # if component is a top-level DHS thing, file as 'dhs'
  # otherwise, the component is the agency for our purposes
  if component.startswith('dhs_'):
    report['agency'] = 'dhs'
  else:
    report['agency'] = component

  timestamp = result.select("td")[0].text.strip()
  published_on = datetime.strptime(timestamp, "%m/%d/%y")
  report['published_on'] = datetime.strftime(published_on, "%Y-%m-%d")
  report['year'] = published_on.year

  link = result.select("td")[2].select("a")[0]
  report_url = urlparse.urljoin(url, link['href'])
  title = link.text.strip()
  report['url'] = report_url
  report['title'] = title

  report_path = urlparse.urlsplit(report_url).path
  extension = report_path.split(".")[-1]
  report['file_type'] = extension

  report['report_id'] = result.select("td")[1].text.strip()

  print report

  return report


def url_for(options, component):
  base = "http://www.oig.dhs.gov/index.php?option=com_content&view=article"
  return "%s&id=%s&Itemid=%s" % (base, COMPONENTS[component][0], COMPONENTS[component][1])


# Component handle, with associated ID and itemID query string params
#   Note: I believe only the ID is needed.
# Not every component is an agency. Some of these will be collapsed into 'dhs'
#   for a report's 'agency' field.
# Some additional info on DHS components: https://www.dhs.gov/department-components
COMPONENTS = {
  'secret_service': (58, 49),
  'coast_guard': (19, 48),
  'uscis': (20, 47),
  'tsa': (22, 46),
  'ice': (24, 44),
  'fema': (25, 38),
  'cbp': (26, 37),
  'dhs_other': (59, 50),
  'dhs_mgmt': (23, 45),
  'dhs_cigie': (168, 150), # Council of the Inspectors General on Integrity and Efficiency
}

# 'Oversight areas' as organized by DHS. This is unused now, but
# could be used to run over the lists and associate a category with
# reports previously identified when running over each component.
# values are associated IT and itemID query strinhg params.
#   Note: I believe only the ID is needed.
AREAS = {
  'Border Security': (60, 30),
  'Counterterrorism': (61, 31),
  'Cybersecurity': (62, 32),
  'Disaster Preparedness, Response, Recovery': (63, 33),
  'Immigration': (64, 34),
  'Management': (33, 51),
  'Transportation Security': (66, 35),
}

utils.run(run)