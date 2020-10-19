# UManitobaCS-Discord-bot
A custom bot for the University of Manitoba's Computer Science Discord server. 



## Ideas/What I want this bot to do.   
- Custom welcome messages that change depending on the invite joined with 
- generate temp invite through a command (for events) 
- manage invites 
- Check forum responses and send out invites automatically  
    - flag invalid responses, non-UM email, already filled out the form, etc 
    - use code from the existing script  
- auto assign roles to people who joined with certain invites (as in don't give a role to someone who joined for an event) 
    - assign student/alumni roles, maybe year roles too? 
    - include a year(s) question in the forum? 
- prep event channels through a command 
- manage problematic forms through a private discord channel 
- colours & year roles like we have now 
- mod commands to mute users? 
- only allow commands from users with the Student or Alumni roles 

### User Commands:
- `.colour {colour}`
    - sets the users color, leave colour blank or `.colour remove` to remove 
    - setting a colour removes the current set colour first 

- `.setyear {n}` 
    - 0 < n <= 4 
    - can have multiple, mainly used to allow users to view class specific classes 

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
    - Generates a temporary invite that lasts until after 12am

- `.event greeting {message}`
    - set the message that displays when someone joins with an event invite