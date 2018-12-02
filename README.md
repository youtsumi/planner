- Need to compile sqlite with
	$ ./configure --prefix=/subhome/hinotori.hiroshima-u.ac.jp --enable-load-extension

- Need to compile an extension library
	gcc -fPIC -shared -lm -I .  -o libsqlitefunctions.so extension-functions.c     

- Need to enable SQLITE LOAD EXTENSION by editing setup.py in 2076, following the comment
	# Comment this out if you want the sqlite3 module to be able to load extensions.
	sqlite_defines.append(("SQLITE_OMIT_LOAD_EXTENSION", "1"))


