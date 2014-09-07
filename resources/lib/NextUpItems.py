#################################################################################################
# NextUp TV Updater
#################################################################################################

import xbmc
import xbmcgui
import xbmcaddon

import json
import threading
from datetime import datetime
import urllib
from DownloadUtils import DownloadUtils

_MODE_BASICPLAY=12

#define our global download utils
downloadUtils = DownloadUtils()

class NextUpUpdaterThread(threading.Thread):

    logLevel = 0
    
    def __init__(self, *args):
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        level = addonSettings.getSetting('logLevel')        
        self.logLevel = 0
        if(level != None):
            self.logLevel = int(level)           
    
        xbmc.log("XBMB3C NextUpUpdaterThread -> Log Level:" +  str(self.logLevel))
        
        threading.Thread.__init__(self, *args)    
    
    def logMsg(self, msg, level = 1):
        if(self.logLevel >= level):
            xbmc.log("XBMB3C NextUpUpdaterThread -> " + msg)
    
    def getImageLink(self, item, type, item_id):
        originalType = type
        if type == "Primary2":
            type = "Primary"
        imageTag = "none"
        if(item.get("ImageTags") != None and item.get("ImageTags").get(type) != None):
            imageTag = item.get("ImageTags").get(type)
        query = "&type=" + type + "&tag=" + imageTag
        if originalType=="Primary":
          addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
          if addonSettings.getSetting('showIndicators')=='true' and addonSettings.getSetting('showUnplayedIndicators')=='true':
            mb3Host = addonSettings.getSetting('ipaddress')
            mb3Port = addonSettings.getSetting('port')    
            userName = addonSettings.getSetting('username')     
        
            userid = downloadUtils.getUserId()  
            seriesUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items/" + item_id +"?format=json"
            jsonData = downloadUtils.downloadUrl(seriesUrl, suppress=False, popup=1 )
            result = json.loads(jsonData)
            userData = result.get("UserData")   
            UnWatched = 0 if userData.get("UnplayedItemCount")==None else userData.get("UnplayedItemCount")        
            if UnWatched <> 0:
              query = query + "&UnplayedCount=" + str(UnWatched)
            query = query + "&height=685&width=480"
        elif originalType=="Primary2":
          addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
          if addonSettings.getSetting('showIndicators')=='true' and addonSettings.getSetting('showUnplayedIndicators')=='true':
            mb3Host = addonSettings.getSetting('ipaddress')
            mb3Port = addonSettings.getSetting('port')    
            userName = addonSettings.getSetting('username')     
        
            userid = downloadUtils.getUserId()  
            seriesUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items/" + item_id +"?format=json"
            jsonData = downloadUtils.downloadUrl(seriesUrl, suppress=False, popup=1 )
            result = json.loads(jsonData)
            userData = result.get("UserData")   
            UnWatched = 0 if userData.get("UnplayedItemCount")==None else userData.get("UnplayedItemCount")        
            if UnWatched <> 0:
              query = query + "&UnplayedCount=" + str(UnWatched)
            query = query + "&height=220&width=156"            
        return "http://localhost:15001/?id=" + str(item_id) + query   
        
    def run(self):
        self.logMsg("Started")
        
        self.updateNextUp()
        lastRun = datetime.today()
        
        while (xbmc.abortRequested == False):
            td = datetime.today() - lastRun
            secTotal = td.seconds
            
            if(secTotal > 300):
                self.updateNextUp()
                lastRun = datetime.today()

            xbmc.sleep(3000)
                        
        self.logMsg("Exited")
        
    def updateNextUp(self):
        self.logMsg("updateNextUp Called")
        
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        
        mb3Host = addonSettings.getSetting('ipaddress')
        mb3Port = addonSettings.getSetting('port')    
        userName = addonSettings.getSetting('username')     
        
        userid = downloadUtils.getUserId()
        self.logMsg("updateNextUp UserID : " + userid)
        
        self.logMsg("Updating NextUp List")
        
        nextUpUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Shows/NextUp?UserId=" + userid + "&Fields=Path,Genres,MediaStreams,Overview&format=json"
        
        jsonData = downloadUtils.downloadUrl(nextUpUrl, suppress=False, popup=1 )
        result = json.loads(jsonData)
        self.logMsg("NextUP TV Show Json Data : " + str(result), level=2)
        
        result = result.get("Items")
        WINDOW = xbmcgui.Window( 10000 )
        if(result == None):
            result = []   

        item_count = 1
        for item in result:
            title = "Missing Title"
            if(item.get("Name") != None):
                title = item.get("Name").encode('utf-8')
                
            seriesName = "Missing Name"
            if(item.get("SeriesName") != None):
                seriesName = item.get("SeriesName").encode('utf-8')   

            eppNumber = "X"
            tempEpisodeNumber = "XX"
            if(item.get("IndexNumber") != None):
                eppNumber = item.get("IndexNumber")
                if eppNumber < 10:
                  tempEpisodeNumber = "0" + str(eppNumber)
                else:
                  tempEpisodeNumber = str(eppNumber)
            
            seasonNumber = item.get("ParentIndexNumber")
            tempSeasonNumber = "XX"
            if seasonNumber < 10:
              tempSeasonNumber = "0" + str(seasonNumber)
            else:
              tempSeasonNumber = str(seasonNumber)
            rating = str(item.get("CommunityRating"))
            plot = item.get("Overview")
            if plot == None:
                plot=''
            plot=plot.encode('utf-8')

            item_id = item.get("Id")
           
            if item.get("Type") == "Episode" or item.get("Type") == "Season":
               series_id = item.get("SeriesId")
            
            poster = self.getImageLink(item, "Primary", str(series_id))
            small_poster = self.getImageLink(item, "Primary2", series_id)
            thumbnail = self.getImageLink(item, "Primary", str(item_id))
            logo = self.getImageLink(item, "Logo", str(series_id))
            fanart = self.getImageLink(item, "Backdrop", str(series_id))
            banner = self.getImageLink(item, "Banner", str(series_id))
            if item.get("SeriesThumbImageTag") != None:
              seriesthumbnail = self.getImageLink(item, "Thumb", str(series_id))
            else:
              seriesthumbnail = fanart
            
            url =  mb3Host + ":" + mb3Port + ',;' + item_id
            playUrl = "plugin://plugin.video.xbmb3c/?url=" + url + '&mode=' + str(_MODE_BASICPLAY)
            playUrl = playUrl.replace("\\\\","smb://")
            playUrl = playUrl.replace("\\","/")    

            # Process UserData
            userData = item.get("UserData")
            if(userData != None):
                resume = str(userData.get("PlaybackPositionTicks"))
                if (resume == "0"):
                    resume = "False"
                else:
                    resume = "True"

            self.logMsg("NextUpEpisodeMB3." + str(item_count) + ".EpisodeTitle = " + title, level=2)
            self.logMsg("NextUpEpisodeMB3." + str(item_count) + ".ShowTitle = " + seriesName, level=2)
            self.logMsg("NextUpEpisodeMB3." + str(item_count) + ".EpisodeNo = " + tempEpisodeNumber, level=2)
            self.logMsg("NextUpEpisodeMB3." + str(item_count) + ".SeasonNo = " + tempSeasonNumber, level=2)
            self.logMsg("NextUpEpisodeMB3." + str(item_count) + ".Thumb = " + thumbnail, level=2)
            self.logMsg("NextUpEpisodeMB3." + str(item_count) + ".Path  = " + playUrl, level=2)
            self.logMsg("NextUpEpisodeMB3." + str(item_count) + ".Rating  = " + rating, level=2)
            self.logMsg("NextUpEpisodeMB3." + str(item_count) + ".Art(tvshow.fanart)  = " + fanart, level=2)
            self.logMsg("NextUpEpisodeMB3." + str(item_count) + ".Art(tvshow.clearlogo)  = " + logo, level=2)
            self.logMsg("NextUpEpisodeMB3." + str(item_count) + ".Art(tvshow.banner)  = " + banner, level=2)  
            self.logMsg("NextUpEpisodeMB3." + str(item_count) + ".Art(tvshow.poster)  = " + poster, level=2)
            self.logMsg("NextUpEpisodeMB3." + str(item_count) + ".Plot  = " + plot, level=2)
            self.logMsg("NextUpEpisodeMB3." + str(item_count) + ".Resume  = " + resume, level=2)
            
            
            WINDOW.setProperty("NextUpEpisodeMB3." + str(item_count) + ".EpisodeTitle", title)
            WINDOW.setProperty("NextUpEpisodeMB3." + str(item_count) + ".ShowTitle", seriesName)
            WINDOW.setProperty("NextUpEpisodeMB3." + str(item_count) + ".EpisodeNo", tempEpisodeNumber)
            WINDOW.setProperty("NextUpEpisodeMB3." + str(item_count) + ".SeasonNo", tempSeasonNumber)
            WINDOW.setProperty("NextUpEpisodeMB3." + str(item_count) + ".Thumb", thumbnail)
            WINDOW.setProperty("NextUpEpisodeMB3." + str(item_count) + ".SeriesThumb", seriesthumbnail)
            WINDOW.setProperty("NextUpEpisodeMB3." + str(item_count) + ".Path", playUrl)            
            WINDOW.setProperty("NextUpEpisodeMB3." + str(item_count) + ".Rating", rating)
            WINDOW.setProperty("NextUpEpisodeMB3." + str(item_count) + ".Art(tvshow.fanart)", fanart)
            WINDOW.setProperty("NextUpEpisodeMB3." + str(item_count) + ".Art(tvshow.clearlogo)", logo)
            WINDOW.setProperty("NextUpEpisodeMB3." + str(item_count) + ".Art(tvshow.banner)", banner)
            WINDOW.setProperty("NextUpEpisodeMB3." + str(item_count) + ".Art(tvshow.poster)", poster)
            WINDOW.setProperty("NextUpEpisodeMB3." + str(item_count) + ".Art(tvshow.small_poster)", small_poster)
            WINDOW.setProperty("NextUpEpisodeMB3." + str(item_count) + ".Plot", plot)
            WINDOW.setProperty("NextUpEpisodeMB3." + str(item_count) + ".Resume", resume)
            
            WINDOW.setProperty("NextUpEpisodeMB3.Enabled", "true")
            
            item_count = item_count + 1
            
        if(item_count < 10):
            # blank any not available
            for x in range(item_count, 11):           
                WINDOW.setProperty("NextUpEpisodeMB3." + str(x) + ".EpisodeTitle", "")
                WINDOW.setProperty("NextUpEpisodeMB3." + str(x) + ".ShowTitle", "")
                WINDOW.setProperty("NextUpEpisodeMB3." + str(x) + ".EpisodeNo", "")
                WINDOW.setProperty("NextUpEpisodeMB3." + str(x) + ".SeasonNo", "")
                WINDOW.setProperty("NextUpEpisodeMB3." + str(x) + ".Thumb", "")
                WINDOW.setProperty("NextUpEpisodeMB3." + str(x) + ".Path", "")            
                WINDOW.setProperty("NextUpEpisodeMB3." + str(x) + ".Rating", "")
                WINDOW.setProperty("NextUpEpisodeMB3." + str(x) + ".Art(tvshow.fanart)", "")
                WINDOW.setProperty("NextUpEpisodeMB3." + str(x) + ".Art(tvshow.clearlogo)", "")
                WINDOW.setProperty("NextUpEpisodeMB3." + str(x) + ".Art(tvshow.banner)", "")
                WINDOW.setProperty("NextUpEpisodeMB3." + str(x) + ".Art(tvshow.poster)", "")
                WINDOW.setProperty("NextUpEpisodeMB3." + str(x) + ".Plot", "")
                WINDOW.setProperty("NextUpEpisodeMB3." + str(x) + ".Resume", "")        
            
            
            
            
