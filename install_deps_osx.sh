#!/bin/sh
! (which brew >/dev/null) && echo "Homebrew required. Please visit http://github.com/Homebrew/homebrew" && exit 1
brew install --with-djvu ghostscript
while read -p "Install DjView.app? (y/n): " input; do
	! [ "$input" == "y" ] && break
	brew install caskroom/cask/brew-cask
	brew cask install djview
	#need a cask for the caminova finder/safari plugin too
done
