#!/bin/bash

# AWS Service Cleanup Verification Script
# Run this to ensure all expensive services are deleted

echo "🔍 VERIFYING AWS CLEANUP - Checking for running services..."
echo "============================================================"
echo ""

# Check RDS instances
echo "1️⃣  Checking RDS Instances..."
RDS_INSTANCES=$(aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier,DBInstanceStatus]' --output table 2>/dev/null)
if [ -z "$RDS_INSTANCES" ] || echo "$RDS_INSTANCES" | grep -q "None"; then
    echo "   ✅ No RDS instances found"
else
    echo "   ❌ RDS INSTANCES STILL RUNNING:"
    echo "$RDS_INSTANCES"
    echo ""
    echo "   💡 Delete with: aws rds delete-db-instance --db-instance-identifier <NAME> --skip-final-snapshot"
fi
echo ""

# Check ElastiCache clusters
echo "2️⃣  Checking ElastiCache Clusters..."
ELASTICACHE=$(aws elasticache describe-cache-clusters --query 'CacheClusters[*].[CacheClusterId,CacheClusterStatus]' --output table 2>/dev/null)
if [ -z "$ELASTICACHE" ] || echo "$ELASTICACHE" | grep -q "None"; then
    echo "   ✅ No ElastiCache clusters found"
else
    echo "   ❌ ELASTICACHE STILL RUNNING:"
    echo "$ELASTICACHE"
    echo ""
    echo "   💡 Delete with: aws elasticache delete-cache-cluster --cache-cluster-id <ID>"
fi
echo ""

# Check WAF WebACLs
echo "3️⃣  Checking AWS WAF WebACLs..."
WAF_GLOBAL=$(aws wafv2 list-web-acls --scope CLOUDFRONT --region us-east-1 --query 'WebACLs[*].[Name,Id]' --output table 2>/dev/null)
WAF_REGIONAL=$(aws wafv2 list-web-acls --scope REGIONAL --query 'WebACLs[*].[Name,Id]' --output table 2>/dev/null)

if ([ -z "$WAF_GLOBAL" ] || echo "$WAF_GLOBAL" | grep -q "None") && ([ -z "$WAF_REGIONAL" ] || echo "$WAF_REGIONAL" | grep -q "None"); then
    echo "   ✅ No WAF WebACLs found"
else
    echo "   ⚠️  WAF WebACLs found:"
    if [ ! -z "$WAF_GLOBAL" ]; then
        echo "   GLOBAL (CloudFront):"
        echo "$WAF_GLOBAL"
    fi
    if [ ! -z "$WAF_REGIONAL" ]; then
        echo "   REGIONAL:"
        echo "$WAF_REGIONAL"
    fi
    echo ""
    echo "   💡 Note: Basic WAF rules may be acceptable. Check if they're necessary."
fi
echo ""

# Check EC2 instances
echo "4️⃣  Checking EC2 Instances..."
EC2_INSTANCES=$(aws ec2 describe-instances --query 'Reservations[*].Instances[?State.Name!=`terminated`].[InstanceId,InstanceType,State.Name]' --output table 2>/dev/null)
if [ -z "$EC2_INSTANCES" ] || echo "$EC2_INSTANCES" | grep -q "None"; then
    echo "   ✅ No EC2 instances running"
else
    echo "   ❌ EC2 INSTANCES STILL RUNNING:"
    echo "$EC2_INSTANCES"
    echo ""
    echo "   💡 Stop with: aws ec2 stop-instances --instance-ids <ID>"
    echo "   💡 Terminate with: aws ec2 terminate-instances --instance-ids <ID>"
fi
echo ""

# Check NAT Gateways (expensive!)
echo "5️⃣  Checking NAT Gateways..."
NAT_GATEWAYS=$(aws ec2 describe-nat-gateways --query 'NatGateways[?State==`available`].[NatGatewayId,State]' --output table 2>/dev/null)
if [ -z "$NAT_GATEWAYS" ] || echo "$NAT_GATEWAYS" | grep -q "None"; then
    echo "   ✅ No NAT Gateways found"
else
    echo "   ❌ NAT GATEWAYS STILL RUNNING ($0.045/hour = $32/month each!):"
    echo "$NAT_GATEWAYS"
    echo ""
    echo "   💡 Delete with: aws ec2 delete-nat-gateway --nat-gateway-id <ID>"
fi
echo ""

# Check EBS Volumes (unattached)
echo "6️⃣  Checking Unattached EBS Volumes..."
EBS_VOLUMES=$(aws ec2 describe-volumes --filters Name=status,Values=available --query 'Volumes[*].[VolumeId,Size,State]' --output table 2>/dev/null)
if [ -z "$EBS_VOLUMES" ] || echo "$EBS_VOLUMES" | grep -q "None"; then
    echo "   ✅ No unattached EBS volumes"
else
    echo "   ⚠️  Unattached EBS volumes found ($0.10/GB/month):"
    echo "$EBS_VOLUMES"
    echo ""
    echo "   💡 Delete with: aws ec2 delete-volume --volume-id <ID>"
fi
echo ""

# Check Load Balancers
echo "7️⃣  Checking Load Balancers..."
ALB=$(aws elbv2 describe-load-balancers --query 'LoadBalancers[*].[LoadBalancerName,State.Code]' --output table 2>/dev/null)
if [ -z "$ALB" ] || echo "$ALB" | grep -q "None"; then
    echo "   ✅ No Application Load Balancers found"
else
    echo "   ❌ LOAD BALANCERS STILL RUNNING ($16-22/month each):"
    echo "$ALB"
    echo ""
    echo "   💡 Delete with: aws elbv2 delete-load-balancer --load-balancer-arn <ARN>"
fi
echo ""

# Summary
echo "============================================================"
echo "📊 COST ESTIMATE FOR CURRENT RUNNING SERVICES:"
echo "============================================================"
echo ""
echo "If all ✅ above: Expected monthly cost: \$1-3"
echo "If any ❌ remain: Each service adds \$16-100/month"
echo ""
echo "💡 TIPS TO REDUCE COSTS:"
echo "   • CloudWatch: Delete old log groups"
echo "   • S3: Enable Intelligent-Tiering for old photos"
echo "   • Lambda: Already on free tier (1M requests/month)"
echo "   • DynamoDB: Already on free tier (25GB)"
echo ""
echo "✅ Verification complete!"

