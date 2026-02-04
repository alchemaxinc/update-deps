terraform {
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "3.1.0"
    }
  }
}

resource "null_resource" "example" {
  triggers = {
    always_run = timestamp()
  }
}
