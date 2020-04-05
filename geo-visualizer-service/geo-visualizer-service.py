import flask
import numpy as np
import pandas as pd
import requests

from flask import request, Response, jsonify
from flask_cors import CORS

segment_COUNT = 100

# Pandas to_dict flatten JSON hierarchy and add dots in prop name instead, this function recursively inflate the hierearchy
# Example: inflate_hierarchy({"a.b": 5, "a.c": 6}) --> {"a": {"b": 5, "c": 6}}
def inflate_hierarchy(obj):
    if isinstance(obj, list):
        result = []
        for item in obj:
            result.append(inflate_hierarchy(item))
        return result
    
    if not isinstance(obj, dict):
        return obj
    
    result = {}
    for prop in obj:
        index = prop.find('.')
        if index < 0:
            # Copy to result, but don't override if result already contains prop from previous iterations
            if prop in result:
                for subProp in obj[prop]:
                    result[prop][subProp] = obj[prop][subProp]
            else:
                result[prop] = obj[prop]
            continue
        
        propPrefix = prop[0:index]
        propSuffix = prop[index+1:]
        if not (propPrefix in result):
            result[propPrefix] = {}
        if propSuffix in result[propPrefix]:
            for subProp in obj[prop]:
                result[propPrefix][propSuffix][subProp] = obj[prop][subProp]
        else:
            result[propPrefix][propSuffix] = obj[prop]
    
    for prop in result:
        result[prop] = inflate_hierarchy(result[prop])
    
    return result

response = requests.get('https://gisweb02.z6.web.core.windows.net/Points.json')
points = response.json()
points_df = pd.io.json.json_normalize(points['features'])
# normalize date columns and set thm as index
points_df['fromTime'] = pd.to_datetime(points_df['properties.fromTime'] // 1000, unit='s')
points_df = points_df.set_index(pd.DatetimeIndex(points_df['fromTime']))
minTime = int(points_df['properties.fromTime'].min())
maxTime = int(points_df['properties.toTime'].max())

# Split time range into buckets

bucketTimes = range(minTime, maxTime, int((maxTime - minTime) / segment_COUNT))
timeRange = {
    'min': minTime,
    'max': maxTime,
    'bucketsMetadata': []
};

buckets = []
for i in range(0, segment_COUNT - 1):
    bucket = points_df.loc[ \
        (points_df['properties.toTime'] > bucketTimes[i]) & \
        (points_df['properties.fromTime'] < bucketTimes[i + 1])];
    
    # JSON serialization problems workaround
    nanDate = np.isnan(bucket['properties.Date'])
    bucket.loc[nanDate, 'properties.Date'] = [None] * len(bucket.loc[nanDate])
    
    bucketDict = bucket.to_dict(orient='records')
    
    # Reverse Pandas hierarchy flattenning
    bucketDict = inflate_hierarchy(bucketDict)
    
    if not bucket.empty:
        buckets.append({
            'type': 'FeatureCollection',
            'features': bucketDict
        });
        
        timeRange['bucketsMetadata'].append({
            'minTime': int(bucket['properties.fromTime'].min()),
            'maxTime': int(bucket['properties.toTime'].max())
        });

# http service setup

app = flask.Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def home():
    return 'Home'


@app.route('/timeRange', methods=['GET'])
def time_range():
    return jsonify(timeRange)

@app.route('/pointsByTimeBucket/<bucketIndex>', methods=['GET'])
def points_by_time_bucket(bucketIndex):
    return jsonify(buckets[int(bucketIndex)])

app.run(port=8090)