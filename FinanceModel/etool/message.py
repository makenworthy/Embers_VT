#!/usr/bin/env python

import logging
import hashlib
import dateutil.parser
import datetime

log = logging.getLogger(__name__)

def add_embers_ids(obj, parent_id=None, derived_ids=None):
    '''
    Create an EMBERS identifier for an object if none exists. 
    The id is just a SHA1 hash of the object content.
    '''
    if not obj.has_key('embersId'):
        obj['embersId'] = hashlib.sha1(str(obj)).hexdigest()

    if parent_id:
        obj['parentId'] = parent_id

    if derived_ids:
        obj['derivedIds'] = derived_ids

    return obj

def normalize_date(obj, path):
    '''
    Find a date field in an object and convert it to
    a UTC ISO formatted date and write it back as 
    the 'date' field of the object.
    path - a field name, or array of field names describing the path to the source field.
    '''
    if obj.has_key('date'):
        return obj

    value = None
    if isinstance(path, basestring):
        value = obj.get(path, None)
    else:
        tmp = obj
        for p in path:
            if isinstance(tmp, dict):
                tmp = tmp.get(p, None) 
        
        value = tmp

    result = None
    if isinstance(value, basestring):
        try:
            dt = dateutil.parser.parse(value)
            tt = dt.utctimetuple()
            # this is painful, but the only way I could figure to normalize the date
            # naive dates (e.g. datetime.now()) will have no conversion
            dt = datetime.datetime(*tt[0:6])
            result = dt.isoformat()
        except Exception as e:
            log.exception('Could not parse date "%s"', value)

    obj['date'] = result
    return obj
