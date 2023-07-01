#!/usr/bin/python3
import argparse
import os
import sys
import time
import logging
from watchdog.observers import Observer  #creating an instance of the watchdog.observers.Observer from watchdogs class.
from watchdog.events import LoggingEventHandler  #implementing a subclass of watchdog.events.FileSystemEventHandler which is LoggingEventHandler in our case
from watchdog.events import FileModifiedEvent

update_events = 0
update_list = list()

class FileEvent(FileModifiedEvent):
    def dispatch(self, event):
        if event.is_directory == False and event.event_type  == 'modified':
            #print(event)
            global update_events, update_list
            update_events = update_events + 1
            update_list.append(event)

class DirEvent(FileModifiedEvent):
    def dispatch(self, event):
        if event.src_path not in ignore_list:
            #print(event)
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
                    
#print("Ignore List: ", ignore_list)



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
 
# Parse the arguments
args = parser.parse_args() 
print(args)

# Bool true if location specified is dir
location_is_dir = False 
 
# Bool true if execution item is provided by user
execution_provided = False if args.exec == None else True
 
print("Location: " , args.location)
# Check if location path exists 
if os.path.exists(args.location):
    print(args.location , " exists") 
    # If location path exists check if its a dir
    if os.path.isdir(args.location):
        location_is_dir = True
else:
    # If location path doesn't exist terminate program
    print(args.location + " does not exist, exiting program")
    exit()
print(args.location + " is a dir" if location_is_dir else args.location + " is a file")

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s')

if execution_provided == True:
    if location_is_dir == True:
        event_handler = DirEvent(args.location)
    else:
        event_handler = FileEvent(args.location)
else:
    event_handler = LoggingEventHandler()
observer = Observer()
observer.schedule(event_handler, args.location, recursive=True)  #Scheduling monitoring of a path with the observer instance and event handler. There is 'recursive=True' because only with it enabled, watchdog.observers.Observer can monitor sub-directories
observer.start()  #for starting the observer thread
print("Keyboard interrupt to end program")
try:
    while True: 
        time.sleep(args.timing)
        if execution_provided == True and update_events != 0:
            print("exec")
            print(update_events)
            print(update_list)
            update_events = 0
            update_list = list()
        else:
            print("dont exec")
        
except KeyboardInterrupt:
    observer.stop()
observer.join()  