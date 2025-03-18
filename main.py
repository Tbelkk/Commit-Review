import os
import threading
import time
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
        
        # Store repo path and initialize repository
        self.repo_path = os.getcwd()
        self.repo = Repo(self.repo_path)
        
        # Store last analyzed commit hash
        self.last_commit_hash = self.repo.head.commit.hexsha

        # UI elements
        label = customtkinter.CTkLabel(self, text="Commit Review", font=("Arial", 20))
        label.pack(pady=20)

        self.my_frame = customtkinter.CTkScrollableFrame(self, width=500, height=300)
        self.my_frame.pack()

        self.text_label = customtkinter.CTkLabel(self.my_frame, text="Initializing...", 
                                                wraplength=450, justify="left", 
                                                font=("Arial", 15))
        self.text_label.pack(pady=10, padx=10, anchor="w")
        
        # Status indicator
        self.status_label = customtkinter.CTkLabel(self, text="Monitoring for changes...", 
                                                  font=("Arial", 12))
        self.status_label.pack(pady=10)
        
        # Start with initial review
        self.update_commit_review()
        
        # Start the monitoring thread
        self.running = True
        self.monitor_thread = threading.Thread(target=self.check_commits_periodically)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        """Handle the window closing event."""
        self.running = False
        self.destroy()
    
    def check_commits_periodically(self):
        """Periodically check for new commits and update the UI."""
        while self.running:
            time.sleep(30)  # Check every 30 seconds
            
            try:
                # Update status
                self.status_label.configure(text="Checking for new commits...")
                
                # Pull latest changes
                self.repo.remotes.origin.pull()
                
                # Check if HEAD has changed
                current_hash = self.repo.head.commit.hexsha
                
                if current_hash != self.last_commit_hash:
                    self.status_label.configure(text="New commit found! Updating review...")
                    self.last_commit_hash = current_hash
                    
                    # Update the UI from the main thread
                    self.after(0, self.update_commit_review)
                else:
                    self.status_label.configure(text="Monitoring for changes...")
            except Exception as e:
                self.status_label.configure(text=f"Error: {str(e)}")

    def update_commit_review(self):
        """Update the review text based on the latest commit."""
        try:
            current_commit = self.repo.head.commit
            
            # Get the diff
            code = ""
            for diff in current_commit.diff("HEAD~1", create_patch=True):
                code += str(diff.diff.decode('utf-8', errors='replace'))
            
            # Prepare the prompt with commit info
            text_prompt = f"This is my commit {code} and this is my commit message {current_commit.message}"
            
            # Get AI response
            text = ai_response(text_prompt)
            
            # Update the label
            self.text_label.configure(text=text)
            
            # Update status
            self.status_label.configure(text=f"Last updated: {time.strftime('%H:%M:%S')}")
            
        except Exception as e:
            self.text_label.configure(text=f"Error generating review: {str(e)}")


if __name__ == "__main__":
    app = CommitReviewApp()
    app.mainloop()
            







