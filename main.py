import os
import sys
import threading
import time
from datetime import datetime
import queue
from git import Repo, GitCommandError
import customtkinter as ctk
import ollama

# Set appearance mode and default color theme
ctk.set_appearance_mode("System")  # Follows system theme (dark/light)
ctk.set_default_color_theme("blue")  # Blue theme

def get_repository_path():
    """
    Gets the repository path, handling both development and PyInstaller environments.
    
    Returns:
        str: Path to the Git repository
    """
    # Check if we're running as an executable or in development
    if getattr(sys, 'frozen', False):
        # If running as executable, use the directory where the exe is located
        base_path = os.path.dirname(sys.executable)
    else:
        # If running as script, use the current working directory
        base_path = os.getcwd()
    
    try:
        # Check if the base path itself is a Git repository
        Repo(base_path)
        return base_path
    except:
        # If not, return None to prompt selection
        return None

def ai_response(prompt):
    """
    Get AI response from Ollama model with improved prompt engineering.
    
    Args:
        prompt (str): User prompt containing commit info
        
    Returns:
        str: AI-generated code review
    """
    try:
        response = ollama.chat(model='llama3.2', messages=[
            {
                'role': 'system',
                'content': """You are an expert code reviewer analyzing Git commits. Your task is to:
                
1. Evaluate code quality, readability, and adherence to best practices
2. Assess the commit message clarity and completeness
3. Identify potential bugs, security issues, or performance concerns
4. Suggest specific improvements with clear examples where applicable

Provide your analysis in a structured format:

## Summary
[Brief 1-2 sentence overview of the changes]

## Code Review
- [Key observations about code quality]
- [Potential issues or improvements]

## Commit Message Review
- [Assessment of commit message quality]
- [Suggested improvements if needed]

## Recommendations
- [Prioritized actionable items]

Format your response in markdown for readability.""",
            },
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        return response['message']['content']
    except Exception as e:
        return f"Error generating AI response: {str(e)}\n\nPlease check your Ollama setup and ensure the model is available."

class CommitReviewApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Commit Review Assistant")
        self.geometry("850x700")
        self.minsize(700, 600)
        
        # Try to set icon if available
        try:
            icon_path = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd(), "app_icon.ico")
            if os.path.exists(icon_path):
                self.after(200, lambda: self.iconbitmap(icon_path))
        except Exception:
            pass
        
        # Initialize variables
        self.repo = None
        self.repo_path = None
        self.last_commit_hash = None
        self.running = False
        self.monitor_thread = None
        self.animation_running = False
        self.ai_queue = queue.Queue()
        self.ai_worker_running = True
        
        # Create UI components
        self._create_ui()
        
        # Start AI worker thread
        self.ai_worker_thread = threading.Thread(target=self._ai_worker, daemon=True)
        self.ai_worker_thread.start()
        
        # Try to initialize with default repository
        self.repo_path = get_repository_path()
        if self.repo_path:
            self.initialize_repo(self.repo_path)
        else:
            self.update_status("No repository selected. Please select a repository.", "warning")
        
        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start progress bar animation
        self.animate_progress_bar()
    
    def _create_ui(self):
        """Create and organize all UI components"""
        # Create main frame with padding
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self._create_header()
        self._create_repo_section()
        self._create_status_section()
        self._create_content_section()
        self._create_footer()
    
    def _create_header(self):
        """Create header with logo and title"""
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.logo_label = ctk.CTkLabel(self.header_frame, text="🔍", font=ctk.CTkFont(size=28, weight="bold"))
        self.logo_label.pack(side="left", padx=(5, 0))
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="Commit Review Assistant",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(side="left", padx=10)
    
    def _create_repo_section(self):
        """Create repository selection section"""
        self.repo_frame = ctk.CTkFrame(self.main_frame)
        self.repo_frame.pack(fill="x", padx=10, pady=10)
        
        self.repo_label = ctk.CTkLabel(
            self.repo_frame, 
            text="Repository:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.repo_label.pack(side="left", padx=10)
        
        self.repo_path_label = ctk.CTkLabel(
            self.repo_frame,
            text="No repository selected",
            font=ctk.CTkFont(size=12),
            width=400,
            anchor="w"
        )
        self.repo_path_label.pack(side="left", padx=10, fill="x", expand=True)
        
        self.repo_button = ctk.CTkButton(
            self.repo_frame, 
            text="Select Repository",
            command=self.select_repository,
            font=ctk.CTkFont(size=12),
            height=32
        )
        self.repo_button.pack(side="right", padx=10)
    
    def _create_status_section(self):
        """Create status section with progress animation"""
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Status: Initializing...",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10, fill="x", expand=True)
        
        self.progress_bar = ctk.CTkProgressBar(self.status_frame, width=150)
        self.progress_bar.pack(side="right", padx=10)
        self.progress_bar.set(0)
    
    def _create_content_section(self):
        """Create the content section with commit info and review"""
        # Review content section title
        self.content_label = ctk.CTkLabel(
            self.main_frame,
            text="Commit Analysis",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.content_label.pack(anchor="w", padx=15, pady=(5, 0))
        
        # Commit info section
        self.commit_info_frame = ctk.CTkFrame(self.main_frame)
        self.commit_info_frame.pack(fill="x", padx=10, pady=5)
        
        self.commit_info = ctk.CTkLabel(
            self.commit_info_frame,
            text="No commit data available",
            font=ctk.CTkFont(size=12),
            anchor="w",
            justify="left",
            wraplength=800
        )
        self.commit_info.pack(fill="x", padx=10, pady=5)
        
        # Review text section
        self.review_frame = ctk.CTkFrame(self.main_frame)
        self.review_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.review_text = ctk.CTkTextbox(
            self.review_frame,
            font=ctk.CTkFont(family="Consolas" if os.name == 'nt' else "Courier", size=13),
            wrap="word"
        )
        self.review_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.review_text.insert("0.0", "Waiting for repository selection...")
        self.review_text.configure(state="disabled")
    
    def _create_footer(self):
        """Create footer with controls"""
        self.footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.footer_frame.pack(fill="x", padx=10, pady=(5, 0))
        
        # Action buttons
        self.button_frame = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        self.button_frame.pack(side="right")
        
        self.refresh_button = ctk.CTkButton(
            self.button_frame,
            text="🔄 Refresh Repo",
            command=self.refresh_repository,
            font=ctk.CTkFont(size=12),
            state="disabled",
            width=120,
            height=32
        )
        self.refresh_button.pack(side="left", padx=(0, 10))
        
        self.check_now_button = ctk.CTkButton(
            self.button_frame,
            text="✓ Check Now",
            command=self.check_now,
            font=ctk.CTkFont(size=12),
            state="disabled",
            width=120,
            height=32
        )
        self.check_now_button.pack(side="left", padx=0)
        
        # Left side controls
        self.controls_frame = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        self.controls_frame.pack(side="left", fill="x")
        
        self.auto_check_var = ctk.BooleanVar(value=True)
        self.auto_check = ctk.CTkSwitch(
            self.controls_frame,
            text="Auto Check",
            variable=self.auto_check_var,
            command=self.toggle_auto_check,
            font=ctk.CTkFont(size=12)
        )
        self.auto_check.pack(side="left", padx=10)
        
        self.check_interval_label = ctk.CTkLabel(
            self.controls_frame,
            text="Interval:",
            font=ctk.CTkFont(size=12)
        )
        self.check_interval_label.pack(side="left", padx=(20, 5))
        
        self.check_interval_var = ctk.StringVar(value="30")
        self.check_interval = ctk.CTkComboBox(
            self.controls_frame,
            values=["15", "30", "60", "300", "600"],
            variable=self.check_interval_var,
            width=70,
            font=ctk.CTkFont(size=12)
        )
        self.check_interval.pack(side="left", padx=0)
        
        self.interval_unit_label = ctk.CTkLabel(
            self.controls_frame,
            text="sec",
            font=ctk.CTkFont(size=12)
        )
        self.interval_unit_label.pack(side="left", padx=5)
        
        # Status line at bottom
        self.status_line_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=25)
        self.status_line_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        self.last_check_label = ctk.CTkLabel(
            self.status_line_frame,
            text="Last check: Never",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.last_check_label.pack(side="left", padx=10)
    
    def _ai_worker(self):
        """Background worker to process AI requests"""
        while self.ai_worker_running:
            try:
                # Get task from queue with timeout
                prompt, callback = self.ai_queue.get(timeout=1.0)
                
                # Process AI request
                response = ai_response(prompt)
                
                # Send result back to main thread
                self.after(0, lambda r=response: callback(r))
                
                # Mark task as done
                self.ai_queue.task_done()
                
            except queue.Empty:
                # Queue is empty, continue waiting
                continue
            except Exception as e:
                # Error occurred, log it and continue
                print(f"AI worker error: {e}")
                continue
    
    def animate_progress_bar(self):
        """Animate the progress bar when checking for commits"""
        if self.animation_running:
            current = self.progress_bar.get()
            if current >= 1.0:
                next_val = 0
            else:
                next_val = current + 0.05
            self.progress_bar.set(next_val)
            self.after(100, self.animate_progress_bar)
        else:
            self.progress_bar.set(0)
    
    def start_animation(self):
        """Start the progress bar animation"""
        self.animation_running = True
        self.animate_progress_bar()
    
    def stop_animation(self):
        """Stop the progress bar animation"""
        self.animation_running = False
        self.progress_bar.set(0)
    
    def toggle_auto_check(self):
        """Toggle automatic checking"""
        if self.auto_check_var.get():
            self.update_status("Auto-checking enabled", "info")
            if self.repo and not self.running:
                self.start_monitoring()
        else:
            self.update_status("Auto-checking disabled", "info")
            self.running = False
            # If the thread exists and is alive, it will stop on next loop iteration
    
    def check_now(self):
        """Manually check for updates"""
        if self.repo:
            self.update_status("Manually checking for updates...", "info")
            self.start_animation()
            self.update_commit_review()
    
    def refresh_repository(self):
        """Refresh the current repository"""
        if self.repo_path:
            try:
                self.update_status("Refreshing repository...", "info")
                self.repo = Repo(self.repo_path)
                if hasattr(self.repo.remotes, 'origin'):
                    self.repo.remotes.origin.fetch()
                self.update_status("Repository refreshed", "success")
                self.update_commit_info()
                self.check_now()
            except Exception as e:
                self.update_status(f"Error refreshing repository: {str(e)}", "error")
    
    def update_status(self, message, status_type="info"):
        """Update status with different styling based on status type"""
        status_colors = {
            "info": "gray60",
            "success": "green",
            "warning": "orange",
            "error": "red"
        }
        color = status_colors.get(status_type, "gray60")
        self.status_label.configure(text=f"Status: {message}", text_color=color)
    
    def select_repository(self):
        """Let user select a Git repository."""
        from tkinter import filedialog
        self.update_status("Selecting repository...", "info")
        
        repo_path = filedialog.askdirectory(title="Select Git Repository")
        if repo_path:
            try:
                # Check if valid Git repository
                Repo(repo_path)
                self.initialize_repo(repo_path)
            except Exception as e:
                self.update_status(f"Not a valid Git repository: {str(e)}", "error")
        else:
            self.update_status("Repository selection cancelled", "warning")
    
    def initialize_repo(self, repo_path):
        """Initialize repository monitoring."""
        try:
            self.repo_path = repo_path
            self.repo = Repo(self.repo_path)
            self.last_commit_hash = self.repo.head.commit.hexsha
            
            # Update UI
            self.repo_path_label.configure(text=os.path.basename(repo_path))
            self.update_status("Repository initialized", "success")
            self.check_now_button.configure(state="normal")
            self.refresh_button.configure(state="normal")
            
            # Display commit info
            self.update_commit_info()
            
            # Start monitoring if auto-check is enabled
            if self.auto_check_var.get():
                self.start_monitoring()
            
            # Initial review
            self.update_commit_review()
            
        except Exception as e:
            self.update_status(f"Error initializing repository: {str(e)}", "error")
    
    def update_commit_info(self):
        """Update the commit info display"""
        if not self.repo:
            return
            
        try:
            commit = self.repo.head.commit
            author = commit.author.name
            date = datetime.fromtimestamp(commit.committed_date).strftime("%Y-%m-%d %H:%M")
            
            # Format full commit message
            message_lines = commit.message.strip().split('\n')
            message_first_line = message_lines[0]
            
            # Detailed info
            info_text = f"Latest Commit: {commit.hexsha[:10]} by {author} on {date}\n"
            info_text += f"Subject: {message_first_line}"
            
            # Add additional commit message lines if present
            if len(message_lines) > 1 and any(line.strip() for line in message_lines[1:]):
                additional_lines = '\n'.join(line for line in message_lines[1:] if line.strip())
                if additional_lines:
                    info_text += f"\nDetails: {additional_lines[:100]}"
                    if len(additional_lines) > 100:
                        info_text += "..."
            
            # Add branch info
            try:
                branch_name = self.repo.active_branch.name
                info_text += f"\nBranch: {branch_name}"
            except:
                pass  # Detached HEAD state or other issue
            
            self.commit_info.configure(text=info_text)
        except Exception as e:
            self.commit_info.configure(text=f"Error getting commit info: {str(e)}")
    
    def start_monitoring(self):
        """Start the monitoring thread"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self.check_commits_periodically)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            self.update_status("Monitoring for changes", "info")
            self.start_animation()
    
    def on_closing(self):
        """Handle the window closing event."""
        self.running = False
        self.ai_worker_running = False
        # Wait a moment for threads to clean up
        time.sleep(0.2)
        self.destroy()
    
    def check_commits_periodically(self):
        """Periodically check for new commits and update the UI."""
        while self.running and self.auto_check_var.get():
            try:
                # Get check interval (default to 30 seconds if invalid)
                try:
                    interval = int(self.check_interval_var.get())
                    if interval < 5:  # Minimum 5 seconds
                        interval = 5
                except:
                    interval = 30
                
                # Pull latest changes if remote exists
                if hasattr(self.repo.remotes, 'origin'):
                    try:
                        self.repo.remotes.origin.fetch()
                    except GitCommandError:
                        # Log but don't fail on fetch errors
                        print("Warning: Could not fetch from remote")
                
                # Check if HEAD has changed
                current_hash = self.repo.head.commit.hexsha
                
                if current_hash != self.last_commit_hash:
                    self.after(0, lambda: self.update_status("New commit found! Updating review...", "success"))
                    self.last_commit_hash = current_hash
                    
                    # Update the UI from the main thread
                    self.after(0, self.update_commit_review)
                    self.after(0, self.update_commit_info)
                
                # Update last check time
                check_time = time.strftime("%H:%M:%S")
                self.after(0, lambda t=check_time: self.last_check_label.configure(
                    text=f"Last check: {t}"
                ))
                
            except Exception as e:
                self.after(0, lambda e=e: self.update_status(f"Error: {str(e)}", "error"))
            
            # Wait before next check
            time.sleep(interval)
    
    def update_commit_review(self):
        """Update the review text based on the latest commit."""
        if not self.repo:
            return
            
        try:
            current_commit = self.repo.head.commit
            
            # Get the diff
            code_diff = ""
            try:
                # For first commit or if HEAD~1 doesn't exist
                if len(list(self.repo.iter_commits())) > 1:
                    for diff in current_commit.diff("HEAD~1", create_patch=True):
                        code_diff += str(diff.diff.decode('utf-8', errors='replace'))
                else:
                    # If this is the first commit
                    for blob in current_commit.tree.traverse():
                        if blob.type == 'blob':  # This is a file
                            code_diff += f"+++ {blob.path}\n"
                            code_diff += "+"+blob.data_stream.read().decode('utf-8', errors='replace').replace('\n', '\n+')
            except Exception as e:
                code_diff = f"Could not get diff: {str(e)}"
            
            # Get affected files
            files_changed = []
            try:
                if len(list(self.repo.iter_commits())) > 1:
                    for diff_item in current_commit.diff("HEAD~1"):
                        if diff_item.a_path:
                            files_changed.append(diff_item.a_path)
                        elif diff_item.b_path:
                            files_changed.append(diff_item.b_path)
                else:
                    # For first commit, list all files
                    for blob in current_commit.tree.traverse():
                        if blob.type == 'blob':
                            files_changed.append(blob.path)
            except:
                pass
            
            # Prepare the prompt with commit info
            text_prompt = (
                f"Please review the following Git commit:\n\n"
                f"COMMIT HASH: {current_commit.hexsha}\n"
                f"AUTHOR: {current_commit.author.name}\n"
                f"DATE: {datetime.fromtimestamp(current_commit.committed_date).strftime('%Y-%m-%d %H:%M')}\n"
                f"COMMIT MESSAGE:\n{current_commit.message}\n\n"
                f"FILES CHANGED: {', '.join(files_changed)}\n\n"
                f"DIFF:\n{code_diff}"
            )
            
            # Update status while waiting for AI
            self.review_text.configure(state="normal")
            self.review_text.delete("0.0", "end")
            self.review_text.insert("0.0", "Generating review with AI... This may take a moment.")
            self.review_text.configure(state="disabled")
            self.update_status("Generating review with AI...", "info")
            
            # Queue AI task
            def process_ai_response(response):
                self.review_text.configure(state="normal")
                self.review_text.delete("0.0", "end")
                self.review_text.insert("0.0", response)
                self.review_text.configure(state="disabled")
                
                # Update status
                check_time = time.strftime("%H:%M:%S")
                self.last_check_label.configure(text=f"Last check: {check_time}")
                self.update_status("Review updated successfully", "success")
                self.stop_animation()
            
            # Add task to queue
            self.ai_queue.put((text_prompt, process_ai_response))
            
        except Exception as e:
            self.update_status(f"Error generating review: {str(e)}", "error")
            self.review_text.configure(state="normal")
            self.review_text.delete("0.0", "end")
            self.review_text.insert("0.0", f"Error generating review: {str(e)}")
            self.review_text.configure(state="disabled")
            self.stop_animation()


if __name__ == "__main__":
    app = CommitReviewApp()
    app.mainloop()