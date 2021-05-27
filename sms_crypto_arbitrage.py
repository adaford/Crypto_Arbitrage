from shutil import copyfile
import SMS
import ast


recent_text = False
s = set()
with open('/home/ec2-user/script/sms.log') as f:
	x = f.read().splitlines()
	for a in x:
		s.add(a[1])
	if 0 not in s and '0' not in s:
		recent_text = True

with open('/home/ec2-user/script/output.log') as f:
	x = f.read().splitlines()
	if x == ['[0,0,0,0]'] or x == ['[0, 0, 0, 0]']:
		if recent_text == True:
			SMS.send("All coins now leveled out")
			copyfile('/home/ec2-user/script/output.log', '/home/ec2-user/script/sms.log')
		exit(0)
	for a in x:
		if a[1] not in s:
			copyfile('/home/ec2-user/script/output.log', '/home/ec2-user/script/sms.log')
			with open('/home/ec2-user/script/sms.log') as g:
				SMS.send(g.read())
				exit(0)
