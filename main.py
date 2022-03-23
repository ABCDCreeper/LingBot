# -*- coding: UTF-8 -*-
import configparser
import base64
import datetime
import json
import os
import random
import re
import sys
import threading
import time
import traceback
import hypixel
from io import BytesIO

import requests
import websocket
from mcstatus import MinecraftServer
from PIL import Image, ImageDraw, ImageFont

hypixel.setKeys(["69a1e20d-94ba-4322-91c5-003c6a5dd271"])
hypixel.setCacheTime(3600.0)

SERVER_ADDR = "127.0.0.1"
ADMIN_LIST = [1790194105, 1584784496, 2734583, 2908331301, 3040438566]
HYPBAN_COOKIE = None
SEND_AD_LIST = {}
BLACK_LIST = []
CACHE_MESSAGE = []
BANCHECK_UID = {}
WSURL = SERVER_ADDR+":10540"
HTTPURL = SERVER_ADDR+":10500"
MC_MOTD_COLORFUL = re.compile(r"§.")
ALL_MESSAGE = 0
MESSAGE_PRE_MINUTE = [0, 0]
ALL_AD = 0
BILI_BV_RE = re.compile(r"BV([a-z|A-Z|0-9]{10})")
REQ_TEXT = re.compile(r"get±.*±")
timePreMessage = 0
recordTime = int(time.time())
isChatBypassOpened = False
unicodeSymbolList = ["‍", "‌", "‭"]
ANTISPAMMER = {}
IGNORE_GROUP = [1079822858]
FEEDBACKS = {}


def readConfig():
    global ADMIN_LIST, BLACK_LIST, FEEDBACKS
    config = configparser.ConfigParser()
    config.read("config.ini")
    s = config["DEFAULT"]
    try:
        ADMIN_LIST = [int(i) for i in s["admin"].split(",")]
    except:
        pass
    try:
        BLACK_LIST = [int(i) for i in s["blacklist"].split(",")]
    except:
        pass
    config = configparser.ConfigParser()
    config.read("feedback.ini")
    try:
        FEEDBACKS = config["FEEDBACKS"]
    except:
        pass


def saveConfig():
    global ADMIN_LIST, BLACK_LIST, FEEDBACKS
    config = configparser.ConfigParser()
    config["DEFAULT"] = {
        "admin": ",".join('%s' %id for id in ADMIN_LIST),
        "blacklist": ",".join('%s' %id for id in BLACK_LIST)
    }
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    config = configparser.ConfigParser()
    config["FEEDBACKS"] = FEEDBACKS
    with open('feedback.ini', 'w') as configfile:
        config.write(configfile)


def quit():
    print("Try to Quit...")
    saveConfig()

def SpammerChecker(group, user):
    global ANTISPAMMER
    if group not in ANTISPAMMER:
        ANTISPAMMER[group] = {}
    if user not in ANTISPAMMER[group]:
        ANTISPAMMER[group][user] = [0, 0]
    if time.time()-ANTISPAMMER[group][user][0] <= 15:
        ANTISPAMMER[group][user][1] += 1
    else:
        ANTISPAMMER[group][user][0] = time.time()
        ANTISPAMMER[group][user][1] = 1
    if ANTISPAMMER[group][user][1] > 8:
        ANTISPAMMER[group][user] = [0, 0]
        return True
    else:
        return False


def getRuntime():
    nowtime = int(time.time())
    return "{}秒".format(int(nowtime - recordTime))
    

def text2image(text):
    imageuid = str(random.randint(10000000,9999999999))
    fontSize = 22
    max_w = 0
    lines = text.split('\n')
    # print(len(lines))
    fontPath = r"a.ttf"
    font = ImageFont.truetype(fontPath, fontSize)
    for i in lines:
        try:
            if max_w <= font.getmask(i).getbbox()[2]:
                max_w = font.getmask(i).getbbox()[2]
        except:
            pass
    im = Image.new("RGB", (max_w+11, len(lines)*(fontSize+8)), (255, 255, 255))
    dr = ImageDraw.Draw(im)
    dr.text((1, 1), text, font=font, fill="#000000")
    im.save(imageuid+".cache.png")
    with open(imageuid+".cache.png", "rb") as f:
        return base64.b64encode(f.read()).decode()


