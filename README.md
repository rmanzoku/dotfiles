# dotfiles

[chezmoi](https://www.chezmoi.io/) で管理する dotfiles。

配布 skill の復元一覧は [docs/skills-install-manifest.md](docs/skills-install-manifest.md) を正本にします。

## セットアップ (新しいマシン)

git も Homebrew も入っていない完全に新しい Mac では、Terminal で以下を実行します。
Homebrew の installer が必要に応じて Command Line Tools を要求します。

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" && \
if [ -x /opt/homebrew/bin/brew ]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
elif [ -x /usr/local/bin/brew ]; then
  eval "$(/usr/local/bin/brew shellenv)"
else
  echo "Homebrew が見つかりません" >&2
  exit 1
fi && \
brew install git chezmoi && \
mkdir -p "$HOME/.local/share" && \
git clone https://github.com/rmanzoku/dotfiles.git "$HOME/.local/share/chezmoi" && \
chezmoi apply && \
brew bundle --file="$HOME/.local/share/chezmoi/Brewfile" && \
"$HOME/.local/share/chezmoi/scripts/bootstrap-workspace"
```

既に Homebrew が入っている場合は、以下だけで復元できます。

```bash
# git と chezmoi をインストール
brew install git chezmoi

# dotfiles repo を chezmoi の標準 source path に clone
mkdir -p "$HOME/.local/share"
git clone https://github.com/rmanzoku/dotfiles.git "$HOME/.local/share/chezmoi"

# dotfiles を適用
chezmoi apply

# 必要なら 1Password secret reference を設定
mkdir -p ~/.config/op
cp ~/.config/op/dotfiles.env.example ~/.config/op/dotfiles.env
chmod 600 ~/.config/op/dotfiles.env
$EDITOR ~/.config/op/dotfiles.env

# Homebrew パッケージを復元
brew bundle --file="$HOME/.local/share/chezmoi/Brewfile"

# 1Password にサインイン後、secret-backed file を復元
opmaterialize restore

# project に依存しない workspace repo を clone / pull
"$HOME/.local/share/chezmoi/scripts/bootstrap-workspace"
```

配布 skill と third-party external skill の復元は script を持たず、[docs/skills-install-manifest.md](docs/skills-install-manifest.md) に記録した `gh skill install` 一覧を使います。

### サブエージェントの復元

`personal` や `tech` などのサブエージェントは skill ではなく、Claude Code / Codex の private agent 定義として管理します。
定義ファイルや private secretary の facts / assets は git に入れず、1Password の `Secrets Manifest` から `opmaterialize restore` で復元します。

新しいマシンでは 1Password にサインインして `opmaterialize restore` を実行した後、サブエージェント関連 target を再 apply します。

```bash
opmaterialize restore

chezmoi apply --parent-dirs \
  ~/.claude/agents \
  ~/.codex/agents \
  ~/.config/private-secretary
```

復元確認:

```bash
test -r ~/.claude/agents/personal.md
test -r ~/.claude/agents/biz.md
test -r ~/.claude/agents/tech.md
test -r ~/.codex/agents/personal.toml
test -r ~/.codex/agents/biz.toml
test -r ~/.codex/agents/tech.toml
test -r ~/.config/private-secretary/facts.jsonl
```

更新手順と source / target 対応は [docs/adr/0039-restore-private-agent-definitions-from-1password.md](docs/adr/0039-restore-private-agent-definitions-from-1password.md) を参照してください。

`scripts/bootstrap-workspace` は `ghq` が利用できる場合は `ghq root` 配下に
`rmanzoku/workspace` を clone / fast-forward pull します。
`ghq` がない場合は `~/workspace/github.com/rmanzoku/workspace` を fallback とします。
古い Conductor 配下の clone は移行期間の互換として残し、新規 bootstrap の標準にはしません。

## 日常の操作

```bash
# dotfile の変更を chezmoi に反映
chezmoi add ~/.zshrc

# 差分を確認
chezmoi diff

# 変更をコミット
chezmoi cd
git add -A && git commit -m "update dotfiles"
git push
```

### chezmoi 管理外の変更を検出 (`chezmoi-drift`)

ツールやアプリが dotfile を直接変更した場合のケア:

```bash
# source と .chezmoiignore の不整合を確認
scripts/chezmoi-drift --check-ignore

# 差分のあるファイルを確認
scripts/chezmoi-drift

# 外部の変更を chezmoi ソースに取り込む
scripts/chezmoi-drift --apply

# chezmoi ソースの状態に戻す
scripts/chezmoi-drift --restore
```

### Worktree での AI 編集

Conductor などのツールが git worktree を立ち上げて dotfiles を編集する際、`setup.sh` が自動実行されます。このスクリプトは chezmoi ソースとの差分を検出し、編集前にドリフトがあれば警告します。

## 主なファイル

### chezmoi で配備するファイル

| 実ファイル | 用途 |
|---------|------|
| `.zshrc` | Zsh 設定 |
| `.zshenv` | Zsh の local override と 1Password env file path 設定 |
| `.zprofile` | Zsh ログイン時初期化 (Homebrew, `rbenv`) |
| `.profile` | 汎用プロファイル |
| `.gitconfig` | Git 設定 |
| `.config/git/ignore` | グローバル gitignore |
| `.config/op/dotfiles.env.example` | 1Password secret reference 用 dotenv 例 |
| `.local/bin/env` | PATH 設定スクリプト |
| `.local/bin/oprun` | `op run --env-file` 用ラッパー |
| `.local/bin/opmaterialize` | `onepassword-secret-materialize` skill 同梱 script を呼び出すラッパー |
| `.local/bin/gws-account` | Google Workspace CLI の account profile 選択ラッパー |
| `.local/bin/freee-mcp-account` | freee MCP の account profile 選択ラッパー |
| `.claude/CLAUDE.md` | Claude Code グローバル設定 |
| `.claude/settings.json` | Claude Code 設定 |
| `.codex/AGENTS.md` | Codex エージェント設定 |
| `.codex/config.toml` | Codex モデル・プロジェクト設定 |
| `.qwen/QWEN.md` | Qwen ユーザー設定 |
| `.qwen/settings.json` | Qwen モデルプロバイダー設定 |

### repo ローカルで管理するファイル

| パス | 用途 |
|---------|------|
| `Brewfile` | Homebrew パッケージ復元 manifest |
| `./.claude/skills/` | このリポジトリ専用の Claude Code スキル |
| `skills/` | `gh skill --from-local` で配布する publisher 形式の first-party skill |
| `docs/` | 運用ルール、ADR、補助ドキュメント |
| `scripts/` | repo 運用スクリプト |

### chezmoi ソースとの主な対応

| 実ファイル | chezmoi ソース |
|-----------|----------------|
| `.claude/CLAUDE.md` | `dot_claude/CLAUDE.md` |
| `.claude/settings.json` | `dot_claude/settings.json` |
| `.codex/AGENTS.md` | `dot_codex/AGENTS.md` |
| `.codex/config.toml` | `dot_codex/private_config.toml.tmpl` |
| `.config/op/dotfiles.env.example` | `dot_config/private_op/dotfiles.env.example` |
| `.local/bin/oprun` | `dot_local/bin/executable_oprun` |
| `.local/bin/opmaterialize` | `dot_local/bin/executable_opmaterialize` |
| `.local/bin/gws-account` | `dot_local/bin/executable_gws-account` |
| `.local/bin/freee-mcp-account` | `dot_local/bin/executable_freee-mcp-account` |
| `.qwen/QWEN.md` | `dot_qwen/QWEN.md` |
| `.qwen/settings.json` | `dot_qwen/settings.json` |

`dot_` はドットファイル化です。`private_` はファイル名変換ではなく、target の group / world 権限を外す属性です。
`./.claude/skills/` は repo ローカル運用とし、chezmoi ではホームディレクトリへ配備しません。配布する first-party skill は `skills/` を正本とし、`gh skill install --from-local` で `~/.claude/skills/` や `~/.codex/skills/` へ入れます。
詳細は [chezmoi-knowledge/SKILL.md](.claude/skills/chezmoi-knowledge/SKILL.md) と [semantics.md](.claude/skills/chezmoi-knowledge/references/semantics.md) を参照してください。

## シークレット管理

API キーなどのシークレット実値は 1Password に保存し、CLI では `op://...` secret reference 経由で受け渡します。
`~/.config/op/dotfiles.env` は `op run --env-file` 用の管理外 dotenv とし、実値ではなく secret reference だけを書きます。

```bash
mkdir -p ~/.config/op
cp ~/.config/op/dotfiles.env.example ~/.config/op/dotfiles.env
chmod 600 ~/.config/op/dotfiles.env
$EDITOR ~/.config/op/dotfiles.env

# 例: GEMINI_API_KEY を必要とするコマンドを 1Password 経由で実行
oprun gemini --help

# 直接読む必要がある単発処理
op read 'op://<vault>/<item>/<field>'
```

`oprun` は `$OP_DOTFILES_ENV_FILE` があればそのファイルを、なければ `~/.config/op/dotfiles.env` を使って `op run --env-file` を実行します。
`OP_ACCOUNT` は既定で `my.1password.com` を使います。
`opmaterialize` は `$OP_DOTFILES_MATERIALIZE_VAULT` があればその Vault を、なければ `Dotfiles Secrets` を使います。
`~/.local/bin/opmaterialize` はグローバルにインストールされた `onepassword-secret-materialize` skill の `scripts/opmaterialize` を呼び出す薄いラッパーです。
`~/.zshenv.local` は secret の置き場ではなく、マシン固有の非 secret local override に限定します。

### Secret-backed file の配置

VPN 設定のようにファイルとして必要な secret は、repo に実値や個別 item 名を置かず、1Password の Document アイテム `Secrets Manifest` に生成ルールを保存します。
新しいマシンでは 1Password にサインインした後に以下を実行します。

```bash
opmaterialize diff
opmaterialize restore
```

`Secrets Manifest` は tab-separated 形式で、列は `type`、`item`、`out_path`、`mode`、`vault` です。
`vault` は任意で、不要な場合は `-` にします。
`opmaterialize` は実行時だけ manifest を取得し、処理後にローカルコピーを削除します。

```tsv
# type	item	out_path	mode	vault
document	<VPN Document Item>	$HOME/.config/wireguard/<vpn-name>.conf	0600	-
```

既存ファイルと内容が同じなら何もしません。
`opmaterialize diff` は secret の内容を表示せず、`missing`、`changed`、`unchanged` だけを表示します。
差分がある場合は終了ステータス `1` になります。
内容が変わっている場合は誤上書きを避けて停止するため、置き換える場合だけ明示的に実行します。

```bash
opmaterialize restore --force
```

ローカルにある secret-backed file を 1Password の指定 Vault に保存し、`Secrets Manifest` に登録する場合は `add` を使います。
`--out-path` を省略すると現在の絶対パスを `$HOME/...` 形式に正規化して登録します。
`--item` を省略すると `dotfiles:<out-path>` が 1Password Document の item 名になります。

```bash
opmaterialize add "$HOME/.config/wireguard/example.conf"

# dotenv 形式の secret reference ファイルも同じ仕組みで復元対象にできる
opmaterialize add "$HOME/.config/op/dotfiles.env"
```

### Google / Freee のマルチアカウント OAuth

Google Workspace CLI は `gws-account <profile> ...` で account profile を選びます。
profile 名、実アカウント対応、`.env` への cache 方針は、Personal 側または各作業リポジトリが決めます。
各 profile は `GOOGLE_WORKSPACE_CLI_CONFIG_DIR=~/.config/gws/accounts/<profile>` を使い、default の `~/.config/gws` には依存しません。
呼び出し元が credential file を明示したい場合は、`GWS_ACCOUNT_CREDENTIALS_FILE` を渡します。

```bash
gws-account <profile> auth status
gws-account <profile> auth login
gws-account <profile> drive files list --params '{"pageSize": 5}'
```

`GOOGLE_WORKSPACE_CLI_TOKEN` と `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` は profile 指定より優先されるため、`gws-account` はそれらが設定されている場合に停止します。
認証失敗時に別アカウントへ切り替える fallback は行いません。

Freee MCP は `freee-mcp-account <profile> <command>` で account profile を選びます。
各 profile は `XDG_CONFIG_HOME=~/.config/freee-mcp/accounts/<profile>/xdg` を使い、`config.json`、`tokens.json`、`sign-config.json`、`sign-tokens.json` を profile ごとに分離します。
呼び出し元が config root を明示したい場合は、`FREEE_MCP_ACCOUNT_XDG_CONFIG_HOME` を渡します。

```bash
freee-mcp-account <profile> configure
freee-mcp-account <profile> server
```

OAuth / token / client secret の実体は git では管理せず、必要な profile ファイルを `opmaterialize add` で 1Password の `Secrets Manifest` に登録します。
`gws` の `credentials.enc` は同一マシン内の暗号化保存として扱い、別マシン復元用には `credentials.json` または `client_secret.json` を登録します。
token 更新、再ログイン、1Password への書き戻しはツールごとの credential lifecycle として扱い、各ツール用の runner / adapter 側で決めます。

```bash
opmaterialize add "$HOME/.config/gws/accounts/<profile>/client_secret.json"
opmaterialize add "$HOME/.config/gws/accounts/<profile>/credentials.json"
opmaterialize add "$HOME/.config/freee-mcp/accounts/<profile>/xdg/freee-mcp/config.json"
opmaterialize add "$HOME/.config/freee-mcp/accounts/<profile>/xdg/freee-mcp/tokens.json"
```

Freee の作成・更新・削除・送信・承認、Google の送信・共有・権限変更では fallback を禁止します。
読み取り診断であっても、別 principal / 別 company / 別 profile への自動切替は行わず、必要なら profile を明示して再実行します。
