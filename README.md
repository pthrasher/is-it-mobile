Is It Mobile?
=============

This is a tool that will test a list of domains to see if they have a mobile version. It can run multi threaded, it can output to a file in either json, or csv formats, and it can accept a custom input file (must be in alexa top one million csv format)

In addition, it can fetch the latest top one million list from alexa if you don't have a local list, or just want a fresh copy.

	# ./isitmobile.py -h  
	isitmobile.py: 
	This script tests whether or not sites have a mobile version
	    -h / --help         show this text
	    -q / --quiet        don't print to console
	    -o / --output=      File you want the output data to go (default: results.out)
	    -t / --type=        Putput data type (csv, json - default: json)
	    -f / --fetch        Fetch new list of top 1 million from alexa.com
	    -i / --input=       Specify a different input filename (default: top-1m.csv)
	    -n / --numhosts=    Number of top hosts's to test. (default: 1000)
	    -T / --threads=     Specify number of worker threads to spawn (default: 10)
