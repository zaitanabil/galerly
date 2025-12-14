# Creating Your First AWS IAM Admin User

## You Have: Root Email + Password + Account ID
## You Need: Access Keys to run automation

**Never use root credentials for automation. Create an admin IAM user first.**

---

## Step 1: Sign in to AWS Console

1. Go to: https://console.aws.amazon.com/
2. Click **"Sign in to the Console"**
3. Select **"Root user"**
4. Enter your **root email address**
5. Enter your **root password**
6. Complete MFA if enabled

---

## Step 2: Create Initial Admin User (via Console)

### A. Go to IAM Service

1. In AWS Console, search for **"IAM"** in top search bar
2. Click **"IAM"** to open IAM Dashboard

### B. Create User

1. In left sidebar, click **"Users"**
2. Click **"Create user"** button
3. **User name:** `your-name-admin` (e.g., `nz-admin`)
4. Click **"Next"**

### C. Set Permissions

1. Select **"Attach policies directly"**
2. Search for and select: **"AdministratorAccess"**
3. Click **"Next"**

### D. Review and Create

1. Review settings
2. Click **"Create user"**
3. ✓ User created!

---

## Step 3: Generate Access Keys

### A. Open User

1. Click on your newly created user name
2. Click **"Security credentials"** tab

### B. Create Access Key

1. Scroll to **"Access keys"** section
2. Click **"Create access key"**
3. Select **"Command Line Interface (CLI)"**
4. Check the box: "I understand..."
5. Click **"Next"**
6. (Optional) Add description: "Local development"
7. Click **"Create access key"**

### C. Save Credentials

⚠️ **CRITICAL: Save these now - you can't see them again!**

```
Access Key ID: AKIA...
Secret Access Key: ...
```

**Options to save:**
- Click **"Download .csv file"** (recommended)
- Copy both values to a secure note
- Take a screenshot (delete after saving securely)

8. Click **"Done"**

---

## Step 4: Configure AWS CLI

Now use these credentials:

```bash
aws configure
```

Enter when prompted:
```
AWS Access Key ID: AKIA... (paste your access key)
AWS Secret Access Key: ... (paste your secret key)
Default region name: us-east-1
Default output format: json
```

**Test it:**
```bash
aws sts get-caller-identity
```

Should show:
```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-name-admin"
}
```

---

## Step 5: Run Galerly IAM Setup

Now you can run the automation:

```bash
cd /Users/nz-dev/Desktop/business/galerly.com
.github/scripts/create-iam-setup.sh
```

This creates the 3 Galerly-specific users with proper permissions.

---

## Alternative: Use Root Access Keys (NOT RECOMMENDED)

If you absolutely must use root credentials:

### Generate Root Access Keys

1. In AWS Console (signed in as root)
2. Click your account name (top right)
3. Click **"Security credentials"**
4. Scroll to **"Access keys"**
5. Click **"Create access key"**
6. ⚠️ Warning will appear - acknowledge it
7. Save the keys
8. Use with `aws configure`

**⚠️ Security Risk:**
- Root has unlimited access
- Cannot be restricted
- Should only be used for initial setup
- **Delete root access keys immediately after creating admin user**

---

## Summary

### What You're Doing

1. **Root account** → Create admin IAM user
2. **Admin user** → Get access keys
3. **Access keys** → Configure AWS CLI
4. **AWS CLI** → Run Galerly automation
5. **Automation** → Creates 3 Galerly users

### Why This Way

- ✓ Root account stays secure
- ✓ Admin user can create other users
- ✓ Access keys can be rotated
- ✓ Follows AWS best practices

---

## Quick Console Path

```
AWS Console (root login)
  ↓
IAM → Users → Create user
  ↓
User name: nz-admin
  ↓
Attach policies: AdministratorAccess
  ↓
Create user
  ↓
Security credentials → Create access key
  ↓
Choose: CLI
  ↓
Copy Access Key ID + Secret Access Key
  ↓
Terminal: aws configure
  ↓
Terminal: .github/scripts/create-iam-setup.sh
```

---

## Troubleshooting

### "I can't find IAM in console"
- Direct link: https://console.aws.amazon.com/iam/
- Or search "IAM" in top search bar

### "AdministratorAccess not found"
- Type "AdministratorAccess" in search box
- Make sure to select the checkbox next to it

### "Access key creation failed"
- Root account may have max keys already
- Go to Security credentials → Delete old access keys first

### "aws configure not found"
- Install AWS CLI: `brew install awscli`
- Or download from: https://aws.amazon.com/cli/

---

## After Setup

Once you have AWS CLI configured:

```bash
# Verify
aws sts get-caller-identity

# Create Galerly IAM users
.github/scripts/create-iam-setup.sh

# Update GitHub
.github/scripts/update-github-with-cicd-keys.sh

# Verify
.github/scripts/verify-iam-setup.sh
```

---

## Need Help?

If you get stuck:

1. **Check AWS docs:** https://docs.aws.amazon.com/IAM/latest/UserGuide/getting-started.html
2. **Verify AWS CLI:** `aws --version`
3. **Check credentials:** `cat ~/.aws/credentials`
4. **Test access:** `aws sts get-caller-identity`

---

## Security Checklist

After everything works:

- [ ] Root MFA enabled
- [ ] Root access keys deleted (if created)
- [ ] Admin user has MFA (optional but recommended)
- [ ] Access keys saved securely
- [ ] `.github/credentials/` is gitignored
- [ ] Never commit credentials to git