def strQ2B(ustring):
    rstring = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 12288:
            inside_code = 32
        elif inside_code >= 65281 and inside_code <= 65374:
            inside_code -= 65248

        rstring += chr(inside_code)
    return rstring


def acg_img():
    try:
        a = "https://img.xjh.me/random_img.php?return=json"
        a1 = requests.get(url=a).json()
        return base64.b64encode(requests.get(url='https:'+a1["img"]).content).decode()
    except Exception as e:
        return text2image("获取图片失败\n"+traceback.format_exc())
    

def on_message2(ws, message):
    global HYPBAN_COOKIE, isChatBypassOpened, CACHE_MESSAGE, timePreMessage, MESSAGE_PRE_MINUTE, ALL_MESSAGE, ALL_AD, FEEDBACKS
    try:
        # 处理消息内容
        a = json.loads(message)
        message_text = ""
        message_id = 0
        ad = a
        if ad["post_type"] == "message":
            if ad["message_type"] != "group":
                return
        else:
            return
        message_text = ad["message"]
        message_text = strQ2B(message_text)
        for i in unicodeSymbolList:
            message_text.replace(i, "")
        sender_qqnumber = ad["sender"]["user_id"]
        sender_name = ad["sender"]["nickname"]
        group_number = ad["group_id"]
        message_id = ad["message_id"]
        if message_text == "":
            return
        if time.time() - MESSAGE_PRE_MINUTE[0] >= 60:
            MESSAGE_PRE_MINUTE = [time.time(), 1]
        else:
            MESSAGE_PRE_MINUTE[1] += 1
        ALL_MESSAGE += 1

        def fastReply(message, at=True, reply=True):
            temp1 = [None, None]

            if at:
                temp1[0] == sender_qqnumber
            
            if reply:
                temp1[1] == message_id
            
            sendMessage(message, target_qq=temp1[0], target_group=group_number, message_id=temp1[1])
        
        print("[{0}] {1}({2}) {3}".format(group_number, sender_name, sender_qqnumber, message_text))

        reScan = re.search(
            r"定制水影|加群(:)[0-9]{5,10}|.*内部|\n元|破甲|天花板|工具箱|绕更新|开端|不封号|外部|.* toolbox|替换au|绕过(盒子)vape检测|外部|防封|封号|waibu|晋商|禁商|盒子更新后|跑路|小号机|群(号)(:)[0-9]{5,10}|\d{2,4}红利项目|躺赚|咨询(\+)|捡钱(模式)|(个人)创业|交流群|带价私聊|出.*号|裙(号)(:)[0-9]{5,10}|群(号)(:)[0-9]{5,10}|Q[0-9]{5,10}|免费(获取)|.*launcher|.*配置|3xl?top|.*小卖铺",
            message_text.replace(" ", "").replace(".", "").replace("\n", "").lower())
        if len(message_text) > 35 and reScan != None:
            if sender_qqnumber in ADMIN_LIST:
                sendMessage("{}发送的一条消息触发了正则 并且此人在超管名单内\n内容:\n{}".format(sender_qqnumber, message_text), target_group=868218262)
                return
            mutePerson(group_number, sender_qqnumber, 600)
            recall(message_id)
            ALL_AD  += 1
            return

        multiMsg = re.search(r'\[CQ:forward,id=(.*)\]', message_text)
        if multiMsg != None:
            a = requests.get(url="http://"+HTTPURL+"/get_forward_msg?message_id="+str(multiMsg.group(1))).json()["data"]["messages"]
            multiMsg_raw = ""
            for i in a:
                multiMsg_raw += i["content"]
            reScan = re.search(
                r"定制水影|加群(:)[0-9]{5,10}|.*内部|\n元|破甲|天花板|工具箱|绕更新|开端|不封号|外部|.* toolbox|替换au|绕过(盒子)vape检测|外部|防封|封号|waibu|晋商|禁商|盒子更新后|跑路|小号机|群(号)(:)[0-9]{5,10}|\d{2,4}红利项目|躺赚|咨询(\+)|捡钱(模式)|(个人)创业|交流群|带价私聊|出.*号|裙(号)(:)[0-9]{5,10}|群(号)(:)[0-9]{5,10}|Q[0-9]{5,10}|免费(获取)|.*launcher|.*配置|3xl?top|.*小卖铺",
                multiMsg_raw.replace(" ", "").replace(".", "").replace("\n", "").lower())
            if reScan != None:
                fastReply("您发送的合并转发内容貌似有广告!")
                mutePerson(group_number, sender_qqnumber, 600)
                recall(message_id)
                ALL_AD  += 1
                return

        
        try:
            if SpammerChecker(group_number, sender_qqnumber):
                mutePerson(group_number, sender_qqnumber, 600)
                recall(message_id)
                fastReply("不要刷屏哟~~", reply=False)
        except:
            pass

        if sender_qqnumber in BLACK_LIST:
            recall(message_id)
            return
        
        if message_text.lower().count("[cq:image") >= 3:
            if sender_qqnumber in ADMIN_LIST:
                mutePerson(group_number, sender_qqnumber, 600)
                recall(message_id)
                fastReply("太...太多图片了..", reply=False)

        command_list = message_text.split(" ")
        if message_text in ["!test", "凌状态"]:
            fastReply("Hello! 已处理 {} 条消息\n已经运行了 {}\n平均每条消息耗时 {} 秒\n拦截了 {} 条广告 占全部处理消息的 {}%".format(ALL_MESSAGE, getRuntime(), timePreMessage, ALL_AD, (ALL_AD/ALL_MESSAGE)*100))
            
        if command_list[0] in ["!help", "菜单"]:
            fastReply("请访问: https://lingbot.guimc.ltd/\nLingbot官方群：308089090")

        if message_text == "一语":
            fastReply(requests.get("http://api.muxiuge.cn/API/society.php").json()["text"])
        
        if message_text.find("[CQ:json,data=") != -1:
            message_text = message_text.replace("\\", "")
            if message_text.find('https://b23.tv/') != -1:
                str1 = requests.get(url="https://api.bilibili.com/x/web-interface/view?bvid={}".format(re.findall(r'<link data-vue-meta="true" rel="canonical" href="https://www.bilibili.com/video/.*/">',requests.get(json.loads(re.search(r"\[CQ:json,data=(.*)\]",message_text).group(1).replace("&amp;", "&"))["meta"]["news"]["jumpUrl"]).text)[0].replace(r'<link data-vue-meta="true" rel="canonical" href="https://www.bilibili.com/video/', "")[:-3])).json()
                if str1["code"] != 0:
                    print("查询失败")
                    return
                str1 = str1["data"]
                response = requests.get(str1["pic"])
                im_vl = Image.open(BytesIO(response.content))
                im_v = im_vl.resize((430, 270), Image.ANTIALIAS)
                imageuid = str(random.randint(10000000,9999999999))
                fontSize = 22
                max_w = 0
                s = ""
                if str1["copyright"] == 1:
                    s = "自制"
                elif str1["copyright"] == 2:
                    s = "转载"
                else:
                    s = "未曾设想的投稿类型: {}  (不是转载也不是自制?)".format(str1["copyright"])
                text = """标题: {}
UP主: {} ({})
投稿分区: {} ({})
投稿类型: {}
视频链接: https://www.bilibili.com/video/{}/
播放量: {}
简介:
{}""".format(str1["title"], str1["owner"]["name"], str1["owner"]["mid"],
            str1["tname"], str1["tid"], s, str1["bvid"], str1["stat"]["view"], str1["desc"])
                lines = text.split('\n')
                # print(len(lines))
                fontPath = r"a.ttf"
                font = ImageFont.truetype(fontPath, fontSize)
                for i in lines:
                    try:
                        if max_w <= font.getmask(i).getbbox()[2]:
                            max_w = font.getmask(i).getbbox()[2]
                    except:
                        pass
                im = Image.new("RGB", (max_w+11, (len(lines)*(fontSize+8))+280), (255, 255, 255))
                im.paste(im_v, (0,0))
                dr = ImageDraw.Draw(im)
                dr.text((1, 280), text, font=font, fill="#000000")
                im.save(imageuid+"_cache.png")
                with open(imageuid+"_cache.png", "rb") as f:
                    fastReply("[CQ:image,file=base64://"+base64.b64encode(f.read()).decode()+"]")
        
        if message_text == "一英":
            fastReply(requests.get("http://open.iciba.com/dsapi/").json()["content"] + "\n" +
                         requests.get("http://open.iciba.com/dsapi/").json()["note"])

        if message_text == "二次元":
            fastReply("[CQ:image,file=base64://"+acg_img()+"]")

        if message_text == "必应壁纸":
            fastReply("[CQ:image,file=base64://"+base64.b64encode(requests.get("http://www.xgstudio.xyz/api/bing.php").content).decode()+"]")

        if message_text == "一话":
            req1 = requests.get("http://open.iciba.com/dsapi/").json()
            fastReply(
                         requests.get("http://api.muxiuge.cn/API/society.php").json()["text"])
            fastReply(req1["content"] + "\n" + req1["note"])
        
        if command_list[0] == "!feedback":
            fastReply("该功能已经下线了! https://lingbot.guimc.ltd/#/AboutFeedback")

        if command_list[0] == "!admin":
            if command_list[1] == "list":
                fastReply("{}".format(ADMIN_LIST))
            if sender_qqnumber not in ADMIN_LIST:
                fastReply("你的权限不足!")
                return
            if command_list[1] == "add":
                if int(command_list[2]) in ADMIN_LIST:
                    fastReply("超管内已经有这个人了")
                    return
                ADMIN_LIST.append(int(command_list[2]))
                fastReply("操作成功")
            elif command_list[1] == "remove":
                if int(command_list[2]) not in ADMIN_LIST:
                    fastReply("超管内没有这个人")
                    return
                elif int(command_list[2]) == 1584784496:
                    fastReply("不可以这么干哟~~")
                    sendMessage("{}尝试把您(Owner)从超管列表删除".format(sender_qqnumber), target_group=868218262)
                    return
                ADMIN_LIST.remove(int(command_list[2]))
                fastReply("操作成功")
        
        if command_list[0] == "!blacklist":
            if command_list[1] == "list":
                fastReply("{}".format(BLACK_LIST))
            if sender_qqnumber not in ADMIN_LIST:
                fastReply("你的权限不足!")
                return
            if command_list[1] == "add":
                if int(command_list[2]) in BLACK_LIST:
                    fastReply("黑名单内已经有这个人了")
                    return
                elif int(command_list[2]) == 1584784496:
                    fastReply("不可以这么干哦~~")
                    sendMessage("{}尝试把您(Owner)添加进黑名单".format(sender_qqnumber), target_group=868218262)
                    return
                BLACK_LIST.append(int(command_list[2]))
                fastReply("操作成功")
            elif command_list[1] == "remove":
                if int(command_list[2]) not in BLACK_LIST:
                    fastReply("黑名单内没有这个人")
                    return
                BLACK_LIST.remove(int(command_list[2]))
                fastReply("操作成功")


        if command_list[0] == "/mcping":
            server = MinecraftServer.lookup(command_list[1]).status()
            aaa = "Motd:\n{0}\n在线人数:{1}/{2}\nPing:{3}\nVersion:{4} (protocol:{5})".format(
                re.sub(MC_MOTD_COLORFUL, "", server.description), server.players.online, server.players.max,
                server.latency, re.sub(MC_MOTD_COLORFUL, "", server.version.name), server.version.protocol)
            aaa = aaa.replace("Hypixel Network", "嘉心糖 Network")
            aaa = "[CQ:image,file=base64://{}]".format(text2image(aaa))
            if server.favicon is not None:
                aaa = aaa + "\n[CQ:image,file="+server.favicon.replace("data:image/png;base64,", "base64://")+"]"
            fastReply(aaa)
                
        if command_list[0] == "!hypban":
            if len(command_list)<=2:
                fastReply("正确格式:#hypban <USERNAME> <BANID>")
            else:
                if sender_qqnumber not in BANCHECK_UID or sender_qqnumber in ADMIN_LIST:
                    BANCHECK_UID[sender_qqnumber] = time.time()
                elif time.time() - BANCHECK_UID[sender_qqnumber] <= 60:
                    fastReply("进入冷却时间 可在{}秒后使用".format(round(60.0 - (time.time() - BANCHECK_UID[sender_qqnumber]), 2)))
                    return
                fastReply("请稍等 正在向远程服务器发送请求")
                userName = command_list[1]
                BanID = command_list[2].replace("#", "")
                while True:
                    print("Username:{} BanID:{}".format(userName, BanID))
                    a = requests.get("http://127.0.0.1/hypban.php?name={0}&banid={1}&type=api".format(userName, BanID), headers={'Host': 'api.getfdp.today'}).text
                    if a.find("too many request") == -1:
                        break
                    time.sleep(3)
                print(a)
                if a.find("ERR|") != -1:
                    fastReply(a)
                else:
                    BANCHECK_UID[sender_qqnumber] = time.time()
                    fastReply( "[CQ:image,file=base64://"+text2image(a)+"]")

        if command_list[0] == "!send":
            if sender_qqnumber in ADMIN_LIST:
                msg1 = " ".join(command_list[2:])
                all_req = re.match(REQ_TEXT, msg1)
                print(all_req)
                if all_req != None:
                    msg1 = msg1.replace(all_req.group(0), urlget(all_req.group(0).replace("get±", "").replace("±", "")))
                if command_list[1] == "all":
                    s = getGroups()
                    fastReply("正在群发... 目标:{}个群".format(len(s)))
                    for i in s:
                        if i not in IGNORE_GROUP:
                            sendMessage(msg1, target_group=i)
                            time.sleep(random.randint(500, 800)/1000)
                    fastReply("群发完成")
                else:
                    sendMessage(msg1, target_group=command_list[1])
            else:
                fastReply("你的权限不足!")

        if command_list[0] == "!mute":
            if sender_qqnumber in ADMIN_LIST:
                if command_list[1] == "this":
                    command_list[1] = group_number
                else:
                    command_list[1] = int(command_list[1])
                command_list[2] = int(command_list[2].replace("@", ""))
                command_list[3] = int(command_list[3])
                if command_list[3] == 0:
                    unmutePerson(command_list[1], command_list[2])
                else:
                    mutePerson(command_list[1], command_list[2], command_list[3] * 60)
                    fastReply("已尝试在群 {} 禁言 {} {}分钟".format(command_list[1], command_list[2], command_list[3]))
            else:
                fastReply("你的权限不足!")
        
        if command_list[0] == "!namelocker":
            fastReply("恭喜你找到了一个彩蛋!")
            # 鬼!
            return
        
        if command_list[0] == "!search":
            if sender_qqnumber not in ADMIN_LIST:
                fastReply("你的权限不足!")
                return
            fastReply("正在从机器人所有加入的群搜索此人")
            a = search_user(int(command_list[1]))
            fastReply("搜索完成:\n{}".format(a))

        if command_list[0] == "!fdpinfo":
            if command_list[1] == "online":
                url = "https://bstats.org/api/v1/plugins/11076/charts/minecraftVersion/data"
                a = requests.get(url=url).json()
                onlinePlayer = 0
                for i in a:
                    onlinePlayer += i["y"]
                fastReply("[CQ:image,file=base64://"+text2image("OnlinePlayers: {}".format(onlinePlayer))+"]")
            elif command_list[1] == "versions":
                url = "https://bstats.org/api/v1/plugins/11076/charts/pluginVersion/data"
                a = requests.get(url=url).json()
                onlineVersion = []
                for i in a:
                    onlineVersion.append("{}: {}".format(i["name"], i["y"]))
                fastReply("[CQ:image,file=base64://"+text2image("OnlineVersionsInfo:\n{}".format("\n".join(onlineVersion)))+"]")
            elif command_list[1] == "systems":
                url = "https://bstats.org/api/v1/plugins/11076/charts/os/data"
                a = requests.get(url=url).json()
                onlineSystem = []
                for i in a["seriesData"]:
                    onlineSystem.append("{}: {}".format(i["name"], i["y"]))
                fastReply("[CQ:image,file=base64://"+text2image("OnlineSystms:\n{}".format("\n".join(onlineSystem)))+"]")
            elif command_list[1] == "countries":
                url = "https://bstats.org/api/v1/plugins/11076/charts/location/data"
                a = requests.get(url=url).json()
                onlineCountry = []
                for i in a:
                    onlineCountry.append("{}: {}".format(i["name"].replace("Hong Kong", "Hong Kong, China").replace("Taiwan", "Taiwan, China"),
                        i["y"]))
                fastReply("[CQ:image,file=base64://"+text2image("OnlineCountrys:\n{}".format("\n".join(onlineCountry)))+"]")
            elif command_list[1] == "beta":
                fastReply( "Please wait...")
                url = "https://api.github.com/repos/UnlegitMC/FDPClient/actions/runs"
                a = requests.get(url=url).json()
                objectIDs = []
                for i in a["workflow_runs"]:
                    if i["name"] == "build":
                        objectIDs.append(i["id"])
                actionInfo = requests.get(url="https://api.github.com/repos/UnlegitMC/FDPClient/actions/runs/{}".format(objectIDs[0])).json()
                updTime = actionInfo["head_commit"]["timestamp"]
                updMsg = actionInfo["head_commit"]["message"]
                updAuthor = "{} ({})".format(actionInfo["head_commit"]["author"]["name"], actionInfo["head_commit"]["author"]["email"])
                fastReply("Update Time:{}\n"
                             "Update Message:{}\n"
                             "Author:{}\n"
                             "Download URL:https://nightly.link/UnlegitMC/FDPClient/actions/runs/{}/FDPClient.zip\n".format(updTime, updMsg, updAuthor, objectIDs[0]))
            elif command_list[1] == "release":
                url = "https://api.github.com/repos/UnlegitMC/FDPClient/releases/latest"
                a = requests.get(url=url).json()
                files = []
                for i in a["assets"]:
                    files.append("{}: {}".format(i["name"], i["browser_download_url"].replace("github.com", "hub.fastgit.org")))
                fastReply("Version: {}\n".format(a["name"])+"\n".join(files))
        if command_list[0] == "!hyp":
            if len(command_list) == 1:
                fastReply("格式貌似有点问题?\n访问 https://lingbot.guimc.ltd/#/Commands 找一找你想要的功能罢")
                return
            
            # 获取玩家信息
            try:
                player1 = hypixel.Player(command_list[1])
            except:
                fastReply("貌似没有这个玩家?\n访问 https://lingbot.guimc.ltd/#/Commands 找一找你想要的功能罢")
                return
            pI = player1.getPlayerInfo()
            print(pI)
            if "lastLogin" not in pI: 
                pI["lastLogin"] = 0
            playerSkin = requests.get("https://crafatar.com/renders/body/"+pI["uuid"])
            pmsg = "---查询结果---\n玩家名称: [{}]{}\n等级: {}\nKarma(人品值): {}\n上次登陆: {}\n首次登陆: {}".format(pI["rank"]["rank"].replace(" ","").replace("PLUS", "+"), pI["displayName"], pI["networkLevel"], pI["karma"], datetime.datetime.utcfromtimestamp(pI["lastLogin"]/1000).strftime("%Y-%m-%d %H:%M:%S"), datetime.datetime.utcfromtimestamp(pI["firstLogin"]/1000).strftime("%Y-%m-%d %H:%M:%S"))
            if playerSkin.status_code == 200:
                pmsg = "[CQ:image,file=base64://"+base64.b64encode(playerSkin.content).decode()+"]\n"+pmsg
            fastReply(pmsg)
        
        BVID = re.match(BILI_BV_RE, message_text)
        if BVID != None:
            str1 = requests.get(url="https://api.bilibili.com/x/web-interface/view?bvid={}".format(BVID.group(0))).json()
            if str1["code"] != 0:
                print("查询失败")
                return
            str1 = str1["data"]
            response = requests.get(str1["pic"])
            im_vl = Image.open(BytesIO(response.content))
            im_v = im_vl.resize((430, 270), Image.ANTIALIAS)
            imageuid = str(random.randint(10000000,9999999999))
            fontSize = 22
            max_w = 0
            s = ""
            if str1["copyright"] == 1:
                s = "自制"
            elif str1["copyright"] == 2:
                s = "转载"
            else:
                s = "未曾设想的投稿类型: {}  (不是转载也不是自制?)".format(str1["copyright"])
            text = """标题: {}
UP主: {} ({})
投稿分区: {} ({})
投稿类型: {}
视频链接: https://www.bilibili.com/video/{}/
播放量: {}
简介:
{}""".format(str1["title"], str1["owner"]["name"], str1["owner"]["mid"],
        str1["tname"], str1["tid"], s, str1["bvid"], str1["stat"]["view"], str1["desc"])
            lines = text.split('\n')
            # print(len(lines))
            fontPath = r"a.ttf"
            font = ImageFont.truetype(fontPath, fontSize)
            for i in lines:
                try:
                    if max_w <= font.getmask(i).getbbox()[2]:
                        max_w = font.getmask(i).getbbox()[2]
                except:
                    pass
            im = Image.new("RGB", (max_w+11, (len(lines)*(fontSize+8))+280), (255, 255, 255))
            im.paste(im_v, (0,0))
            dr = ImageDraw.Draw(im)
            dr.text((1, 280), text, font=font, fill="#000000")
            im.save(imageuid+"_cache.png")
            with open(imageuid+"_cache.png", "rb") as f:
                fastReply("[CQ:image,file=base64://"+base64.b64encode(f.read()).decode()+"]")
    except Exception as e:
        fastReply("很抱歉，我们在执行你的指令时出现了一个问题 =_=\n各指令用法请查看 https://lingbot.guimc.ltd/")
        print(traceback.format_exc())


