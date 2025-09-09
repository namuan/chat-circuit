General Rules:

- MUST Start any task by running `make start-work` with a feature name. Eg `make start-work FEATURE=user-config`
- Use ast-grep for code searching and refactoring
- MUST Add extensive logging to help with debugging as this is a GUI application
- MUST Run `make check` before starting a new check list item to make sure there aren't any existing issues to resolve
- Run `make run` to run the application
- Always prefer to use `make` commands
- Use `uv add` to add any dependencies. Use `uv add --dev` if it is a dev dependency.
- MUST Whenever you’re about to complete a user request, call the MCP interactive_feedback instead of simply ending the process. Keep calling MCP until the user’s feedback is empty, then end the request.

Coding Rules:
Always add import at the top of the file
Use consistent patterns - Avoid novelty in function structure; standardize how similar logic is implemented across the codebase.
Break up complex chains - Split long function chains, iterators, or comprehensions into logical groups using helper functions or intermediate variables.
Simplify conditionals - Keep condition tests short and prefer sequences of the same logical operator (avoid mixing && and || when possible).
Minimize nesting depth - Avoid deep indentation; refactor deeply nested logic into separate functions.
Use distinct, descriptive names - Choose visually distinguishable and meaningful variable names; never shadow variables.
Minimize variable lifespan - Declare variables close to where they're used and limit how long they remain in scope.
