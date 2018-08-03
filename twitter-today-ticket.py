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
from xml.sax.saxutils import *

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


#
# 特定の条件を満たすTweetを検索
# 引数：twitterのid(tenhouginsama)
# 戻り値: 条件を満たしたツイートの検索結果
# https://dev.twitter.com/rest/reference/get/search/tweets
#
def SearchTweet(today):

    url = "https://api.twitter.com/1.1/search/tweets.json"

    searchWord = \
        '-RT list:' + twitterListName +  ' ' + \
        'since:' + today.strftime("%Y-%m-%d") + '_00:00:00_JST ' \
        u'"当日券" OR "当日予約" -"全て完売" -"全ての回完売" -tenhouginsama'

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
def PostHatena(nazoList, today):

    day1 = today.strftime("%Y/%m/%d")

    year = str(today.strftime("%Y"))

    title = u'今日行ける「リアル脱出ゲーム・謎解きイベント」の当日券情報（自動更新）'

    body = \
        u'<p><img class="hatena-fotolife" title="画像" src="https://cdn-ak.f.st-hatena.com/images/fotolife/l/lirlia/20170228/20170228220149.png" alt="f:id:lirlia:20161124194747j:plain" /></p>' \
        u'<p><!-- more --></p>' \
        u'<p> 最終更新日時: <strong>' + str(today.strftime("%Y/%m/%d %H:%M:%S")) + '</strong></p>'  \
        u'<p></p>' \
        u'<p></p>' \
        u'<p>こんにちは、<span id="myicon"> </span><a href="https://twitter.com/intent/user?original_referer=https://www.nazomap.com/&amp;region=follow&amp;screen_name=tenhouginsama&amp;tw_p=followbutton&amp;variant=2.0">ぎん</a>です。 <br /><br />' \
        u'<p> </p>' \
        u'<p>この記事ではTwitterで公開されている今遊べるリアル脱出ゲーム・リアル謎解きの<strong>「当日券情報」</strong>を紹介します。10分間隔で更新されますので、空いている公演をみつけていまから謎解きに行きましょう！</p>' \
        u'<p> </p>' \
        u'<ul><li>当日券情報が複数ある場合は一番上のツイートが最新です</li></ul>' \
        u'<p> </p>' \
        u'<p>[:contents]</p>' \
        u'<p> </p>' \
        u'<h3>当日券情報一覧</h3>' \

    i_before = ""
    # 配列内の辞書要素（Twitter名）で並び替え
    import time
    sortNazoList = sorted(nazoList, key=lambda k: (k['userName'],int(k['tweetID'])),reverse=True)

    if len(sortNazoList) == 0:
        body = body + u'<p>本日の当日券の情報はありません。</p>'

    for i in sortNazoList:
        if i_before != "":
            if i['userName'] == i_before['userName']:
                body = body + u'<p>[https://twitter.com/' + i['twitterID'] + u'/status/' + str(i['tweetID']) + u':embed]</p>'
            else:
                body = body + u'<h4>' + i['userName'].replace(u'&',u' ') + u'</h4>' + \
              u'<p>[https://twitter.com/' + i['twitterID'] + u'/status/' + str(i['tweetID']) + u':embed]</p>'
        else:
            body = body + u'<h4>' + i['userName'].replace(u'&',u' ') + u'</h4>' + \
          u'<p>[https://twitter.com/' + i['twitterID'] + u'/status/' + str(i['tweetID']) + u':embed]</p>'

        i_before = i

    day1 = today.strftime("%Y-%m-%d")
    body = body + u'<h3>この記事について</h3>' \
        u'<h4>集計の条件</h4>' \
        u'<ul>' \
        u'<li>本日(' + day1 + u')投稿されたツイートであること</li>' \
        u'<li>集計対象Twitterアカウントに入っていること</li>' \
        u'<li>Twitter検索にて「list:tenhouginsama/nazo-news "当日券" OR "当日予約" -"全て完売" -"全ての回完売" since:' + day1 + u'_00:00:00_JST 」でツイートがヒットすること</li>' \
        u'</ul><p></p>' \
        u'<h4>集計対象のTwitterアカウント</h4>' \
        u'<p>下記のTwitterリストに入っているアカウントが集計対象となります。</p>' \
        u'<ul><li>https://twitter.com/tenhouginsama/lists/nazo-news/members</ul></li>' \
        u'<p>「このアカウントも収集対象に追加して欲しい」というご要望があれば[https://twitter.com/intent/user?original_referer=http%3A%2F%2Flirlia.hatenablog.com%2F&amp;region=follow&amp;screen_name=tenhouginsama&amp;tw_p=followbutton&amp;variant=2.0:title=(@tenhouginsama)]までご連絡ください。</p>' \
        u'<h4>記事の修正について</h4>' \
        u'<p>この記事は<strong>自動投稿</strong>されています。明らかに違うツイートが貼り付けられている場合はお手数ですが[https://twitter.com/intent/user?original_referer=http%3A%2F%2Flirlia.hatenablog.com%2F&amp;region=follow&amp;screen_name=tenhouginsama&amp;tw_p=followbutton&amp;variant=2.0:title=(@tenhouginsama)]までご連絡ください。</p>'
    body = escape(body)
    data = \
        u'<?xml version="1.0" encoding="utf-8"?>' \
        u'<entry xmlns="http://www.w3.org/2005/Atom"' \
        u'xmlns:app="http://www.w3.org/2007/app">' \
        u'<title>' + title + u'</title>' \
        u'<author><name>ぎん</name></author>' \
        u'<updated>2017-03-01T00:00:00</updated>' \
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

    ## その他の変数
    # AWS Lamdaで稼働させる場合UTCのため、JSTに変換するために0900を足す
    # たさない場合日がずれてしまい、意図通りに集計できない

    # lambda_handlerの中じゃないと時刻が再取得されない場合があるので移動
    # http://qiita.com/yutaro1985/items/a24b572624281ebaa0dd
    today = datetime.datetime.today() + datetime.timedelta(hours=9)

    nazoList = []

    # 対象のアカウントのツイートから条件を満たしているものを抽出
    for tweet in SearchTweet(today)['statuses']:

        # データの格納
        nazoList.append({
            'userName': tweet['user']['name'],
            'tweetID': tweet['id_str'],
            'twitterID': tweet['user']['screen_name']
        })


    # ブログへ記事を投稿
    PostHatena(nazoList, today)

    return { "date": today.strftime("%Y/%m/%d %H:%M:%S") }
