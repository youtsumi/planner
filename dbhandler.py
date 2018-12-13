#!/subhome/hinotori.hiroshima-u.ac.jp/bin/python
# -*- coding: utf-8 -*-
"""
This script contains core routines to enable the planner system
"""
import sqlite3
import os
import re
import datetime, time
import sys
from dateutil.parser import parse

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
	    "create table galaxies (galid unique, ra, dec, dist);",
	    "create table observation (galid, eventid, obsid, state, updated datetime, filter, depth, obsdatetime datetime, observer, hastransient );",
	    "create table events (eventid, inserted datetime, state);",
	    "create table observatories (obsid unique, password);"
	    "create table obsgroups (obsid unique, obsgroup );"
	    ]:
	    print >> sys.stderr,  sql
	    conn.execute(sql)
    conn.close()

def ingestgallist( lines,eventid ):
    galaxies=map(lambda x: fs.split(x.rstrip()), lines[1:])
    conn = sqlite3.connect(path)
    now = datetime.datetime.utcnow()
    msg = "insert into events values ( \"%s\", \"%s\", null); " % ( eventid, now )
    print  >> sys.stderr,  msg
    conn.execute(msg)
    for agalaxy in galaxies:
	try:
	    galid = agalaxy[3]
	except:
	    continue
	
	for msg in [
	    "insert into candidates values (\"%s\", \"%s\", %e, \"%s\");"
		% ( galid, eventid, float(agalaxy[0]), now ),
	    "insert or replace into galaxies values (\"%s\", %lf, %lf, %lf);"
		% ( galid, float(agalaxy[1]), float(agalaxy[2]), float(agalaxy[4]) ) ]:
	    print  >> sys.stderr,  msg
	    try:
	        conn.execute(msg)
	    except sqlite3.IntegrityError:
	        pass
    conn.commit()
    conn.close()

def showcandidates( eventid, excludelist=None, includelist=None, group=None ):
    conn = sqlite3.connect(path)
    conn.create_aggregate("myjoin", 1, myjoin)
    conn.enable_load_extension(True)
    conn.execute("select load_extension('libsqlitefunctions')")
    cur = conn.cursor()

    msg = """
    	select inserted from events
		where events.eventid="%s" order by inserted desc limit 1   
    	""" % eventid
    cur.execute(msg)
    result = [ row for row in cur.execute( msg ) ][0][0]
    ndays = (datetime.datetime.utcnow()-parse(result)).total_seconds()/3600/24

    if excludelist is not None:
        msg = """
    	create temporary view subobservation as select * 
    		from observation
    			where obsid not in ( %s )
    	""" % ( ",".join( map( lambda x: "\"%s\"" % x, excludelist ) ) )
    elif includelist is not None:
        msg = """
    	create temporary view subobservation as select * 
    		from observation
    			where obsid in ( %s )
    	""" % ( ",".join( map( lambda x: "\"%s\"" % x, includelist ) ) )
    elif group is not None:
        msg = """
    	create temporary view subobservation as select * 
    		from observation, obsgroups
    			where 
    			    observation.obsid = obsgroups.obsid
    			    and obsgroups.obsgroup in ( %s )
    	""" % ( ",".join( map( lambda x: "\"%s\"" % x, group ) ) )
    else:
        msg = """
    	create temporary view subobservation as select * 
    		from observation
    	"""

    cur.execute(msg)

    msg = """
	select * from ( 
            select master.*, galaxies.ra, galaxies.dec, galaxies.dist,
		round(0.7*min(%d,5)+9+5*log10(galaxies.dist),1) as OptExpected,  --- from Masaomi san's rough estimation
		round(10+5*log10(galaxies.dist),1) as NirExpected,  --- from Utsumi 's rough estimation
 	         ( select subobservation.state
 	             from subobservation
 	             	where subobservation.galid = master.galid
 				and subobservation.eventid = master.eventid
 			order by subobservation.updated desc limit 1 ) as state,
 	         ( select myjoin(subobservation.obsid)
 	             from subobservation
 	             	where subobservation.galid = master.galid
 				and subobservation.eventid = master.eventid
 			order by subobservation.updated desc ) as obsids,
 	         ( select subobservation.updated
 	             from subobservation
 	             	where subobservation.galid = master.galid
 				and subobservation.eventid = master.eventid
 			order by subobservation.updated desc limit 1 ) as updated,
 	         ( select myjoin(subobservation.filter||"="||subobservation.depth)
 	             from subobservation
 	             	where subobservation.galid = master.galid 
 				and subobservation.eventid = master.eventid
 				and subobservation.filter not like "None"
 				and subobservation.depth not like "None"
 			order by subobservation.updated desc ) as "filter and depth (5&sigma;AB)",
	         ( select subobservation.hastransient
	             from subobservation
	             	where subobservation.galid = master.galid
				and subobservation.eventid = master.eventid
				and subobservation.hastransient not in ( "None" )
			order by subobservation.updated desc limit 1 ) as hastransient
	         from ( select *
	             from candidates
	             where candidates.eventid == \"%s\"  ) as master -- 先に eventid が一致する candidates を得る
			, galaxies
	             where master.galid = galaxies.galid
                     order by  master.inserted asc
	         ) group by galid order by prob desc;
	""" % ( ndays, eventid )
    result = [ row for row in cur.execute( msg ) ]
    result.insert(0, [ col[0] for col in cur.description ])
    conn.close()
    return result

