import discord
import os
import aiohttp
from openai import OpenAI
from dotenv import load_dotenv
import datetime
import glob

# .envファイルから環境変数を読み込む
load_dotenv()

# --- 設定読み込み ---
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OBSIDIAN_VAULT_FOLDER_PATH = os.getenv("OBSIDIAN_VAULT_FOLDER_PATH")
# --------------------

# OpenAIクライアントの初期化
client_openai = OpenAI(api_key=OPENAI_API_KEY)

# Discord BotのIntents設定
intents = discord.Intents.default()
intents.message_content = True

client_discord = discord.Client(intents=intents)

@client_discord.event
async def on_ready():
    """Botがログインしたときに実行される処理"""
    print(f'{client_discord.user} としてログインしました。')
    print(f'Obsidianの保存先: {OBSIDIAN_VAULT_FOLDER_PATH}')
    print('---------------------------------')
    print('ボイスメモの投稿を待っています...')

@client_discord.event
async def on_message(message):
    """メッセージが投稿されたときに実行される処理"""
    # Bot自身のメッセージは無視する
    if message.author == client_discord.user:
        return

    # テキストメッセージに反応する機能を追加（デバッグ用）
    if message.content.lower() == "ping":
        await message.reply("pong! Botは正常に動作しています。")
        return
    
    # デバッグコマンド：既存ノート一覧表示
    if message.content.lower() == "debug":
        existing_notes = read_existing_notes()
        debug_info = f"📋 **既存ノート確認**\n\n**読み込み済みノート数**: {len(existing_notes)}\n\n"
        debug_info += "**ファイル一覧**:\n"
        for filename in list(existing_notes.keys())[:10]:  # 最初の10件のみ表示
            debug_info += f"- {filename}\n"
        if len(existing_notes) > 10:
            debug_info += f"... および他 {len(existing_notes) - 10} 件"
        await message.reply(debug_info)
        return

    # デバッグ情報を出力
    print(f"メッセージを受信: {message.content}")
    print(f"添付ファイル数: {len(message.attachments)}")
    
    if message.attachments:
        for i, attachment in enumerate(message.attachments):
            print(f"添付ファイル{i}: {attachment.filename}, タイプ: {attachment.content_type}")
    
    # テキストメッセージの処理（音声メッセージ以外）
    if message.content and not message.attachments and message.content.lower() != "ping":
        try:
            await message.reply("📝 テキストメモを処理中です...")
            
            # テキストをそのまま使用
            raw_text = message.content

            # ChatGPTで要約・整形
            summarized_text = await summarize_with_chatgpt(raw_text)

            # 既存ノートを読み込み
            existing_notes = read_existing_notes()
            
            # 関連性分析
            related_notes = await find_related_notes(raw_text, existing_notes)

            # Obsidianに保存（関連ノートも含める）
            saved_filename = save_to_obsidian(raw_text, summarized_text, related_notes)

            # 結果をDiscordに返信
            reply_text = f"✅ テキスト要約・関連性分析が完了し、Obsidianに保存しました。\nファイル名: {saved_filename}\n\n"
            
            if related_notes:
                reply_text += f"🔗 **関連ノート発見**: {', '.join(related_notes)}\n\n"
            
            reply_text += f"**元のテキスト:**\n```\n{raw_text}\n```\n\n**AIによる要約・整形:**\n```\n{summarized_text}\n```"
            
            await message.reply(reply_text)
            
        except Exception as e:
            print(f"テキスト処理でエラーが発生しました: {e}")
            await message.reply(f"❌ テキスト処理中にエラーが発生しました: {e}")
        
        return
    
    # 添付ファイルがあり、それがボイスメッセージの場合のみ処理
    if message.attachments and message.attachments[0].content_type and message.attachments[0].content_type.startswith('audio/'):
        attachment = message.attachments[0]

        try:
            # ユーザーに処理中であることを通知
            await message.reply("🎙️ ボイスメモを認識中です...")

            # 音声ファイルをダウンロード
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status == 200:
                        audio_data = await resp.read()

                        # OpenAI Whisper APIで文字起こし
                        transcription = client_openai.audio.transcriptions.create(
                            model="whisper-1",
                            file=("voice_memo.ogg", audio_data, "audio/ogg")
                        )
                        raw_text = transcription.text

                        # ChatGPTで要約・整形
                        summarized_text = await summarize_with_chatgpt(raw_text)

                        # 既存ノートを読み込み
                        existing_notes = read_existing_notes()
                        
                        # 関連性分析
                        related_notes = await find_related_notes(raw_text, existing_notes)

                        # Obsidianに保存（関連ノートも含める）
                        saved_filename = save_to_obsidian(raw_text, summarized_text, related_notes)

                        # 結果をDiscordに返信
                        reply_text = f"✅ 文字起こし・要約・関連性分析が完了し、Obsidianに保存しました。\nファイル名: {saved_filename}\n\n"
                        
                        if related_notes:
                            reply_text += f"🔗 **関連ノート発見**: {', '.join(related_notes)}\n\n"
                        
                        reply_text += f"**元の文字起こし:**\n```\n{raw_text}\n```\n\n**AIによる要約・整形:**\n```\n{summarized_text}\n```"
                        
                        await message.reply(reply_text)
                    else:
                        await message.reply("❌ 音声ファイルのダウンロードに失敗しました。")

        except Exception as e:
            print(f"エラーが発生しました: {e}")
            await message.reply(f"❌ 処理中にエラーが発生しました: {e}")

