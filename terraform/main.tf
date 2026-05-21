data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    # Matches exclusively standard AL2023 images, effectively avoiding 'bottlerocket' parsing errors
    values = ["al2023-ami-2023*-x86_64"]
  }
}

resource "aws_key_pair" "focus_ssh" {
  key_name   = "focus-ssh-key"
  public_key = file("~/.ssh/focus-ssh.pub")
}

resource "aws_instance" "focustrack_server" {
  ami           = data.aws_ami.al2023.id
  instance_type = var.instance_type
  key_name      = aws_key_pair.focus_ssh.key_name
  vpc_security_group_ids = [aws_security_group.focustrack_sg.id]

  user_data = <<-EOF
              #!/bin/bash
              # Update packages
              dnf update -y
              
              # Install Docker
              dnf install -y docker
              
              # Enable and start Docker service
              systemctl enable docker
              systemctl start docker
              
              # Add ec2-user to docker group
              usermod -aG docker ec2-user
              
              # Install Docker Compose plugin
              curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
              chmod +x /usr/local/bin/docker-compose
              ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
              EOF

  tags = {
    Name = "${var.project_name}-ec2"
  }
}