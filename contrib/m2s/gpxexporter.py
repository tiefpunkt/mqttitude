#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__    = 'Jan-Piet Mens <jpmens()gmail.com>'
__copyright__ = 'Copyright 2013 Jan-Piet Mens'

# I'm doing this 'manually' for now. (I could have used gpxpy from 
# https://github.com/tkrajina/gpxpy, but I find that more complicated
# than doing it myself. :| )

import sys
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.etree import ElementTree as ET
from ElementTree_pretty import prettify
from dbschema import Location
from datetime import datetime
from dateutil import tz
import getopt


def print_usage():
    print "gpxexporter -u username -d device -f fromdate -t todate -T title [-X]"

def main(argv):
    from_date = '2013-11-24'
    to_date = '2013-11-28'
    username = None
    device = None
    title = 'My Trip'
    xcode = False

    try:
        opts, args = getopt.getopt(argv, "f:t:u:d:T:X",
            ["from", "to", "username", "device", 'Title', 'Xcode' ])
    except getopt.GetoptError as e:
        print_usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-d', '--device'):
            device = arg
        if opt in ('-u', '--username'):
            username = arg
        if opt in ('-f', '--from'):
            from_date = arg
        if opt in ('-t', '--to'):
            to_date = arg
        if opt in ('-T', '--title'):
            title = arg
        if opt in ('-X', '--Xcode'):
            xcode = True

    if username is None:
        print "You must provide a username"
        sys.exit(2)
    if device is None:
        print "You must provide a device name"
        sys.exit(2)
    
    root = ET.Element('gpx')
    root.set('version', '1.0')
    root.set('creator', 'MQTTitude GPX Exporter')
    root.set('xmlns', "http://www.topografix.com/GPX/1/0")
    root.append(Comment('Hi JP'))

    if not xcode:
        track = Element('trk')
        track_name = SubElement(track, 'name')
        track_name.text = title
        track_desc = SubElement(track, 'desc')
        track_desc.text = "Length: xxx km or so"

        segment = Element('trkseg')
        track.append(segment)

    trackpoints = []
    waypoints = []

    query = Location.select().where(
                (Location.username == username) & 
                (Location.device == device) &
                (Location.tst.between(from_date, to_date))
                )
    query = query.order_by(Location.tst.asc())
    for l in query:
    
        dbid    = l.id
        topic   = l.topic
        lat     = l.lat
        lon     = l.lon
        dt      = l.tst
        weather = l.weather
        revgeo  = l.revgeo
        desc    = l.waypoint

        tp = Element('trkpt')
        tp.set('lat', lat)
        tp.set('lon', lon)
        tp_time = SubElement(tp, 'time')
        tp_time.text = dt.isoformat()[:19]+'Z'
        tp.append(Comment(u'#%s %s' % (dbid, topic)))
        trackpoints.append(tp)
    
        if xcode:
            wpt = Element('wpt')
            wpt.set('lat', lat)
            wpt.set('lon', lon)
            waypoints.append(wpt)

        else:
            if (weather is not None and revgeo is not None) or (desc is not None):
    
                wpt = Element('wpt')
                wpt.set('lat', lat)
                wpt.set('lon', lon)
                wpt_name = SubElement(wpt, 'name')
                wpt_name.text = u'%s' % (dt.isoformat()[:19]+'Z')
                wpt_desc = SubElement(wpt, 'desc')
                if desc is not None:
                    wpt_desc.text = u'%s' % (desc)
                else:
                    wpt_desc.text = u'(%s) %s' % (weather, revgeo)
    
                waypoints.append(wpt)
    
    
    root.extend(waypoints)

    if not xcode:
        root.append(track)
        segment.extend(trackpoints)
    
    print prettify(root)
    
    #tree = ET.ElementTree(root)
    #tree.write('p.xml',
    #    xml_declaration=True, encoding='utf-8',
    #    method="xml")

if __name__ == '__main__':
    main(sys.argv[1:])
