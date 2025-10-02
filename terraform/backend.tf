terraform {
  required_version = ">= 1.5.0"

  backend "s3" {
    bucket  = "raonileite-terraform-state"
    key     = "vpc-api/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}