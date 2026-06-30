import json
from openai import OpenAI

from poi_search import search_pois
from wikivoyage_rag import get_travel_context


def retrieve_guides(destination, query):
    return get_travel_context(destination, query)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_pois",
            "description": "Search points of interest",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string"
                    },
                    "interests": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": [
                    "city",
                    "interests"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_guides",
            "description": "Retrieve travel guide context",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string"
                    },
                    "query": {
                        "type": "string"
                    }
                },
                "required": [
                    "destination",
                    "query"
                ]
            }
        }
    }
]


def run_agent(
    api_key,
    city,
    interests,
    days
):

    client = OpenAI(api_key=api_key)

    state = {
        "pois": [],
        "guides": [],
        "city": city
    }

    messages = [
        {
            "role": "user",
            "content":
                f"""
                Create a {days}-day trip plan
                for {city}.
                Interests:
                {interests}
                """
        }
    ]

    MAX_STEPS = 5

    for _ in range(MAX_STEPS):

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content, state

        messages.append(msg)

        for tool_call in msg.tool_calls:

            name = tool_call.function.name

            args = json.loads(
                tool_call.function.arguments
            )

            if name == "search_pois":

                result = search_pois(
                    args["city"],
                    args["interests"]
                )

                state["pois"] = result

            elif name == "retrieve_guides":

                result = retrieve_guides(
                    args["destination"],
                    args["query"]
                )

                state["guides"] = result

            else:
                result = []

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id":
                        tool_call.id,
                    "content":
                        json.dumps(result)
                }
            )

    return "Maximum steps reached", state