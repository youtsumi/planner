- Compile sqlite with
    ```
    $ ./configure --prefix=/subhome/hinotori.hiroshima-u.ac.jp --enable-load-extension
    ```

- Compile an extension library
    ```
    gcc -fPIC -shared -lm -I .  -o libsqlitefunctions.so extension-functions.c     
    ```

- Compile python enabling SQLITE LOAD EXTENSION by editing setup.py in 2076, following the comment
    ```
    # Comment this out if you want the sqlite3 module to be able to load extensions.
    sqlite_defines.append(("SQLITE_OMIT_LOAD_EXTENSION", "1"))
    ```


