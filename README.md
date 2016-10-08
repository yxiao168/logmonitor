# logmonitor


### Summary
logmonitor is a python script to monitor log  files.

It runs on a Linux unit to catch and log pre-defined error messages from
monitored log files. logmonitor is a tool for end-to-end test. It collects
all possible error messages in the backend during the test operation.

It monitors log files with regular expressions. When the matching is triggered,
all monitored log files would be copied onto a time-stamped sub-directory, and
matching events would be recorded in logmonitor's log file.

For each log file to be monitored, multiple pattern variables could be defined.

If no pattern variable is defined, this log file would not be monitored but
would be copied while other matchings are triggered.

For each pattern variable, It uses a "filter pattern" to match all possible
messages first; then to use multiple "post negative patterns" to eliminate all
false-positive messages. See "Syntax of Log Section" in detail.



invicta.ini - pre-defined configuration file for INVICTA system.



### Author
Yanming Xiao
yanming_xiao@yahoo.com




### Test Steps
0. Copy over all files to a test directory, and su to root.
(most of system log files are only accessible to root).

1. Edit the test.ini file. The format and content are self-explanatory.

2. Test Run
  (1). generate test1.log and test2.log files
```sh
     # ./step0.sh
```

  (2). start the logmonitor
```sh
        # python logmonitor test.ini
        Press Ctrl+C to exit
        Running Configuration File: test.ini

         logmonitor 0.16 - Log Monitor



         Subject: test logmonitor

         applhistory:
        sh: 1: applhistory: not found

         Checking log files every 2 seconds ...
```


  (3). from another console, append a line onto test1_monitored.log matching
       the regular expression defined in test.ini
```sh       
        # ./step1.sh
```
The console for logmonitor would be look alike:
```sh       
        # python logmonitor test.ini
        Press Ctrl+C to exit
        Running Configuration File: test.ini

         logmonitor 0.14 - Log Monitor



         Subject: test logmonitor

         applhistory:
        sh: 1: applhistory: not found

         Checking log files every 2 seconds ...



        --- 06/05/2014 16:45:33   ./test1_monitored.log ---
        Line   : xyzabcd1234
        Name   : pattern11
        Pattern: ^.+abcd\d+$
        Backup Subdir: 20140605_164533
```       


  (4). from another console, append a line onto test2_monitored.log matching
       the regular expression defined in test.ini
```sh       
        # ./step2.sh
```


     The console for logmonitor would be look alike:
```sh
        # python logmonitor test.ini
        Press Ctrl+C to exit
        Running Configuration File: test.ini

         logmonitor 0.14 - Log Monitor



         Subject: test logmonitor

         applhistory:
        sh: 1: applhistory: not found

         Checking log files every 2 seconds ...



        --- 06/05/2014 16:45:33   ./test1_monitored.log ---
        Line   : xyzabcd1234
        Name   : pattern11
        Pattern: ^.+abcd\d+$
        Backup Subdir: 20140605_164533
        --- 06/05/2014 16:45:35   ./test2_monitored.log ---
        Line   : 1234abcdxyz
        Name   : pattern22
        Pattern: ^\d+abcd.+$
        Backup Subdir: 20140605_164535
```

  (5). stop logmonitor
```sh
       Use "Ctrl+C" on the console for logmonitor.


        # python logmonitor test.ini
        Press Ctrl+C to exit
        Running Configuration File: test.ini

         logmonitor 0.14 - Log Monitor



         Subject: test logmonitor

         applhistory:
        sh: 1: applhistory: not found

         Checking log files every 2 seconds ...



        --- 06/05/2014 16:45:33   ./test1_monitored.log ---
        Line   : xyzabcd1234
        Name   : pattern11
        Pattern: ^.+abcd\d+$
        Backup Subdir: 20140605_164533
        --- 06/05/2014 16:45:35   ./test2_monitored.log ---
        Line   : 1234abcdxyz
        Name   : pattern22
        Pattern: ^\d+abcd.+$
        Backup Subdir: 20140605_164535
        ^CYou pressed Ctrl+C!
```



### Regular expression tool
http://www.regexr.com/
https://pythex.org/

Regular Expression Reference: Special Groups
http://www.regular-expressions.info/refadv.html


### Syntax of Log Section
```sh
[section_name]
file=full_path_of_log_file
#
# comment lines
#
# (1). patterns are optional.
# (2). the 1st pattern is "filter pattern",
#      all follow-up patterns are "post negative patterns".
# (3). no limitation to the amount of post-negative-patterns,
#      all seperated by a comma
#
first_pattern_name=filter_pattern
second_pattern_name=filter_pattern,first_post_negative_pattern,second_post_negative_pattern
```


### Deployment
logmonitor should be deployed on DUT server with
following steps.

(1). Copy over the sub-directory "logmonior" to DUT (Device Under
Test)'s /root/logmonior

(2). Log in as root

(3). Verify the configuration to be used. The content of "do.sh" should be:
```sh
# cat do.sh
python logmonitor.py inviata.ini
```
(4). Run logmonitor
```sh
    a. Run in frontend.
    # ./do.sh

    b. Run in backend.
    # nohup ./do.sh &
```


(5). Check logmonitor's log while running logmonitor in backend.
```sh
# tail -f inviata.log
```

(6). While observing a bug and ready to file a bug, use "Control-C"
to exit the frontend running process, or "kill" to exit a backend
running process. Zip all files under the lastest Backup Subdir.
```sh
# tar cvfz 20140605_164535.tar.gz 20140605_164535/*
```
(7). Put the zipped logs (e.g., 20140605_164535.tar.gz) onto
bugzilla with your Bug number.