def mutePerson(group, qqnumber, mutetime):
    if mutetime > (43199*60):
        mutetime = 43199*60
    data1 = {
        "group_id": int(group),
        "user_id": int(qqnumber),
        "duration": int(mutetime)
    }
    requests.post(url="http://" + HTTPURL + "/set_group_ban", data=data1)


def unmutePerson(group, qqnumber):
    mutePerson(group, qqnumber, 0)


def recall(msgid):
    data1 = {
        "message_id": int(msgid)
    }
    requests.post(url="http://" + HTTPURL + "/delete_msg", data=data1)

def sendMessage(message, target_qq=None, target_group=None, message_id=None):
    if target_qq == None and target_group == None:
        raise Exception()
    
    if target_group != None:
        # 消息前缀 通常用于 At 回复消息
        prefix = ""

        if target_qq != None:
            prefix += "[CQ:at,qq={}]".format(target_qq)
        
        if message_id != None:
            prefix += "[CQ:reply,id={}]".format(message_id)
        
        # 构建数据
        data1 = {
            "group_id": int(target_group),
            "message": prefix+message
        }

        # 发送消息
        s = requests.post(url="http://" + HTTPURL + "/send_group_msg", data=data1)
        if s.ok != True:
            # 如果请求失败
            s.raise_for_status()
    else:
        print("WARN: 目前暂时不支持发送私聊消息")


