#!/usr/bin/python
import untangle
import os 
import io
import sys, getopt
import subprocess as sp

targetdir = ''
FFMPEG_BIN = "ffmpeg"

# http://stackoverflow.com/a/287944
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_help():
    print 'help'

def convert_xml(song):
	songname = os.path.basename(song).decode('utf-8')
	# Get current folder
	folder = songname
	info = folder.split(' - ')
	# Get artist info from folder name
	artist = info[0]
	title = info[1]

	# Parse XML file containing notes
	xml = untangle.parse(song + os.path.sep + 'notes.xml')

	# Get song "metadata"
	tempo = float(xml.MELODY['Tempo'])*2
	genre = xml.MELODY['Genre']
	year = xml.MELODY['Year']
	version = int(xml.MELODY['Version'])

	normpath = str(os.path.normpath(song)).split(os.sep)
	
	print "--------------------------------"
	print "Creating Ultrastar TXT:"
	print "XML Version: ", str(version)
	print "Edition: ", normpath[len(normpath)-2]
	print "Artist: ", artist
	print "Title: ", title
	print "Genre: ", genre
	print "Year: ", year
	print "BPM: ", str(tempo)
	print "Filename template: ", songname
	print " "

	#### Write Header ####
	content = unicode('')
	content += u'#EDITION:' + unicode(normpath[len(normpath)-2]) + u'\n'
	content += u'#ARTIST:' +  unicode(artist) + u'\n'
	content += u'#TITLE:' + unicode(title) + u'\n'
	content += u'#LANGUAGE:' + u'\n'
	content += u'#GENRE:' + unicode(genre) + u'\n'
	content += u'#YEAR:' + unicode(year) + u'\n'
	content += u'#BPM:' + unicode(tempo) + u'\n'
	content += u'#MP3:' + songname + u'.mp3' + u'\n'
	content += u'#BACKGROUND:' + songname + u'.png' + u'\n'
	content += u'#COVER:' + songname + u'.png' + u'\n'
	content += u'#VIDEO:' + songname + u'.m4v' + u'\n'
	content += u'#VIDEOGAP:' + u'\n'
	content += u'#GAP:' + u'\n'


	#### Parse Content ####
	start_delay = 0
	first = True
	pos = 0

	if version == 2:
		track = xml.MELODY.TRACK
	else:
		track = [0]

	for i in track:
		if version == 2:
			sent = i.SENTENCE
			player = str(i['Name'])
			if  player == 'Player1':
				content += 'P1\n'
			elif player == 'Player2':
				content += 'P2\n'

		else:
			sent = xml.MELODY.SENTENCE

		for sentence in sent:
			pitch = 0
			for note in sentence.NOTE:
				# Pitch
				pitch = note['MidiNote']
				# Duration
				duration = int(note['Duration'])
				# Lyric
				word = note['Lyric']

				# Check if it's the first line
				if first:
					first = False
					start_delay = duration

				# Check If it's a golden note
				golden = False
				if note['Bonus']:
					golden = True

				# Check if it's a freestyle note
				freestyle = False
				if note['Freestyle']:
					freestyle = True

				# Calculate timestamp
				marker = pos - start_delay

				# Exclude all unnecessary breaks
				if word != '':
					# Normal note
					if (not freestyle and not golden):
						content += u':' + u' ' + unicode(marker) + u' ' + unicode(duration) + u' ' + unicode(pitch) + u'  ' + unicode(word) + u'\n'
						#content += u' '.join((':', ' ', str(marker), ' ', str(duration), ' ', str(pitch), '  ', word, '\n')).encode('utf-8')

					# Golden note
					if golden:
						#content += '*' + ' ' + str(marker) + ' ' + str(duration) + ' ' + str(pitch) + '  ' + str(word) + '\n'
						content += u'*' + u' ' + unicode(marker) + u' ' + unicode(duration) + u' ' + unicode(pitch) + u'  ' + unicode(word) + u'\n'

					# Freestyle note
					if freestyle:
						#content += 'F' + ' ' + str(marker) + ' ' + str(duration) + ' ' + str(pitch) + '  ' + str(word) + '\n'
						content += u'F' + u' ' + unicode(marker) + u' ' + unicode(duration) + u' ' + unicode(pitch) + u'  ' + unicode(word) + u'\n'

				# Update current position		
				pos += duration

			# Calculate timestamp for end of sentence
			marker = pos - start_delay
			content += '-' + ' ' + str(marker) + '\n'

	content += 'E\n'
	content += '###########################################################'

	# Write to file
	try:
		print 'Writing to file',song+os.path.sep+songname.encode('utf-8')+'.txt'
		f = io.open(song+os.path.sep+songname.encode('utf-8')+'.txt', 'w', encoding='utf8')
		f.write(content)
		f.close()
	except IOError:
		print('There was an error while creating the .txt file of a song.')
		sys.exit(0)

