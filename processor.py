#!/usr/bin/env python
import cgi
import dbhandler
import json
import urllib

print "Content-Type: application/json"
print

form = cgi.FieldStorage()
mode = form.getvalue("mode")

try:
	eventid=form.getvalue("eventid")
	if mode.upper() == "LOG":
		table=dbhandler.showobslog(eventid)
	elif mode.upper() == "SUBMIT":
		obsid=form.getvalue("obsid")
		galid=form.getvalue("galid").replace(" ","+")
		state=form.getvalue("state")
		filter=form.getvalue("filter")
		depth=form.getvalue("depth")
		obsdatetime=form.getvalue("obsdatetime")
		observer=form.getvalue("observer")
		hastransient=form.getvalue("hastransient")
		dbhandler.addobservation(galid,eventid,obsid,state,filter,depth,obsdatetime,observer,hastransient)
		table=[ [ galid,eventid,obsid,state ] ]
	elif mode.upper() == "EVENT":
		table=dbhandler.showeventlog()
	elif mode.upper() == "CANDIDATE":
		table=dbhandler.showcandidates(eventid)
	elif mode.upper() == "ADMIN":
		state=form.getvalue("state")
		inserted=urllib.unquote(form.getvalue("inserted"))
		if state == "Ignore":
			dbhandler.setignoreevent(eventid,state,inserted)
		table=dbhandler.showeventlog()
	else:
		table=dbhandler.showeventlog()

except:
	table=dbhandler.showeventlog()

print   json.dumps(table)
