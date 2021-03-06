from scrapy import Spider, Request
from scrapy.item import DictItem
from scrapy.utils.trackref import NoneType
from mediaspider.items import VInfoItem,ReplyInfoItem,DanmuInfoItem,UInfoItem,VInfoDynamicItem
import json
import logging
import requests
import re
import time
import datetime



class BilibiliSpider(Spider):     
    name = 'bilibili'
    
    url_userspace=r'https://api.bilibili.com/x/space/arc/search?mid={mid}&pn={pn}&ps={ps}'
    url_videoinfo=r'http://api.bilibili.com/x/web-interface/view?bvid={bvid}'
    url_reply=r'http://api.bilibili.com/x/v2/reply?type={Type}&oid={oid}&pn={pn}&ps={ps}'
    
    def __init__(self, *args, mid: str=None, ps: int=None, **kwargs):
        """初始化

            Args:
                mid: 用户id
                ps: 视频列表每页视频数量，默认100
        """

        super().__init__(*args, **kwargs)

        if mid is None: mid = 672328094  #用户的id 老番茄 546195 番剧 928123 影视 15773384 嘉然 672328094
        if ps is None: ps = 100

        self.mid = mid
        self.ps = ps
        self.count=0
        # 视频列表链接模版 （一个参数）
        self.url = self.url_userspace.format(mid=mid, ps=ps, pn='{}')

        self.pn = 1
        # self.maxpn=int(GetArchivecount(mid)/ps)+1
        # self.logger.debug('======'  + str(maxpn) + "======")
        # 初始链接
        self.start_urls = [self.url.format(self.pn)]

    def parse(self, response):
        
        jresponse=json.loads(response.text)
        

        # logging.warning('======'  + str(len(vlist)) + "======")
        # logging.warning('======code'  + str(jresponse['code']) + "======")
        logging.warning(str(self.pn)+'======status:'  + str(response.status) + "======")

        
        vlist=jresponse['data']['list']['vlist']
        if len(vlist)>0:
            for vinfo in vlist:
                bvid=vinfo['bvid']
                oid=vinfo['aid']
                vurl=self.url_videoinfo.format(bvid=bvid)
                rurl=self.url_reply.format(Type=1,oid=oid,pn=100,ps=50)
                logging.warning('======'  + str(bvid) + "======")
                
                yield Request(url=vurl, callback=self.ParseVideoInfo,dont_filter =True)
                
                yield Request(url=rurl, callback=self.ParseReplyInfo,dont_filter = True)

        
            self.pn += 1
            url = self.url.format(self.pn)
            yield Request(url=url, callback=self.parse,dont_filter = True)
            
    
    

    def ParseVideoInfo(self, response):
        # logging.warning('======code:'  + str(json.loads(response.text)['code']) + "======")
        # logging.warning('======code:'  + str(response.status) + "======")
        if json.loads(response.text)['code']==-412:
            yield None
        else:
            data=json.loads(response.text)['data']
            #基本信息
            
            aid = data['aid']  # 视频ID
            
            bvid = data['bvid']  # 视频ID
            cid = data['cid']  # 弹幕连接id
            tid = data['tid']  # 区       
            iscopy=data['copyright'] # 是否转载  
            tname=data['tname']  # 子分区
            pic = data['pic']  # 封面
            title = data['title']  # 标题
            desc = data['desc']  # 简介
            duration = data['duration']  # 总时长，所有分P时长总和
            dimension=str(data['dimension'] ) #视频1P分辨率
            videos = data['videos']  # 分P数
            pubdate = data['pubdate']  # 发布时间
            ctime=data['ctime'] #用户投稿时间      
            
            
            #视频状态
            stat=data['stat']            
            view = stat['view']  # 播放数
            danmaku = stat['danmaku']   # 弹幕数
            reply = stat['reply']   # 评论数
            like = stat['like']   # 点赞数
            dislike = stat['dislike']   # 点踩数
            coin = stat['coin']   # 投币数
            favorite = stat['favorite']   # 收藏数
            share = stat['share']  # 分享数
            now_rank=stat['now_rank'] #当前排名 
            his_rank=stat['his_rank'] #历史最高排名

            # UP主信息
            owner=data['owner']
            mid = owner['mid']  # UP主ID

            item = VInfoItem(
                    
                aid = aid ,
                bvid = bvid,
                cid = cid  ,
                iscopy=iscopy ,
                tid = tid  ,
                tname=tname ,
                pic = pic  ,
                title = title ,
                descs = desc ,
                duration =duration ,
                dimension=dimension ,
                videos = videos  ,
                pubdate = pubdate  ,
                ctime=ctime ,
                

                
                view = view  ,
                danmaku = danmaku  ,
                reply = reply   ,
                likes =like  ,
                dislikes = dislike  ,
                coin = coin  ,
                favorite = favorite  ,
                share = share  ,
                now_rank=now_rank ,
                his_rank=his_rank ,
                    
                
                mid = mid 
                )
            yield item

    def ParseReplyInfo(self, response):

        
        if json.loads(response.text)['code']==-412:
            
            yield None
        else:
            data=json.loads(response.text)['data']
            logging.warning(json.loads(response.text)['code'])
            # logging.warning(data)
            item_list=[]
            RepliList=data['replies']
            for Repli in RepliList:
                objRepli={}
                objRepli['oid']=Repli['oid']
                objRepli['message']=Repli['content']['message']
                objRepli['mid']=Repli['mid']
                objRepli['likes']=Repli['like']
                objRepli['ctime']=Repli['ctime']
                objRepli['rpid']=Repli['rpid']
                item= objRepli
                yield item
                  
