# coding: utf-8
import os
import json
import glob
import dataset
from normality import slugify
from sqlalchemy import BigInteger
from datetime import datetime
from pprint import pprint # noqa

from common import DATA_PATH, database


SOURCE_PATH = os.path.join(DATA_PATH, 'raw')
try:
    os.makedirs(SOURCE_PATH)
except:
    pass

DEST_PATH = os.path.join(DATA_PATH, 'csv')
try:
    os.makedirs(DEST_PATH)
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
        row[name] = val
    return row


def column_types(row):
    types = {}
    for k, v in row.items():
        if isinstance(v, int):
            types[k] = BigInteger
    return types


def parse_file(path):
    with open(path, 'rb') as fh:
        ctx = json.load(fh)

    #if ctx['source_name'] not in ['MZ']:
    #    return

    layers = ctx.pop('layers')
    for layer in layers:
        lctx = ctx.copy()
        lctx['layer_name'] = layer['name']
        lctx['layer_id'] = layer['id']
        lctx.pop('rest_url', None)

        tbl_name = slugify('%(source_name)s %(layer_name)s' % lctx, sep='_')
        database[tbl_name].drop()
        tbl = database[tbl_name]

        features = layer['data']['features']
        print ' -> Generating:', tbl_name
        print '    ', layer['name'], layer['id'], len(features)

        types = None
        for feature in features:
            attrs = convrow(feature.get('attributes'))
            attrs.update(lctx)
            attrs.pop('id', None)
            if types is None:
                types = column_types(attrs)
            tbl.insert(attrs, types=types)

        dataset.freeze(tbl, prefix=DEST_PATH, filename='%s.csv' % tbl_name, format='csv')


if __name__ == '__main__':
    for file_path in glob.glob(os.path.join(SOURCE_PATH, '*')):
        parse_file(file_path)
