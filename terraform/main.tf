terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.10.0" 
}

provider "aws" {
  region = "us-east-1" 
}

resource "aws_vpc" "honeypot_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = {
    Name = "Deception-Network-VPC"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.honeypot_vpc.id
}

resource "aws_subnet" "public_trap_subnet" {
  vpc_id                  = aws_vpc.honeypot_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true 
  tags = {
    Name = "Trap-Subnet-Public"
  }
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.honeypot_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
}

resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public_trap_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

# --- NEW: AWS WAF IP Set for the Python Brain to control ---

resource "aws_wafv2_ip_set" "deception_blocklist" {
  name               = "DeceptionBlocklist"
  description        = "Malicious IPs automatically captured by the Go Honeypot"
  scope              = "REGIONAL" 
  ip_address_version = "IPV4"

  addresses = []
}

output "waf_ipset_id" {
  value       = aws_wafv2_ip_set.deception_blocklist.id
  description = "Copy this ID into your main.py file"
}