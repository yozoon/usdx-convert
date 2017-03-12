#!/usr/bin/python
import untangle
import os 
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
	songname = os.path.basename(song)
	# Get current folder
	folder = str(songname)
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

	normpath = str(os.path.normpath(song)).split(os.sep)

	#### Write Header ####
	content = ''
	content += '#EDITION:' + normpath[len(normpath)-2] + '\n'
	content += '#ARTIST:' +  artist + '\n'
	content += '#TITLE:' + title + '\n'
	content += '#LANGUAGE:' + '\n'
	content += '#GENRE:' + genre + '\n'
	content += '#YEAR:' + year + '\n'
	content += '#BPM:' + str(tempo) + '\n'
	content += '#MP3:' + songname + '.mp3' + '\n'
	content += '#BACKGROUND:' + songname + '.png' + '\n'
	content += '#COVER:' + songname + '.png' + '\n'
	content += '#VIDEO:' + songname + '.m4v' + '\n'
	content += '#VIDEOGAP:' + '\n'
	content += '#GAP:' + '\n'


	#### Parse Content ####
	start_delay = 0
	first = True
	pos = 0

	for sentence in xml.MELODY.SENTENCE:
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
					content += ':' + ' ' + str(marker) + ' ' + str(duration) + ' ' + str(pitch) + '  ' + word + '\n'

				# Golden note
				if golden:
					content += '*' + ' ' + str(marker) + ' ' + str(duration) + ' ' + str(pitch) + '  ' + word + '\n'

				# Freestyle note
				if freestyle:
					content += 'F' + ' ' + str(marker) + ' ' + str(duration) + ' ' + str(pitch) + '  ' + word + '\n'

			# Update current position		
			pos += duration

		# Calculate timestamp for end of sentence
		marker = pos - start_delay
		content += '-' + ' ' + str(marker) + '\n'

	content += 'E\n'
	content += '###########################################################'

	# Write to file
	try:
		print 'Writing to file',song+os.path.sep+songname+'.txt'
		f = open(song+os.path.sep+songname+'.txt', 'w')
		f.write(content)
		f.close()
	except:
		print('Something went wrong!')
		sys.exit(0)

def convert_media(song):
	songname = os.path.basename(song)
	FNULL = open(os.devnull, 'w')
	# Convert OGG to MP3
	command = [ FFMPEG_BIN, '-y', '-i', song + os.path.sep + 'music.ogg','-acodec', 'libmp3lame', song + os.path.sep + songname + '.mp3']
	pipe = sp.Popen(command, stdout=FNULL, stderr=sp.STDOUT)
	# Rename Cover
	command = [ 'mv', song + os.path.sep + 'cover.png', song + os.path.sep + songname + '.png']
	pipe = sp.Popen(command, stdout=FNULL, stderr=sp.STDOUT)
	# Rename Video
	command = [ 'mv', song + os.path.sep + 'video.m4v', song + os.path.sep + songname + '.m4v']
	pipe = sp.Popen(command, stdout=FNULL, stderr=sp.STDOUT)
	# Rename xml
	command = [ 'mv', song + os.path.sep + 'notes.xml', song + os.path.sep + 'notes']
	pipe = sp.Popen(command, stdout=FNULL, stderr=sp.STDOUT)


def convert(song):
	convert_xml(song)
	convert_media(song)

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

			if notesxml == 1 and audio == 1 and video == 1 and cover == 1:
				print bcolors.OKGREEN + '[', count, ']', song + bcolors.ENDC
				songlist.append(current_dir)
			elif notesxml == 1:
				print bcolors.OKBLUE + '[', count, ']', song + bcolors.ENDC
				songlist.append(current_dir)
			else:
				print bcolors.FAIL + '[', count, ']', song + bcolors.ENDC

			count += 1
	if len(songlist) == 0:
		sys.exit()
	else:
		print 'Select song from list by entering its index, or press enter to convert all songs in this directory.'
		select = sys.stdin.readline()
		if select == '\n':
			for song in songlist:
				convert(song)
		else:
			select = int(select)
			if select >= 0 and select < len(songlist):
				print 'go'
				convert(songlist[select])
		sys.exit()

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
