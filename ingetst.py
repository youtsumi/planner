#!/usr/bin/env python
#### INVOKED BY CRON
#### HOME=/subhome/hinotori.hiroshima-u.ac.jp
#### * * * * * ( cd ${HOME}/public_html/GW/planner/ && ${HOME}/bin/python ingetst.py ./ >> ./cronlog )
import dbhandler
import re
import os
import sys
import datetime

def ingest( path ):
	if os.path.exists(path) is not True:
		exit(-1)

	dt = datetime.datetime.fromtimestamp(os.stat(path).st_mtime)
	dtsec = (datetime.datetime.now() - dt).total_seconds()
	print path, dtsec

	if dtsec > 600:
		return

	p=re.compile("skyprob\.(.*)\.ascii")
	result=p.search(path)
	eventid=result.groups(0)[0]
	print eventid, path

	with open(path) as f:
		lines = f.readlines()
		dbhandler.ingestgallist(lines,eventid)
	os.system("mv %s %s/stored/" % ( path, os.path.dirname(path)) )

pathtodir=sys.argv[1]
print pathtodir, os.listdir(pathtodir)

for apath in filter(lambda x: True if re.search("^skyprob\.", x) is not None else False, os.listdir(pathtodir)):
	ingest(pathtodir+"/"+apath)
