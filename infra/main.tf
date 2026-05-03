data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.common_tags
}

resource "azurerm_container_registry" "acr" {
  name                = var.container_registry_name
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = var.acr_sku_name
  admin_enabled       = true
  tags                = local.common_tags
}

resource "azurerm_service_plan" "plan" {
  name                = var.app_service_plan_name
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  os_type             = "Linux"
  sku_name            = var.app_service_sku_name
  tags                = local.common_tags
}

resource "azurerm_key_vault" "kv" {
  name                       = var.key_vault_name
  location                   = var.location
  resource_group_name        = azurerm_resource_group.rg.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  rbac_authorization_enabled  = true
  public_network_access_enabled = true
  tags                       = local.common_tags
}

resource "azurerm_key_vault_secret" "api_key" {
  name         = var.api_key_secret_name
  value        = var.api_key
  key_vault_id = azurerm_key_vault.kv.id

  depends_on = [azurerm_role_assignment.current_user_kv_secrets_officer]
}

resource "azurerm_key_vault_secret" "secret_key" {
  name         = var.secret_key_secret_name
  value        = var.secret_key
  key_vault_id = azurerm_key_vault.kv.id

  depends_on = [azurerm_role_assignment.current_user_kv_secrets_officer]
}

resource "azurerm_linux_web_app" "staging" {
  name                = var.staging_app_name
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  service_plan_id     = azurerm_service_plan.plan.id
  https_only          = true
  tags                = merge(local.common_tags, { environment = "staging" })

  identity {
    type = "SystemAssigned"
  }

  app_settings = merge(local.common_app_settings, {
    APP_ENV   = "staging"
    LOG_LEVEL = "DEBUG"
  })

  site_config {
    always_on         = true
    health_check_path = "/health"
    health_check_eviction_time_in_min = 2
    ftps_state        = "Disabled"
    minimum_tls_version = "1.2"

    application_stack {
      docker_image_name = "${var.image_repository}:${var.image_tag}"
      docker_registry_url = "https://${azurerm_container_registry.acr.login_server}"
      docker_registry_username = azurerm_container_registry.acr.admin_username
      docker_registry_password = azurerm_container_registry.acr.admin_password
    }
  }
}

resource "azurerm_linux_web_app" "production" {
  name                = var.production_app_name
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  service_plan_id     = azurerm_service_plan.plan.id
  https_only          = true
  tags                = merge(local.common_tags, { environment = "production" })

  identity {
    type = "SystemAssigned"
  }

  app_settings = merge(local.common_app_settings, {
    APP_ENV   = "production"
    LOG_LEVEL = "INFO"
  })

  site_config {
    always_on         = true
    health_check_path = "/health"
    health_check_eviction_time_in_min = 2
    ftps_state        = "Disabled"
    minimum_tls_version = "1.2"

    application_stack {
      docker_image_name = "${var.image_repository}:${var.image_tag}"
      docker_registry_url = "https://${azurerm_container_registry.acr.login_server}"
      docker_registry_username = azurerm_container_registry.acr.admin_username
      docker_registry_password = azurerm_container_registry.acr.admin_password
    }
  }
}

resource "azurerm_role_assignment" "current_user_kv_secrets_officer" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "staging_webapp_kv_secrets_user" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_linux_web_app.staging.identity[0].principal_id
}

resource "azurerm_role_assignment" "production_webapp_kv_secrets_user" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_linux_web_app.production.identity[0].principal_id
}
