data "aws_vpc" "default" {
  default = true
}

resource "aws_security_group" "focustrack_sg" {
  name        = "${var.project_name}-sg"
  description = "Security group for FocusTrack AI"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "Allow App Traffic"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
