output "public_ip" {
  description = "The public IP address of the FocusTrack AI server."
  value       = aws_instance.focustrack_server.public_ip
}

output "ssh_command" {
  description = "SSH command to connect to the instance."
  value       = "ssh -i \"~/.ssh/focus-ssh\" ec2-user@${aws_instance.focustrack_server.public_ip}"
}
