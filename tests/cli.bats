#!/usr/bin/env bats

@test "CLI" {
  wb-cli --help
}

@test "setup_root_folder" {

  # Remove anything currently in the base_folder/
  rm -rf base_folder

  # Set up the base folder
  wb-cli \
    --base-folder base_folder \
    --profile test \
    setup_root_folder

  # Validate that all files were created as appropriate
  [ -d base_folder ]
  [ -d base_folder/test ]
  [ -d base_folder/test/configs ]
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
  wb-cli \
    --base-folder base_folder \
    --profile test \
    index_dataset \
    --path ${EXT_FOLDER}

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
  wb-cli \
    --base-folder base_folder \
    --profile test \
    index_collection \
    --path ${EXT_FOLDER}

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

@test "show_datasets" {

  # Create another subfolder inside the previously-created collection
  EXT_FOLDER=ext_data/data_folder_2/data_folder_3
  mkdir $EXT_FOLDER

  # Index the newly created folder as a dataset
  wb-cli \
    --base-folder base_folder \
    --profile test \
    index_dataset \
    --path ${EXT_FOLDER}

  # List all indexed folders
  DATASETS="""$(wb-cli \
    --base-folder base_folder \
    --profile test \
    show_datasets)"""

  # Make sure that all three folders are found
  [ $(echo "$DATASETS" | jq 'length') == 3 ]

}
