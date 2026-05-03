variable "location" {
  description = "Azure region where resources will be created"
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
  default     = "ApiDevOps-RG"
}

variable "name_prefix" {
  description = "Prefix used to build resource names"
  type        = string
  default     = "apidevops-fcorrea"
}

variable "container_registry_name" {
  description = "ACR name"
  type        = string
  default     = "apidevops-fcorrea-acr"
}

variable "app_service_plan_name" {
  description = "App Service Plan name"
  type        = string
  default     = "apidevops-fcorrea-plan"
}

variable "staging_app_name" {
  description = "Staging Web App name"
  type        = string
  default     = "apidevops-fcorrea-staging"
}

variable "production_app_name" {
  description = "Production Web App name"
  type        = string
  default     = "apidevops-fcorrea-prod"
}

variable "key_vault_name" {
  description = "Key Vault name"
  type        = string
  default     = "apidevops-fcorrea-kv"
}

variable "app_service_sku_name" {
  description = "Linux App Service Plan SKU"
  type        = string
  default     = "S1"
}

variable "acr_sku_name" {
  description = "Azure Container Registry SKU"
  type        = string
  default     = "Basic"
}

variable "image_repository" {
  description = "Docker image repository name"
  type        = string
  default     = "devops-api"
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

variable "api_key_secret_name" {
  description = "Key Vault secret name for API key"
  type        = string
  default     = "api-key"
}

variable "secret_key_secret_name" {
  description = "Key Vault secret name for JWT secret"
  type        = string
  default     = "secret-key"
}

variable "api_key" {
  description = "API key value for the application"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "JWT secret key value for the application"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default = {
    project   = "DevOpsApiFCorrea"
    managedBy = "Terraform-fcorrea"
  }
}