def showobslog( eventid ):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
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

def showobsgroup( ):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    msg = """
	select reported.obsid as obsid,
		( select obsgroups.obsgroup
		from obsgroups
		where obsgroups.obsid=reported.obsid ) as obsgroup 
	from ( select obsid
		from observation group by obsid order by obsid ) as reported;
	"""
    result = [ row for row in cur.execute( msg ) ]
    result.insert(0, [ col[0] for col in cur.description ])
    conn.close()
    return result

def setignoreevent( eventid, flag, inserted, updated=None ):
    conn = sqlite3.connect(path)
    if updated==None:
        updated = datetime.datetime.utcnow()
    for msg in [
        """
        update events set state = \"%s\" where eventid = \"%s\" and inserted = \"%s\"
        """ % ( flag, eventid, inserted )]:
        conn.execute(msg)
    conn.commit()
    conn.close()

def setignoreeventifndayspassed( ndays=3 ):
    conn = sqlite3.connect(path)
    ndaysbefore = datetime.datetime.utcnow()-datetime.timedelta(ndays)
    for msg in [
        """
        update events set state = \"Ignore\" where eventid like  \"_______\" and inserted < \"%s\"
        """ % ( ndaysbefore)]:
        print msg
        conn.execute(msg)
    conn.commit()
    conn.close()

def addobservation( galid, eventid, obsid, state, filter="N/A", depth="N/A", obsdatetime="N/A", observer="N/A", hastransient="N/A", updated=None ):
    try:
        if updated==None:
    	    updated = datetime.datetime.utcnow()
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
    eventid="U181121"
#    init(path)
#    for eventid in ["G270580"]:
#    for eventid in ["G268556", "M266380","M263908","M263909","M263911","M263912","M263913"]:
#        with open("skyprob.%s.ascii" % eventid ) as f:
#            lines = f.readlines()
#            ingestgallist(lines,eventid)
    print showcandidates(eventid,group=["A"])
#    setignoreevent( "M266380", "Ignore", "2017-01-20 14:01:13.822307" )
#    addobservation( "GL092844+590022", eventid, "HASC-HONIR", "Reserved" )
#    addobservation( "GL092844+590022", eventid, "HASC-HOWPOL", "Reserved" )
#    addobservation( "GL100513+675234", eventid, "HASC-HOWPOL", "Reserved" )
#    addobservation( "GL084526+524504", eventid, "HASC-HOWPOL", "Observed" )
#    print showobslog(eventid)
    
