# -*- coding: utf-8 -*-

from requests_oauthlib import OAuth1Session
import os
import sys
import urllib
import json
import datetime
import random
from pytz import timezone
from dateutil import parser
import hashlib
import base64
import requests
import re

## Twitter系の変数
# OAuth認証 セッションを開始
CK = os.getenv('Twitter_Consumer_Key')          # Consumer Key
CS = os.getenv('Twitter_Consumer_Secret_Key')   # Consumer Secret
AT = os.getenv('Twitter_Access_Token_Key')      # Access Token
AS = os.getenv('Twitter_Access_Token_Secret')   # Accesss Token Secert

twitter = OAuth1Session(CK, CS, AT, AS)
twitterListCount = 500              # 一度に取得するリストのアカウント数
twitterListName = 'tenhouginsama/nazo-news'

regionName = 'ap-northeast-1'               # 使用するリージョン名

## Hatena系の変数
hatenaUsername = 'lirlia'
hatenaPassword = os.environ.get('Hatena_Password')
hatenaBlogname = 'lirlia.hatenablog.com'
hatenaDraft = 'no'
hatenaBlogEntryId = '10328749687222146045'

## その他の変数
today = datetime.date.today()

#
# 特定の条件を満たすTweetを検索
# 引数：twitterのid(tenhouginsama)
# 戻り値: 条件を満たしたツイートの検索結果
# https://dev.twitter.com/rest/reference/get/search/tweets
#
def SearchTweet():

    url = "https://api.twitter.com/1.1/search/tweets.json"

    searchWord = \
        '-RT list:' + twitterListName +  ' ' + \
        'since:' + today.strftime("%Y-%m-%d") + ' ' \
        u'"当日券" OR "当日予約" -"全て完売" -"全ての回完売"'

    params = {'q': searchWord, 'count': 100 }
    req = twitter.get(url, params = params)

    # レスポンスを確認
    if req.status_code != 200:
        print ("Error: %d" % req.status_code)
        sys.exit()

    return json.loads(req.text)


#
# WSSE認証の取得
#
def Wsse():
    created = datetime.datetime.now().isoformat() + 'Z'
    nonce = hashlib.sha1(str(random.random())).digest()
    digest = hashlib.sha1(nonce + created + hatenaPassword).digest()

    return 'UsernameToken Username="{}", PasswordDigest="{}", Nonce="{}", Created="{}"'.format(hatenaUsername, base64.b64encode(digest), base64.b64encode(nonce), created)

