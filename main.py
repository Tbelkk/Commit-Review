import os
from git import Repo

repo = Repo(os.getcwd())

print(repo.head.commit.message)