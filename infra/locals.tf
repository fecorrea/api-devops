locals {
  common_tags = merge(var.tags, {
    environment = "shared"
  })

  image_name = "${var.image_repository}:${var.image_tag}"

  common_app_settings = {
    WEBSITES_PORT                       = "8000"
    WEBSITES_ENABLE_APP_SERVICE_STORAGE = "true"
    REPLAY_STORE_PATH                   = "/home/data/replay_store.db"
    API_KEY = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.api_key.versionless_id})"
    SECRET_KEY = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.secret_key.versionless_id})"
  }
}
