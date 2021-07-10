![snipe](https://user-images.githubusercontent.com/36104864/115669007-c3bdbd80-a382-11eb-908e-ec4a9e7d9aba.png)

[![GitHub license](https://img.shields.io/github/license/88IO/snipe)](https://github.com/88IO/snipe/blob/master/LICENSE)

# 🔫 discordbot-snipe

予め設定した時刻に通話を強制切断するDiscord Botです。

ボイスチャットで話が弾んで離席しずらい状況になったことはあります。本プロダクトは指定時刻に電話が鳴るアプリで会食から退出しやすくするアイデアを基にし、VC版としての利用を想定しています。

## デモ

![Peek](https://user-images.githubusercontent.com/36104864/125148662-edf76e00-e16e-11eb-8fb6-1022e7a2ed4c.gif)

## 機能

- 時分単位で通話切断予約
  - 指定時刻にVCから切断
  - 指定時間後にVCから切断
- 通話切断３分前、切断時にDMで通知
- 自分の予約を全削除
- BotのVC参加
  - ~~切断３分前に機械音声で通知~~

## 要件

* [Python >= 3.9](https://www.python.org/)
  * Python 3.8以降でも動作可
    * pip等で`discord.py[voice]`, `python-dotenv`をインストールする必要あり
* [Poetry](https://github.com/python-poetry/poetry)

```bash
pip install poetry
```

- [FFmpeg](https://www.ffmpeg.org/)

## セットアップ

#### 1. Discord Botを作成 & サーバーに招待

**インテント（Botタブ）：**

![](https://user-images.githubusercontent.com/36104864/125148766-87bf1b00-e16f-11eb-9806-e6f84d2b0733.png)

**スコープ（OAuth2タブ）：**

![](https://user-images.githubusercontent.com/36104864/125148742-5e05f400-e16f-11eb-8593-e2ab853a000d.png)

**権限（OAuth2タブ）：**

![](https://user-images.githubusercontent.com/36104864/116031938-b746a700-a699-11eb-90b3-4586bc77e2fe.png)

詳細は [こちら](https://discordpy.readthedocs.io/ja/latest/discord.html#:~:text=Make%20sure%20you're%20logged%20on%20to%20the%20Discord%20website.&text=%E3%80%8CNew%20Application%E3%80%8D%E3%83%9C%E3%82%BF%E3%83%B3%E3%82%92%E3%82%AF%E3%83%AA%E3%83%83%E3%82%AF,%E3%83%A6%E3%83%BC%E3%82%B6%E3%83%BC%E3%82%92%E4%BD%9C%E6%88%90%E3%81%97%E3%81%BE%E3%81%99%E3%80%82)

**メモ: Bot TOKEN**

#### 2. `.env` ファイルを作成、トークンを入力

プロジェクトフォルダ下で`.env`ファイルを以下のように作成し、Discord Botのトークンを入力

```bash
# Example
TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### 3. Pythonモジュールの導入

プロジェクトフォルダ下で

```bash
poetry install
```

#### 5. Botを起動

プロジェクトフォルダ下で

```
poetry run bot
```

Botがオンライン状態になっていることを確認

## 使い方（コマンド）

Botを`snipebot`として進める。（`@snipebot`はメンション）

#### ■ 通話切断予約

**指定時刻に切断予約**（コマンド末尾のメンションで複数ユーザ指定）

```bash
@snipebot reserve XX:XX
```

**指定時間後に切断予約**（コマンド末尾のメンションで複数ユーザ指定）

```
@snipebot reservein XX:XX
```

**短縮形式**

```
@snipebot XX:XX
```

1. Botが上記メッセージに「⏰時刻」と 「⏲️時間後」のボタン付きのメッセージを返信
2. 1分以内にいずれかのボタンを選択
   - 「⏰時刻」の場合、指定時刻に予約
   -  「⏲️時間後」の場合、指定時間後に予約

**スラッシュコマンド**（v0.4.0~）

```
/reserve XX:XX
```

```
/reservein XX:XX
```

#### ※ 時間指定の例

```
21:30
21時30分
21 30
45分
45m
45min
23時
23H
23hour
3時間5分
5
```

#### ■ 予約管理

**予約を表示**

```
@snipebot show
```

```
/schedule
```

**自分の予約を全キャンセル**（コマンド末尾のメンションで複数ユーザ指定）

```
@snipebot clear
```

```
/cancel
```

~~**同一時刻の予約を統合**（ベータ）~~

※ `@snipebot show`コマンドに統合

#### ■ 音声関連

**BotをVCに参加**（ベータ）

```
@snipebot connect
```

**BotをVCから退出**（ベータ）

```
@snipebot disconnect
```

## ノート

- [ ] イベントループの改良
- [x] 複数サーバー招待への対応
- [ ] タイムゾーンの複数対応
- [ ] 音声周りの見直し
- [x] 予約統合方法の見直し
- [x] スラッシュコマンド対応
- [x] ボタン対応

## ライセンス

"snipe" is under [MIT license](https://en.wikipedia.org/wiki/MIT_License).
