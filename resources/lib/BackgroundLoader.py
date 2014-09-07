#################################################################################################
# Start of BackgroundRotationThread
# Sets a backgound property to a fan art link
#################################################################################################

import xbmc
import xbmcgui
import xbmcaddon

import json
import threading
from datetime import datetime
import urllib
import urllib2
import random
import time
from DownloadUtils import DownloadUtils

_MODE_BASICPLAY=12

#define our global download utils
downloadUtils = DownloadUtils()

class BackgroundRotationThread(threading.Thread):

    movie_art_links = []
    tv_art_links = []
    music_art_links = []
    global_art_links = []
    item_art_links = {}
    current_movie_art = 0
    current_tv_art = 0
    current_music_art = 0
    current_global_art = 0
    current_item_art = 0
    linksLoaded = False
    logLevel = 0
   
    def __init__(self, *args):
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        level = addonSettings.getSetting('logLevel')        
        self.logLevel = 0
        if(level != None):
            self.logLevel = int(level)           
    
        xbmc.log("XBMB3C BackgroundRotationThread -> Log Level:" +  str(self.logLevel))
        
        threading.Thread.__init__(self, *args)    
    
    def logMsg(self, msg, level = 1):
        if(self.logLevel >= level):
            xbmc.log("XBMB3C BackgroundRotationThread -> " + msg)
    
    def run(self):
        self.logMsg("Started")
        
        try:
            self.loadLastBackground()
        except Exception, e:
            self.logMsg("loadLastBackground Exception : " + str(e), level=0)
            
        WINDOW = xbmcgui.Window( 10000 )
        filterOnParent_Last = WINDOW.getProperty("MB3.Background.Collection")
        
        last_id = ""
        self.updateArtLinks()
        #self.setBackgroundLink(filterOnParent_Last)
        lastRun = datetime.today()
        itemLastRun = datetime.today()
        
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        
        backgroundRefresh = int(addonSettings.getSetting('backgroundRefresh'))
        if(backgroundRefresh < 10):
            backgroundRefresh = 10
            
        itemBackgroundRefresh = 5
        lastUserName = addonSettings.getSetting('username')

        while (xbmc.abortRequested == False):
            td = datetime.today() - lastRun
            td2 = datetime.today() - itemLastRun
            secTotal = td.seconds
            secTotal2 = td2.seconds
            
            userName = addonSettings.getSetting('username')  
            self.logMsg("Server details string : (" + userName + ") (" + lastUserName + ")", level=2)
            
            Collection = WINDOW.getProperty("MB3.Background.Collection")
            if(secTotal > backgroundRefresh or filterOnParent_Last != Collection or userName != lastUserName):
                lastUserName = userName
                if(self.linksLoaded == False):
                    self.updateArtLinks()
                lastRun = datetime.today()
                filterOnParent_Last = Collection
                backgroundRefresh = int(addonSettings.getSetting('backgroundRefresh'))
                self.setBackgroundLink(Collection)
                if(backgroundRefresh < 10):
                    backgroundRefresh = 10
            
            # update item BG every 7 seconds
            if(secTotal2 > itemBackgroundRefresh):
                self.setItemBackgroundLink()
                itemLastRun = datetime.today()
                
            # update item BG on selected item changes
            current_id = xbmc.getInfoLabel('ListItem.Property(ItemGUID)')
            if current_id != last_id:
                self.setItemBackgroundLink()
                itemLastRun = datetime.today()
                last_id = current_id
                
            xbmc.sleep(1000)
        
        try:
            self.saveLastBackground()
        except Exception, e:
            self.logMsg("saveLastBackground Exception : " + str(e), level=0)  
            
        self.logMsg("Exited")

    def loadLastBackground(self):
        
        __addon__       = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        __addondir__    = xbmc.translatePath( __addon__.getAddonInfo('profile') )         
        
        lastDataPath = __addondir__ + "LastBgLinks.json"
        dataFile = open(lastDataPath, 'r')
        jsonData = dataFile.read()
        dataFile.close()
        
        self.logMsg(jsonData)
        result = json.loads(jsonData)
        
        WINDOW = xbmcgui.Window( 10000 )
        if(result.get("global") != None):
            WINDOW.setProperty("MB3.Background.Global.FanArt", result.get("global")["url"])
            self.logMsg("MB3.Background.Global.FanArt=" + result.get("global")["url"], level=2)
            WINDOW.setProperty("MB3.Background.Global.FanArt.Poster", result.get("global")["poster"])
            self.logMsg("MB3.Background.Global.FanArt.Poster=" + result.get("global")["poster"], level=2)    
            WINDOW.setProperty("MB3.Background.Global.FanArt.Action", result.get("global")["action"])
            self.logMsg("MB3.Background.Global.FanArt.Action=" + result.get("global")["action"], level=2)             

        if(result.get("movie") != None):
            self.logMsg("Setting Movie Last : " + str(result.get("movie")), level=2)
            WINDOW.setProperty("MB3.Background.Movie.FanArt", result.get("movie")["url"])      
            
        if(result.get("tv") != None):
            self.logMsg("Setting TV Last : " + str(result.get("tv")), level=2)
            WINDOW.setProperty("MB3.Background.TV.FanArt", result.get("tv")["url"])    

        if(result.get("music") != None):
            self.logMsg("Setting Music Last : " + str(result.get("music")), level=2)
            WINDOW.setProperty("MB3.Background.Music.FanArt", result.get("music")["url"])   

    def saveLastBackground(self):
    
        data = {}
        if(len(self.global_art_links) > 0):
            data["global"] = self.global_art_links[self.current_global_art]
        if(len(self.movie_art_links) > 0):
            data["movie"] = self.movie_art_links[self.current_movie_art]
        if(len(self.tv_art_links) > 0):
            data["tv"] = self.tv_art_links[self.current_tv_art]
        if(len(self.music_art_links) > 0):
            data["music"] = self.music_art_links[self.current_music_art]

        __addon__       = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        __addondir__    = xbmc.translatePath( __addon__.getAddonInfo('profile') )            
            
        lastDataPath = __addondir__ + "LastBgLinks.json"
        dataFile = open(lastDataPath, 'w')
        stringdata = json.dumps(data)
        self.logMsg("Last Background Links : " + stringdata)
        dataFile.write(stringdata)
        dataFile.close()        
    
    def setBackgroundLink(self, filterOnParent):

        WINDOW = xbmcgui.Window( 10000 )
        
        if(len(self.movie_art_links) > 0):
            self.logMsg("setBackgroundLink index movie_art_links " + str(self.current_movie_art + 1) + " of " + str(len(self.movie_art_links)), level=2)
            artUrl =  self.movie_art_links[self.current_movie_art]["url"]
            WINDOW.setProperty("MB3.Background.Movie.FanArt", artUrl)
            self.logMsg("MB3.Background.Movie.FanArt=" + artUrl)
            self.current_movie_art = self.current_movie_art + 1
            if(self.current_movie_art == len(self.movie_art_links)):
                self.current_movie_art = 0         
        
        if(len(self.tv_art_links) > 0):
            self.logMsg("setBackgroundLink index tv_art_links " + str(self.current_tv_art + 1) + " of " + str(len(self.tv_art_links)), level=2)
            artUrl =  self.tv_art_links[self.current_tv_art]["url"]
            WINDOW.setProperty("MB3.Background.TV.FanArt", artUrl)
            self.logMsg("MB3.Background.TV.FanArt=" + artUrl)
            self.current_tv_art = self.current_tv_art + 1
            if(self.current_tv_art == len(self.tv_art_links)):
                self.current_tv_art = 0
                
        if(len(self.music_art_links) > 0):
            self.logMsg("setBackgroundLink index music_art_links " + str(self.current_music_art + 1) + " of " + str(len(self.music_art_links)), level=2)
            artUrl =  self.music_art_links[self.current_music_art]["url"] 
            WINDOW.setProperty("MB3.Background.Music.FanArt", artUrl)
            self.logMsg("MB3.Background.Music.FanArt=" + artUrl)
            self.current_music_art = self.current_music_art + 1
            if(self.current_music_art == len(self.music_art_links)):
                self.current_music_art = 0
            
        if(len(self.global_art_links) > 0):
            self.logMsg("setBackgroundLink index global_art_links " + str(self.current_global_art + 1) + " of " + str(len(self.global_art_links)), level=2)
            
            next, nextItem = self.findNextLink(self.global_art_links, self.current_global_art, filterOnParent)
            #nextItem = self.global_art_links[self.current_global_art]
            self.current_global_art = next
            
            backGroundUrl = nextItem["url"]
            posterUrl = nextItem["poster"]
            actionUrl = nextItem["action"]
            
            addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')               
            selectAction = addonSettings.getSetting('selectAction')
            if(selectAction == "1"):
                actionUrl = "RunPlugin(plugin://plugin.video.xbmb3c/?id=" + nextItem["id"] + "&mode=17)"     
            else:
                actionUrl = nextItem["action"]
                
            WINDOW.setProperty("MB3.Background.Global.FanArt", backGroundUrl)
            self.logMsg("MB3.Background.Global.FanArt=" + backGroundUrl)
            WINDOW.setProperty("MB3.Background.Global.FanArt.Poster", posterUrl)
            self.logMsg("MB3.Background.Global.FanArt.Poster=" + posterUrl)    
            WINDOW.setProperty("MB3.Background.Global.FanArt.Action", actionUrl)
            self.logMsg("MB3.Background.Global.FanArt.Action=" + actionUrl) 

            
    def findNextLink(self, linkList, startIndex, filterOnParent):
        currentIndex = startIndex
        
        isParentMatch = False
        
        #xbmc.log("findNextLink : filterOnParent=" + str(filterOnParent) + " isParentMatch=" + str(isParentMatch))
        
        while(isParentMatch == False):
        
            currentIndex = currentIndex + 1
            
            if(currentIndex == len(linkList)):
                currentIndex = 0
                
            if(currentIndex == startIndex):
                return (currentIndex, linkList[currentIndex]) # we checked everything and nothing was ok so return the first one again

            isParentMatch = True
            if(filterOnParent != None and filterOnParent != ""):
                isParentMatch = filterOnParent in linkList[currentIndex]["collections"]
             
        nextIndex = currentIndex + 1
        
        if(nextIndex == len(linkList)):
            nextIndex = 0

        return (nextIndex, linkList[currentIndex])                
                
    def updateArtLinks(self):
        t1 = time.time()
        result01 = self.updateCollectionArtLinks()
        t2 = time.time()
        result02 = self.updateTypeArtLinks()
        t3 = time.time()
        diff = t2 - t1
        xbmc.log("TIMEDIFF01 : " + str(diff))
        diff = t3 - t2
        xbmc.log("TIMEDIFF02 : " + str(diff))
        
        if(result01 and result02):
            xbmc.log("BackgroundRotationThread Update Links Worked")
            self.linksLoaded = True
        else:
            xbmc.log("BackgroundRotationThread Update Links Failed")
            self.linksLoaded = False
            
        
    def updateActionUrls(self):
        xbmc.log("BackgroundRotationThread updateActionUrls Called")
        WINDOW = xbmcgui.Window( 10000 )
        
        for x in range(0, 10):
            contentUrl = WINDOW.getProperty("xbmb3c_collection_menuitem_content_" + str(x))
            if(contentUrl != None):
                index = contentUrl.find("SessionId=(")
                if(index > -1):
                    index = index + 11
                    index2 = contentUrl.find(")", index+1)
                    timeNow = time.time()
                    newContentUrl = contentUrl[:index] + str(timeNow) + contentUrl[index2:]
                    xbmc.log("xbmb3c_collection_menuitem_content_" + str(x) + "=" + newContentUrl)
                    WINDOW.setProperty("xbmb3c_collection_menuitem_content_" + str(x), newContentUrl)
    
    def updateCollectionArtLinks(self):
        self.logMsg("updateCollectionArtLinks Called")
        
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        
        mb3Host = addonSettings.getSetting('ipaddress')
        mb3Port = addonSettings.getSetting('port')    
        userName = addonSettings.getSetting('username')    
        
        # get the user ID       
        userid = downloadUtils.getUserId()
        self.logMsg("updateCollectionArtLinks UserID : " + userid)
        
        userUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items/Root?format=json"
        jsonData = downloadUtils.downloadUrl(userUrl, suppress=False, popup=1 )    
        self.logMsg("updateCollectionArtLinks UserData : " + str(jsonData), 2)
        result = json.loads(jsonData)
        
        parentid = result.get("Id")
        self.logMsg("updateCollectionArtLinks ParentID : " + str(parentid), 2)
            
        userRootPath = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/items?ParentId=" + parentid + "&SortBy=SortName&Fields=CollectionType,Overview,RecursiveItemCount&format=json"
    
        jsonData = downloadUtils.downloadUrl(userRootPath, suppress=False, popup=1 ) 
        self.logMsg("updateCollectionArtLinks userRootPath : " + str(jsonData), 2)            
        result = json.loads(jsonData)
        result = result.get("Items")
    
        artLinks = {}
        collection_count = 0
        WINDOW = xbmcgui.Window( 10000 )
        
        # process collections
        for item in result:
        
            collectionType = item.get("CollectionType", "")
            name = item.get("Name")
            childCount = item.get("RecursiveItemCount")
            self.logMsg("updateCollectionArtLinks Name : " + str(name), level=1)
            self.logMsg("updateCollectionArtLinks RecursiveItemCount : " + str(childCount), level=1)
            if(childCount == None or childCount == 0):
                continue
            
            self.logMsg("updateCollectionArtLinks Processing Collection : " + name + " of type : " + collectionType, level=2)

            #####################################################################################################
            # Process collection item menu item
            timeNow = time.time()
            contentUrl = "plugin://plugin.video.xbmb3c?mode=16&ParentId=" + item.get("Id") + "&CollectionType=" + collectionType + "&SessionId=(" + str(timeNow) + ")"
            actionUrl = "ActivateWindow(VideoLibrary, plugin://plugin.video.xbmb3c/?mode=21&ParentId=" + item.get("Id") + "&Name=" + name + ",return)"
            xbmc.log("COLLECTION actionUrl: " + actionUrl)
            WINDOW.setProperty("xbmb3c_collection_menuitem_name_" + str(collection_count), name)
            WINDOW.setProperty("xbmb3c_collection_menuitem_action_" + str(collection_count), actionUrl)
            WINDOW.setProperty("xbmb3c_collection_menuitem_collection_" + str(collection_count), name)
            WINDOW.setProperty("xbmb3c_collection_menuitem_content_" + str(collection_count), contentUrl)
            #####################################################################################################

            #####################################################################################################
            # Process collection item backgrounds
            collectionUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/items?ParentId=" + item.get("Id") + "&IncludeItemTypes=Movie,Series,MusicArtist,Trailer,MusicVideo&Fields=ParentId,Overview&Recursive=true&CollapseBoxSetItems=false&format=json"
   
            jsonData = downloadUtils.downloadUrl(collectionUrl, suppress=False, popup=1 ) 
            collectionResult = json.loads(jsonData)

            collectionResult = collectionResult.get("Items")
            if(collectionResult == None):
                collectionResult = []   
        
            for col_item in collectionResult:
                
                id = col_item.get("Id")
                name = col_item.get("Name")
                images = col_item.get("BackdropImageTags")
                
                if(images != None and len(images) > 0):
                    stored_item = artLinks.get(id)
                    
                    if(stored_item == None):
                    
                        stored_item = {}
                        collections = []
                        collections.append(item.get("Name"))
                        stored_item["collections"] = collections
                        links = []
                        images = col_item.get("BackdropImageTags")
                        parentID = col_item.get("ParentId")
                        name = col_item.get("Name")
                        if (images == None):
                            images = []
                        index = 0
                        
                        # build poster image link
                        posterImage = ""
                        actionUrl = ""
                        if(col_item.get("Type") == "Movie" or col_item.get("Type") == "Trailer" or col_item.get("Type") == "MusicVideo"):
                            imageTag = col_item.get("ImageTags").get("Primary")
                            if imageTag == None:
                                imageTag = ""
                            posterImage = "http://localhost:15001/?id=" + str(id) + "&type=Primary" + "&tag=" + imageTag
                            url =  mb3Host + ":" + mb3Port + ',;' + id
                            url = urllib.quote(url)
                            #actionUrl = "ActivateWindow(VideoLibrary, plugin://plugin.video.xbmb3c/?mode=" + str(_MODE_BASICPLAY) + "&url=" + url + " ,return)"
                            actionUrl = "RunPlugin(plugin://plugin.video.xbmb3c/?mode=" + str(_MODE_BASICPLAY) + "&url=" + url + ")"

                        elif(col_item.get("Type") == "Series"):
                            imageTag = col_item.get("ImageTags").get("Primary")
                            if imageTag == None:
                                imageTag = ""
                            posterImage = "http://localhost:15001/?id=" + str(id) + "&type=Primary" + "&tag=" + imageTag
                            actionUrl = "ActivateWindow(VideoLibrary, plugin://plugin.video.xbmb3c/?mode=21&ParentId=" + id + "&Name=" + name + ",return)"
                        plot = col_item.get("Overview")
                        for backdrop in images:
                          
                            info = {}
                            info["url"] = "http://localhost:15001/?id=" + str(id) + "&type=Backdrop" + "&index=" + str(index) + "&tag=" + backdrop
                            info["poster"] = posterImage
                            info["action"] = actionUrl
                            info["index"] = index
                            info["id"] = id
                            info["action"] = "None"
                            info["plot"] = plot
                            info["parent"] = parentID
                            info["name"] = name
                            links.append(info)
                            index = index + 1   

                        stored_item["links"] = links
                        artLinks[id] = stored_item
                    else:
                        stored_item["collections"].append(item.get("Name"))
            #####################################################################################################
            
            collection_count = collection_count + 1
            
        # build global link list
        final_global_art = []
        
        for id in artLinks:
            item = artLinks.get(id)
            collections = item.get("collections")
            links = item.get("links")
            
            for link_item in links:
                link_item["collections"] = collections
                final_global_art.append(link_item)
                #xbmc.log("COLLECTION_DATA GROUPS " + str(link_item))
        
        self.global_art_links = final_global_art
        random.shuffle(self.global_art_links)
        self.logMsg("Background Global Art Links : " + str(len(self.global_art_links)))        
        
        return True
        
    def updateTypeArtLinks(self):
        self.logMsg("updateTypeArtLinks Called")
        
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        
        mb3Host = addonSettings.getSetting('ipaddress')
        mb3Port = addonSettings.getSetting('port')    
        userName = addonSettings.getSetting('username')     
        
        # get the user ID
        userid = downloadUtils.getUserId()
        self.logMsg("updateTypeArtLinks UserID : " + userid)

        # load Movie BG
        moviesUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Fields=ParentId,Overview&CollapseBoxSetItems=false&Recursive=true&IncludeItemTypes=Movie&format=json"

        jsonData = downloadUtils.downloadUrl(moviesUrl, suppress=False, popup=1 ) 
        result = json.loads(jsonData)

        result = result.get("Items")
        if(result == None):
            result = []   

        for item in result:
            images = item.get("BackdropImageTags")
            id = item.get("Id")
            parentID = item.get("ParentId")
            name = item.get("Name")
            plot = item.get("Overview")
            url =  mb3Host + ":" + mb3Port + ',;' + id
            url = urllib.quote(url)        
            actionUrl = "RunPlugin(plugin://plugin.video.xbmb3c/?mode=" + str(_MODE_BASICPLAY) + "&url=" + url + ")"
            if (images == None):
                images = []
            index = 0
            for backdrop in images:
              
              info = {}
              info["url"] = "http://localhost:15001/?id=" + str(id) + "&type=Backdrop" + "&index=" + str(index) + "&tag=" + backdrop
              info["index"] = index
              info["id"] = id
              info["plot"] = plot
              info["action"] = actionUrl
              info["parent"] = parentID
              info["name"] = name
              self.logMsg("BG Movie Image Info : " + str(info), level=2)
              
              if (info not in self.movie_art_links):
                  self.movie_art_links.append(info)
              index = index + 1
        
        random.shuffle(self.movie_art_links)
        self.logMsg("Background Movie Art Links : " + str(len(self.movie_art_links)))

        # load TV BG links
        tvUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Fields=ParentId,Overview&CollapseBoxSetItems=false&Recursive=true&IncludeItemTypes=Series&format=json"

        jsonData = downloadUtils.downloadUrl(tvUrl, suppress=False, popup=1 ) 
        result = json.loads(jsonData)        
        
        result = result.get("Items")
        if(result == None):
            result = []   

        for item in result:
            images = item.get("BackdropImageTags")
            id = item.get("Id")
            parentID = item.get("ParentId")
            name = item.get("Name")
            plot = item.get("Overview")
            if (images == None):
                images = []
            index = 0
            for backdrop in images:
              
              info = {}
              info["url"] = "http://localhost:15001/?id=" + str(id) + "&type=Backdrop" + "&index=" + str(index) + "&tag=" + backdrop
              info["index"] = index
              info["id"] = id
              info["action"] = "None"
              info["plot"] = plot
              info["parent"] = parentID
              info["name"] = name
              self.logMsg("BG TV Image Info : " + str(info), level=2)
              
              if (info not in self.tv_art_links):
                  self.tv_art_links.append(info)    
              index = index + 1
              
        random.shuffle(self.tv_art_links)
        self.logMsg("Background Tv Art Links : " + str(len(self.tv_art_links)))

        # load music BG links
        musicUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Fields=ParentId,Overview&CollapseBoxSetItems=false&Recursive=true&IncludeItemTypes=MusicArtist&format=json"
        
        jsonData = downloadUtils.downloadUrl(musicUrl, suppress=False, popup=1 ) 
        result = json.loads(jsonData)        
        
        result = result.get("Items")
        if(result == None):
            result = []   

        for item in result:
            images = item.get("BackdropImageTags")
            id = item.get("Id")
            parentID = item.get("ParentId")
            name = item.get("Name")
            plot = item.get("Overview")
            if (images == None):
                images = []
            index = 0
            for backdrop in images:
              
              info = {}
              info["url"] = "http://localhost:15001/?id=" + str(id) + "&type=Backdrop" + "&index=" + str(index) + "&tag=" + backdrop
              info["index"] = index
              info["id"] = id
              info["action"] = "None"
              info["plot"] = plot
              info["parent"] = parentID
              info["name"] = name
              self.logMsg("BG Music Image Info : " + str(info), level=2)

              if (info not in self.music_art_links):
                  self.music_art_links.append(info)
              index = index + 1
              
        random.shuffle(self.music_art_links)
        self.logMsg("Background Music Art Links : " + str(len(self.music_art_links)))
        
        #
        # build a map indexed by id that contains a list of BG art for each item
        # this is used for selected item BG rotation
        #
        self.item_art_links = {}
        
        # add movie BG links
        for bg_item in self.movie_art_links:
            item_id = bg_item["id"]
            if(self.item_art_links.get(item_id) != None):
                self.item_art_links[item_id].append(bg_item)
            else:
                bg_list = []
                bg_list.append(bg_item)
                self.item_art_links[item_id] = bg_list
                
        # add TV BG links
        for bg_item in self.tv_art_links:
            item_id = bg_item["id"]
            if(self.item_art_links.get(item_id) != None):
                self.item_art_links[item_id].append(bg_item)
            else:
                bg_list = []
                bg_list.append(bg_item)
                self.item_art_links[item_id] = bg_list 

        # add music BG links
        for bg_item in self.music_art_links:
            item_id = bg_item["id"]
            if(self.item_art_links.get(item_id) != None):
                self.item_art_links[item_id].append(bg_item)
            else:
                bg_list = []
                bg_list.append(bg_item)
                self.item_art_links[item_id] = bg_list
        
        
        return True
        
    def setItemBackgroundLink(self):
    
        id = xbmc.getInfoLabel('ListItem.Property(ItemGUID)')
        self.logMsg("setItemBackgroundLink ItemGUID : " + id, 1)
    
        WINDOW = xbmcgui.Window( 10000 )
        if id != None and id != "":    
    
            listOfBackgrounds = self.item_art_links.get(id)
            
            # if for some reson the item is not in the cache try to load it now
            if(listOfBackgrounds == None or len(listOfBackgrounds) == 0):
                self.loadItemBackgroundLinks(id)
            
            listOfBackgrounds = self.item_art_links.get(id)
            
            if listOfBackgrounds != None:
                if listOfBackgrounds[0]["plot"] != None and listOfBackgrounds[0]["plot"] != "":
                    plot=listOfBackgrounds[0]["plot"]
                    plot=plot.encode("utf-8")
                    WINDOW.setProperty("MB3.Plot", plot )
                else:
                    WINDOW.clearProperty("MB3.Plot")                            

                if listOfBackgrounds[0]["action"] != None and listOfBackgrounds[0]["action"] != "":
                    action=listOfBackgrounds[0]["action"]
                    WINDOW.setProperty("MB3.Action", action )
                else:
                    WINDOW.clearProperty("MB3.Action")
                    
            if(listOfBackgrounds != None and len(listOfBackgrounds) > 0):
                self.logMsg("setItemBackgroundLink Image " + str(self.current_item_art + 1) + " of " + str(len(listOfBackgrounds)), 1)
                try: 
                    artUrl = listOfBackgrounds[self.current_item_art]["url"] 
                except IndexError:
                    self.current_item_art = 0
                    artUrl = listOfBackgrounds[self.current_item_art]["url"] 
                    
                WINDOW.setProperty("MB3.Background.Item.FanArt", artUrl)
                self.logMsg("setItemBackgroundLink MB3.Background.Item.FanArt=" + artUrl, 1)
                
                self.current_item_art = self.current_item_art + 1
                if(self.current_item_art == len(listOfBackgrounds)):
                    self.current_item_art = 0
                    
            else:
                self.logMsg("setItemBackgroundLink Resetting MB3.Background.Item.FanArt", 1)
                WINDOW.clearProperty("MB3.Background.Item.FanArt")         
                    
        else:
            self.logMsg("setItemBackgroundLink Resetting MB3.Background.Item.FanArt", 1)
            WINDOW.clearProperty("MB3.Background.Item.FanArt")
            WINDOW.clearProperty("MB3.Plot") 
            WINDOW.clearProperty("MB3.Action") 
      
            
    def loadItemBackgroundLinks(self, id):
    
        self.logMsg("loadItemBackgroundLinks Called for id : " + id)
        
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        mb3Host = addonSettings.getSetting('ipaddress')
        mb3Port = addonSettings.getSetting('port')
        userName = addonSettings.getSetting('username')
                   
        userid = downloadUtils.getUserId()
        itemUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items/" + id + "?Fields=ParentId,Overview&format=json"
        
        jsonData = downloadUtils.downloadUrl(itemUrl, suppress=False, popup=1 ) 
        item = json.loads(jsonData)
        
        self.logMsg("loadItemBackgroundLinks found item : " + str(item), 2);
        
        if(item == None):
            item = []

        #for item in result:
        images = item.get("BackdropImageTags")
        plot = item.get("Overview")
        id = item.get("Id")
        urlid = id
        parentID = item.get("ParentId")
        origid = id
        name = item.get("Name")
        if (images == None or images == []):
          images = item.get("ParentBackdropImageTags")
          urlid = item.get("ParentBackdropItemId")
          if (images == None):
            images = []
            
        index = 0
        url =  mb3Host + ":" + mb3Port + ',;' + id
        url = urllib.quote(url)        
        actionUrl = "RunPlugin(plugin://plugin.video.xbmb3c/?mode=" + str(_MODE_BASICPLAY) + "&url=" + url + ")"
      
        newBgLinks = []
        for backdrop in images:
            info = {}
            info["url"] = "http://localhost:15001/?id=" + str(urlid) + "&type=Backdrop" + "&index=" + str(index) + "&tag=" + backdrop
            info["plot"] = plot
            info["action"] = actionUrl
            info["index"] = index
            info["id"] = urlid
            info["parent"] = parentID
            info["name"] = name
            self.logMsg("BG Item Image Info : " + str(info), level=2)
            newBgLinks.append(info)
            index = index + 1
            


        if(len(newBgLinks) > 0):
            self.item_art_links[origid] = newBgLinks
           
    
    