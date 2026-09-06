output "validate_lambda_arn" {
  description = "ARN of the validation Lambda"
  value       = aws_lambda_function.validate.arn
}

output "log_metrics_lambda_arn" {
  description = "ARN of the metrics logging Lambda"
  value       = aws_lambda_function.log_metrics.arn
}

output "step_function_arn" {
  description = "ARN of the MLOps Step Function"
  value       = aws_sfn_state_machine.mlops_pipeline.arn
}