#
# HatenaBlogへの記事の投稿
#
def PostHatena(nazoList):

    day1 = today.strftime("%Y/%m/%d")

    year = str(today.strftime("%Y"))

    title = u'今日行ける「リアル脱出ゲーム・謎解きイベント」の当日券情報（自動更新）'

    body = \
      u'[f:id:lirlia:20170228220149p:plain]\n' \
      u'====\n' \
      u'こんばんは、[https://twitter.com/intent/user?original_referer=http%3A%2F%2Flirlia.hatenablog.com%2F&amp;region=follow&amp;screen_name=tenhouginsama&amp;tw_p=followbutton&amp;variant=2.0:title=(@tenhouginsama)]です。  \n' \
      u'\n「' + day1 + u'」のリアル脱出ゲーム・リアル謎解き当日券情報です。\n' \
      u'いまから謎解きに行こう！(この記事は5分間隔で自動更新されます)\n' \
      u'\n' \
      u'同一公演の当日券情報が複数ある場合、ツイート情報は新しい順番から並んでいます。最新の当日券情報は一番上のツイートを参照してください。\n' \
      u'\n' \
      u'*目次\n' \
      u'[:contents]\n' \
      u'\n' \
      u'*当日券情報一覧\n\n'


    i_before = ""
    # 配列内の辞書要素（Twitter名）で並び替え
    import time
    sortNazoList = sorted(nazoList, key=lambda k: (k['userName'],int(k['tweetID'])),reverse=True)

    if len(sortNazoList) == 0:
        body = body + u'本日(' + day1 + u')の当日券の情報はありません。'

    for i in sortNazoList:
        if i_before != "":
            if i['userName'] == i_before['userName']:
                body = body + u'\n[https://twitter.com/' + i['twitterID'] + u'/status/' + str(i['tweetID']) + u':embed]  '
            else:
                body = body + u'\n**' + i['userName'].replace(u'&',u' ') + u'\n' + \
              u'[https://twitter.com/' + i['twitterID'] + u'/status/' + str(i['tweetID']) + u':embed]  '
        else:
            body = body + u'\n**' + i['userName'].replace(u'&',u' ') + u'\n' + \
          u'[https://twitter.com/' + i['twitterID'] + u'/status/' + str(i['tweetID']) + u':embed]  '


        body = body + u'\n\n'

        i_before = i

    body = body +  u'\n*集計条件\n' \
      u'- 本日(' + day1 + u')投稿されたツイートであること。\n' \
      u'- 集計対象Twitterアカウントに入っていること\n' \
      u'- Twitter検索にて「list:tenhouginsama/nazo-news "当日券" OR "当日予約" -"全て完売" -"全ての回完売" since:' + day1 + u' 」でツイートがヒットすること\n' \
      u'\n' \
      u'*集計対象Twitterアカウント\n' \
      u'下記のTwitterリストに入っているアカウントが集計対象となります。\n' \
      u'-https://twitter.com/tenhouginsama/lists/nazo-news/members\n' \
      u'\n' \
      u'<b>「このアカウントも収集対象に追加して欲しい」</b>というご要望があれば[https://twitter.com/intent/user?original_referer=http%3A%2F%2Flirlia.hatenablog.com%2F&amp;region=follow&amp;screen_name=tenhouginsama&amp;tw_p=followbutton&amp;variant=2.0:title=(@tenhouginsama)]までご連絡ください。' \
      u'\n' \
      u'*記事の修正について\n' \
      u'この記事は<b>自動投稿</b>されています。明らかに違うツイートが貼り付けられている場合はお手数ですが[https://twitter.com/intent/user?original_referer=http%3A%2F%2Flirlia.hatenablog.com%2F&amp;region=follow&amp;screen_name=tenhouginsama&amp;tw_p=followbutton&amp;variant=2.0:title=(@tenhouginsama)]までご連絡ください。\n' \
      u'\n'

    data = \
        u'<?xml version="1.0" encoding="utf-8"?>' \
        u'<entry xmlns="http://www.w3.org/2005/Atom"' \
        u'xmlns:app="http://www.w3.org/2007/app">' \
        u'<title>' + title + '</title>' \
        u'<author><name>name</name></author>' \
        u'<content type="text/plain">' + body + u'</content>' \
        u'<category term="当日券情報" />' \
        u'<app:control>' \
        u'<app:draft>' + hatenaDraft + '</app:draft>' \
        u'</app:control>' \
        u'</entry>'

    headers = {'X-WSSE': Wsse()}
    url = 'http://blog.hatena.ne.jp/{}/{}/atom/entry/{}'.format(hatenaUsername, hatenaBlogname, hatenaBlogEntryId)
    req = requests.put(url, data=data.encode('utf-8'), headers=headers)

    if req.status_code != 200:
        print ("Error: %d" % req.status_code)
        sys.exit()

def lambda_handler(event, context):

    nazoList = []

    # 対象のアカウントのツイートから条件を満たしているものを抽出
    for tweet in SearchTweet()['statuses']:

        # データの格納
        nazoList.append({
            'userName': tweet['user']['name'],
            'tweetID': tweet['id_str'],
            'twitterID': tweet['user']['screen_name']
        })


    # ブログへ記事を投稿
    PostHatena(nazoList)

    return { "messages":"success!" }
