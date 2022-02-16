#!/usr/bin/env bats

@test "CLI available" {
  wb-cli --help
}

@test "Set up root directory" {
  wb-cli \
    --base-folder base_folder \
    --profile test \
    setup_root_folder
}
