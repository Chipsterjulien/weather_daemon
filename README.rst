Weather_daemon
==============

It's a python's script who download json's file on wunderground (You
must register on wunderground). After, informations are wrote to
/tmp/weather (see /etc/weather_daemon_example.conf). After you can
display it on screen with conky or something else (dzen2, ...)


Depends
=======

yaml-python
python-requests


Installation
============

```
git clone https://github.com/Chipsterjulien/weather_daemon.git
python setup.py install
```


Usage
=====

```
python sshd_autoban -h
```


License
=======
<a href="http://en.wikipedia.org/wiki/Gplv3#Version_3">GPL v3</a>
