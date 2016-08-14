import os
import re
import eyed3


def normalize_track_name(name):
    """
    Gets file  or trackname and normalizes it, removing non-alphabetic/numeric chars in order to create correlation
    between file name and track name.
    :param name:  The name of the track/file
    :return: Normalized name (string)
    """
    name = name.split(".mp3", 1)[0]
    name = re.sub(r'[^0-9a-zA-Z() ]', '', name)
    return name.lower()


def fix_files(path, choice, album_obj):
    """
    Gets path, iterate through .mp3 files on it  and attempt to fix their ID3 metadata using data taken from Spotify API,
    represented by the spotify_handler.Album object.
    :param path: The path where the files are.
    :param choice: Value between 1-3, chosen by the user, 1 being fix metadata, 2 being fix album art, 3 being fix both.
    :param album_obj: Initialized spotify_handler.Album object, containing the metdata we wish to fix
    :return: number of files fixed.
    """
    cntr = 0

    for mp3_file in filter(lambda file: file.lower().endswith('.mp3'),os.listdir(path)):
        # for .mp3 files in path
        norm_file = normalize_track_name(mp3_file) # normalize file name
        for track in album_obj.tracklist.keys():
            # for tracks in album( as recieved from Spotify API
            if re.search(r'\b' + normalize_track_name(track) + r'\b', norm_file):
                # found track
                audiofile = eyed3.load(os.path.join(path, mp3_file))
                if audiofile.tag is None:
                    audiofile.tag = eyed3.id3.Tag()
                audiofile.tag.version = (2, 3, 0)# Windows appear not to like ID3 >2.3.0
                #region Fix ID3 Header
                if choice in (1, 3):
                    # User wanted to fix ID3 metadata
                    audiofile.tag.artist = unicode(album_obj.artist)
                    audiofile.tag.album = unicode(album_obj.name)
                    audiofile.tag.title = unicode(track)
                    audiofile.tag.track_num = album_obj.tracklist[track]
                    audiofile.tag.recording_date = album_obj.date
                    #audiofile.tag.genre = unicode(genre)
                #endregion
                #region Fix Album Art
                if choice in (2, 3):
                    # User wanted to fix ID3 album art
                    audiofile.tag.images.set(3, album_obj.albumart, "image/jpeg", u"Album Art")
                audiofile.tag.save(filename=os.path.join(path, mp3_file))
                #endregion
                break# found track, no need to continue

                cntr += 1
    return cntr