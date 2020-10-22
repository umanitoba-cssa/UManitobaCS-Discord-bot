# UManitobaCS-Discord-bot
A custom bot for the University of Manitoba's Computer Science Discord server. 


## Ideas/What I want this bot to do.   
- Custom welcome messages that change depending on the invite joined with 
- manage invites 
- Check forum responses and send out invites automatically  
    - flag invalid responses, non-UM email, already filled out the form, etc 
    - use code from the existing script 
    - a way to manage flagged responses within the discord 
- auto assign roles to people who joined with certain invites (as in don't give a role to someone who joined for an event) 
    - assign student/alumni roles, maybe year roles too? 
    - include a year(s) question in the forum? 
- prep event channels through a command 
- colours & year roles like we have now 
- mod commands to mute users? 
- only allow commands from users with the Student or Alumni roles 
- generate special invite for events through a command (not a temp invite)
    - Gives whoever joins a 'event' role that has limited access. 
    - auto kicks all users who have that role after 12am the day of the event

---

### User Commands:
#### Registered users:
- `.colour {colour}`
    - sets the users color, leave colour blank or `.colour remove` to remove 
    - setting a colour removes the current set colour first 

- `.setyear {n}` 
    - 0 < n <= 4 
    - can have multiple, mainly used to allow users to view class specific classes 

#### All users 
- `.form`
    - respond with the link to the sign-up form

- `.wics`
    - respond with info about wics (dm?)

- `.cssa`
    - respond with info about cssa 

- `.devclub`
    - respond with info about devclub

### Admin Commands:

- `.form greeting {message}`
    - set the message that displays when someone joins through the form

- `.colour delete {colour}`
    - remove the given colour 

- `.colour add {colour}`
    - add the given colour for users to use with `.colour`

- `.info wics {message}`
    - set the text to be displayed when `.wics is run`

- `.info cssa {message}`
    - set the text to be displayed when `.cssa is run`

- `.info devclub {message}`
    - set the text to be displayed when `.devclub is run`


#### Events:
- `.event prep {title} text:{n} voice:{n} -p`
    - title = Name of the event 
    - text:n = number of text channels 
    - voice:n = number of voice channels 
    - -p (optional) = set the channels to public on creation 

- `.event open` 
    - sets all event channels to public 

- `.event close`
    - sets all event channels to private

- `.event cleanup`
    - delete invite/channels related to the current event 

- `.event invite` 
    - Generates a temporary invite that lasts until 12am the day of creation

- `.event greeting {message}`
    - set the message that displays when someone joins with an event invite