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

    # The function to run will be determined by the --filesystem
    # as well as the subcommand. The pattern used to map the CLI
    # command to the exact function in the library is:
    # wb.utils.filesystem.<filesystem>.<subcommand>

    # First get the module used for this filesystem
    filesystem_lib = wb.utils.filesystem.__dict__.get(args.filesystem)

    assert filesystem_lib is not None, f"Cannot find filesystem module {args.filesystem}"

    # Next, get the function defined in that module
    func = filesystem_lib.__dict__.get(args.func)

    assert func is not None, f"Cannot find function {args.func} for filesystem {args.filesystem}"

    # Run the function which was selected by the user
    func(
        # Every function takes a logger
        logger=logger,
        # Pass through all of the command line argument, except for the
        # 'func' key, which maps to the function which should be invoked
        **{
            k: v
            for k, v in args.__dict__.items()
            if k not in ["func", "filesystem"]
        }
    )
