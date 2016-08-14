import os
import requests
import re
import shutil
from datetime import datetime
import time

def try_http_get(url):
    """
    Attempt to HTTP GET a url. Will try 3 times in case of ConnectionError.
    :param url:  The url to connect to.
    """
    i = 0
    while i < 3:
        try:
            resp = requests.get(url)
            return resp
        except requests.exceptions.ConnectionError:
            'Connecting to the Spotify API failed. Please check your internet connection. Program will attempt reconnection in 10 seconds.'
            time.sleep(10)
            continue
    raise Exception('Connection to Spotify API failed 3 times. Please check your internet connection.')


def lookup_album(artist_name, album_name):
    """
    Search for an album on Spotify API by artist name and album name, return all albums for matching search criteria.
    If nothing was found, None will be returned.
    This does not return all the data we need, just basic stuff. In order to receive more data about each album we're
    going to have  to call get_album_metadata with the album id found in the JSON response.
    :param artist_name:  The name of the artist.
    :param album_name: The name of the album.
    :return: A list of albums matching the search criteria or None if no albums were found.
    """
    resp = try_http_get('https://api.spotify.com/v1/search?q=album:%s artist:%s&type=album' % (album_name, artist_name))
    album_list = resp.json()['albums']['items']
    if len(album_list) < 1:
        #didn't find album
        return None
    return album_list


def get_album_metadata(album_id):
    """
    Gets album id and returns the metadata for that album.
    The metadata is parsed and returned as an Album object.
    :param album_id:  The album ID in Spotify (gotten from lookup_album)
    :return: Album object representing the album metadata.
    """
    resp = try_http_get('https://api.spotify.com/v1/albums/%s' % album_id)
    return Album(resp.json())


def download_image(image_url):
    """
    Gets a url to an image and download it, returning the binary response.
    :param image_url: The url to the image.
    :return: The image (as string encoded binary)
    """
    resp = try_http_get(image_url)
    return resp.content


class Album:
    """
    A class representing Album metadata. Should contain these attributes after being initialized:
    name (album name), artist (name of the artist/artists), release_date (as  datetime object)
    and a tracklist dictionary containing track names as keys and their number as values.
    """
    def __init__(self, json_resp):
        """
        Initialize an object based on the JSON response from Spotify API (/v1/albums/{album_id})
        :param json_resp: JSON response from Spotify API (/v1/albums/{album_id})
        """
        try:
            self.name = json_resp['name']
            self.artist = ''
            for artist in json_resp['artists']:
                self.artist += artist['name'] + ','
            self.artist = self.artist[:-1] # get rid of last ','
            self.date = datetime.strptime(json_resp['release_date'], '%Y-%m-%d')
            # self.genre = json_resp['genres'][0] - never managed to get Spotify api to actually return the genre.
            self.tracklist = {}
            for track in json_resp['tracks']['items']:
                self.tracklist[track['name']] = track['track_number']
            self.albumart = download_image(json_resp['images'][0]['url'])
        except KeyError:
            #key is missing in json response
            raise Exception('Error! Insufficent data for this album was found on Spotify . Sorry :(')






