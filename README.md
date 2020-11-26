# UManitobaCS-Discord-bot
A custom bot for the University of Manitoba's Computer Science Discord server. 


## Ideas/What I want this bot to do.   
- manage invites 
- Check forum responses and send out invites automatically  
    - flag invalid responses, non-UM email, already filled out the form, etc 
    - use code from the existing script 
    - a way to manage flagged responses within the discord 
- auto assign roles to people who joined with certain invites
    - assign student/alumni roles, 
    - maybe year roles too, include a year(s) question in the forum? 
- prep event channels through a command 
- colours & year roles like we have now 
- generate special invite for events through a command (not a temp invite)
    - Gives whoever joins a 'event' role that has limited access. 
    - auto kicks all users who have that role after 12am the day of the event

---

Commands with a '*' have not been implemented yet

### User Commands:
#### Registered users:

- `.iam {colour}`
    - sets the users color, `.iamn colour` to remove 
    - setting a colour removes the current set colour first 

- `.iam {year}` 
    - year = first,second,third,fourth
    - Used to gain access to the course channels of the given year
    - Can have multiple  

- `.iamn {colour}`
    - removes colour role from user

- `.iamn {year}`
    - removes year role from user

- `.notify {category}`
    - gives the user a role specific to an announcement type
    - will be automatic once forum integration is added

- `.unnotify {category}`
    - removes an announcement role from a user

#### All users 
- *`.form`
    - respond with the link to the sign-up form

- *`.wics`
    - respond with info about wics 

- *`.cssa`
    - respond with info about cssa 

- *`.devclub`
    - respond with info about devclub  

The content for the three above commands may need to be added to the bot manually (for formatting reasons)
 
### Admin Commands:

- `.setGreetMessage {message}`
    - set the message that displays when someone joins through the form

- `.colour add #{colour} {label}`
    - add the given colour for users to use with `.colour`
    - #{colour} must be a hex colour value  
    - {label} is what people type to change to this colour

- `.colour remove {colour}`
    - remove the given colour 

- `.autoassignrole`
    - temporary command for toggling the auto assignment of the student role.
    - will be removed once this is automatically done from the forum responses


### Event Commands:  
Can be used by any Exec
- *`.event prep "{title}" text:{n} voice:{n} -p`
    - title = Name of the event - must have quotes
    - text:n = number of text channels 
    - voice:n = number of voice channels 
    - -p (optional) = set the channels to public on creation 

- *`.event open` 
    - sets all event channels to public 

- *`.event close`
    - sets all event channels to private

- *`.event cleanup`
    - delete invite/channels related to the current event 

- *`.event invite` 
    - Generates a temporary invite that lasts until 12am the day of creation
    - If an invite is already generated, share that one again

- *`.event greeting {message}`
    - set the message that displays when someone joins with an event invite
