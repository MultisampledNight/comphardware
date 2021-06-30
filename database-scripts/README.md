# comphardware/database-scripts

Here are some scripts for maintaining the GPU and CPU databases and keeping them
up-to-date.

Currently, here are only 3 scripts of interest, the other `.py` files are only
helpers and supporters:
- For GPUs
  * `update-gpu-database.py` - Parses Wikipedia for GPUs by intel, amd and
    nvidia
- For CPUs
  * `update-cpu-database.py` - Walks through the intel ARK and stores
    information about every CPU found
  * `convert-divinity76s-database.py` - Converts divinity76's database at
    https://github.com/divinity76/intel-cpu-database to a database the rest of
    the library can read

For bootstrapping, you might run both `update-gpu-database.py` and
`convert-divinity76s-database.py`. Else, consider running
`update-cpu-database.py` when you got time and `update-gpu-database.py` anytime.

I didn't find any "official" database suitable for parsing AMD cpus, which
would be quite of interest. Feel free to open an issue with a link/a pull
request which adds parsing of that database to `update-cpu-database.py`.
