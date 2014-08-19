;; load-path
(defun add-to-load-path (&rest paths)
  (mapc '(lambda (path)
           (add-to-list 'load-path path))
        (mapcar 'expand-file-name paths)))

;; lisp directory's path
(add-to-load-path "~/.emacs.d/lisp")
(add-to-load-path "~/.emacs.d/elpa")
;; load
(load "make-backup-file")
(load "package")

(require 'auto-complete-config)
(add-to-list 'ac-dictionary-directories "/home/ubuntu/.emacs.d/lisp/ac-dict")
(ac-config-default)

;; Markdown
(autoload 'markdown-mode "markdown-mode.el" "Major mode for editing Markdown files" t)
(add-to-list 'auto-mode-alist '("\\.md\\'" . markdown-mode))

;; Python
(load "jedi")
;;(load "python-pep8")

;; YAML
(load "yaml-mode")
(require 'yaml-mode)
    (add-to-list 'auto-mode-alist '("\\.yml$" . yaml-mode))

(load "ansible")
(require 'ansible)
(add-hook 'yaml-mode-hook '(lambda () (ansible 1)))

;; nginx
(require 'nginx-mode)
(add-to-list 'auto-mode-alist '("nginx\\(.*\\).conf[^/]*$" . nginx-mode))

;; js
(load "js2-mode")

(load "angular-mode")
(add-to-list 'auto-mode-alist '("\\.js$"     . angular-mode))
(add-to-list 'auto-mode-alist '("\\.js$"     . js2-mode))

(load "angular-html-mode")
(add-to-list 'auto-mode-alist '("\\.html$"     . angular-html-mode))
