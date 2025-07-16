# Discord Bot - Audio Transcription & Obsidian Integration

けいすけさんのDiscord音声メモシステムを参考に開発したBot。音声メモとテキストメッセージを自動で文字起こし・要約・関連性分析し、Obsidianに保存する。

## 機能

### ✅ 実装済み機能

1. **Discord音声メモ → Whisper文字起こし**
   - スマホのDiscordから音声投稿
   - OpenAI Whisper APIで高精度文字起こし

2. **ChatGPT要約・整形**
   - 音声内容の自動要約（3-5行）
   - 重要キーワードの箇条書き抽出
   - TODO項目の自動生成
   - Markdown形式での整理

3. **既存メモとの関連性分析**
   - obsidianフォルダ内の全ファイルをスキャン
   - ChatGPTによる関連性分析
   - 自動[[リンク]]作成

4. **Obsidian自動保存**
   - YYYYMMDD_HHMMSS形式のファイル名
   - 専用obsidianフォルダに保存
   - リアルタイム同期

5. **テキストメッセージ対応**
   - 音声と同じ処理フロー
   - テキスト入力でも完全対応

### 📂 ファイル構成

```
discord-bot/
├── bot.py          # メインプログラム
├── .env           # APIキー設定（秘匿）
└── README.md      # このファイル

obsidian/          # 自動生成されるメモ
├── 20250716_134839.md
├── 20250716_135750.md
└── ...
```

### 🔧 セットアップ

1. **必要な環境**
   - Python 3.13+
   - Discord Bot Token
   - OpenAI API Key

2. **ライブラリインストール**
   ```bash
   pip3 install discord.py openai python-dotenv
   ```

3. **環境変数設定**
   ```bash
   # .envファイルに記述
   DISCORD_BOT_TOKEN="your_discord_bot_token"
   OPENAI_API_KEY="your_openai_api_key"
   OBSIDIAN_VAULT_FOLDER_PATH="/path/to/obsidian/folder"
   ```

4. **Bot実行**
   ```bash
   cd discord-bot
   python3 bot.py
   ```

### 📋 使用方法

1. **音声メモ**: Discordでマイクボタン長押し → 音声録音 → 送信
2. **テキストメモ**: Discordで普通にテキスト入力 → 送信
3. **デバッグ**: `debug`コマンドで既存ノート確認
4. **接続確認**: `ping`コマンドでBot動作確認

### 📄 生成ファイル例

```markdown
# 音声メモ 2025-07-16 13:57:50

## AI要約・整形
[ChatGPTによる要約・キーワード・TODO]

## 関連ノート
- [[20250716_134839]]
- [[20250716_135750]]

## 元の文字起こし
[元の音声/テキスト内容]
```

### 🚀 今後の拡張予定

- SNS投稿用形式変換機能
- Discord UIボタン + Twitter API連携
- より高度な関連性分析

---

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>