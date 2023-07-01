#!/usr/bin/python3
import argparse
import os
import sys
import time
import logging
from watchdog.observers import Observer  #creating an instance of the watchdog.observers.Observer from watchdogs class.
from watchdog.events import LoggingEventHandler  #implementing a subclass of watchdog.events.FileSystemEventHandler which is LoggingEventHandler in our case
from watchdog.events import FileModifiedEvent
import subprocess
from datetime import datetime

# Create argument parser object 
parser = argparse.ArgumentParser(
                    prog='Follow',
                    description='A program that follows file changes and executes a command or set of commands when those changes occur',
                    epilog='Epilog') 

# Add location argument to specify what file or dir to follow. If blank current dir is used
parser.add_argument('location', help="The location to be followed, can be dir or file", nargs='?', default=os.getcwd())

# Add exec argument to specify what command of file containing multiple commands to be executed during execution period
parser.add_argument('-e', '--exec', nargs='?', help="The commands or command to be executed. Can be string, path to file, or nothing. Nothing will default to printing changes")

# Add timing argument to specify how long to wait to check if command execution is needed, default is 20
parser.add_argument('-t', '--timing', nargs='?', default=20, type=float, help="Time in between checking for execution, default 20 seconds")

parser.add_argument('--verbose', action='store_true', default=False, help="Sets flag enabling verbose")
 
# Parse the arguments
args = parser.parse_args()  


def log(log_string, log_type='log'):
    '''Logging function, logs to stdout. Valid log types are 'log', 'error', and 'verbose' '''
    if log_type == 'error':
        print(datetime.now() , " ERROR: " , log_string)
    elif log_type == 'verbose' and args.verbose == True:
        print(datetime.now() , " VERBOSE: " , log_string)
    elif log_type == 'log':
        print(log_string)




update_events = 0
update_list = list()

class FileEvent(FileModifiedEvent):
    def dispatch(self, event):
        if event.is_directory == False and event.event_type  == 'modified':
            log("File Event Seen: " + str(event), 'verbose')
            global update_events, update_list
            update_events = update_events + 1
            update_list.append(event)

class DirEvent(FileModifiedEvent):
    def dispatch(self, event):
        if event.src_path not in ignore_list:
            log("Dir Event Seen: " + str(event), 'verbose')
            global update_events, update_list
            update_events = update_events + 1
            update_list.append(event)

# List of absolute paths that will be ignored by the program
ignore_list = list()

# Populate the ignore list.
if os.path.isfile(os.path.join(os.path.curdir , ".followignore")):
    ignore_file = open(os.path.join(os.path.curdir , ".followignore"), 'r')
    for line in ignore_file:
        ignore_list.append(os.path.abspath(line.strip()))
    ignore_file.close()

    additional_ignored = list()
    for path in ignore_list:
        if os.path.isdir(os.path.join(os.path.curdir, path)):
            for dirpath, dirs, files in os.walk(os.path.join(os.path.curdir, path)):
                #additional_ignored.append(dirpath)
                for dir in dirs:
                    additional_ignored.append(os.path.abspath(os.path.join(dirpath, dir)))
                for file in files:
                    additional_ignored.append(os.path.abspath(os.path.join(dirpath, file)))
    ignore_list = ignore_list + additional_ignored

# Bool true if location specified is dir
location_is_dir = False 
 
# Bool true if execution item is provided by user
execution_provided = False if args.exec == None else True

exec_list = list()
if execution_provided == True:
    if os.path.isfile(args.exec):
        exec_file = open(args.exec)
        for line in exec_file:
            exec_list.append(line.strip())
    else:
        exec_list.append(args.exec)

log("Command List: " + str(exec_list), 'verbose')

log("Follow Location: " + args.location, "verbose")
# Check if location path exists 
if os.path.exists(args.location): 
    log(args.location + " exists", 'verbose') 
    # If location path exists check if its a dir
    if os.path.isdir(args.location):
        location_is_dir = True
else:
    # If location path doesn't exist terminate program
    log("Location:'" + args.location + "' does not exist, exiting program", 'error')
    exit(1)



logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s')

if execution_provided == True:
    if location_is_dir == True:
        event_handler = DirEvent(args.location)
    else:
        event_handler = FileEvent(args.location)
else:
    event_handler = LoggingEventHandler() 

log("Starting follow process:\n")
log(args.location + " is a valid directory" if location_is_dir else args.location + " is a valid file")
log("Commands to run when update is registered:")
for command in exec_list:
    log("   " + str(command))
observer = Observer()
observer.schedule(event_handler, args.location, recursive=True)  #Scheduling monitoring of a path with the observer instance and event handler. There is 'recursive=True' because only with it enabled, watchdog.observers.Observer can monitor sub-directories
observer.start()  #for starting the observer thread
log("Use keyboard interrupt to exit program")
try:
    while True: 
        # Wait to check if update is needed
        time.sleep(args.timing)
        
        # If file or directory is deleted or removed from computer, cleanup and end program
        if os.path.exists(os.path.abspath(args.location)) == False:
            observer.stop()
            observer.join()
            log("Path: " + os.path.abspath(args.location) + " does not exist anymore", 'error')
            exit(1)    
        
        # If a execution file or string was provided and there was a update event
        if execution_provided == True and update_events != 0:
            # Loop through commands and run them, waiting for return before running the next command
            for command in exec_list:
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.wait()
                log("Command output:\n " + process.stdout.read().decode('utf-8'))
                log("Ran command: '" + str(command) + "' with return value of: " + str(process.returncode))
            # Reset the update events variables for next check
            update_events = 0
            update_list = list() 
        else:
            log("No updates detected, no execution of command", 'verbose') 
        
except KeyboardInterrupt:
    observer.stop()
observer.join()