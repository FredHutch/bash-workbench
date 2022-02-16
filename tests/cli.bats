#!/usr/bin/env bats

@test "CLI" {
  wb-cli --help
}

@test "setup_root_folder" {
  wb-cli \
    --base-folder base_folder \
    --profile test \
    setup_root_folder

  [ -d base_folder ]
  [ -d base_folder/test ]
  [ -d base_folder/test/configs ]
  [ -d base_folder/test/data ]
  [ -d base_folder/test/tools ]
}
