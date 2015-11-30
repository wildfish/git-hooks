# git-hooks
A tool for organising your hooks

# Usage

## Initialisation
Used to initialise the git repository to use the instlled hooks. 

```
$> git hooks init
```

## Install
Used to install a hook into the git repository. 

```
$> git hooks install <hook_type> <hook_url>
```

where:

```
hook_type: The type of hook to install the script as eg pre-commit, post-commit etc
hook_url: This can be the url of a sript to install or url to a git repository containing a file with the hook type name
```

Alternatively the `-r` flag can be used to install all the hooks listed within a requirements file

# Creating hooks
Creating a hook is simple. Each hook comsists of a script that will return either 0 if all test pass or non zero if there is 
a failure. Each type of hook takes a different set of positional arguments.

## pre-commit
pre-commit hooks recieve a list of the files to check. For example a script that tests `flake8` may look something like:

```
#!/usr/bin/env python
import subprocess
import sys

sys.exit(subprocess.call(['flake8'] + sys.argv[1:]))
```

This could also exclude file patterns based on an eviroonmet variable etc.
