#!/usr/bin/env make -f
#make a github release of the calibre plugin

VERSION := $(shell python __init__.py)
LAST_TAG != git describe --abbrev=0 --tags

USER := kfix
PLUGIN := djvumaker
REPO := calibre_plugin_djvumaker
ZIP := $(PLUGIN).zip

GH_RELEASE_JSON = '{"tag_name": "v$(VERSION)","target_commitish": "master","name": "v$(VERSION)","body": "calibre plugin of version $(VERSION)","draft": false,"prerelease": false}'

all: clean release

tag:
	git tag -f -a v$(VERSION) -m 'release $(VERSION)'

$(ZIP): tag
	git archive --format=zip --output=$@ v$(VERSION) *.py *.txt

ifneq ($(GITHUB_ACCESS_TOKEN),)
release: $(ZIP)
	git push -f --tags
	posturl=$$(curl --data $(GH_RELEASE_JSON) "https://api.github.com/repos/$(USER)/$(REPO)/releases?access_token=$(GITHUB_ACCESS_TOKEN)" | jq -r .upload_url | sed 's/[\{\}]//g') && \
	dload=$$(curl --fail -X POST -H "Content-Type: application/gzip" --data-binary "@$(ZIP)" "$$posturl=$(ZIP)&access_token=$(GITHUB_ACCESS_TOKEN)" | jq -r .browser_download_url | sed 's/[\{\}]//g') && \
	echo "Plugin now available for download at $$dload"
	#update attachment @ http://www.mobileread.com/forums/showthread.php?p=2881112#post2881112
else
release:
	@echo You need to export \$$GITHUB_ACCESS_TOKEN to make a release!
	@exit 1
endif

clean:
	-rm *.zip

test: $(ZIP)
	calibre-customize -a $(ZIP)
	calibre-debug -r djvumaker -- convert -p test.pdf

.PHONY: clean tag release all test
