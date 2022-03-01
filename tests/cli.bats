#!/usr/bin/env bats

@test "CLI" {
  wb --help
}

@test "setup_root_folder" {

  # Set the location of the workbench index
  export WB_BASE=base_folder
  export WB_PROFILE=test

  # Remove anything currently in the base_folder/
  rm -rf base_folder

  # Set up the base folder
  wb setup_root_folder

  # Validate that all files were created as appropriate
  [ -d base_folder ]
  [ -d base_folder/test ]
  [ -d base_folder/test/launcher ]
  [ -d base_folder/test/data ]
  [ -d base_folder/test/tool ]
  [ -d base_folder/test/repositories ]
  [ -d base_folder/test/linked_repositories ]
  [ -d base_folder/test/params ]
}

@test "index_folder" {

  # Create a folder and subfolder outside of the base folder
  rm -rf ext_data
  mkdir ext_data
  EXT_FOLDER=ext_data/data_folder_1
  mkdir ${EXT_FOLDER}

  # Index the newly created folder as a dataset
  wb index_folder --path ${EXT_FOLDER}

  # Construct the path which is expected to contain the index
  INDEX_JSON=${EXT_FOLDER}/._wb/index.json

  # Validate that the index file was created
  [ -s $INDEX_JSON ]

  # Show the contents of the index JSON for debugging purposes
  echo "Contents of index JSON"
  cat ${INDEX_JSON}
  echo

  # Validate that the index contents are as expected
  [ $(cat ${INDEX_JSON} | jq '.name') = '"data_folder_1"' ]

  # Validate that a link was created for that folder in the home directory
  echo "Checking for valid symlink"
  (( $(diff base_folder/test/data/data_folder_1/._wb/index.json ${INDEX_JSON} | wc -l) == 0 ))
}

@test "list_datasets" {

  # Create another subfolder outside of the base folder
  EXT_FOLDER=ext_data/data_folder_2
  mkdir ${EXT_FOLDER}

  # Index the newly created folder
  wb index_folder --path ${EXT_FOLDER}

  # Create another subfolder inside the previously-created dataset
  EXT_FOLDER=ext_data/data_folder_2/data_folder_3
  mkdir $EXT_FOLDER

  # Index the newly created folder as a dataset
  wb index_folder --path ${EXT_FOLDER}

  # List all indexed folders
  # Make sure that all three folders are found
  [ $(wb list_datasets | jq 'length') == 3 ]

}

@test "find_datasets" {

  make_dataset(){
    FP=$1
    NAME=$2
    DESC=$3

    echo "FP=$FP"
    echo "NAME=$NAME"
    echo "DESC=$DESC"

    mkdir $FP
    wb index_folder --path $FP
    wb change_name --path $FP --name $NAME
    wb change_description --path $FP --description $DESC
  }

  # Create another two subfolders inside the previously-created dataset
  make_dataset ext_data/data_folder_2/data_folder_4a 'Data Folder 4A' 'Very Useful Data Folder 4A'
  make_dataset ext_data/data_folder_2/data_folder_4b 'Data Folder 4B' 'Very Useful Data Folder 4B'

  # Test the find_datasets function based on the number of datasets found

  # Searching for the top-level dataset will yield a single result
  [ $(wb find_datasets --name data_folder_2 | jq 'length') == 1 ]

  # Searching for a subfolder will yield that folder and its parent
  [ $(wb find_datasets --name data_folder_3 | jq 'length') == 2 ]

  # Searching for a substring shared by two datasets will yield both (and their parent)
  [ $(wb find_datasets --name Data Folder 4 | jq 'length') == 3 ]

  # Searching the description field will yield the same
  [ $(wb find_datasets --description Very Useful | jq 'length') == 3 ]

}

