output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.rg.name
}

output "acr_login_server" {
  description = "ACR login server"
  value       = azurerm_container_registry.acr.login_server
}

output "key_vault_uri" {
  description = "Key Vault URI"
  value       = azurerm_key_vault.kv.vault_uri
}

output "staging_url" {
  description = "Staging app URL"
  value       = "https://${azurerm_linux_web_app.staging.default_hostname}"
}

output "production_url" {
  description = "Production app URL"
  value       = "https://${azurerm_linux_web_app.production.default_hostname}"
}

output "staging_app_name" {
  description = "Staging app name"
  value       = azurerm_linux_web_app.staging.name
}

output "production_app_name" {
  description = "Production app name"
  value       = azurerm_linux_web_app.production.name
}
