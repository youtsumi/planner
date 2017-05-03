#!/usr/bin/env python
import sqlite3
import os
import re
import datetime
import sys

path="./test.db"
fs=re.compile("[\t\s]+")

class myjoin:
    def __init__(self):
        self.arry = []

    def step(self, value):
        if value=="None":
            return
        self.arry.append( value )

    def finalize(self):
        return ", ".join(set(self.arry))

def adapt_datetime(ts):
    return time.mktime(ts.timetuple())

sqlite3.register_adapter(datetime.datetime, adapt_datetime)

def sqlite3connect( path ):
    conn = sqlite3.connect(path)
    return conn

def init( path ):
    if os.path.exists(path):
	os.remove(path) 
    conn=sqlite3connect(path)
    with conn:
	for sql in [
	    "create table candidates (galid, eventid, prob, inserted datetime);",
	    "create table galaxies (galid unique, ra, dec);",
	    "create table observation (galid, eventid, obsid, state, updated datetime, filter, depth, obsdatetime datetime, observer, hastransient );",
	    "create table events (eventid, inserted datetime, state);",
	    "create table observatories (obsid unique, password);"
	    ]:
	    print >> sys.stderr,  sql
	    conn.execute(sql)
    conn.close()

def ingestgallist( lines,eventid ):
    galaxies=map(lambda x: fs.split(x.rstrip()), lines[1:])
    conn = sqlite3.connect(path)
    now = datetime.datetime.now()
    msg = "insert into events values ( \"%s\", \"%s\", null); " % ( eventid, now )
    print  >> sys.stderr,  msg
    conn.execute(msg)
    for agalaxy in galaxies:
	galid = agalaxy[3]
	for msg in [
	    "insert into candidates values (\"%s\", \"%s\", %e, \"%s\");"
		% ( galid, eventid, float(agalaxy[0]), now ),
	    "insert into galaxies values (\"%s\", %lf, %lf);"
		% ( galid, float(agalaxy[1]), float(agalaxy[2]) ) ]:
	    print  >> sys.stderr,  msg
	    try:
	        conn.execute(msg)
	    except sqlite3.IntegrityError:
	        pass
    conn.commit()
    conn.close()

def showcandidates( eventid ):
    conn = sqlite3.connect(path)
    conn.create_aggregate("myjoin", 1, myjoin)
    cur = conn.cursor()

    msg = """
	select * from ( 
            select master.*, galaxies.ra, galaxies.dec,
	         ( select observation.state
	             from observation
	             	where observation.galid = master.galid
			and observation.eventid = \"%s\"
			order by observation.updated desc limit 1 ) as state,
	         ( select myjoin(observation.obsid)
	             from observation
	             	where observation.galid = master.galid
			order by observation.updated desc ) as observer,
	         ( select observation.updated
	             from observation
	             	where observation.galid = master.galid
			order by observation.updated desc limit 1 ) as updated,
	         ( select myjoin(observation.filter||"="||observation.depth)
	             from observation
	             	where observation.galid = master.galid 
				and observation.filter not like "None"
				and observation.depth not like "None"
			order by observation.updated desc ) as "filter and depth (5&sigma;AB)"
	         from ( select *
	             from candidates
	             where candidates.eventid == \"%s\" ) as master, galaxies
	             where master.galid = galaxies.galid
                     order by master.inserted asc
	         ) group by galid order by prob desc;
	""" % ( eventid, eventid )
    result = [ row for row in cur.execute( msg ) ]
    result.insert(0, [ col[0] for col in cur.description ])
    conn.close()
    return result

def showobslog( eventid ):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
#    msg = """
#	select observation.galid, ra,dec, eventid, obsid, state, updated, filter, depth
#	    from galaxies, observation
#	    where observation.eventid = \"%s\" 
#	    	and galaxies.galid=  observation.galid
#		order by observation.updated desc
#		;
#	""" % ( eventid )
    msg = """
	select galid, 
		( select galaxies.ra from galaxies
			where galaxies.galid = observation.galid limit 1 ) as ra,
		( select galaxies.dec from galaxies
			where galaxies.galid = observation.galid limit 1 ) as dec,
		eventid, obsid, state, updated, filter, depth, obsdatetime, observer, hastransient
	    from observation
	    where observation.eventid = \"%s\" 
		order by observation.updated desc
		;
	""" % ( eventid )

    result = [ row for row in cur.execute( msg ) ]
    result.insert(0, [ col[0] for col in cur.description ])
    conn.close()
    return result

def showeventlog( ):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    msg = """
	select *
	    from events
            order by inserted desc;
	"""
    result = [ row for row in cur.execute( msg ) ]
    result.insert(0, [ col[0] for col in cur.description ])
    conn.close()
    return result

def setignoreevent( eventid, flag, inserted, updated=None ):
    conn = sqlite3.connect(path)
    if updated==None:
        updated = datetime.datetime.now()
    for msg in [
#        """
#        insert into observation
#            select  galid, \"%s\", "admin", \"%s\", \"%s\"
#                from ( 
#                    select galid,eventid
#                        from candidates
#				where candidates.eventid = \"%s\"
#				and candidates.inserted = \"%s\"  );
#	""" % ( eventid, flag, updated, eventid, inserted ),
        """
        update events set state = \"%s\" where eventid = \"%s\" and inserted = \"%s\"
        """ % ( flag, eventid, inserted )]:
#    print msg
        conn.execute(msg)
    conn.commit()
    conn.close()

def addobservation( galid, eventid, obsid, state, filter="N/A", depth="N/A", obsdatetime="N/A", observer="N/A", hastransient="N/A", updated=None ):
    try:
        if updated==None:
    	    updated = datetime.datetime.now()
        conn = sqlite3.connect(path)
        msg = """
    	insert into observation values (\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\");
    	""" % ( galid, eventid, obsid, state, updated, filter, depth, obsdatetime, observer, hastransient )
        print  >> sys.stderr,  msg
        conn.execute(msg)
        conn.commit()
        conn.close()
    except Exception as ex:
        print ex.reason

if __name__=="__main__":
    eventid="G268556"
   # init(path)
    for eventid in ["G270580"]:
#    for eventid in ["G268556", "M266380","M263908","M263909","M263911","M263912","M263913"]:
        with open("skyprob.%s.ascii" % eventid ) as f:
            lines = f.readlines()
            ingestgallist(lines,eventid)
#    print showcandidates(eventid)
#    setignoreevent( "M266380", "Ignore", "2017-01-20 14:01:13.822307" )
#    addobservation( "GL092844+590022", eventid, "HASC-HONIR", "Reserved" )
#    addobservation( "GL092844+590022", eventid, "HASC-HOWPOL", "Reserved" )
#    addobservation( "GL100513+675234", eventid, "HASC-HOWPOL", "Reserved" )
#    addobservation( "GL084526+524504", eventid, "HASC-HOWPOL", "Observed" )
#    print showobslog(eventid)
    
