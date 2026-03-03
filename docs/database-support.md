# Database Support

- the database should be implemented with sqlalchemy. 
- The connection string to the database should be defined in a detenv file.
- the ENV variable should be DB_URL
- the database should losely (by losely I mean these can be adjusted as seen fit in order to accomodate the design requirements) contain the following tables / columns:
    * users: id, name, conversations
    * conversations: id, messages
    * messages: id, input text, output text, input tokens, output tokens, energy
    
- to support user functionality the extension should prompt for a login, to support this login use keycloak authentication
- make sure to document how keycloak should be configured to support the login
    * this includes documentation of the steps to setup the docker container that will run keycloak

- once logged in everytime a user sends a message in the chat a message should be recorded and this message should be tagged with a conversation and the conversation attached to a user.

- deppending on the conversation that the user is in (based on the URL) that conversation's message stats will be displayed on the graph that currently displays the file's data. 
    * remove the file display functionality and replace it with functionality to display the current conversation messages as datapoints on the graph.

- document all further setup requirements clear in a file docs/setup-requirements.md 

NOTE: remember to read through the source file before making any changes. Also if possible test the implementation itteratively.


## Energy From Messages

- the Y-axis displayed on the chart should reflect an estimation of the total energy cost of a input-text / output text message pair.

- this enery should be calculated by providing the model trained in ml-training with the input and output text and gathering the estimated energy from it's result.

- the energy should be calculated once and stored / retrived from the database after that.