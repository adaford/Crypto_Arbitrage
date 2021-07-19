with open('/home/ec2-user/script/output.log', 'w') as f:
	f.truncate(0)
with open('/home/ec2-user/script/sms.log', 'w') as f:
	f.truncate(0)
	f.write('[[0,0,0,0,0]]')