def urlget(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 4 Build/JOP40D) AppleWebKit/535.19 (KHTML, '
                      'like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19'}
    temp = requests.get(url, headers=headers)
    return temp.text


def sendTempMsg(target1, target2, text):
    # 会风控
    print(text)


def getGroupUser(groupID: int):
    users = []
    a = requests.get(url="http://" + HTTPURL + "/get_group_member_list?group_id={}".format(groupID))
    if a.status_code != 200:
        raise ConnectionError()
    else:
        for i in a.json()["data"]:
            users.append(i["user_id"])
        return users


def getGroups():
    groups = []
    a = requests.get(url="http://" + HTTPURL + "/get_group_list")
    if a.status_code != 200:
        raise ConnectionError()
    else:
        print(a.json()["data"])
        for i in a.json()["data"]:
            groups.append(i["group_id"])
        return groups


def permCheck(groupID, target):
    return True


def search_user(uid):
    groups = []
    for i in getGroups():
        if uid in getGroupUser(i):
            groups.append(i)
        time.sleep(random.randint(35,65)/100)
    return groups


def temps_message(ws, message):
    global timePreMessage
    a = time.time()
    try:
        on_message2(ws, message)
    except:
        pass
    b = time.time()
    sflTime = b-a
    if timePreMessage == 0:
        timePreMessage = sflTime
    else:
        timePreMessage = (timePreMessage+sflTime)/2


