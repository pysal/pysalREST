import numpy as np
import pysal as ps
import geojson

"""
Originally prototyped by Serge - I need this for the REST API
"""

class PolygonCollection:
    def __init__(self, polygons, bbox=None):
        """

        Parameters
        ==========
        polygons: dict
                  key is polygon Id, value is PySAL Polygon object
        bbox: list (optional)
              [left, lower, right, upper]

        Notes
        =====
        bbox is supported in geojson specification at both the feature and feature collection level. However, not all geojson writers generate the bbox at the feature collection level.
        In those cases, the bbox property will be set on initial access.

        """

        self.type=ps.cg.Polygon
        self.n = len(polygons)
        self.polygons = polygons
        if bbox is None:
            self._bbox = None
        else:
            self._bbox = bbox

    @property
    def bbox(self):
        bboxes = np.array([self.polygons[p].bbox for p in self.polygons])
        mins = bboxes.min(axis=0)
        maxs = bboxes.max(axis=0)
        self._bbox = [ mins[0], mins[1], maxs[2], maxs[3] ]
        return self._bbox

    def __getitem__(self, index):
        return self.polygons[index]


def find_features(d, key='features'):
    """
    Recursively search a nested dictionary for a 'features' key.
    This handles geojson extraction when the geojson object is not at the
     top level.
    """
    if 'features' in d:
        yield d[key]
    for k, value in d.iteritems():
        if isinstance(value, dict):
            for m in d[k].itervalues():
                for n in find_features(m):
                    yield n

def queen_geojson(gjobj):
    """
    Constructs a PySAL queen contiguity W from a geojson object.

    This is a modification to Serge's code that performs a search for
    """
    features = list(find_features(gjobj))[0]
    
    polys = []
    ids = []
    i = 0
    for feature in features:
        polys.append(ps.cg.asShape(feature['geometry']))
        ids.append(i)
        i += 1
    polygons = PolygonCollection(dict(zip(ids,polys)))
    neighbors = ps.weights.Contiguity.ContiguityWeightsPolygons(polygons).w
    return ps.W(neighbors)
