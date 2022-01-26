# UManitobaCS-Discord-bot
A custom bot for the University of Manitoba's Computer Science Discord server. 


## todo.   


---

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
    - can use `all` in place of a category to be added to all notification roles

- `.unnotify {category}`
    - removes an announcement role from a user
    - can use `all` in place of a category to be removed from all notification roles

#### All users 
- `.form`
    - respond with the link to the sign-up form

- `.wics`
    - respond with info about wics 

- `.cssa`
    - respond with info about cssa 

- `.devclub`
    - respond with info about devclub  

- `.help`
    - help command

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


