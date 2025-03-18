import os
import time
import threading
from git import Repo, GitCommandError
from llm import ai_response
import customtkinter

def check_new_commits(repo):
    """Checks if there are new commits in the remote repository."""
    try:
        repo.remotes.origin.fetch()  # Fetch latest changes from remote
        local_hash = repo.head.commit.hexsha
        remote_hash = repo.remotes.origin.refs[repo.active_branch.name].commit.hexsha
        return local_hash != remote_hash
    except GitCommandError:
        return False  # Return False if an error occurs (e.g., no internet)

def get_commit_diff(repo):
    """Gets the latest commit diff and message."""
    current_commit = repo.head.commit

    code = ""
    for diff in current_commit.diff("HEAD~1", create_patch=True):
        code += diff.diff.decode('utf-8', errors='ignore')  # Decode for proper text format

    return f"This is my commit:\n\n{code}\n\nAnd this is my commit message:\n{current_commit.message}"

class CommitReviewApp(customtkinter.CTk):
    def __init__(self, repo):
        super().__init__()

        self.repo = repo
        self.text = "Waiting for new commits..."
        
        self.title("Commit Review")
        self.geometry("600x400")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1), weight=1)
        self.resizable(False, False)

        label = customtkinter.CTkLabel(self, text="Commit Review", font=("Arial", 20))
        label.pack(pady=20)

        self.my_frame = customtkinter.CTkScrollableFrame(self, width=500, height=300)
        self.my_frame.pack()

        self.text_label = customtkinter.CTkLabel(self.my_frame, text=self.text, wraplength=450, justify="left", font=("Arial", 15))
        self.text_label.pack(pady=10, padx=10, anchor="w")

        # Start a background thread to check for new commits
        self.check_commits_thread = threading.Thread(target=self.check_for_updates, daemon=True)
        self.check_commits_thread.start()

    def check_for_updates(self):
        """Continuously checks for new commits and updates the UI."""
        while True:
            if check_new_commits(self.repo):
                new_text = ai_response(get_commit_diff(self.repo))
                self.update_text(new_text)
            time.sleep(10)  # Check every 10 seconds

    def update_text(self, new_text):
        """Updates the text label dynamically."""
        self.text_label.configure(text=new_text)

if __name__ == "__main__":
    repo = Repo(os.getcwd())
    app = CommitReviewApp(repo)
    app.mainloop()
