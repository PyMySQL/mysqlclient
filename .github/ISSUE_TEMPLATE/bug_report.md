---
name: Bug report
about: Report an issue of this project
title: ''
labels: ''
assignees: ''

---

### Read this first

We don't use this issue tracker to help users.  If you had trouble, please ask it on some user community.
Please use this tracker only when you are sure about it is an issue of this software.

And please provide full information from first.  I don't want to ask questions like "What is your Python version?", "Do you confirm MySQL error log?".  If the issue report looks incomplete, I will just close it.

Are you ready?  Please remove until here and make a good issue report!!


### Describe the bug

A clear and concise description of what the bug is.

### To Reproduce

**Schema**

```
create table ....
```

**Code**

```py
con = MySQLdb.connect(...)
cur = con.cursor()
cur.execute(...)
```

### Environment

**MySQL Server**

- Server OS (e.g. Windows 10, Ubuntu 20.04):
- Server Version (e.g. MariaDB 10.3.16):

**MySQL Client**

- OS (e.g. Windows 10, Ubuntu 20.04):

- Python (e.g. Homebrew Python 3.7.5):

- Connector/C (e.g. Homebrew mysql-client 8.0.18): 


### Additional context

Add any other context about the problem here.
