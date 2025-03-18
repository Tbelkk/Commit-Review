import os
from git import Repo, GitCommandError
from llm import ai_response
import customtkinter

def check_new_commits(repo_path):
    """Checks if there are new commits in the remote repository.

    Args:
        repo_path (str): The path to the local Git repository.

    Returns:
        bool: True if there are new commits, False otherwise.
    """
    repo = Repo(repo_path)
    repo.remotes.origin.fetch()  # Fetch latest changes from remote

    # Get local and remote commit hashes
    local_hash = repo.head.commit.hexsha
    remote_hash = repo.remotes.origin.refs[repo.active_branch.name].commit.hexsha
    
    return local_hash != remote_hash


class CommitReviewApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Commit Review")
        self.geometry("600x400")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1), weight=1)
        self.resizable(False, False)

        label = customtkinter.CTkLabel(self, text="Commit Review", font=("Arial", 20))
        label.pack(pady=20)

        self.my_frame = customtkinter.CTkScrollableFrame(self, width=500, height=300)
        self.my_frame.pack()

        self.text_label = customtkinter.CTkLabel(self.my_frame, text=text, wraplength=450, justify="left", font=("Arial", 15))
        self.text_label.pack(pady=10, padx=10, anchor="w")

if __name__ == "__main__":
    repo = Repo(os.getcwd())

    commits = list(repo.iter_commits('HEAD'))

    current_commit = repo.head.commit

    code = """"""
    for diff in current_commit.diff("HEAD~1", create_patch=True):
        code = diff.diff

    text_prompt = f"This is my commit {code} and this is my commit message {current_commit.message}"

    text = ai_response(text_prompt)

    app = CommitReviewApp()
    app.mainloop()
            







