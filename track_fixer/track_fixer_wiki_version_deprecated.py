import xml.etree.ElementTree as ET
import urllib
import re
import eyed3
import os
import shutil


def normalize_filename(fileName):
    # Get file name and normalizes it, removing non-alphabetic/numeric chars
    # and replacing and "-","_" with whitespace, for later comparison
    return re.sub("[^0-9a-zA-Z() ]+", "", re.sub("[-_]", " ", fileName.split(".mp3", 1)[0])).title()


def try_conn(url):
    # Attempts connection to a URL. If successful, returns the page's contents. Else, throws you out.
    try:
        url = urllib.urlopen(url)
        return url.read()
    except IOError:
        print "Error: You have no internet access! Get yourself some internets and try again!"
        exit(1)


def query_wikipedia(albumName, artistName):
    # Queries Wikipedia for album details in various ways. If successful, returns the XML's relevant data as a string..
    # Else, returns None.
    print "Querying Wikipedia for album %s..." % (albumName)
    urlContents = try_conn(
        "http://en.wikipedia.org/w/api.php?format=xml&action=query&titles=" + albumName + "&prop=revisions&rvprop=content&redirects=yes")
    if "Infobox album" not in urlContents:
        urlContents = try_conn(
            "http://en.wikipedia.org/w/api.php?format=xml&action=query&titles=" + albumName + "_%28" + artistName + "_album%29&prop=revisions&rvprop=content&redirects=yes")
        if "Infobox album" not in urlContents:
            urlContents = try_conn(
                "http://en.wikipedia.org/w/api.php?format=xml&action=query&titles=" + albumName + "_%28album%29&prop=revisions&rvprop=content&redirects=yes")
            if "Infobox album" not in urlContents:
                print "Error: Couldn't find album on Wikipedia"
                exit(1)
    print "Query successful!"
    return ET.fromstring(urlContents).findall("query/pages/page/revisions/rev")[0].text


def parse_wikipedia_data(data, choice):
    # Gets the data from the query and parses it, returning only the relevant data according to the user's choice,
    # neatly ordered.
    year = None
    genre = None
    tracklist = None
    titles = None  # check later
    albumart = None
    if choice in (1, 2, 3):  # fix later
        # Creates a dictionary in format - "TrackName:TrackNumber", for ID3 data fixing.
        try:
            if "{{tracklist" in data:
                tracklist = data.lower().split("{{tracklist", 1)[1].split("}}", 1)[0].split("\n")
            else:
                tracklist = data.lower().split("{{track list", 1)[1].split("}}", 1)[0].split("\n")
        except:
            print "Critical Error: there was a problem processing the data from the query. Sorry :("
            exit(1)
        try:
            if "{{Start date|" in data:
                year = data.split("Released   = {{Start date|")[1].split("|", 1)[0]
            else:
                year = data.split("Released   = ")[1].split(" ", 3)[2].split("\n")[0]
            genre = data.split("| Genre      = [[", 1)[1].split("]]", 1)[0]
        except:
            if raw_input(
                    "There was a problem extracting the genre and year fields from Wikipedia. Type 'Y' to skip these, or any other key to quit.").upper() != "Y":
                exit(1)
        cntr = 1
        titles = dict()
        for i in tracklist:
            if i.startswith("| title"):
                try:
                    if i.rfind("|") != 0:
                        titles.update(
                            {(re.sub("[^0-9a-zA-Z() ]+", "", str(i.split("|")[2].split("]]")[0])).title()): cntr})
                    elif i.find("[[") != -1:
                        titles.update(
                            {(re.sub("[^0-9a-zA-Z() ]+", "", str(i.split("[[")[1].split("]]")[0])).title()): cntr})
                    else:
                        titles.update({re.sub("[^0-9a-zA-Z() ]+", "", str(i.split("= ")[1])).title(): cntr})
                except:
                    pass
                cntr += 1

    if choice in (2, 3):
        # Attempting to extract album art from Wikipedia.
        data = re.sub(" +", " ", data)
        imageUrl = data.split("| Cover = ")[1].split("\n", 1)[0].replace(" ", "_")
        imagePage = try_conn(
            "http://en.wikipedia.org/w/api.php?format=xml&action=query&titles=File:" + imageUrl + "&prop=imageinfo&iiprop=url&redirects=yes")
        albumart = try_conn(ET.fromstring(imagePage).findall("query/pages/page/imageinfo/ii")[0].attrib["url"])

    return titles, year, genre, albumart


if __name__ == "__main__":
    print "Welcome to Track Fixer"
    print "What would you like the script to do? Type the appropriate number."
    print "1 - Fix ID3 data (aka MP3 metadata) for MP3 album (artist name, track number, etc)"
    print "2 - Download album art for MP3 album"
    print "3 - Both!"
    while True:
        try:
            choice = int(raw_input("Choose now!\n"))
            if choice in (1, 2, 3):
                break
            else:
                raise
        except:
            print "Silly you, you were supposed to type in 1, 2 or 3."

    artistName = raw_input("Insert Artist Name:")
    albumName = raw_input("Insert Album Name:")
    path = os.path.abspath(raw_input("Insert path for files:"))

    print "Backing up the files..."
    try:
        shutil.copytree(path, os.path.join(path + "\\Backup"))
    except:
        if raw_input(
                "Couldn't back up the files. If you would like to continue after backing the files up manually type 'Y'").upper() != "Y":
            exit(1)

    data = query_wikipedia(albumName,
                           artistName)  # tracklist for the album, basically take everything from "{{tracklist" or "{{track list" to "}}" in the XML.
    titles, year, genre, albumArt = parse_wikipedia_data(data,
                                                         choice)  # tracklist for the album, basically take everything from "{{tracklist" or "{{track list" to "}}" in the XML.

    cntr = 0
    for file in os.listdir(path):
        if file.lower().endswith(".mp3"):
            normFile = normalize_filename(file)
            for title in titles.keys():
                if (title in normFile):
                    audiofile = eyed3.load(os.path.join(path, file))
                    audiofile.tag.version = (2, 3, 0)
                    if choice in (1, 3):
                        audiofile.tag.artist = unicode(artistName)
                        audiofile.tag.album = unicode(albumName)
                        audiofile.tag.title = unicode(title)
                        audiofile.tag.track_num = titles[title]
                        audiofile.tag.recording_date = year
                        audiofile.tag.genre = unicode(genre)
                    if choice in (2, 3):
                        audiofile.tag.images.set(3, albumArt, "image/jpeg", u"Album Art")
                    audiofile.tag.save()
                    cntr += 1

    print "Updated %i out of %i files successfully!" % (cntr, len(titles))