# 定义一个用来接收监听数据的方法
def on_message(ws, message):
    threading.Thread(target=temps_message, args=(ws, message)).start()


# 定义一个用来处理错误的方法
def on_error(ws, error):
    print("-----连接出现异常,异常信息如下-----")
    print(error)


# 定义一个用来处理关闭连接的方法
def on_close(ws, a, b):
    print("-------连接已关闭------")


def updatet(a):
    # print("s1")
    pass


def githubSub():
    # print("s2")
    url = "https://api.github.com/repos/UnlegitMC/FDPClient/actions/runs"
    newest = None
    try:
        a = requests.get(url=url).json()
        objectIDs = []
        for i in a["workflow_runs"]:
            if i["name"] == "build":
                objectIDs.append(i["id"])
        print(objectIDs)
        newest = objectIDs[0]
    except:
        print("github请求失败", url)
        print(traceback.format_exc())
    while True:
        try:
            a = requests.get(url=url).json()
            objectIDs = []
            for i in a["workflow_runs"]:
                if i["name"] == "build":
                    objectIDs.append(i["id"])
            if objectIDs[0] != newest:
                newest = objectIDs[0]
                actionInfo = requests.get(url="https://api.github.com/repos/UnlegitMC/FDPClient/actions/runs/{}".format(objectIDs[0])).json()
                updTime = actionInfo["head_commit"]["timestamp"]
                updMsg = actionInfo["head_commit"]["message"]
                updAuthor = "{} ({})".format(actionInfo["head_commit"]["author"]["name"], actionInfo["head_commit"]["author"]["email"])
                sendMessage("监听到 FDPClient 的 actions 有新的任务\nUpdate Time:{}\n"
                             "Update Message:{}\n"
                             "Author:{}\n"
                             "Download URL:https://nightly.link/UnlegitMC/FDPClient/actions/runs/{}/FDPClient.zip\n".format(updTime, updMsg, updAuthor, objectIDs[0]),
                             target_group = 628715712)
        except KeyboardInterrupt:
            quit()
        except:
            pass
        time.sleep(60)


def main():
    try:
        print("Starting... (0/5)")
        readConfig()
        print("Starting... (1/5)")
        # t2 = threading.Thread(target=githubSub)
        ws = websocket.WebSocketApp("ws://" + WSURL + "/all?verifyKey=uThZyFeQwJbD&qq=3026726134",
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close,
                                    )
        t3 = threading.Thread(target=ws.run_forever)
        # t2.daemon = True
        t3.daemon = True
        print("Starting... (2/5)")
        print("Starting... (3/5)")
        # t2.start()
        print("Starting... (4/5)")
        t3.start()
        print("Starting... (5/5)")
        print("Bot Ready!")
        while True:
            time.sleep(1)
        quit()
    except KeyboardInterrupt:
        quit()
    except Exception:
        print("遇到无法恢复的错误 即将退出")
        print(traceback.format_exc())
        quit()

main()