class VInfoSpider(Spider):    
    name='vinfospider'

    url=r'http://api.bilibili.com/x/web-interface/view?bvid={bvid}'
    def __init__(self,bvid='BV1154y1n75N',addition=True):
       self.bvid=bvid
       self.addition=addition
       
    #    self.start_urls = [self.url.format(bvid=self.bvid)]

    def start_requests(self):
        # logging.warning(self.url.format(bvid=self.bvid))
        yield Request(self.url.format(bvid=self.bvid),callback=self.parse)

    def parse(self, response):
        if json.loads(response.text)['code']==0:

            data=json.loads(response.text)['data']
            vdict={}
            #基本信息
                                       
            
            vdict['bvid'] = data['bvid']  # 视频ID
            
            #视频状态
            stat=data['stat']            
            vdict['view'] = stat['view']  # 播放数
            vdict['danmaku ']= stat['danmaku']   # 弹幕数
            vdict['reply'] = stat['reply']   # 评论数
            vdict['likes'] = stat['like']   # 点赞数
            vdict['dislikes'] = stat['dislike']   # 点踩数
            vdict['coin'] = stat['coin']   # 投币数
            vdict['favorite ']= stat['favorite']   # 收藏数
            vdict['share'] = stat['share']  # 分享数
            vdict['now_rank']=stat['now_rank'] #当前排名 
            vdict['his_rank']=stat['his_rank'] #历史最高排名

            # UP主信息
            owner=data['owner']
            vdict['mid'] = owner['mid']  # UP主ID

            if self.addition:
                vdict['recordtime']=time.time()
                # logging.warning(time.time())
                item= VInfoDynamicItem(VItem= vdict) 
                return item


            vdict['aid'] = data['aid']  # 视频ID
            vdict['cid ']= data['cid']  # 弹幕连接id
            vdict['tid ']= data['tid']  # 区       
            vdict['iscopy']=data['copyright'] # 是否转载  
            vdict['tname']=data['tname']  # 子分区
            vdict['pic'] = data['pic']  # 封面
            vdict['title'] = data['title']  # 标题
            vdict['descs'] = data['desc']  # 简介
            vdict['duration'] = data['duration']  # 总时长，所有分P时长总和
            vdict['dimension']=str(data['dimension'] ) #视频1P分辨率
            vdict['videos ']= data['videos']  # 分P数
            vdict['pubdate ']= data['pubdate']  # 发布时间
            vdict['ctime']=data['ctime'] #用户投稿时间 

            item= VInfoItem(VItem= vdict) 


            return item
    
    # def GetVinfo(self, response):

