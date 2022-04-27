class ParamsMenu:
    """Class used to coordinate the user-driven editing of parameters."""

    def __init__(
        self,
        config:dict=None,
        params:dict=None,
        menu=None,
        confirm_text:str="Review and run"
    ):
        """Set up a set of parameters which must conform to a particular configuration."""

        # Make sure that all inputs were provided
        assert config is not None
        assert params is not None
        assert menu is not None
        assert confirm_text is not None

        # Attach the inputs
        self.config = config
        self.params = params
        self.menu = menu
        self.confirm_text = confirm_text

        # For each of the configured parameters
        for param_key in self.config:

            # If no value was provided
            if self.params.get(param_key) is None:

                # If there is a default in the configuration
                if self.config[param_key].get("default") is not None:

                    # Set the default from the configuration
                    self.params[param_key] = self.config[param_key]["default"]

        # Check to see if all required parameters are provided
        self.validate_params(echo=False)

    def invalidate(self, msg, echo=False):
        """Set the parameters to an invalid state and report to the user (if echo is set)."""

        # If echo was set
        if echo:

            # Tell the user
            self.menu.print_line(msg)
        
        # The parameters are not valid
        self.approved = False

    def validate_params(self, echo=False):
        """Check to see if all required parameters are provided."""

        # Parameters are valid by default
        self.approved = True
        
        # For each of the parameters in the configuration
        for key, val in self.config.items():

            # If the parameter is supposed to be provided as a list
            if val.get("nargs", "?") not in ["?", 1]:

                # If there is a default value
                if val.get("default") is not None:

                    # It must be a list
                    msg = f"Param {key} is formatted as a list, but the default value is not formatted as a list"
                    assert isinstance(val["default"], list), msg

                # If there is a parameter provided
                if self.params.get(key) is not None:

                    # If it is not a list
                    if not isinstance(self.params[key], list):

                        # Turn it into a list
                        self.params[key] = [self.params[key]]

            # If the parameter is required
            if val.get("required", False):

                # And it is not present
                if self.params.get(key) is None:

                    # The parameters are not valid
                    self.invalidate(
                        f"Required parameter '{key}' is missing", 
                        echo=echo
                    )

            # If the number of arguments was not specified, or not required
            if val.get("nargs", "?") in ["?", "*"]:

                # Then we will not apply any check to the number of elements
                pass

            # If a specific number of arguments was provided
            elif isinstance(val.get("nargs"), int):

                # And it is not present
                if self.params.get(key) is None:

                    # The parameters are not valid
                    self.invalidate(
                        f"Required parameter '{key}' is missing", 
                        echo=echo
                    )

                # If it is present
                else:

                    # If the parameter is not a list
                    if not isinstance(self.params[key], list):

                        # Make sure it is a list
                        self.params[key] = [self.params[key]]

                    # If the number of elements in the param does not meet the requirement
                    if len(self.params[key]) != val["nargs"]:

                        # The parameters are not valid
                        self.invalidate(
                            f"Parameter '{key}' must contain {val['nargs']} elements", 
                            echo=echo
                        )

    def review_and_run(self):
        """If the user opts to review and run, validate the parameters and reprompt if needed."""

        # Validate the parameters
        self.validate_params(echo=True)

        if self.approved:
            self.menu.print_line("Dataset is fully configured")
        else:
            self.menu.print_line("Cannot run - dataset is not yet fully configured")

        # If the parameters are not valid
        if not self.approved:

            # Go back to the prompt
            self.prompt()

    def back_to_main_menu(self):
        """Return the to main menu."""

        # Set the parameters as not being approved
        self.invalidate("Returning to main menu", echo=True)

    def format_value(self, param_key):
        """Format the value of a parameter as a string."""

        # If there is no value currently
        if self.params.get(param_key) is None:

            return "no value"

        else:

            # Get the value
            param_value = self.params[param_key]

            # If it is a list
            if isinstance(param_value, list):

                # Return a comma delimited list
                return ", ".join(map(str, param_value))

            # Otherwise
            else:

                # Return a string
                return str(param_value)

    def prompt(self):
        """Show the user a list of all parameters, giving them the opportunity
        to edit any of them, approve them, or exit."""
        
        # Make a list of all of the parameters, showing the current
        # value and giving the user an opportunity to edit
        resp = self.menu.questionary(
            "select",
            "Select a parameter to edit",
            choices=[
                f"{param_key}: {self.format_value(param_key)}\n      {self.config[param_key].get('help', '')}"
                for param_key in self.config
            ] + [
                self.confirm_text,
                "Back to main menu", 
            ]
        )

        if resp == self.confirm_text:
            self.review_and_run()
        elif resp == "Back to main menu":
            self.back_to_main_menu()
        else:
            param_key = resp.split(": ", 1)[0]
            self.edit_param(param_key)

    def edit_param(self, param_key):
        """Menu used to edit a single parameter."""

        # Get the parameter config
        param_config = self.config[param_key]

        # Get the current value for the parameter
        param_value = self.params.get(param_key)

        # Set up a header to display with the list of options
        header = param_config.get("name", f"Parameter: {param_key}")

        # If there is help text
        if param_config.get("help") is not None:

            # Add it to the header
            header = header + "\n- " + param_config.get("help") + "\n"

        # If there is a value
        if param_value is not None:

            # Show the current value
            header = header + "\n" + f"Current value: {self.format_value(param_key)}"
        
        # Set up the list of options to display
        options = []

        # If the arguments are supposed to be provided as a list
        if param_config.get("nargs", "?") not in ["?", 1]:

            # If there are value(s) already provided
            if param_value is not None and len(param_value) > 0:

                # Give the user the option to remove an argument
                options.append(
                    ("Remove a value", lambda: self.remove_value(param_key))
                )

            # Give the user the option to add an argument
            options.append(
                ("Add a value", lambda: self.add_value(param_key))
            )

        # If the argument is not a list
        else:

            # If there is a value already provided
            if param_value is not None:

                # Give the user the option to edit the value
                options.append(
                    ("Edit value", lambda: self.edit_value(param_key))
                )

            # If no value has been provided
            else:

                # Give the user the option to provide a value
                options.append(
                    ("Enter value", lambda: self.edit_value(param_key))
                )


        # No matter what, give the user the option to completely remove the value
        options.append(
            ("Clear parameter", lambda: self.clear_value(param_key))
        )

        # The last option is to go back to the list of all parameters
        options.append(
            ("Done", self.done)
        )

        # Prompt the user to select from these options
        self.menu.select_func(header, options)

        # After editing the parameter, go back to the prompt
        self.prompt()

    def done(self):
        """Function called when no action should be taken."""
        pass

    def remove_value(self, param_key):
        """Remove a value from the list available for a given parameter."""

        # Get the list of options to remove
        value_list = self.params.get(param_key)

        assert isinstance(value_list, list)
        assert len(value_list) > 0

        # Pick an option to remove
        resp = self.menu.questionary(
            "select",
            "Select a value to remove",
            choices=value_list
        )

        # Remove the option
        value_list.pop(
            value_list.index(resp)
        )

        # Update the paramters
        self.params[param_key] = value_list

    def add_value(self, param_key):
        """Add a value to the list for a parameter."""

        # Prompt the user
        resp = self.prompt_single_entry(param_key)
        
        # Add to the list
        self.params[param_key].append(resp)

    def edit_value(self, param_key):
        """Edit a value already provided for a parameter."""

        # Prompt the user
        resp = self.prompt_single_entry(
            param_key, 
            default=None if isinstance(self.params.get(param_key), list) else self.params.get(param_key)
        )
        
        # Add to the list
        self.params[param_key] = resp

    def clear_value(self, param_key):
        """Clear any value provided for a parameter."""

        # Clear the value
        del self.params[param_key]

    def prompt_single_entry(self, param_key, **kwargs):
        """Prompt for a single entry of the parameter type defined."""

        # Get the type of value to prompt for
        wb_type = self.config[param_key].get("wb_type")

        assert wb_type is not None, f"Parameter {param_key} must have 'wb_type' defined"

        # Get the type of questionary prompt to use
        questionary_type_dict = dict(
            string="text",
            password="password",
            file="path",
            folder="path",
            select="select",
            integer="text",
            float="text",
            bool="select"
        )

        questionary_type = questionary_type_dict.get(wb_type)

        msg = f"Parameter ({param_key}) wb_type ({wb_type}) is not recognized [{', '.join(list(questionary_type_dict))}]"
        assert questionary_type is not None, msg

        # Add wb_type specific options to the questionary prompt
        if wb_type == "folder":
            kwargs["only_directories"] = True
        elif wb_type == "select":

            choices = self.config[param_key].get("wb_choices")
            msg = "Must provide `wb_choices` for arguments where `wb_type` == 'select'"
            assert choices is not None, msg
            kwargs["choices"] = choices

        # For boolean selectors
        elif wb_type == "bool":

            default = self.config[param_key].get("default")
            assert default is not None, f"Must provide a default value (true/false) for {param_key}"
            assert isinstance(default, bool), f"Must provide a default value (true/false) for {param_key}"

            if default:
                kwargs["default"] = "true"
            else:
                kwargs["default"] = "false"

            # Present two choices
            kwargs["choices"] = ["true", "false"]
            # Transform the output back into a boolean
            kwargs["output_f"] = lambda v: dict(true=True, false=False)[v]

        elif wb_type == "integer":
            kwargs["validate_type"] = lambda v: int(v)
            kwargs["output_f"] = lambda v: int(v)
        elif wb_type == "float":
            kwargs["validate_type"] = lambda v: float(v)
            kwargs["output_f"] = lambda v: float(v)

        msg = f"Error: no prompt type specified for variables of type {wb_type}"
        assert wb_type is not None, msg

        # This variable can be used to add a header above the prompt
        header = ""

        if wb_type in ["file", "folder"]:
            # Give the user some tips for selecting files and folders
            header = "Use ../ to select the parent folder, or / to enter an absolute path\n  Press <TAB> at any time for autocomplete\n  "

        # Delete empty values in the kwargs
        kwargs = {
            k: v
            for k, v in kwargs.items()
            if v is not None
        }

        return self.menu.questionary(questionary_type, f"{header}{wb_type}:", **kwargs)
