from shutil import copyfile
import SMS
import json
import ast


recent_text = False
s = set()
with open('/home/ec2-user/script/sms.log') as f:
	l1 = []
	for line in f:
		currentPlace = line[:-1]
		l1.append(currentPlace)

	try:
		l1 = ast.literal_eval(l1[0]+']')
	except:
		print(l1)

	if l1 != [[0,0,0,0,0]]: #and l1!= ['[0,0,0,0,0]'] and l1 != ['[0, 0, 0, 0, 0]']:
		recent_text = True
		for a in l1:
			s.add(a[0])
with open('/home/ec2-user/script/output.log') as f:
	l = []
	for line in f:
		currentPlace = line[:-1]
		l.append(currentPlace)
	try:
		l = ast.literal_eval(l[0]+']')
	except:
		print(l)

	if l == [[0,0,0,0,0]]:# or l == ['[0,0,0,0]'] or l == ['[0, 0, 0, 0]']:
		if recent_text:
			SMS.send("All coins now leveled out")
			copyfile('/home/ec2-user/script/output.log', '/home/ec2-user/script/sms.log')
		exit(0)

	for a in l:
		#print(a,l)
		if a[0] not in s:
			#print(a,a[0],s,l,l1)
			copyfile('/home/ec2-user/script/output.log', '/home/ec2-user/script/sms.log')
			with open('/home/ec2-user/script/sms.log') as g:
				SMS.send(g.read())
				exit(0)
