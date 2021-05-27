import smtplib

carriers = {
	'att':    '@mms.att.net',
	'tmobile':' @tmomail.net',
	'verizon':  '@vzwpix.com',
	'sprint':   '@pm.sprint.com'
}

def send(message):
	try:
	        # Replace the number with your own, or consider using an argument\dict for multiple people.
	    to_numbers = ['2486603999{}'.format(carriers['verizon']), 
	    			  '2487978087{}'.format(carriers['verizon'])] 
	    			  #'2027172066{}'.format(carriers['sprint'])]
	    			  #'2489612358{}'.format(carriers['tmobile'])]
	    			  
	    auth = (email, password)
	    server = smtplib.SMTP( "smtp.gmail.com", 587 )
	    server.starttls()
	    server.login(auth[0], auth[1])
	    for to_number in to_numbers:
	    	server.sendmail(auth[0], to_number, '\r\n\r\n' + message)
	except:
		print("problem sending message")

#send("testing")

