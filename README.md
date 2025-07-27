# auraaa-demo
This is a demo repo for Agentic AI which has 3 sub agents works to summarize, question answer from the documents provided and realtime data extraction and question answering and to containarization of the app using docker.

# Steps to run this project
1. clone this repo or download and unzip it.

2. Start the docker desktop and run following command
  
    docker build -t auraa-agent-api .

    docker run -d -p 8000:8000 --env-file ./.env auraa-agent-api

3. open browser and hit this url http://127.0.0.1:8000/docs#/

4. to stop and remove the container

    to know container id : docker ps

    to stop : docker stop <containerid>

    to remove : docker rm <containerid>

# Main Route:   /process_query
# main agent query params
## example 1
{
  "user_prompt": "Summarize the given document and extract keywords. Artificial intelligence (AI) is intelligence demonstrated by machines, unlike the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of 'intelligent agents': any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. Colloquially, the term 'artificial intelligence' is often used to describe machines that mimic 'cognitive' functions that humans associate with the human mind, such as 'learning' and 'problem-solving'.\nAI applications include advanced web search engines (e.g., Google Search), recommendation systems (used by YouTube, Amazon, and Netflix), understanding human speech (such as Siri and Alexa), self-driving cars (e.g., Waymo), generative AI (e.g., ChatGPT, Midjourney), and competing at the highest level in strategic game systems (such as chess and Go).\nAs machines become increasingly capable, tasks considered to require 'intelligence' are often removed from the definition of AI, a phenomenon known as the AI effect. For instance, optical character recognition is frequently excluded from the definition of AI, having become a routine technology."
}
## Response
{
  "query": "Summarize the given document and extract keywords. Artificial intelligence (AI) is intelligence demonstrated by machines, unlike the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of 'intelligent agents': any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. Colloquially, the term 'artificial intelligence' is often used to describe machines that mimic 'cognitive' functions that humans associate with the human mind, such as 'learning' and 'problem-solving'.\nAI applications include advanced web search engines (e.g., Google Search), recommendation systems (used by YouTube, Amazon, and Netflix), understanding human speech (such as Siri and Alexa), self-driving cars (e.g., Waymo), generative AI (e.g., ChatGPT, Midjourney), and competing at the highest level in strategic game systems (such as chess and Go).\nAs machines become increasingly capable, tasks considered to require 'intelligence' are often removed from the definition of AI, a phenomenon known as the AI effect. For instance, optical character recognition is frequently excluded from the definition of AI, having become a routine technology.",
  "response": "Summary:\nArtificial intelligence (AI) refers to machine-based systems—“intelligent agents”—that perceive their environment and take actions to achieve goals, often mimicking human cognitive functions such as learning and problem-solving. AI powers technologies like web search engines, recommendation systems, speech assistants, self-driving cars, generative models (e.g., ChatGPT), and high-level game-playing. As capabilities advance, previously “intelligent” tasks (for example, optical character recognition) become routine and are no longer labeled AI, a phenomenon known as the AI effect.\n\nKeywords:\nartificial intelligence, AI, intelligent agents, machines, natural intelligence, cognitive functions, learning, problem-solving, web search engines, recommendation systems, speech recognition, self-driving cars, generative AI, ChatGPT, Midjourney, Siri, Alexa, Google Search, YouTube, Amazon, Netflix, Waymo, strategic game systems, chess, Go, AI effect, optical character recognition",
  "justification": "The `summarize_document` tool was chosen because the user specifically requested a concise summary of the provided text along with extracted keywords."
}

## Example 2
{
  "user_prompt": "Answer this question based on the following context: The capital of France is Paris. Paris is known for the Eiffel Tower. Tokyo is the capital of Japan and is famous for its cherry blossoms. The Amazon River is the largest river by discharge volume of water in the world. Question: What is Tokyo famous for?"

}

## response
{
  "query": "Answer this question based on the following context: The capital of France is Paris. Paris is known for the Eiffel Tower. Tokyo is the capital of Japan and is famous for its cherry blossoms. The Amazon River is the largest river by discharge volume of water in the world. Question: What is Tokyo famous for?",
  "response": "Tokyo is famous for its cherry blossoms.",
  "justification": "The ‘answer_query_from_documents’ tool was chosen because it efficiently retrieves precise answers directly from the provided context."
}

