terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Variables
variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "epoch5-app"
}

# Resource Group
resource "azurerm_resource_group" "epoch5_rg" {
  name     = "${var.app_name}-rg"
  location = var.location

  tags = {
    Environment = var.environment
    Project     = "EPOCH5"
    ManagedBy   = "Terraform"
  }
}

# Virtual Network
resource "azurerm_virtual_network" "epoch5_vnet" {
  name                = "${var.app_name}-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.epoch5_rg.location
  resource_group_name = azurerm_resource_group.epoch5_rg.name

  tags = {
    Environment = var.environment
  }
}

# Subnets
resource "azurerm_subnet" "epoch5_subnet" {
  name                 = "${var.app_name}-subnet"
  resource_group_name  = azurerm_resource_group.epoch5_rg.name
  virtual_network_name = azurerm_virtual_network.epoch5_vnet.name
  address_prefixes     = ["10.0.1.0/24"]

  delegation {
    name = "containerinstance"
    service_delegation {
      name    = "Microsoft.ContainerInstance/containerGroups"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action", "Microsoft.Network/virtualNetworks/subnets/prepareNetworkPolicies/action"]
    }
  }
}

# Network Security Group
resource "azurerm_network_security_group" "epoch5_nsg" {
  name                = "${var.app_name}-nsg"
  location            = azurerm_resource_group.epoch5_rg.location
  resource_group_name = azurerm_resource_group.epoch5_rg.name

  security_rule {
    name                       = "HTTP"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "8080"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = {
    Environment = var.environment
  }
}

# Associate NSG with subnet
resource "azurerm_subnet_network_security_group_association" "epoch5_nsg_association" {
  subnet_id                 = azurerm_subnet.epoch5_subnet.id
  network_security_group_id = azurerm_network_security_group.epoch5_nsg.id
}

# Container Registry
resource "azurerm_container_registry" "epoch5_acr" {
  name                = "${replace(var.app_name, "-", "")}acr"
  resource_group_name = azurerm_resource_group.epoch5_rg.name
  location            = azurerm_resource_group.epoch5_rg.location
  sku                 = "Standard"
  admin_enabled       = true

  tags = {
    Environment = var.environment
  }
}

# Application Insights
resource "azurerm_application_insights" "epoch5_insights" {
  name                = "${var.app_name}-insights"
  location            = azurerm_resource_group.epoch5_rg.location
  resource_group_name = azurerm_resource_group.epoch5_rg.name
  application_type    = "web"

  tags = {
    Environment = var.environment
  }
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "epoch5_workspace" {
  name                = "${var.app_name}-workspace"
  location            = azurerm_resource_group.epoch5_rg.location
  resource_group_name = azurerm_resource_group.epoch5_rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = {
    Environment = var.environment
  }
}

# Container Instance (Blue environment)
resource "azurerm_container_group" "epoch5_blue" {
  name                = "${var.app_name}-blue"
  location            = azurerm_resource_group.epoch5_rg.location
  resource_group_name = azurerm_resource_group.epoch5_rg.name
  ip_address_type     = "Public"
  dns_name_label      = "${var.app_name}-blue"
  os_type             = "Linux"
  subnet_ids          = [azurerm_subnet.epoch5_subnet.id]

  container {
    name   = var.app_name
    image  = "ghcr.io/epochcore5/epoch5-template:latest"
    cpu    = "1"
    memory = "2"

    ports {
      port     = 8080
      protocol = "TCP"
    }

    environment_variables = {
      ENVIRONMENT = "blue"
    }

    liveness_probe {
      http_get {
        path   = "/health"
        port   = 8080
        scheme = "Http"
      }
      initial_delay_seconds = 30
      period_seconds        = 10
      timeout_seconds       = 5
      failure_threshold     = 3
      success_threshold     = 1
    }

    readiness_probe {
      http_get {
        path   = "/health"
        port   = 8080
        scheme = "Http"
      }
      initial_delay_seconds = 10
      period_seconds        = 5
      timeout_seconds       = 3
      failure_threshold     = 3
      success_threshold     = 1
    }
  }

  image_registry_credential {
    server   = azurerm_container_registry.epoch5_acr.login_server
    username = azurerm_container_registry.epoch5_acr.admin_username
    password = azurerm_container_registry.epoch5_acr.admin_password
  }

  tags = {
    Environment = "${var.environment}-blue"
  }
}

# Container Instance (Green environment)
resource "azurerm_container_group" "epoch5_green" {
  name                = "${var.app_name}-green"
  location            = azurerm_resource_group.epoch5_rg.location
  resource_group_name = azurerm_resource_group.epoch5_rg.name
  ip_address_type     = "Public"
  dns_name_label      = "${var.app_name}-green"
  os_type             = "Linux"
  subnet_ids          = [azurerm_subnet.epoch5_subnet.id]

  container {
    name   = var.app_name
    image  = "ghcr.io/epochcore5/epoch5-template:latest"
    cpu    = "1"
    memory = "2"

    ports {
      port     = 8080
      protocol = "TCP"
    }

    environment_variables = {
      ENVIRONMENT = "green"
    }

    liveness_probe {
      http_get {
        path   = "/health"
        port   = 8080
        scheme = "Http"
      }
      initial_delay_seconds = 30
      period_seconds        = 10
      timeout_seconds       = 5
      failure_threshold     = 3
      success_threshold     = 1
    }

    readiness_probe {
      http_get {
        path   = "/health"
        port   = 8080
        scheme = "Http"
      }
      initial_delay_seconds = 10
      period_seconds        = 5
      timeout_seconds       = 3
      failure_threshold     = 3
      success_threshold     = 1
    }
  }

  image_registry_credential {
    server   = azurerm_container_registry.epoch5_acr.login_server
    username = azurerm_container_registry.epoch5_acr.admin_username
    password = azurerm_container_registry.epoch5_acr.admin_password
  }

  tags = {
    Environment = "${var.environment}-green"
  }
}

# Traffic Manager Profile
resource "azurerm_traffic_manager_profile" "epoch5_tm" {
  name                   = "${var.app_name}-tm"
  resource_group_name    = azurerm_resource_group.epoch5_rg.name
  traffic_routing_method = "Weighted"

  dns_config {
    relative_name = "${var.app_name}-tm"
    ttl           = 30
  }

  monitor_config {
    protocol                     = "HTTP"
    port                         = 8080
    path                         = "/health"
    interval_in_seconds          = 30
    timeout_in_seconds           = 10
    tolerated_number_of_failures = 3
  }

  tags = {
    Environment = var.environment
  }
}

# Traffic Manager Endpoints
resource "azurerm_traffic_manager_azure_endpoint" "epoch5_blue_endpoint" {
  name               = "blue-endpoint"
  profile_id         = azurerm_traffic_manager_profile.epoch5_tm.id
  target_resource_id = azurerm_container_group.epoch5_blue.id
  weight             = 100
}

resource "azurerm_traffic_manager_azure_endpoint" "epoch5_green_endpoint" {
  name               = "green-endpoint"
  profile_id         = azurerm_traffic_manager_profile.epoch5_tm.id
  target_resource_id = azurerm_container_group.epoch5_green.id
  weight             = 0
}

# Outputs
output "blue_container_fqdn" {
  description = "FQDN of the blue container group"
  value       = azurerm_container_group.epoch5_blue.fqdn
}

output "green_container_fqdn" {
  description = "FQDN of the green container group"
  value       = azurerm_container_group.epoch5_green.fqdn
}

output "traffic_manager_fqdn" {
  description = "FQDN of the traffic manager profile"
  value       = azurerm_traffic_manager_profile.epoch5_tm.fqdn
}

output "container_registry_login_server" {
  description = "Login server for the container registry"
  value       = azurerm_container_registry.epoch5_acr.login_server
}