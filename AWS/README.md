# AWS Learning Notes

Notes and hands-on exercises for cloud infrastructure and services on Amazon Web Services.

## Topics

- Identity and access management
- Compute, storage, and networking
- Infrastructure deployment
- Monitoring, security, and cost management

## Amazon EC2

### Understand instance status checks

In the EC2 console, select an instance and review its **Status checks**. The standard instance health checks are:

| Check | What it monitors | If it fails |
|---|---|---|
| **System status check** | AWS infrastructure supporting the instance, such as the host, power, or network | Check AWS Health and instance events. For an EBS-backed instance, a stop/start may move it to a healthy host; a reboot usually does not. |
| **Instance status check** | The guest operating system and its network configuration | Investigate boot, OS, memory, filesystem, and network problems. Use the system log, EC2 Serial Console, or Systems Manager if available. |

Both standard checks passing means AWS can reach the host and the instance. It does not confirm that an application such as Nginx is running or responding correctly; check the service and its endpoint separately.

The console may show an additional EBS status check for supported configurations. This check monitors attached EBS volume reachability and is separate from the two standard checks. The number of checks displayed can vary, so “3/3 checks passed” is not a universal EC2 health indicator.

New instances can show checks as **Initializing** while AWS completes its monitoring. Wait for initialization to finish, then investigate any failed check using the failure type rather than relying only on the total count.

### Public IPv4 addresses and Elastic IPs

An automatically assigned public IPv4 address can change after an instance is stopped and started. If clients need a stable IPv4 address, an Elastic IP address can be allocated and associated with the instance, then remapped to a replacement instance if needed.

An Elastic IP is not required for a domain name. DNS can point to an address that changes, but records may need updating; a stable address or an appropriate DNS/load-balancing design avoids that operational work. Consider whether an Elastic IP is appropriate for the workload, and review current public IPv4 pricing: AWS may charge for public IPv4 addresses, including Elastic IPs.

When an Elastic IP is no longer needed, disassociate it if necessary and release it from the account. Terminating an instance does not necessarily release a separately allocated Elastic IP.

### Create a Linux user

Connect to the Ubuntu instance using an account with administrative privileges, then create a user. Replace `mahesh` with the username you want:

```bash
sudo adduser mahesh
```

On Ubuntu, `adduser` creates the account and home directory and prompts you to set a password. Optional profile details can be left blank.

Grant administrative privileges only if the user needs them:

```bash
sudo usermod -aG sudo mahesh
```

Switch to the new user's login shell to verify the account:

```bash
sudo -iu mahesh
whoami
```

The final command should print the new username. Use `exit` to return to the previous shell. Adding a user to `sudo` grants broad administrative access; only do this for trusted users who require it. Creating a local password does not by itself enable password-based SSH authentication. Prefer SSH keys or Systems Manager, and do not weaken the instance's SSH configuration just to use the new password.

## Project guide

See the [Ubuntu EC2 and Nginx app server guide](../Projects/linux-app-server/README.md) for a Console-based launch walkthrough, Nginx installation and checks, and teardown steps.
