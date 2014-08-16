#!/usr/bin/expect

./Anaconda-2.0.1-Linux-x86_64.sh

except "Please, press ENTER to continue"
send "\r"

expect "Do you approve the license terms? [yes|no]"
send "yes\r"


