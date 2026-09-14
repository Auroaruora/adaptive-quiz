# Deployment

How the project runs on AWS, and the commands that put it there. Every
step was run by hand from the AWS CLI in `us-east-1`, so this is a record
to follow, not a script to execute: run twice, each create command fails
because the resource already exists. That is what Terraform or
CloudFormation are for, and out of scope here.

Secrets never appear in this file. Names, ids and hostnames do; the
security groups are what protect the resources, not the obscurity of
their names.

---

## Shape

```
browser ──► https://gradient-quiz.duckdns.org
                    │
                    ▼  Elastic IP, ports 80/443
              EC2 t4g.small, docker compose
                caddy ──► /api/*  ──► backend :8000
                      ──► the rest ──► frontend :3000
                                          │
                                          ▼  port 3306, VPC-internal only
                                  RDS MySQL 8.4 (db.t4g.micro, single AZ)
```

One EC2 instance runs three containers: Caddy in front, then the frontend
and backend behind it, from `docker-compose.yml` layered with
`docker-compose.prod.yml`. The database is a managed RDS instance in the
same default VPC, with no public address. The only route to it is from
the instance.

---

## Account setup (once)

- Account on the AWS Free plan: 100 USD of credit, ending 2027-03-13.
  When either runs out the account is suspended and the demo goes dark
  unless the plan is upgraded first.
- MFA on the root user (a passkey).
- An IAM user `aurora-admin` with `AdministratorAccess` and one access
  key, used only by the AWS CLI on the developer's machine. No console
  password; the console is used as root, behind MFA, for the few clicks
  that remain.
- `aws configure` with that key, region `us-east-1`, output `json`.

---

## Step 1 — Images

`backend/Dockerfile` and `frontend/Dockerfile`; see their headers. The
frontend bakes `NEXT_PUBLIC_API_URL` into the browser bundle at build
time, so the image is built for one API origin and rebuilt if it changes.

---

## Step 2 — Database

### Network

Everything lives in the region's default VPC. Two security groups: one
for the instance, created first so the other can reference it, and one
for the database that admits MySQL traffic only from members of the
first. That reference, rather than an IP range, is what keeps the
database unreachable from the internet.

```bash
VPC_ID=$(aws ec2 describe-vpcs --filters Name=is-default,Values=true \
  --query 'Vpcs[0].VpcId' --output text)

WEB_SG=$(aws ec2 create-security-group --group-name adaptive-quiz-web \
  --description "adaptive-quiz EC2 instance" --vpc-id "$VPC_ID" \
  --query GroupId --output text)

MY_IP=$(curl -s https://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress --group-id "$WEB_SG" \
  --protocol tcp --port 22 --cidr "$MY_IP/32"

DB_SG=$(aws ec2 create-security-group --group-name adaptive-quiz-db \
  --description "adaptive-quiz RDS, reachable only from the web group" \
  --vpc-id "$VPC_ID" --query GroupId --output text)

aws ec2 authorize-security-group-ingress --group-id "$DB_SG" \
  --protocol tcp --port 3306 --source-group "$WEB_SG"
```

The web group admits SSH from the developer's IP at the time. When that
IP changes, SSH stops working and this rule is the first thing to update.
Ports for serving the app are added in step 3.

### Instance

```bash
aws rds create-db-instance \
  --db-instance-identifier adaptive-quiz \
  --engine mysql \
  --engine-version 8.4.11 \
  --db-instance-class db.t4g.micro \
  --allocated-storage 20 \
  --storage-type gp3 \
  --storage-encrypted \
  --master-username "$RDS_USER" \
  --master-user-password "$RDS_PASSWORD" \
  --db-name "$RDS_DB" \
  --vpc-security-group-ids "$DB_SG" \
  --no-publicly-accessible \
  --no-multi-az \
  --backup-retention-period 1 \
  --tags Key=project,Value=adaptive-quiz

aws rds wait db-instance-available --db-instance-identifier adaptive-quiz
aws rds describe-db-instances --db-instance-identifier adaptive-quiz \
  --query 'DBInstances[0].Endpoint.Address' --output text
```

| Choice | Why |
| --- | --- |
| MySQL 8.4.11 | Same major as the local `mysql:8.4` pin; `docs/data-model.md` lists what would break below 8.0.16 |
| `db.t4g.micro` | Smallest class, ARM, cheapest; the bank is 54 questions |
| 20 GB gp3, encrypted | The minimum; encryption at rest is free |
| No public access | No public IP; only the security group route exists |
| Single AZ | A standby doubles cost and buys uptime a demo does not need |
| 1 day of backups | The minimum that still lets a mistake be undone |
| `--db-name` | Creates the schema on first boot, so Alembic has a target |

The master password was generated for this instance alone and lives in
the developer's password manager with the username, database name and
endpoint hostname. It was read into a shell variable rather than typed on
the command line so it never entered shell history.

Endpoint: `adaptive-quiz.c0pcemkgavdr.us-east-1.rds.amazonaws.com`, port
3306. This becomes `MYSQL_HOST` in the `.env` on the instance.

