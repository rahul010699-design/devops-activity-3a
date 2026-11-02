
variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
  default     = "lunar-works-316500"
}

variable "region" {
  description = "Google Cloud deployment region"
  type        = string
  default     = "asia-south1"
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "activity-3a-api"
}

variable "repository_name" {
  description = "Artifact Registry repository name"
  type        = string
  default     = "activity-3a-images"
}
