import pymysql

# Use the pure-Python PyMySQL driver as a drop-in replacement for
# mysqlclient, so `django.db.backends.mysql` works with zero native/system
# dependencies. See requirements.txt for how to switch to mysqlclient instead.
pymysql.install_as_MySQLdb()
pymysql.version_info = (2, 2, 4, "final", 0)  # satisfies Django's version check
