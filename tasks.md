- **Task 1**: Streamlit interface with voice recording that automatically detects 5-second pauses
- **Task 2**: FastAPI backend to receive and process audio files
- **Task 3**: Whisper model integration (tiny/small) for CPU-based speech-to-text transcription

### Task 4
Create a langchain agent. The user's voice input can either be a command or he is trying to add product. 
To find that, create a main agent with basic prompt.

### Task 5
Create first tool - find_command - Commands can be - open, close, up or down. Now, when user voices a text, if the text matches 90% with any of the listed command return that command

### Task 6
Create second tool - Add product - If user is trying to add the product, ask user to pronounce the brand name, product name, sales value and quantity

### Task 7
Create third tool - intend classificiation - check if user is trying to voice a command or trying to add a product

### Task 8
If user is trying to voice a command use the first tool, otherwise second tool. Connect this with fast api layer. 

### Task 9
Return the appropriate output to UI to show to the user

### Task 10

At this point, when user voices an input and waits for 5 seconds,
 - it should reach backend as audio via fastapi
 - it should get transcribed via whisper
 - transcribed text reaches the main agent
 - the main agent will perform intend classification
 - if the intend is command, it will find the command and return it to the user
 - if the intend is add product, get the product information and return it
 - Show the command or product info in UI


 ### Tasks 11
Create a tool to identify the voice text which neeeds to be returned to the user. For example: When user gives a command "Open", the tool should return the text - "Running Open command". Similary for addnig the product, it should identify the text using openai. This step is to sound the respone more like a human. Along with the text, perform text to speech and play the text as audio in the UI. 

At the end of this step, when user gives a command, the voice chatbot will talk back with the action. 