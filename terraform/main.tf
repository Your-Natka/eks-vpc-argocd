# ---------------------------------------------------------
# Lambda IAM role
# ---------------------------------------------------------

resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-lambda-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Principal = {
          Service = "lambda.amazonaws.com"
        }

        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ---------------------------------------------------------
# Lambda: ValidateData
# ---------------------------------------------------------

resource "aws_lambda_function" "validate" {
  function_name = "${var.project_name}-validate"

  role = aws_iam_role.lambda_exec.arn

  filename         = data.archive_file.validate.output_path
  source_code_hash = data.archive_file.validate.output_base64sha256

  handler = "validate.handler"
  runtime = "python3.12"

  timeout = 30
}

# ---------------------------------------------------------
# Lambda: LogMetrics
# ---------------------------------------------------------

resource "aws_lambda_function" "log_metrics" {
  function_name = "${var.project_name}-log-metrics"

  role = aws_iam_role.lambda_exec.arn

  filename         = data.archive_file.log_metrics.output_path
  source_code_hash = data.archive_file.log_metrics.output_base64sha256

  handler = "log_metrics.handler"
  runtime = "python3.12"

  timeout = 30
}

# ---------------------------------------------------------
# Step Functions IAM role
# ---------------------------------------------------------

resource "aws_iam_role" "stepfunction_exec" {
  name = "${var.project_name}-stepfunction-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Principal = {
          Service = "states.amazonaws.com"
        }

        Action = "sts:AssumeRole"
      }
    ]
  })
}

# ---------------------------------------------------------
# Step Functions permission to invoke Lambdas
# ---------------------------------------------------------

resource "aws_iam_role_policy" "stepfunction_invoke" {
  name = "${var.project_name}-invoke-lambdas"

  role = aws_iam_role.stepfunction_exec.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Action = [
          "lambda:InvokeFunction"
        ]

        Resource = [
          aws_lambda_function.validate.arn,
          aws_lambda_function.log_metrics.arn
        ]
      }
    ]
  })
}

# ---------------------------------------------------------
# Step Functions State Machine
# ---------------------------------------------------------

resource "aws_sfn_state_machine" "mlops_pipeline" {
  name     = "MLOpsPipeline"
  role_arn = aws_iam_role.stepfunction_exec.arn

  definition = jsonencode({
    Comment = "MLOps training workflow"

    StartAt = "ValidateData"

    States = {
      ValidateData = {
        Type = "Task"

        Resource = aws_lambda_function.validate.arn

        Next = "LogMetrics"
      }

      LogMetrics = {
        Type = "Task"

        Resource = aws_lambda_function.log_metrics.arn

        End = true
      }
    }
  })
}