import config
import util

from audioitem import AudioItem

def cwd(parent, files):
    items = []
    for file in util.find_matches(files, config.SUFFIX_AUDIO_FILES):
        items += [ AudioItem(file, parent) ]
        files.remove(file)
    return items


def remove(files, items):
    del_items = []
    for item in items:
        for file in files:
            if item.type == 'audio' and item.filename == file:
                del_items += [ item ]
                files.remove(file)
                
    return del_items

