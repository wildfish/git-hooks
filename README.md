# git-hooks
A tool for organising your hooks

# Usage

## Initialisation
Used to initialise the git repository to use the installed hooks. 

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

Alternatively you can define which hooks to install in a configuration file, for example, if you include the following
`git-hooks.cfg` in the root of your project:

```
[install]
pre-commit = http://hooks-repo/hook-a
    http://hooks-repo/hook-b
```

Running `git hooks install` will install `hook-a` and `hook-b` from `hooks-repo` into the git repository. Any number 
of hooks can be specified by separating urls with new lines. You can also specify hooks to install in a `setup.cfg` 
file in a `git-hooks.install` section (rather than `install`).
  
If both the `git-hooks.cfg` and `setup.cfg` are present the `git-hooks.cfg` file will be used.

# Creating hooks
Creating a hook is simple. Each hook consists of a script that will return either 0 if all test pass or non zero if there is 
a failure. Each type of hook takes a different set of positional arguments and keyword arguments.

## pre-commit
pre-commit hooks receive a list of the files to check. This list contains all modified or added files. Alternatively
the modified files are listed in the `--modified-files` argument. Similarly for `--added-files` and `--deleted-files`.

Though it is not necessary for hooks to be written in any specific language there are argument parsers to help when
writing pre-commit hooks. To parse the pre-commit arguments you can use `githooks.args.pre_commit`, this will return
an object with the list of modified and added files in the `files` property, the modified files in the `modified`
property, added files in the `added` property and removed files in `removed` property.

For example a script that tests `flake8` may look something like:

```
#!/usr/bin/env python

import subprocess
import sys

from githooks import args

files = [f for f in args.pre_commit().files if re.match('.*\.py$', f)]

if files:
    sys.exit(subprocess.call(['flake8'] + files))
```

This could also exclude file patterns based on an environment variable etc.
