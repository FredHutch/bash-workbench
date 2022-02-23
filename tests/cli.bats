#!/usr/bin/env bats

@test "CLI" {
  wb-cli --help
}

@test "setup_root_folder" {

  # Set the location of the workbench index
  export WB_BASE=base_folder
  export WB_PROFILE=test

  # Remove anything currently in the base_folder/
  rm -rf base_folder

  # Set up the base folder
  wb-cli setup_root_folder

  # Validate that all files were created as appropriate
  [ -d base_folder ]
  [ -d base_folder/test ]
  [ -d base_folder/test/launchers ]
  [ -d base_folder/test/data ]
  [ -d base_folder/test/tools ]
}

@test "index_dataset" {

  # Create a folder and subfolder outside of the base folder
  rm -rf ext_data
  mkdir ext_data
  EXT_FOLDER=ext_data/data_folder_1
  mkdir ${EXT_FOLDER}

  # Index the newly created folder as a dataset
  wb-cli index_dataset --path ${EXT_FOLDER}

  # Construct the path which is expected to contain the index
  INDEX_JSON=${EXT_FOLDER}/._wb_index.json

  # Validate that the index file was created
  [ -s $INDEX_JSON ]

  # Show the contents of the index JSON for debugging purposes
  echo "Contents of index JSON"
  cat ${INDEX_JSON}
  echo

  # Validate that the index contents are as expected
  [ "$(cat ${INDEX_JSON} | jq '.type')" == '"dataset"' ]
  [ $(cat ${INDEX_JSON} | jq '.name') = '"data_folder_1"' ]

  # Validate that a link was created for that folder in the home directory
  echo "Checking for valid symlink"
  (( $(diff base_folder/test/data/data_folder_1/._wb_index.json ${INDEX_JSON} | wc -l) == 0 ))
}

@test "index_collection" {

  # Create another subfolder outside of the base folder
  EXT_FOLDER=ext_data/data_folder_2
  mkdir ${EXT_FOLDER}

  # Index the newly created folder as a collection
  wb-cli index_collection --path ${EXT_FOLDER}

  # Construct the path which is expected to contain the index
  INDEX_JSON=${EXT_FOLDER}/._wb_index.json

  # Validate that the index file was created
  [ -s $INDEX_JSON ]

  # Show the contents of the index JSON for debugging purposes
  echo "Contents of index JSON"
  cat ${INDEX_JSON}
  echo

  # Validate that the index contents are as expected
  [ "$(cat ${INDEX_JSON} | jq '.type')" == '"collection"' ]
  [ $(cat ${INDEX_JSON} | jq '.name') = '"data_folder_2"' ]

  # Validate that a link was created for that folder in the home directory
  echo "Checking for valid symlink"
  (( $(diff base_folder/test/data/data_folder_2/._wb_index.json $INDEX_JSON | wc -l) == 0 ))
}

@test "list_datasets" {

  # Create another subfolder inside the previously-created collection
  EXT_FOLDER=ext_data/data_folder_2/data_folder_3
  mkdir $EXT_FOLDER

  # Index the newly created folder as a dataset
  wb-cli index_dataset --path ${EXT_FOLDER}

  # List all indexed folders
  # Make sure that all three folders are found
  [ $(wb-cli list_datasets --data | jq 'length') == 3 ]

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
    wb-cli index_dataset --path $FP
    wb-cli change_name --path $FP --name $NAME
    wb-cli change_description --path $FP --description $DESC
  }

  # Create another two subfolders inside the previously-created collection
  make_dataset ext_data/data_folder_2/data_folder_4a 'Data Folder 4A' 'Very Useful Data Folder 4A'
  make_dataset ext_data/data_folder_2/data_folder_4b 'Data Folder 4B' 'Very Useful Data Folder 4B'

  # Test the find_datasets function based on the number of datasets found

  # Searching for the top-level collection will yield a single result
  [ $(wb-cli find_datasets --data --name data_folder_2 | jq 'length') == 1 ]

  # Searching for a subfolder will yield that folder and its parent
  [ $(wb-cli find_datasets --data --name data_folder_3 | jq 'length') == 2 ]

  # Searching for a substring shared by two datasets will yield both (and their parent)
  [ $(wb-cli find_datasets --data --name Data Folder 4 | jq 'length') == 3 ]

  # Searching the description field will yield the same
  [ $(wb-cli find_datasets --data --description Very Useful | jq 'length') == 3 ]

}

@test "update_tags" {

  # Add tags to datasets
  wb-cli update_tag --path ext_data/data_folder_1 --key position --value base
  wb-cli update_tag --path ext_data/data_folder_2 --key position --value base
  wb-cli update_tag --path ext_data/data_folder_2/data_folder_3 --key position --value tier1
  wb-cli update_tag --path ext_data/data_folder_2/data_folder_4a --key position --value tier1
  wb-cli update_tag --path ext_data/data_folder_2/data_folder_4b --key position --value tier1
  wb-cli update_tag --path ext_data/data_folder_2/data_folder_4b --key extra --value special

  # Search for the two top-level datasets with position=base
  [ $(wb-cli find_datasets --data --tag position=base | jq 'length') == 2 ]

  # Remove one of those tags
  wb-cli delete_tag --path ext_data/data_folder_1 --key position

  # Now only one remains
  [ $(wb-cli find_datasets --data --tag position=base | jq 'length') == 1 ]

  # Finding tags at nested folders will yield a list which includes the parent
  [ $(wb-cli find_datasets --data --tag position=tier1 | jq 'length') == 4 ]

  # Searching for two tags
  [ $(wb-cli find_datasets --data --tag position=tier1 extra=special | jq 'length') == 2 ]
}

@test "list_tools" {

  # List the basic set of tools available from the package
  [ $(wb-cli list_tools | jq 'length') == 1 ]

}

@test "list_launchers" {

  # List the basic set of launchers available from the package
  [ $(wb-cli list_launchers | jq 'length') == 1 ]

}

@test "setup_dataset" {

  # Set up the assets needed for analysis in a dataset folder
  wb-cli setup_dataset --path ext_data/data_folder_1 --tool make_tar_gz --launcher base
  
}