@test "update_tags" {

  # Add tags to datasets
  wb update_tag --path ext_data/data_folder_1 --key position --value base
  wb update_tag --path ext_data/data_folder_2 --key position --value base
  wb update_tag --path ext_data/data_folder_2/data_folder_3 --key position --value tier1
  wb update_tag --path ext_data/data_folder_2/data_folder_4a --key position --value tier1
  wb update_tag --path ext_data/data_folder_2/data_folder_4b --key position --value tier1
  wb update_tag --path ext_data/data_folder_2/data_folder_4b --key extra --value special

  # Search for the two top-level datasets with position=base
  [ $(wb find_datasets --tag position=base | jq 'length') == 2 ]

  # Remove one of those tags
  wb delete_tag --path ext_data/data_folder_1 --key position

  # Now only one remains
  [ $(wb find_datasets --tag position=base | jq 'length') == 1 ]

  # Finding tags at nested folders will yield a list which includes the parent
  [ $(wb find_datasets --tag position=tier1 | jq 'length') == 4 ]

  # Searching for two tags
  [ $(wb find_datasets --tag position=tier1 extra=special | jq 'length') == 2 ]
}

@test "list_tools" {

  # List the basic set of tools available from the package
  [ $(wb list_tools | jq 'length') == 1 ]

}

@test "list_launchers" {

  # List the basic set of launchers available from the package
  [ $(wb list_launchers | jq 'length') == 1 ]

}

@test "setup_dataset" {

  # Set up the assets needed for analysis in a dataset folder
  wb setup_dataset --path ext_data/data_folder_1 --tool make_tar_gz --launcher base
  
}

@test "set_tool_params" {

  # Make a separate folder with some dummy data files
  mkdir ext_data/unindexed_data_folder_A
  echo FOO > ext_data/unindexed_data_folder_A/foo.txt
  echo BAR > ext_data/unindexed_data_folder_A/bar.txt

  # Move into the dataset that we've set up with the `make_tar_gz` tool
  cd ext_data/data_folder_1

  # Make sure that we can parse the arguments from this tool
  wb set_tool_params --help

  # Set the params on the command line
  wb set_tool_params --archive TEST_ARCHIVE --target ../unindexed_data_folder_A

  # A params file should have been created
  [ -s ._wb/tool/params.json ]

  # An environment file should have been created
  [ -s ._wb/tool/env ]

  # Source the environment variables from that file
  source ._wb/tool/env

  # The environment variables in the working environment should
  # reflect the values set up previously
  [ "${ARCHIVE}" == "TEST_ARCHIVE" ]

}

@test "set_launcher_params" {

  # Move into the dataset that we've set up with the `make_tar_gz` launcher
  cd ext_data/data_folder_1

  # Make sure that we can parse the arguments from this launcher
  wb set_launcher_params --help

  # Set the params on the command line (there are none for the base launcher)
  wb set_launcher_params

  # A params file should have been created
  [ -s ._wb/launcher/params.json ]
  
}

@test "run_dataset" {

  # Move into the dataset that we've set up with the `make_tar_gz` launcher
  cd ext_data/data_folder_1

  # Run the dataset
  wb run_dataset

  # Wait for the process to end (since wb does not block to completion)
  sleep 2

  ls -lahtr

  # Make sure that a file was created as expected
  [ -s TEST_ARCHIVE.tar.gz ]

  # Make sure that the status of the dataset is "COMPLETED"
  [[ "$(cat ._wb/index.json | jq '.status')" == *"COMPLETED"* ]]

}

@test "add_repository" {

  wb add_repo --name FredHutch/bash-workbench-tools

  [ -d base_folder/test/repositories/FredHutch/bash-workbench-tools ]

}

@test "list_repositories" {

  REPO_LIST="$(wb list_repos)"
  echo ${REPO_LIST}

  [[ $(echo ${REPO_LIST} | jq 'length') == 1 ]]
  [[ $(echo ${REPO_LIST} | jq '.[0]') == *"FredHutch/bash-workbench-tools"* ]]

}

@test "update_repository" {

  wb update_repo --name FredHutch/bash-workbench-tools

}

@test "delete_repository" {

  wb delete_repo --name FredHutch/bash-workbench-tools

  [ ! -d base_folder/test/repositories/FredHutch/bash-workbench-tools ]

}