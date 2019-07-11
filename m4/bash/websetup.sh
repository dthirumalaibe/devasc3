# TASK 1: Update hostname (CLI arg)
hostname "$1"

# TASK 2: Install httpd
yum install -y httpd

# TASK 3: Update HTML h1 header (CLI arg)
sed -i "s:<h1>.*</h1>:<h1>$1</h1>:g" \
  /usr/share/httpd/noindex/index.html

# TASK 4: Start httpd
systemctl start httpd

# TASK 5: Add webadmin user
useradd -m -s /bin/bash webadmin
echo webpass | passwd webadmin --stdin

# TASK 6: Allow SSH password auth
sed -i "s/PasswordAuthentication no/PasswordAuthentication yes/g" \
  /etc/ssh/sshd_config
systemctl restart sshd
