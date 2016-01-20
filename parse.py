# coding: utf-8
import os
import json
import glob
from normality import slugify
from datetime import datetime
from pprint import pprint # noqa

from common import DATA_PATH, database

SOURCE_PATH = os.path.join(DATA_PATH, 'raw')
try:
    os.makedirs(SOURCE_PATH)
except:
    pass

# IGNORE_LAYERS = ['Farms', 'Region', 'Districts',
#                  'Withdrawn Areas', 'Divisions',
#                  'Environmentally Sensitive Areas',
#                  'Claims',
#                  u'Áreas de Conservação - Buffer',
#                  u'Áreas de Conservação',
#                  u'Áreas Reservadas']


def convrow(data):
    row = {}
    for name, val in data.items():
        name = name.upper()
        if name.startswith('DTE') and val is not None:
            dt = datetime.fromtimestamp(int(val) / 1000)
            val = dt.date().isoformat()
        if name.startswith('GUID'):
            continue
        if name == 'AREA':
            val = min(val, (2 ** 31) - 1)
        if name == 'ID':
            name = 'FC_ID'
        if val is None or not len(unicode(val).strip()):
            continue
        row[slugify(name, sep='_')] = val
    return row


def parse_file(path):
    with open(path, 'rb') as fh:
        ctx = json.load(fh)

    # if ctx['source_name'] not in ['MZ']:
    #    return

    all_name = slugify('%(source_name)s flexicadastre' % ctx, sep='_')
    all_tbl = database[all_name]
    all_tbl.delete()

    layers = ctx.pop('layers')
    for layer in layers:
        lctx = ctx.copy()
        lctx['layer_name'] = layer['name']
        lctx['layer_id'] = layer['id']
        del lctx['rest_url']

        tbl_name = slugify('%(source_name)s %(layer_name)s' % lctx, sep='_')
        tbl = database[tbl_name]
        tbl.delete()

        features = layer['data']['features']
        print ' -> Generating:', tbl_name
        print '    ', layer['name'], layer['id'], len(features)

        for feature in features:
            attrs = convrow(feature.get('attributes'))
            attrs.update(lctx)
            tbl.insert(attrs)
            all_tbl.insert(attrs)


if __name__ == '__main__':
    for file_path in glob.glob(os.path.join(SOURCE_PATH, '*')):
        parse_file(file_path)
