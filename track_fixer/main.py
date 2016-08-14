from spotify_handler import *
from file_handler import *
import re
import shutil
import os

if __name__ == '__main__':
    #region User Choice
    print "Welcome to Track Fixer"
    print "What would you like the script to do? Type the appropriate number."
    print "1 - Fix ID3 data (aka MP3 metadata) for MP3 album (artist name, track number, etc)"
    print "2 - Download album art for MP3 album"
    print "3 - Both!"
    choice = raw_input("Choose now!\n")
    while not re.match("^[1-3]*$", choice) :
        choice = raw_input("Silly you, you were supposed to type in either 1, 2 or 3. Try again!\n")
    choice = int(choice)
    #endregion
    #region Album Lookup
    found = False

    while not found:
        artist_name = raw_input('Insert artist name:')
        if not re.match("^[a-zA-Z1-9\s]*$", artist_name):
            print "Error! Only letters and numbers are allowed! Please try again."
            continue

        album_name = raw_input('Insert album name:')
        if not re.match("^[a-zA-Z0-9\s]*$", album_name):
            print "Error! Only letters and numbers are allowed! Please try again."
            continue

        album_list = lookup_album('"' + artist_name + '"', '"' +album_name + '"' ) #add "s in order to focus lookup to exact names

        if album_list is None:
            #didn't find album, attempt to broaden search
            album_list = lookup_album(artist_name, album_name )
            if album_list is None:
                print 'Album not found! Please try again.'

        elif len(album_list) > 1:
            print "Found multiple albums. Which one were you looking for? please type the appropriate number!"
            for i in range(len(album_list)):
                print str(i+1) + ' - ' + album_list[i]['name']
            album_index = raw_input("Enter the number of the album you were looking for, or 'B' to go back.")
            while not re.match("^[Bb1-9]*$", album_index) :
                print 'Error! you were supposed to type in a number or the letter 'B' in order to go back. Please try again.'
                album_index = raw_input('Enter the number of the album you were looking for, or 'B' to go back.')
            while not len(album_index) <= int(album_index):
                print 'Error! the number you put in is too big! Please use the appropriate number from the list above.'
                album_index = raw_input('Enter the number of the album you were looking for, or 'B' to go back.')
            try:
                album = album_list[int(album_index)-1]
                found = True
            except ValueError:
                continue #user wanted to go back

        else:
            album = album_list[0]
            found = True
    #endregion
    #region Choose Path
    print 'You chose to fix tracks for album: ' + album['name'] + ', good choice!'
    path = os.path.abspath(raw_input("Insert the path where the album lives (the MP3 files):"))
    while not os.path.exists(path):
        path = os.path.abspath(raw_input("This path doesn't exist silly... Give me a real path please!"))
    #endregion
    #region Backup Files
    print "Backing up the files..."
    try:
        shutil.copytree(path, os.path.join(path, "Backup"))
    except:
        if raw_input("Couldn't back up the files. If you would like to continue after backing the files up manually type 'Y'").upper() != "Y":
            print 'You chose to end the program. Goodbye!'
            exit(1)
    #endregion
    #region Get track list and fix files
    album_obj = get_album_metadata(album['id'])
    files_update = fix_files(path, choice, album_obj)
    print 'Updated ' + str(files_update) + ' files successfully!'
    #endregion

