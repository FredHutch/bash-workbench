import bash_workbench as wb

def cli():
    
    # Get the base parser for the CLI
    parser = wb.cli.args.make_parser()

    # Parse the arguments
    args = parser.parse_args()

    # Get a logger which writes to standard out
    logger = wb.utils.logging.setup_logger(
        log_stdout=True,   # Print to standard out
        log_fp=None,       # Do not write to a file
    )

    # If no subcommand was provided
    if args.__dict__.get("func") is None:

        logger.info("Missing subcommand")
        parser.print_help()

    # If a subcommand was provided
    else:

        # Run the function which was selected by the user
        args.func(
            # Every function takes a logger
            logger=logger,
            # Pass through all of the command line argument, except for the
            # 'func' key, which maps to the function which should be invoked
            **{
                k: v
                for k, v in args.__dict__.items()
                if k != "func"
            }
        )