## Example 3
{
  "user_prompt": "What's the weather report in hyderabad ?"

}

## response
{
  "query": "What's the weather report in hyderabad ?",
  "response": "Here’s the latest available report for Hyderabad (as of 2025-07-28 00:00 IST):\n\nLocation  \n • Hyderabad, Telangana, India  \n • Local time: 2025-07-28 00:06  \n\nCurrent conditions  \n • Condition: Mist  \n • Temperature: 24.1 °C (75.4 °F)  \n • Feels like: 26.1 °C (79.0 °F)  \n • Humidity: 78%  \n • Visibility: 5 km (3 miles)  \n • Cloud cover: 25%  \n\nWind  \n • Speed: 17.9 mph (28.8 km/h) WSW  \n • Gusts up to: 26.5 mph (42.6 km/h)  \n\nPressure & precipitation  \n • Pressure: 1009 mb (29.8 in)  \n • Precipitation: 0.0 mm  \n\nSource: https://www.weatherapi.com/  \n\nIf you need a multi-day forecast or more details (sunrise/sunset, hourly breakdown, etc.), let me know!",
  "justification": "The `search_internet` tool was chosen to fetch the most current and accurate weather data for Hyderabad."
}


# AGent 1 query params
{
  "document_content": "Artificial intelligence (AI) is intelligence demonstrated by machines, unlike the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of 'intelligent agents': any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. Colloquially, the term 'artificial intelligence' is often used to describe machines that mimic 'cognitive' functions that humans associate with the human mind, such as 'learning' and 'problem-solving'.\nAI applications include advanced web search engines (e.g., Google Search), recommendation systems (used by YouTube, Amazon, and Netflix), understanding human speech (such as Siri and Alexa), self-driving cars (e.g., Waymo), generative AI (e.g., ChatGPT, Midjourney), and competing at the highest level in strategic game systems (such as chess and Go).\nAs machines become increasingly capable, tasks considered to require 'intelligence' are often removed from the definition of AI, a phenomenon known as the AI effect. For instance, optical character recognition is frequently excluded from the definition of AI, having become a routine technology."
}

## output response
{
  "doc_summary": "Artificial intelligence (AI) refers to machine-based “intelligent agents” that perceive their environment and take actions to maximize goal achievement, mimicking human cognitive functions such as learning and problem-solving. Common AI applications include web search, recommendation engines, speech recognition, self-driving cars, generative AI tools, and competitive game-playing systems. As AI advances, previously “intelligent” tasks—like optical character recognition—become routine and are dropped from the AI label, a phenomenon known as the AI effect.",
  "keywords": [
    "Artificial intelligence",
    "AI",
    "intelligent agents",
    "environment",
    "actions",
    "goals",
    "cognitive functions",
    "learning",
    "problem-solving",
    "web search engines",
    "recommendation systems",
    "speech recognition",
    "self-driving cars",
    "generative AI",
    "strategic game systems",
    "AI effect",
    "optical character recognition"
  ]
}


# AGent 2 query params
{
  "user_query": "what is the capital of france?",
  "documents_list": ["The capital of France is Paris. Paris is known for the Eiffel Tower.",
         "Tokyo is the capital of Japan and is famous for its cherry blossoms.",
         "The Amazon River is the largest river by discharge volume of water in the world."
  ]
}

## output response
{
  "query": "what is the capital of france?",
  "response": "The capital of France is Paris. (source: Document 1)"
}


# AGent 3 query params

{
  "user_query": "what is the match result of india vs england test ?"
}

## output response
{
  "query": "what is the match result of india vs england test ?",
  "response": "The Fourth Test at Old Trafford finished in a draw. India batted out the final day, ending on 425 for 4 (Jadeja 103* & Sundar 106*), and the match was called level.",
  "source": "https://www.bbc.co.uk/sport/cricket/live/crrzverk2xwt"
}




# All rights reserved for : udaya bhaskara raju patsamatla

# Email : udaybhaskar.patsamatla@gmail.com