async def summarize_with_chatgpt(text):
    """ChatGPT APIを使ってテキストを要約・整形する関数"""
    try:
        response = client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": """あなたは音声メモの要約・整形を行うアシスタントです。
                    以下のルールで音声メモを処理してください：
                    
                    1. 内容を3-5行程度で要約
                    2. 重要なキーワードを箇条書きで抽出
                    3. 関連する行動項目があれば「TODO」として記載
                    4. Markdown形式で整理
                    
                    音声メモが短い場合は、そのまま整理された形で出力してください。"""
                },
                {
                    "role": "user", 
                    "content": f"以下の音声メモを要約・整形してください：\n\n{text}"
                }
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"ChatGPT要約でエラーが発生しました: {e}")
        return f"要約処理中にエラーが発生しました。元のテキスト：\n{text}"

def read_existing_notes():
    """obsidianフォルダ内の既存ノートを読み込む関数"""
    try:
        notes = {}
        md_files = glob.glob(os.path.join(OBSIDIAN_VAULT_FOLDER_PATH, "*.md"))
        
        for file_path in md_files:
            filename = os.path.basename(file_path)
            filename_without_ext = filename.replace('.md', '')
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # ファイル名と内容の最初の500文字を保存
                    notes[filename_without_ext] = content[:500]
            except Exception as e:
                print(f"ファイル読み込みエラー {filename}: {e}")
                continue
                
        print(f"既存ノート {len(notes)} 件を読み込みました")
        return notes
        
    except Exception as e:
        print(f"既存ノート読み込みでエラー: {e}")
        return {}

async def find_related_notes(new_content, existing_notes):
    """新しいメモと既存ノートの関連性を分析する関数"""
    if not existing_notes:
        return []
    
    try:
        # 既存ノートのリストを作成
        notes_summary = "\n".join([f"- {filename}: {content[:100]}..." for filename, content in existing_notes.items()])
        
        response = client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """あなたは音声メモの関連性分析を行うアシスタントです。
                    新しいメモの内容と既存ノートを比較し、内容的に関連があるものを特定してください。
                    
                    関連性の基準：
                    - 同じトピック、テーマ
                    - 関連する技術、概念
                    - 続きや発展的な内容
                    - 類似の課題や解決策
                    
                    応答形式：
                    関連するファイル名のみをカンマ区切りで返してください（拡張子なし）。
                    関連がない場合は「なし」と返してください。"""
                },
                {
                    "role": "user",
                    "content": f"""新しいメモ内容：
{new_content}

既存ノート一覧：
{notes_summary}

関連するノートのファイル名を教えてください。"""
                }
            ],
            max_tokens=200,
            temperature=0.3
        )
        
        result = response.choices[0].message.content.strip()
        
        if result.lower() == "なし" or not result:
            return []
            
        # カンマ区切りでファイル名を分割
        related_files = [name.strip() for name in result.split(',') if name.strip()]
        
        # 実際に存在するファイルのみを返す
        valid_files = [name for name in related_files if name in existing_notes]
        
        print(f"関連ノート発見: {valid_files}")
        return valid_files
        
    except Exception as e:
        print(f"関連性分析でエラー: {e}")
        return []

def save_to_obsidian(raw_text, summarized_text=None, related_notes=None):
    """指定されたフォルダに、現在日時のファイル名でテキストを保存する関数"""
    try:
        # 現在の日時を取得
        now = datetime.datetime.now()
        
        # YYYYMMDD_HHMMSS 形式のファイル名を作成
        file_name = now.strftime("%Y%m%d_%H%M%S") + ".md"
        
        # 保存するファイルのフルパスを生成
        full_path = os.path.join(OBSIDIAN_VAULT_FOLDER_PATH, file_name)
        
        # 書き込む内容をフォーマット
        content_to_save = f"# 音声メモ {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if summarized_text:
            content_to_save += f"## AI要約・整形\n\n{summarized_text}\n\n"
        
        # 関連ノートのリンクを追加
        if related_notes:
            content_to_save += f"## 関連ノート\n\n"
            for note in related_notes:
                content_to_save += f"- [[{note}]]\n"
            content_to_save += "\n"
        
        content_to_save += f"## 元の文字起こし\n\n{raw_text}\n"
        
        # 新しいファイルに書き込みモードで保存
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content_to_save)
        print(f"Obsidianにノートを保存しました: {file_name}")
        
        if related_notes:
            print(f"関連ノートリンク追加: {related_notes}")
        
        return file_name
        
    except Exception as e:
        print(f"ファイルへの書き込み中にエラーが発生しました: {e}")
        return None

# Botを起動
client_discord.run(DISCORD_BOT_TOKEN)