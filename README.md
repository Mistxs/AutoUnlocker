# AutoUnlocker
 
The first project using Flask. The principle is to set up a local server through ngrok that listens for webhooks about record creation. If it turns out to be a record with prepayment, a request is sent to a special route for unlocking after 10 minutes.