class DanmuSpder(Spider):
    name = 'danmuspider'
    url=r'https://comment.bilibili.com/{cid}.xml'
    def __init__(self,cid='21994000'):
        """初始化

            Args:
                oid: 用户id
                ps: 视频列表每页视频数量，默认100
        """
        self.cid=cid

        # self.url = self.url.format(cid=cid)
        # self.start_urls = [self.url]

    def start_requests(self):
        
        yield Request(self.url.format(cid=self.cid),callback=self.parse)

    def parse(self, response):
        
        if response.status==200:
            data=response.text
            reDanmu = re.compile(
        r'<d p="(.*?),(.*?),(.*?),(.*?),(.*?),(.*?),(.*?),(.*?)">(.*?)</d>')
            listDanmu = re.findall(reDanmu, data)
            listDictDanmu = []
            for itemDanmu in listDanmu:
                #去除高级弹幕
                
                if itemDanmu[8] == '':
                    continue
                if itemDanmu[8][0]=='[' :
                    continue
                dictItemDanmu = {}
                dictItemDanmu["cid"] = self.cid
                dictItemDanmu["floattime"] = float(itemDanmu[0])
                dictItemDanmu["mode"] = itemDanmu[1]
                dictItemDanmu["size"] = itemDanmu[2]
                dictItemDanmu["color"] = itemDanmu[3]
                dictItemDanmu["timestamp"] = itemDanmu[4]
                dictItemDanmu["pool"] = itemDanmu[5]
                dictItemDanmu["author"] = itemDanmu[6]
                dictItemDanmu["rowid"] = itemDanmu[7]
                dictItemDanmu["text"] = itemDanmu[8]
                item= DanmuInfoItem(DItem= dictItemDanmu)               
                yield item
               
class ReplySpider(Spider):

    name = 'replyspider'
    url=r'http://api.bilibili.com/x/v2/reply?type={type}&oid={oid}&pn={pn}&ps={ps}'
    def __init__(self,oid='846685722',type=1,pn=1,ps=40):
        """初始化

            Args:
                oid: 用户id
                ps: 视频列表每页视频数量，默认100
        """
        self.oid=oid
        self.ps = ps
        self.pn=pn
        self.type=type
        self.url=self.url.format(pn='{}',oid=self.oid,type=self.type,ps=self.ps)
        # self.start_urls = [self.url.format(self.pn)]
        self.count=0
        self.wrong=0
    def start_requests(self):
        url=self.url.format(self.pn)            
        yield Request(url,callback=self.parse)

    def parse(self, response, **kwargs):
        self.count+=1

        if json.loads(response.text)['code']==-412:
            # logging.warning(json.loads(response.text)['code'])
            logging.warning(json.loads(response.text))
            self.wrong+=1
            yield None
        else:
            data=json.loads(response.text)['data']
            RepliList=data['replies']
            if isinstance(RepliList,list):
                
                for Repli in RepliList:
                    objRepli={}
                    objRepli['oid']=Repli['oid']
                    objRepli['message']=Repli['content']['message']
                    objRepli['mid']=Repli['mid']
                    objRepli['likes']=Repli['like']
                    objRepli['ctime']=Repli['ctime']
                    objRepli['rpid']=Repli['rpid']

                    item= ReplyInfoItem(RItem= objRepli)
                    yield item
                self.pn+=1
                logging.warning(len(RepliList))
                
                url = self.url.format(self.pn)

                yield Request(url=url, callback=self.parse,dont_filter =True)
        # logging.warning(self.oid,"parse 执行了",self.count,"次。失败率：",self.wrong/self.count)
   
