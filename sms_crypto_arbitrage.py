from shutil import copyfile
import SMS
import json


recent_text = False
s = set()
with open('/home/ec2-user/script/sms.log') as f:
	l = json.load(f)
	print(l)
	if l != [0,0,0,0,0]:#['[0,0,0,0,0]'] and l != ['[0, 0, 0, 0, 0]'] and l != :
		recent_text = True
		for a in l:
			s.add(a[0])

with open('/home/ec2-user/script/output.log') as f:
	l = json.load(f)
	if l == [0,0,0,0,0]:#['[0,0,0,0]'] or x == ['[0, 0, 0, 0]']:
		if recent_text:
			SMS.send("All coins now leveled out")
			copyfile('/home/ec2-user/script/output.log', '/home/ec2-user/script/sms.log')
		exit(0)
	for a in l:
		if a[0] not in s:
			copyfile('/home/ec2-user/script/output.log', '/home/ec2-user/script/sms.log')
			with open('/home/ec2-user/script/sms.log') as g:
				SMS.send(g.read())
				exit(0)

