from wb_cli.args import make_parser

def workbench_cli():
    
    # Get the base parser for the CLI
    parser = make_parser()

    # Parse the arguments
    args = parser.parse_args()

