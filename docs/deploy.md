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
browser ──► EC2 (frontend :3000, backend :8000, docker compose)
                    │
                    ▼  port 3306, VPC-internal only
              RDS MySQL 8.4 (db.t4g.micro, single AZ)
```

One EC2 instance runs both containers from `docker-compose.yml` with the
`app` profile. The database is a managed RDS instance in the same default
VPC, with no public address. The only route to it is from the instance.

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