def backup_files(song):
	FNULL = open(os.devnull, 'w')
	command = [ 'cp', '-r', song, targetdir+'backup'+os.path.sep+os.path.basename(song)]
	pipe = sp.Popen(command, stdout=FNULL, stderr=sp.STDOUT)

def convert_media(song):
	songname = os.path.basename(song)
	FNULL = open(os.devnull, 'w')
	# Convert OGG to MP3
	command = [ FFMPEG_BIN, '-y', '-i', song + os.path.sep + 'music.ogg','-acodec', 'libmp3lame', song + os.path.sep + songname + '.mp3']
	pipe = sp.Popen(command, stdout=FNULL, stderr=sp.STDOUT)
	pipe.communicate() # Wait for sp to finish
	# Rename Cover
	command = [ 'mv', song + os.path.sep + 'cover.png', song + os.path.sep + songname + '.png']
	pipe = sp.Popen(command, stdout=FNULL, stderr=sp.STDOUT)
	pipe.communicate() # Wait for sp to finish
	# Rename Video
	command = [ 'mv', song + os.path.sep + 'video.m4v', song + os.path.sep + songname + '.m4v']
	pipe = sp.Popen(command, stdout=FNULL, stderr=sp.STDOUT)
	pipe.communicate() # Wait for sp to finish
	# Rename xml
	command = [ 'mv', song + os.path.sep + 'notes.xml', song + os.path.sep + 'notes']
	pipe = sp.Popen(command, stdout=FNULL, stderr=sp.STDOUT)
	pipe.communicate() # Wait for sp to finish


def convert(song):
	backup_files(song)
	convert_xml(song)
	convert_media(song)

def create_backup_dir(directory):
	FNULL = open(os.devnull, 'w')
	command = [ 'mkdir',directory+'backup']
	pipe = sp.Popen(command, stdout=FNULL, stderr=sp.STDOUT)

def select_songs(songlist):
	print 'Select song from list by entering its index, or press enter to convert all songs in this directory.'
	select = sys.stdin.readline()
	if select == '\n':
		create_backup_dir(targetdir)
		for song in songlist:
			convert(song)
	else:
		try:
			int(select)
		except ValueError:
			print 'Please enter a valid number'
			print ""
			select_songs(songlist)
		else:
			create_backup_dir(targetdir)
			select = int(select)
			if select >= 0 and select < len(songlist):
				convert(songlist[select])
			else :
				print 'Please enter a number between 0 and', len(songlist)-1
				print ""
				select_songs(songlist)
	sys.exit()

def list_songs():
	# Create empty list
	songlist = []
	count = 0
	# Get subdirectories
	for song in os.listdir(targetdir):
		current_dir = os.path.join(targetdir, song)
		if os.path.isdir(current_dir):
			notesxml = 0
			audio = 0
			video = 0
			cover = 0
			# Check for karaoke files in folder
			for x in os.listdir(current_dir):
				if x.endswith('.xml'):
					notesxml = 1
				elif x.endswith('.ogg'):
					audio = 1
				elif x.endswith('.m4v'):
					video = 1
				elif x.endswith('.png'):
					cover = 1

			# Color green if all karaoke files are inside the folder
			if notesxml == 1 and audio == 1 and video == 1 and cover == 1:
				print bcolors.OKGREEN + '[', count, ']', song + bcolors.ENDC
				songlist.append(current_dir)
				count += 1
			# Color blue if only the notes.xml file is inside the folder
			elif notesxml == 1:
				print bcolors.OKBLUE + '[', count, ']', song + bcolors.ENDC
				songlist.append(current_dir)
				count += 1
			# Color red if there are no karaoke files inside the folder
			else:
				print bcolors.FAIL + song + bcolors.ENDC

	if len(songlist) == 0:
		print 'The provided directory doesnt contain any song subdirectories.'
		sys.exit()

	else:
		select_songs(songlist)

def main(argv):
	try:
		opts, args = getopt.getopt(argv,"hi:",["ifile="])
	except getopt.GetoptError:
		print_help()
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print_help()
			sys.exit()
		elif opt in ("-i", "--idir"):
			global targetdir
			targetdir = arg
			print 'Target directory is', targetdir
			list_songs()

if __name__ == "__main__":
   main(sys.argv[1:])