class UserInfoSpider(Spider): 
    name='userspider'
    cookies= {}
    url1=r'http://api.bilibili.com/x/space/acc/info?mid={mid}'
    url2=r'http://api.bilibili.com/x/web-interface/card?mid={mid}'

    def __init__(self,mid='672328094',addition=False,cookies={'SESSDATA':'3589d867%2C1634960121%2Ca96e9e71'}):
       self.mid=mid
       self.addition=addition
       self.cookies=cookies
       self.udict={}
    #    self.start_urls = [self.url.format(bvid=self.bvid)]

    def start_requests(self):
        # logging.warning(self.url.format(bvid=self.bvid))
        yield Request(self.url2.format(mid=self.mid),cookies=self.cookies,callback=self.url2parse)
        

    def url1parse(self, response):
        if json.loads(response.text)['code']==0:

            data=json.loads(response.text)['data']
            udict={}
            #基本信息
            self.udict['mid']=self.mid
            self.udict['sex']=data['sex']
            self.udict['face']=data['face']
            self.udict['sign']=data['sign']
            self.udict['level']=data['level']
            self.udict['coins']=data['coins']               
            # logging.warning(self.udict)           
            yield Request(self.url2.format(mid=self.mid),cookies=self.cookies,callback=self.url2parse)
            # vdict['bvid'] = data['bvid']  # 视频ID
            
            # #视频状态
            # stat=data['stat']            
            # vdict['view'] = stat['view']  # 播放数
            # vdict['danmaku ']= stat['danmaku']   # 弹幕数
            # vdict['reply'] = stat['reply']   # 评论数
            # vdict['likes'] = stat['like']   # 点赞数
            # vdict['dislikes'] = stat['dislike']   # 点踩数
            # vdict['coin'] = stat['coin']   # 投币数
            # vdict['favorite ']= stat['favorite']   # 收藏数
            # vdict['share'] = stat['share']  # 分享数
            # vdict['now_rank']=stat['now_rank'] #当前排名 
            # vdict['his_rank']=stat['his_rank'] #历史最高排名

            # # UP主信息
            # owner=data['owner']
            # vdict['mid'] = owner['mid']  # UP主ID

            # if self.addition:
            #     vdict['recordtime']=time.time()
            #     # logging.warning(time.time())
            #     item= VInfoDynamicItem(VItem= vdict) 
            #     return item


            # vdict['aid'] = data['aid']  # 视频ID
            # vdict['cid ']= data['cid']  # 弹幕连接id
            # vdict['tid ']= data['tid']  # 区       
            # vdict['iscopy']=data['copyright'] # 是否转载  
            # vdict['tname']=data['tname']  # 子分区
            # vdict['pic'] = data['pic']  # 封面
            # vdict['title'] = data['title']  # 标题
            # vdict['descs'] = data['desc']  # 简介
            # vdict['duration'] = data['duration']  # 总时长，所有分P时长总和
            # vdict['dimension']=str(data['dimension'] ) #视频1P分辨率
            # vdict['videos ']= data['videos']  # 分P数
            # vdict['pubdate ']= data['pubdate']  # 发布时间
            # vdict['ctime']=data['ctime'] #用户投稿时间 

            item= UInfoItem(UItem= self.udict) 
            return item
            
    def url2parse(self,response):
        # logging.warning(response.text)
        if json.loads(response.text)['code']==0:

            data=json.loads(response.text)['data']
            self.udict['archive_count']=data['archive_count']
            card=data['card']     

            self.udict['fans']=card['fans']
            self.udict['attention']=card['attention']
            
            
            self.udict['mid']=card['mid']
            self.udict['mname']=card['name']
            self.udict['sex']=card['sex']
            self.udict['face']=card['face']
            self.udict['sign']=card['sign']
            self.udict['levels']=card['level_info']['current_level']
            
            item= UInfoItem(UItem= self.udict) 
            return item


# class UInfoSpider(Spider):


class UserVideoSpider(Spider):
    name = 'uservideospider'
    
    url_userspace=r'https://api.bilibili.com/x/space/arc/search?mid={mid}&pn={pn}&ps={ps}'
 
    
    def __init__(self, mid='672328094', ps: int=None,arglist=[],addition=True):


        if mid is None: mid = 546195  #用户的id 老番茄 546195 番剧 928123 影视 15773384 嘉然 672328094
        if ps is None: ps = 100

        self.mid = mid
        self.ps = ps
  
        self.url = self.url_userspace.format(mid=mid, ps=ps, pn='{}')
        self.pn = 1
        self.start_urls = [self.url.format(self.pn)]
        self.arglist=arglist
        self.addition=addition

    def parse(self, response):
        
        jresponse=json.loads(response.text)
        
        vlist=jresponse['data']['list']['vlist']
        if len(vlist)>0:
            for vinfo in vlist:
                bvid=vinfo['bvid']
                vs=VInfoSpider(bvid=bvid,addition=self.addition)
                yield Request(vs.url.format(bvid=bvid),callback=vs.parse)
                if 'danmu' in self.arglist:
                    cid=vinfo['cid']
                    ds=DanmuSpder(cid=cid)
                    yield Request(ds.url,callback=ds.parse)
                    
                    # ds.start_requests()
                if 'reply' in self.arglist:
                    logging.warning("add")
                    aid=vinfo['aid']
                    rs=ReplySpider(oid=aid)
                    yield Request(rs.url.format(1),callback=rs.parse)
                    # rs.start_requests()
                # logging.warning("skip?")
                


            self.pn += 1
            url = self.url.format(self.pn)
            yield Request(url=url, callback=self.parse,dont_filter = True)
            
    
    
# class RankSpider(Spider):
#     url=



# class KeyWordSpider(Spider):
#     url=

# class PartitionSpider(Spider):
#     url=









        
        






