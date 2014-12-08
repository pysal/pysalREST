import hashlib
import os
import time
import zipfile
from config import ALLOWED_EXTENSIONS

def allowed_file(filename):
    """
    Check that the uploaded file extensions is in the approved list.

    Parameters
    -----------
    filename    (str) The filename, with extension

    Returns
    --------
    Boolean     (bool) True if accepted, else false
    """
    return '.' in filename and \
            filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS

def unzip(filename, path):
    """
    Safe file unzip function.
    """
    with zipfile.ZipFile(filename) as zf:
        for m in zf.infolist():
            words = m.filename.split('/')
            destination = path
            for w in words[:-1]:
                drive, w = os.path.splitdrive(w)
                head, w = os.path.split(w)
                if w in (os.curdir, os.pardir, ''):
                    continue
                destination = os.path.join(path, w)
            zf.extract(m, destination)
    return

def hashname(filename, cuid=None):
    """
    Take a filename and hash into a valid database table name
    in the form userid_shapefilename_timestamp
    """
    basename = os.path.basename(filename.split('.')[0]).lower()
    hashl = hashlib.sha1()
    hashl.update(str(time.time()))

    return '{}_{}_{}'.format(cuid, basename, hashl.hexdigest())
