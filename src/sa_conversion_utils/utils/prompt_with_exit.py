from rich.console import Console
from rich.prompt import Prompt

console = Console()

def prompt_with_exit(prompt_message, choices, default_choice):
    """
    Custom prompt that allows user to select from given choices, with an exit option.
    
    Args:
        prompt_message (str): The prompt text to display.
        choices (list): List of choices the user can pick from.
        default_choice (str): The default option if the user does not input anything.

    Returns:
        str or None: Returns the selected choice, or None if the user selects 'exit'.
    """

    choices = choices + ["exit"]

    while True:
        # Display the prompt and capture the user's choice
        choice = Prompt.ask(prompt_message, choices=choices, default=default_choice)
        
        if choice == "exit":
            console.print("[bold red]Exiting[/bold red]")
            return None  # Return None to signify the user exited
        
        return choice

# Example usage
# choice = prompt_with_exit(
#     "[bold green]Select an option[/bold green]",
#     choices=["option1", "option2", "option3", "exit"],
#     default_choice="option1"
# )

# if choice:
#     console.print(f"You selected: {choice}")
# else:
#     console.print("User exited the prompt.")
