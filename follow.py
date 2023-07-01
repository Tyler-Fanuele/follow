#!/usr/bin/python3
import argparse
import os
import sys
import time
import logging
from watchdog.observers import Observer  #creating an instance of the watchdog.observers.Observer from watchdogs class.
from watchdog.events import LoggingEventHandler  #implementing a subclass of watchdog.events.FileSystemEventHandler which is LoggingEventHandler in our case
from watchdog.events import FileModifiedEvent

class FileEvent(FileModifiedEvent):
    def dispatch(self, event):
        if event.is_directory == False and event.event_type  == 'modified':
            print(event)

class DirEvent(FileModifiedEvent):
    def dispatch(self, event):
        print(event)
            
# Create argument parser object
parser = argparse.ArgumentParser(
                    prog='Follow',
                    description='A program that follows file changes and executes a command or set of commands when those changes occur',
                    epilog='Epilog')

# Add location argument to specify what file or dir to follow. If blank current dir is used
parser.add_argument('location', help="The location to be followed, can be dir or file", nargs='?', default=os.getcwd())

parser.add_argument('-e', '--exec', nargs='?')

# Parse the arguments
args = parser.parse_args() 
print(args)
location_is_dir = False   

execution = args.exec
print("Execution: " + str(execution))
 
# Check if location path exists 
if os.path.exists(args.location):
    print(args.location + " exists") 
    # If location path exists check if its a dir
    if os.path.isdir(args.location):
        location_is_dir = True
else:
    # If location path doesn't exist terminate program
    print(args.location + " does not exist, exiting program")
    exit()
print(args.location + " is a dir" if location_is_dir else args.location + " is a file")

print("In follow")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s')
    path = args.location
    event_handler = FileEvent(args.location) if location_is_dir == False else DirEvent(args.location)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)  #Scheduling monitoring of a path with the observer instance and event handler. There is 'recursive=True' because only with it enabled, watchdog.observers.Observer can monitor sub-directories
    observer.start()  #for starting the observer thread
    try:
        while True: 
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()