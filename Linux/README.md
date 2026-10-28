# Linux Concepts and Commands

A gradual guide to Linux command-line and server administration. The examples target Ubuntu, including an Ubuntu EC2 instance. Try commands in a local virtual machine or a server you control, and add your own notes as you learn.

## Learning path

1. Navigate the shell and inspect files.
2. Create, copy, move, and search files.
3. Understand users, groups, and permissions.
4. Inspect processes and manage services.
5. Install software and inspect logs.
6. Check networking, storage, and system health.
7. Combine commands into small shell scripts.

## 1. Shell and navigation

The shell reads commands and runs programs. A command often has the form `program options arguments`. The prompt's current directory affects relative paths; an absolute path starts at `/`.

```bash
pwd                  # Print the current directory
whoami               # Show the current user
ls                   # List visible files
ls -lah              # Long listing, including hidden files, with readable sizes
cd /var/log          # Change directory
cd ~                 # Go to your home directory
cd -                 # Return to the previous directory
```

Useful path ideas:

- `/` is the filesystem root; `/home` contains regular users' home directories.
- `~` means the current user's home directory.
- `.` means the current directory; `..` means its parent.
- `sudo` runs a command with elevated privileges. Use it only when the task requires it.

## 2. Files and directories

Use `mkdir` to create directories, `cp` to copy, `mv` to move or rename, and `rm` to remove. `rm` usually does not move files to a recoverable trash folder, so inspect the path before running it.

```bash
mkdir -p ~/linux-practice/notes
touch ~/linux-practice/notes/todo.txt
cp ~/linux-practice/notes/todo.txt ~/linux-practice/notes/todo-copy.txt
mv ~/linux-practice/notes/todo-copy.txt ~/linux-practice/notes/archive.txt
cat ~/linux-practice/notes/todo.txt
less /etc/os-release       # Read a file one screen at a time; press q to exit
head -n 5 /etc/os-release  # Show the first five lines
tail -n 20 /var/log/syslog # Show the last twenty lines (file may require sudo)
```

Find files by name and search text inside files:

```bash
find ~/linux-practice -type f -name '*.txt'
grep -n 'error' app.log
grep -Rni 'listen' ./config
```

Use quotes around paths containing spaces, such as `"my notes.txt"`. For commands that modify or delete files, verify the target first with `pwd` and `ls`.

## 3. Users, groups, and permissions

Linux assigns each process a user and group. File permissions control whether the owner, group, and other users can read (`r`), write (`w`), or execute (`x`) a file or directory. Directories need execute permission to be traversed.

```bash
id                         # Show user and group IDs
groups                     # Show your groups
ls -l file.txt             # Inspect owner and permission bits
stat file.txt              # Show detailed file metadata
```

Permission examples:

```bash
chmod u+x script.sh        # Add execute permission for the owner
chmod 640 config.txt       # Owner read/write; group read; others no access
chmod 750 deploy.sh        # Owner full access; group read/execute; others none
sudo chown ubuntu:ubuntu file.txt  # Change owner and group (example Ubuntu user)
```

Avoid `chmod 777`; it gives every local user write access. Use `sudo` for specific administrative operations, and do not make application files broadly writable to fix a permission error.

On a server, create a separate account for each person or service that needs access. For example, an administrator can create a user with `sudo adduser deployer`. Review the prompts and grant extra privileges only when they are needed. Do not disable your existing working access until you have confirmed the new account works.

## 4. Processes and services

A process is a running program. A service is a background program managed by the system service manager, typically `systemd` on Ubuntu.

```bash
ps aux                         # List processes
top                            # Interactive CPU and memory view; press q to exit
pgrep -a nginx                 # Find process IDs and commands matching nginx
```

Use `systemctl` to inspect and manage services:

```bash
systemctl status nginx --no-pager
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx
sudo systemctl enable nginx    # Start automatically at boot
sudo systemctl is-active nginx
```

Restarting a service can interrupt users. Check its status and logs after a change, and prefer reload when the service supports it and only configuration needs re-reading.

## 5. Packages and updates (Ubuntu)

APT installs software from configured package repositories. Refresh package metadata before installing or upgrading packages.

```bash
sudo apt update
apt search nginx
apt show nginx
sudo apt install nginx
sudo apt remove nginx
```

`apt update` refreshes the available package list; it does not upgrade installed packages. Review upgrade changes before accepting them on a server, especially if the service is important.

## 6. Logs and troubleshooting

Logs help explain what happened. `journalctl` reads systemd's journal; application logs may also be stored under `/var/log` or sent to a logging service.

```bash
sudo journalctl -u nginx --since today
sudo journalctl -u nginx -n 50 --no-pager
sudo journalctl -u nginx -f           # Follow new entries; press Ctrl-C to stop
sudo tail -f /var/log/nginx/error.log
```

A simple troubleshooting sequence:

1. Check whether the service is active with `systemctl status SERVICE`.
2. Read recent logs with `journalctl -u SERVICE -n 50 --no-pager`.
3. Check the process and resource use with `ps`, `top`, and `free -h`.
4. Check disk space with `df -h` and network listeners with `ss -lntp`.
5. Make one change, then check service status and logs again.

## 7. Networking

These commands inspect interfaces, routes, name resolution, listening ports, and HTTP responses.

```bash
ip addr                 # Show network interfaces and addresses
ip route                # Show routing table
hostname -I             # Show assigned IP addresses
getent hosts example.com  # Check name resolution
ss -lnt                 # Show listening TCP sockets
curl -I http://localhost # Request response headers from a local web service
```

For an EC2 server, Linux firewall rules are only one part of network access: also check the instance's AWS security group and subnet routing. Allow only the ports and source addresses the service needs. SSH typically uses TCP port 22; a public web server commonly uses 80 (HTTP) and/or 443 (HTTPS).

## 8. Storage and resource checks

```bash
df -h                  # Free/used space by mounted filesystem
du -sh ~/linux-practice # Approximate space used by a directory
free -h                # Memory usage
uptime                 # Uptime and load averages
lsblk                  # Block devices and mount points
```

`df` reports filesystem capacity; `du` estimates the size of files under a path. If a disk is full, find the source before deleting anything. Do not remove database files or system logs blindly.

## 9. Shell scripting basics

A shell script saves repeatable commands in a file. Start with a shebang, quote variable expansions, and use clear exit statuses.

```bash
#!/usr/bin/env bash
set -euo pipefail

CHECK_URL="${1:-http://localhost}"
if curl --fail --silent --show-error --max-time 5 "$CHECK_URL" >/dev/null; then
  echo "OK: $CHECK_URL is responding"
else
  echo "ERROR: $CHECK_URL did not respond" >&2
  exit 1
fi
```

Save as `health-check.sh`, then run:

```bash
chmod +x health-check.sh
./health-check.sh
./health-check.sh http://localhost:8080
```

The script exits with status `0` when the check succeeds and `1` when it fails. A nonzero status helps other scripts and automation detect failure.

## Practice exercises

1. Create a practice directory and a text file, then list and inspect it.
2. Create a shell script that prints the current user and date; make it executable.
3. Install Nginx on an Ubuntu VM, check its service status, and request its local page with `curl`.
4. Find the Nginx error log and inspect its latest entries.
5. Check disk and memory usage, then write down what each command reports.

Record your commands, output, and mistakes as you complete each exercise. Continue with the [Ubuntu EC2 App Server project](../Projects/linux-app-server/README.md) to apply these Linux skills on AWS.
