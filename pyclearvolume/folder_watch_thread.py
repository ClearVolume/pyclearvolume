"""

a simple utility that watches a folder for new image files and
returns the data

"""


from __future__ import absolute_import
from __future__ import print_function
import os
import six.moves.queue
from threading import Thread

from sortedcontainers import SortedList, SortedDict
from collections import Counter


from pyclearvolume.image_file_reader import ImageFolderReader,  ImageFileReader

import time
import numpy as np
import six
from six.moves import range


class WatchThread(Thread):
    """
    """
    TIME_STEP = .1
    def __init__(self,dirName, wildcard="*", deltaTime = 1., func = os.path.getsize):
        maxCount = int(np.ceil(deltaTime/self.TIME_STEP))
        print("setting up watchthread with maxCount %s"%maxCount)
        super(WatchThread,self).__init__()
        self.folderReader = ImageFolderReader(dirName,wildcard, func)
        self.goodFiles = six.moves.queue.Queue()
        self.updatelist = UpdateCountList(maxCount)
        self.processed = set()
        self.setDaemon(True)
    

    def run(self):
        while True:
            allfiles = dict([(k,v) for k,v in self.folderReader.list_files() if not k  in self.processed])
            self.updatelist.update(allfiles)
            
            newfiles = self.updatelist.filter_names()
            if newfiles:
                fName = newfiles[0]
                print("newfile: %s   %s"%(fName, self.updatelist.properties[fName]))
                self.goodFiles.put(fName)
                self.processed.add(fName)
    
            time.sleep(self.TIME_STEP)

    def empty(self):
        return self.goodFiles.empty()

    def get(self):
        fName = self.goodFiles.get()
        print("getting data from ", fName)
        data, meta =  ImageFileReader.load_file(fName)
        print("shape: ", data.shape)
        self.goodFiles.task_done()
        return data, meta
            
            
class UpdateCountList(object):
    """ implements a list of objects with properties that can be updated"""

    def __init__(self,maxCount = 10):
        self.maxCount = maxCount
        self.properties = SortedDict()
        self.counts = Counter()

    def add(self,name,prop):
        if name in self.properties:
            if prop == self.properties[name]:
                self.counts[name] += 1
            else:
                self.properties[name] = prop
        else:
            self.properties[name] = prop
            self.counts[name] = 0

    def is_empty():
        return len(self.properties)==0
            
    def update(self,namedProperties):
        """adds names of a name-property dict
        and removes the ones that are not present"""

        namesNotPresent = [n for n in self.properties.keys()
                           if n not in namedProperties]

        for n in namesNotPresent:
            self.pop(n)

        for n,p in six.iteritems(namedProperties):

            self.add(n,p)
            
    def __repr__(self):
        return "\n".join([str(self.properties),str(self.counts)])

    def pop(self,name):
        return self.properties.pop(name),self.counts.pop(name)


    def filter_names(self):
        """returns the names whose counts are at least maxCount"""
        return [n for n, c in six.iteritems(self.counts) if c>= self.maxCount]


def test_updatelist():
    u = UpdateCountList(maxCount=2)
    alist = dict([(chr(65+i),i) for i in range(10)])

    u.update(alist)
    u.update(alist)
    u.pop(list(alist.keys())[0])    
    u.update(alist)
    print(u.counts)



if __name__ == "__main__":

    # test_updatelist()
    
    a = WatchThread("tests_watch/", deltaTime = 1.)
    a.start()

    while True:
        try:
            fName = a.goodFiles.get(timeout = 1.)
            print("a new file arrived! ", fName)
        except six.moves.queue.Empty:
            pass
        time.sleep(.1)

    
