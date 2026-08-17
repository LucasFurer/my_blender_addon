BLENDER := $(HOME)/my_files/apps/blender-5.2.0-linux-x64/blender

EXTENSION_ID := erosion_terrain_extension
BUILD_DIR := build
SRC_DIR := src
REPO_ID := dev_local
REPO_DIR := extension_repo

.PHONY: build repo install dev clean

build:
	$(BLENDER) --command extension build --source-dir $(SRC_DIR) --output-dir $(BUILD_DIR)

repo:
	mkdir -p $(REPO_DIR)
	$(BLENDER) --command extension repo-add $(REPO_ID) --directory "$(abspath $(REPO_DIR))" --source USER

install: build
	$(BLENDER) --command extension install-file --repo $(REPO_ID) --enable $(BUILD_DIR)/$(EXTENSION_ID)-*.zip

dev: install
	$(BLENDER)

clean:
	rm -rf $(BUILD_DIR)