### What is deferred to step 3

Nothing can connect yet, by design. The first connection, the Alembic
upgrade and the seed all run from the EC2 instance using the backend
image, which is where the security group rule proves itself.

---

## Step 3 — Instance

### Shape on the server

Three containers under Docker Compose, from `docker-compose.yml` layered
with `docker-compose.prod.yml`: Caddy on 80 and 443, the frontend and the
backend behind it on the compose network. The browser sees one origin:
`/api/*` goes to the backend with the prefix stripped, everything else to
the frontend. Caddy obtains the TLS certificate itself once `SITE_ADDRESS`
is a hostname.

The hostname is `gradient-quiz.duckdns.org`, a free subdomain from
DuckDNS. It is a single A record pointed at the Elastic IP, updated by
hand because the IP never changes. It can be swapped for a bought domain
by changing three lines in the server's `.env`.

Images are built on the instance from a clone of the public GitHub repo.
Building on the box keeps the moving parts to one machine; pushing
prebuilt images to ECR is the natural next step and is noted in Phase 7.

### Sizing

`t4g.small`: 2 GB of memory on ARM. The frontend build needs more than
the micro's 1 GB, and ARM matches the developer's machine, so the images
tested locally are the images that run. A 2 GB swap file is added as
margin. Root volume 20 GB gp3, since each rebuild briefly holds two copies
of each image.

### Commands

An SSH key generated locally and only the public half imported, so the
private key never leaves the developer's machine:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/adaptive-quiz -C adaptive-quiz
aws ec2 import-key-pair --key-name adaptive-quiz \
  --public-key-material fileb://~/.ssh/adaptive-quiz.pub
```

The web security group from step 2 gains the two public ports:

```bash
WEB_SG=$(aws ec2 describe-security-groups \
  --filters Name=group-name,Values=adaptive-quiz-web \
  --query 'SecurityGroups[0].GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id "$WEB_SG" \
  --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id "$WEB_SG" \
  --protocol tcp --port 443 --cidr 0.0.0.0/0
```

The current Ubuntu 24.04 ARM image, looked up rather than hard-coded
because AMI ids change with every patch release:

```bash
AMI=$(aws ssm get-parameters --names \
  /aws/service/canonical/ubuntu/server/24.04/stable/current/arm64/hvm/ebs-gp3/ami-id \
  --query 'Parameters[0].Value' --output text)
```

The instance:

```bash
INSTANCE=$(aws ec2 run-instances \
  --image-id "$AMI" \
  --instance-type t4g.small \
  --key-name adaptive-quiz \
  --security-group-ids "$WEB_SG" \
  --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=20,VolumeType=gp3}' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=adaptive-quiz},{Key=project,Value=adaptive-quiz}]' \
  --query 'Instances[0].InstanceId' --output text)
aws ec2 wait instance-running --instance-ids "$INSTANCE"
```

An Elastic IP, so the address survives stops and restarts and the DNS
record is set once:

```bash
read -r ALLOC PUBLIC_IP < <(aws ec2 allocate-address --domain vpc \
  --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=adaptive-quiz}]' \
  --query '[AllocationId,PublicIp]' --output text)
aws ec2 associate-address --instance-id "$INSTANCE" --allocation-id "$ALLOC"
echo "$PUBLIC_IP"
```

Then, on duckdns.org, paste `PUBLIC_IP` into the current ip field for
`gradient-quiz` and click update ip.

Elastic IP: `3.220.9.193`.

### On the instance

```bash
ssh -i ~/.ssh/adaptive-quiz ubuntu@"$PUBLIC_IP"
```

Once in, `scripts/server-setup.sh` installs Docker, adds swap and clones
the repo; it is fetched from GitHub because the checkout does not exist
yet. Log out and back in afterwards so the docker group applies.

Write `~/adaptive-quiz/.env` with these keys. The MySQL values are the RDS
credentials from step 2; the rest describe the public origin:

```
MYSQL_HOST=adaptive-quiz.c0pcemkgavdr.us-east-1.rds.amazonaws.com
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_DATABASE=
SITE_ADDRESS=gradient-quiz.duckdns.org
NEXT_PUBLIC_API_URL=https://gradient-quiz.duckdns.org/api
CORS_ORIGINS=https://gradient-quiz.duckdns.org
```

Then `scripts/deploy.sh`: it builds the images, applies the migrations
against RDS, and starts Caddy, the backend and the frontend. The first
connection to the database happens in the migration step, which is where
the security-group rule from step 2 is proven. Seeding is a one-time
load, run by hand once the schema exists:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  --profile app run --rm --no-deps backend python scripts/seed.py
```

Redeploying after a push is `scripts/deploy.sh` again.

### Elastic IP and cost

An Elastic IP is free while attached to a running instance and billed
hourly while it is not. Stopping the instance to save money keeps the IP
attached; terminating the instance without releasing the IP is the case
that costs.
