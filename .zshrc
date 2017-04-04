#####################
# Prompt
#####################
PS1="%F{green}${USER}@${HOST%%.*}%f %1~ %(!.#.$) "

# iTerm TAB name
echo -ne "\033]0;${HOST}\007"

#####################
# Completions
#####################
fpath=(${HOME}/src/github.com/zsh-users/zsh-completions/src $fpath)
fpath=(${HOME}/usr/local/zsh $fpath)
fpath=(${HOME}/.zsh.d/completion $fpath)

function fpath-search() { for f in $fpath; do ls -d $f/* 2>>/dev/null | grep $1 ; done}

autoload -U compinit
compinit -u

#####################
# direnv
#####################
eval "$(direnv hook zsh)"

#####################
# Includes
#####################
if [ -d /etc/profile.d/ ]; then
    for i in /etc/profile.d/*.sh ; do
	[ -r $i ] && source $i
    done
fi

if [ -f ${HOME}/.zsh.d/zsh_env ]; then
    source ${HOME}/.zsh.d/zsh_env
fi

if [ -f ${HOME}/.zsh.d/zsh_option ]; then
    source ${HOME}/.zsh.d/zsh_option
fi

if [ -f ${HOME}/.zsh.d/zsh_peco ]; then
    source ${HOME}/.zsh.d/zsh_peco
fi

if [ -f ${HOME}/.zsh.d/zsh_aliases ]; then
    source ${HOME}/.zsh.d/zsh_aliases
fi

if [ -f ${HOME}/.zsh.d/zsh_aws ]; then
    source ${HOME}/.zsh.d/zsh_aws
fi

if [ -f ${HOME}/.zsh.d/zsh_tmux ]; then
#    source ${HOME}/.zsh.d/zsh_tmux
fi

if [ -f ${HOME}/.zsh.d/zsh_git ]; then
    source ${HOME}/.zsh.d/zsh_git
fi

if [ -f ${HOME}/.zsh.d/zsh_create_config ]; then
    source ${HOME}/.zsh.d/zsh_create_config
fi

if [ -f ${HOME}/.env ]; then
    source ${HOME}/.env
fi



